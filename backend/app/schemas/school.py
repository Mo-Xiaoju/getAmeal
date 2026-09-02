"""学校相关 Schema。"""
from marshmallow import Schema, fields


class SchoolSchema(Schema):
    """学校信息。"""

    id = fields.Int()
    name = fields.Str()
    address = fields.Str()
    logo_url = fields.Str()
    shop_count = fields.Method('_shop_count')

    def _shop_count(self, obj) -> int:
        """该校下启用店铺数量。

        列表接口由 SchoolService 一次性聚合注入 context.shop_counts，避免逐校查询
        （3000+ 所学校时的 N+1 问题）；嵌套场景（如用户资料里的 school）未注入
        context 时回退为单条 count。
        """
        counts = getattr(self, 'context', None) or {}
        if counts:
            return counts.get(obj.id, 0)
        return obj.shops.filter_by(is_active=True).count()
