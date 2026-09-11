"""add shop zone

Revision ID: b7f2c9a41d38
Revises: 975e70c5b52e
Create Date: 2026-09-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7f2c9a41d38'
down_revision = '975e70c5b52e'
branch_labels = None
depends_on = None


def upgrade():
    # 大分类：校内/周边/外卖，受控词表见 app.categories.ZONES。
    # 可空且**不回溯推断**存量行——地址是自由文本，猜错会把店标到错误的区域，
    # 留 NULL 由商户/管理员在表单里补，前端对空值不渲染角标。
    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.add_column(sa.Column('zone', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('shops', schema=None) as batch_op:
        batch_op.drop_column('zone')
