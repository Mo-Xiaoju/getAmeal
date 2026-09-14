"""平均分增量维护。

同一套增量公式原先在 ShopService.add_review / delete_review 和 cli.py 的
seed-rec-demo 里各抄了一遍；现在评价可以同时挂在店铺和菜品上，抄第四遍必然会漂移，
所以抽到这里共用。只要求目标对象有 avg_rating / rating_count 两个属性（Shop 或 Dish）。

保留浮点全精度、输出时才四舍五入，避免反复加减产生误差累积。
"""


def apply_rating(target, rating: int) -> None:
    """把一条新评分并入目标的平均分。"""
    target.rating_count += 1
    target.avg_rating = (target.avg_rating * (target.rating_count - 1) + rating) / target.rating_count


def revert_rating(target, rating: int) -> None:
    """apply_rating 的逆向：从平均分里撤掉一条评分。"""
    if target.rating_count > 1:
        target.rating_count -= 1
        target.avg_rating = (target.avg_rating * (target.rating_count + 1) - rating) / target.rating_count
    else:
        target.rating_count = 0
        target.avg_rating = 0.0
