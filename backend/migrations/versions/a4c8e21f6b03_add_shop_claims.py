"""add shop_claims

商户认领已有店铺改为「提交申请 → 管理员审核」，需要一张独立的申请表。
刻意不复用 shops.status：那是内容审核（决定店铺是否公开），认领只决定归属，
混用会让一次归属权审批把店铺从公开列表下架。

Revision ID: a4c8e21f6b03
Revises: d3f7a1c95e26
Create Date: 2026-09-14 10:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4c8e21f6b03'
down_revision = 'd3f7a1c95e26'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('shop_claims',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('applicant_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
    sa.Column('reason', sa.String(length=500), nullable=True),
    sa.Column('review_reason', sa.String(length=500), nullable=True),
    sa.Column('reviewed_by', sa.Integer(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
    sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('shop_claims', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_shop_claims_shop_id'), ['shop_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_shop_claims_applicant_id'), ['applicant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_shop_claims_reviewed_by'), ['reviewed_by'], unique=False)
        batch_op.create_index(batch_op.f('ix_shop_claims_status'), ['status'], unique=False)


def downgrade():
    # 直接删表即可：索引与外键随表一起消失。
    # 刻意不逐个 drop_index——三个 ix_* 索引同时被外键 shop_claims_ibfk_* 依赖，
    # MySQL 会以 1553「Cannot drop index needed in a foreign key constraint」拒绝，
    # 且 MySQL 的 DDL 非事务性，中途失败会留下删了一半索引的残表。
    op.drop_table('shop_claims')
