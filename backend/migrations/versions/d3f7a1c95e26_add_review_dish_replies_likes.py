"""add review dish/replies/likes

Revision ID: d3f7a1c95e26
Revises: b7f2c9a41d38
Create Date: 2026-09-11 17:00:00.000000

本仓库**手写**迁移，不要用 `flask db migrate` 自动生成：`posts.shop_id` 在模型里是
nullable=False 而在 caeb7ab3fc4e 里是 nullable=True，autogenerate 已经不可信。

三件事：
1. reviews 关联菜品（可空）+ 点赞数 —— 菜品详情页据此展示「菜品评价」。
2. comments 从「仅笔记评论」扩展为「笔记评论 + 评价回复」共用表（多态惯用法同 favorites），
   并支持两层回复。
3. likes 从「仅笔记点赞」扩展为「笔记 + 评价」；新增 comment_likes 覆盖评论/回复点赞。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3f7a1c95e26'
down_revision = 'b7f2c9a41d38'
branch_labels = None
depends_on = None


def upgrade():
    # ---- 1. reviews：关联菜品（可空 = 纯店铺评价）+ 点赞数 ----
    #
    # 「加列」与「去掉 server_default」必须分成两个 batch 块。
    # SQLite 上 batch_alter_table 靠建临时表 + INSERT ... SELECT 重建，而 INSERT 的列
    # 只列新旧表都有的那些：新列的值只能靠临时表上的 DEFAULT 兜住。所以在同一个块里
    # 先把 server_default 抹掉，重建时就没人给 like_count 兜底了 —— 直接 NOT NULL 失败
    # （实测：NOT NULL constraint failed: _alembic_tmp_reviews.like_count）。
    # MySQL 不重建表、逐句 ALTER 也能过，但拆开后两边都对，没理由留这个坑。
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dish_id', sa.Integer(), nullable=True))
        # NOT NULL 加列必须带 server_default，否则已有数据的表在严格模式下报 1364
        batch_op.add_column(sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('reviews', schema=None) as batch_op:
        # 去掉 server_default，使最终 DDL 与模型（客户端 default=0）一致
        batch_op.alter_column('like_count', existing_type=sa.Integer(),
                              existing_nullable=False, server_default=None)
        # 先显式建索引再建外键：否则 MySQL 会隐式造一个以约束名命名的索引，
        # downgrade 时删不掉、留垃圾。索引名与模型的 index=True 保持一致。
        batch_op.create_index('ix_reviews_dish_id', ['dish_id'], unique=False)
        batch_op.create_foreign_key('fk_reviews_dish', 'dishes', ['dish_id'], ['id'])

    # ---- 2. comments：笔记评论 + 评价回复共用表 ----
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('review_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('reply_to_user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'))

    with op.batch_alter_table('comments', schema=None) as batch_op:
        # 同上：server_default 单独一轮才抹
        batch_op.alter_column('like_count', existing_type=sa.Integer(),
                              existing_nullable=False, server_default=None)
        # NOT NULL → NULL 是 INPLACE 的元数据变更，既有外键/索引无需先删。
        # 存量行 post_id 已填、新列全 NULL，正是「笔记评论」的形态，不需要数据迁移。
        batch_op.alter_column('post_id', existing_type=sa.Integer(), nullable=True)
        batch_op.create_index('ix_comments_review_id', ['review_id'], unique=False)
        batch_op.create_index('ix_comments_parent_id', ['parent_id'], unique=False)
        batch_op.create_foreign_key('fk_comments_review', 'reviews', ['review_id'], ['id'])
        batch_op.create_foreign_key('fk_comments_parent', 'comments', ['parent_id'], ['id'])
        batch_op.create_foreign_key('fk_comments_reply_to_user', 'users', ['reply_to_user_id'], ['id'])

    # ---- 3. likes：笔记赞 + 评价赞 ----
    # 新增列全为 NULL，加唯一约束不会与存量行冲突（MySQL 唯一索引视多个 NULL 互不相同）。
    with op.batch_alter_table('likes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('review_id', sa.Integer(), nullable=True))
        batch_op.alter_column('post_id', existing_type=sa.Integer(), nullable=True)
        batch_op.create_index('ix_likes_review_id', ['review_id'], unique=False)
        batch_op.create_unique_constraint('uq_like_user_review', ['user_id', 'review_id'])
        batch_op.create_foreign_key('fk_likes_review', 'reviews', ['review_id'], ['id'])

    # ---- 4. comment_likes：评论/回复点赞（被赞对象同表，无需多态）----
    op.create_table(
        'comment_likes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_comment_likes_user'),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], name='fk_comment_likes_comment'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'comment_id', name='uq_comment_like_user_comment'),
    )
    # 唯一索引是 (user_id, comment_id)，按最左前缀服务不了 WHERE comment_id IN (...)，
    # 所以点赞数累加/批量清除还需要一个单独的 comment_id 索引。
    op.create_index('ix_comment_likes_comment_id', 'comment_likes', ['comment_id'], unique=False)


def downgrade():
    # 回退会丢弃「评价回复」与「评价点赞」——这两类行 post_id 为空，无法回到旧结构。
    # 顺序是关键：先断外键 → 再删无处可去的行 → 最后才把 post_id 改回 NOT NULL。
    # 反过来会在 MySQL 严格模式报 1048（宽松模式会静默写 0，留下悬空引用）。
    op.drop_table('comment_likes')  # 先断掉它到 comments 的外键

    with op.batch_alter_table('comments', schema=None) as batch_op:
        # 自引用外键必须先解开，否则删父行时子行还在引用它（1451）
        batch_op.drop_constraint('fk_comments_parent', type_='foreignkey')
        batch_op.drop_constraint('fk_comments_review', type_='foreignkey')
        batch_op.drop_constraint('fk_comments_reply_to_user', type_='foreignkey')
    op.execute(sa.text('DELETE FROM comments WHERE post_id IS NULL'))

    with op.batch_alter_table('comments', schema=None) as batch_op:
        # 先删索引再删列：MySQL 拒绝删除外键正在使用的索引（1553），
        # 上面的外键已经断掉，这里的顺序是「外键 → 索引 → 列」的最后一段
        batch_op.drop_index('ix_comments_parent_id')
        batch_op.drop_index('ix_comments_review_id')
        batch_op.drop_column('reply_to_user_id')
        batch_op.drop_column('parent_id')
        batch_op.drop_column('review_id')
        batch_op.drop_column('like_count')
        batch_op.alter_column('post_id', existing_type=sa.Integer(), nullable=False)

    op.execute(sa.text('DELETE FROM likes WHERE post_id IS NULL'))
    with op.batch_alter_table('likes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_likes_review', type_='foreignkey')
        batch_op.drop_constraint('uq_like_user_review', type_='unique')
        batch_op.drop_index('ix_likes_review_id')
        batch_op.drop_column('review_id')
        batch_op.alter_column('post_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.drop_constraint('fk_reviews_dish', type_='foreignkey')
        batch_op.drop_index('ix_reviews_dish_id')
        batch_op.drop_column('like_count')
        batch_op.drop_column('dish_id')
