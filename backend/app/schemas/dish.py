"""菜品相关 Schema。"""
import json

from marshmallow import EXCLUDE, Schema, fields


class DishSchema(Schema):
    """菜品信息。"""

    id = fields.Int()
    shop_id = fields.Int()
    shop_name = fields.Method('_shop_name')
    name = fields.Str()
    price = fields.Function(lambda obj: float(obj.price or 0))
    description = fields.Str()
    image_url = fields.Method('_cover_url')  # 封面 = 图集第一张（兼容单图读取端）
    images = fields.Method('_images')  # 完整图集（JSON 数组列解析）
    tags = fields.Method('_tags')
    avg_rating = fields.Function(lambda obj: round(obj.avg_rating or 0.0, 2))
    rating_count = fields.Int()
    status = fields.Str()  # approved / pending / rejected
    reject_reason = fields.Str()  # 驳回原因（仅供提交者/审核端回显）

    def _shop_name(self, obj) -> str:
        return obj.shop.name if obj.shop else None

    def _tags(self, obj) -> list:
        return [t for t in (obj.tags or '').split(',') if t]

    def _images(self, obj) -> list:
        """图集：优先解析 images JSON；历史行（仅 image_url）回退为单图列表。"""
        try:
            imgs = json.loads(obj.images) if obj.images else None
        except (TypeError, ValueError):
            imgs = None
        if isinstance(imgs, list) and imgs:
            return imgs
        return [obj.image_url] if obj.image_url else []

    def _cover_url(self, obj):
        imgs = self._images(obj)
        return imgs[0] if imgs else None


class DishCreateSchema(Schema):
    """新增菜品请求。"""

    name = fields.Str(required=True)
    price = fields.Float(required=True)
    description = fields.Str(load_default=None)
    image_url = fields.Str(load_default=None)
    # 不带 load_default：请求未带 images 则不涉及图集；显式传 [] 表示清空
    images = fields.List(fields.Str())
    tags = fields.List(fields.Str(), load_default=[])

    class Meta:
        unknown = EXCLUDE


class DishUpdateSchema(Schema):
    """修改菜品请求。"""

    name = fields.Str()
    price = fields.Float()
    description = fields.Str()
    image_url = fields.Str()
    # 不带 load_default：请求未带 images 则不涉及图集（部分更新不动图）；显式传 [] 表示清空
    images = fields.List(fields.Str())
    tags = fields.List(fields.Str())

    class Meta:
        unknown = EXCLUDE
