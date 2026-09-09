"""add dish multi images

Revision ID: e2c8a4d6b1f3
Revises: 701f22793f98
Create Date: 2026-09-09 12:00:00.000000

"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2c8a4d6b1f3'
down_revision = '701f22793f98'
branch_labels = None
depends_on = None


def upgrade():
    # 新增图集列（Text 存 JSON 数组），保留 image_url 作为封面兼容旧数据
    op.add_column('dishes', sa.Column('images', sa.Text(), nullable=True))

    # 历史数据回填：把已有单图 image_url 作为该菜品的首图，避免后续“未改图也误判变更”
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, image_url FROM dishes WHERE image_url IS NOT NULL AND image_url <> ''")
    ).fetchall()
    for dish_id, image_url in rows:
        conn.execute(
            sa.text("UPDATE dishes SET images = :imgs WHERE id = :id"),
            {'imgs': json.dumps([image_url], ensure_ascii=False), 'id': dish_id},
        )


def downgrade():
    op.drop_column('dishes', 'images')
