"""菜品相关 Schema。"""
from marshmallow import EXCLUDE, Schema, fields


class DishSchema(Schema):
    """菜品信息。"""

    id = fields.Int()
    shop_id = fields.Int()
    shop_name = fields.Method('_shop_name')
    name = fields.Str()
    price = fields.Function(lambda obj: float(obj.price or 0))
    description = fields.Str()
    image_url = fields.Str()
    tags = fields.Method('_tags')
    avg_rating = fields.Function(lambda obj: round(obj.avg_rating or 0.0, 2))
    rating_count = fields.Int()
    status = fields.Str()  # approved / pending / rejected

    def _shop_name(self, obj) -> str:
        return obj.shop.name if obj.shop else None

    def _tags(self, obj) -> list:
        return [t for t in (obj.tags or '').split(',') if t]


class DishCreateSchema(Schema):
    """新增菜品请求。"""

    name = fields.Str(required=True)
    price = fields.Float(required=True)
    description = fields.Str(load_default=None)
    image_url = fields.Str(load_default=None)
    tags = fields.List(fields.Str(), load_default=[])

    class Meta:
        unknown = EXCLUDE


class DishUpdateSchema(Schema):
    """修改菜品请求。"""

    name = fields.Str()
    price = fields.Float()
    description = fields.Str()
    image_url = fields.Str()
    tags = fields.List(fields.Str())

    class Meta:
        unknown = EXCLUDE
