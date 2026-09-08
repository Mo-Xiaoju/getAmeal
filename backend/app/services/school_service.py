"""学校业务逻辑。"""
from sqlalchemy import func

from app.extensions import db
from app.models import School, Shop
from app.schemas.school import SchoolSchema
from app.services.shop_service import ShopService
from app.utils.exceptions import NotFoundError


class SchoolService:
    """学校列表与校内店铺。"""

    @staticmethod
    def list_schools() -> list:
        """启用中的学校列表（带店铺数量，聚合查询避免 N+1）。"""
        schools = School.query.filter_by(is_active=True).order_by(School.id).all()
        shop_counts = dict(
            db.session.query(Shop.school_id, func.count(Shop.id))
            .filter(Shop.is_active.is_(True), Shop.status == 'approved')
            .group_by(Shop.school_id)
            .all()
        )
        schema = SchoolSchema(many=True)
        schema.context = {'shop_counts': shop_counts}  # marshmallow 4 通过实例属性注入 context
        return schema.dump(schools)

    @classmethod
    def get_shops_of_school(cls, school_id: int, params: dict) -> dict:
        """某学校下的店铺列表（分页）。"""
        school = School.query.get(school_id)
        if school is None or not school.is_active:
            raise NotFoundError(message='学校不存在', code=4041)
        return ShopService.list_shops({**params, 'school_id': school_id})
