"""店铺分类规范化的唯一事实来源（受控词表 + 别名归一 + 粗粒度族）。

背景：`Shop.category` 曾是自由文本，推荐引擎的"分类偏好"依赖归一化后的精确匹配，
同物异名（奶茶 ≈ 奶茶饮品）会让画像与候选对不上号、个性化静默失效。
这里收敛成三层口径，读路径宽容、写路径严格：

- `CATEGORIES`：前端下拉 / 后端白名单 / 落库展示 的规范值（原地覆盖 `category`）。
- `ALIASES`：读路径别名表，把历史或他方写入的异名归一成规范值（如 奶茶饮品→奶茶）。
- `FAMILIES`：粗粒度族，仅供推荐引擎在精确 miss 时做弱兜底（同族其它成员 ×0.5），
  不改变落库值与展示。

另有一个更粗的**大分类**词表 `ZONES`（校内/周边/外卖，落库 `Shop.zone`），用于店铺卡片
的角标：它是三个固定值的封闭枚举，没有别名与族，故只有归一（读）+ 校验（写）两个函数。
注意它不纯是位置口径——前两项分位置，第三项分经营方式（校外配送），三者互斥、用户单选一个。

改动历史词表只须改本文件：`flask normalize-categories`（存量回填 + 熵审计报告）与
推荐引擎、店铺浏览过滤、写入口白名单均读这里。
"""
from typing import Optional

from app.utils.exceptions import ValidationError

# 规范分类（下拉展示顺序 = 本列表顺序）。快餐暂无现库存量行，属备选词表，可删。
CATEGORIES = [
    '食堂', '小吃', '快餐', '面食', '火锅', '烧烤', '冒菜', '川菜', '轻食',
    '奶茶', '咖啡甜点', '烘焙甜点', '甜品', '茶餐厅', '美食广场',
]
CATEGORY_SET = frozenset(CATEGORIES)

# 别名表：归一 key（strip+lower 后）→ 规范分类。同物异名在此归并。
ALIASES = {
    '奶茶饮品': '奶茶',   # 设计文档 §风险 明示的 奶茶≈奶茶饮品
    '奶盖茶': '奶茶',
    '麻辣烫': '冒菜',     # 校园档口常同指冒菜/麻辣烫
}

# 粗粒度族：仅推荐引擎兜底用，不落库。family_of() 返回整组（含自身）。
FAMILIES = {
    '甜点饮品': ('咖啡甜点', '烘焙甜点', '甜品'),
}

# 大分类：落库 `Shop.zone`，店铺卡片右上角角标展示的就是它。
# 与 CATEGORIES 的区别是「在哪买/怎么买」而不是「卖什么」，三值封闭枚举，无别名/族。
ZONES = ['校内', '周边', '外卖']
ZONE_SET = frozenset(ZONES)


def canonicalize(raw) -> str:
    """读路径归一（宽容）：None/空→''；否则 strip+lower → 别名 → 原样返回。

    非规范值不报错、按原样返回，由调用方自然降级（画像/候选查不到即 0 分）。
    """
    if raw is None:
        return ''
    key = str(raw).strip().lower()
    if not key:
        return ''
    return ALIASES.get(key, key)


def coerce_category(raw) -> Optional[str]:
    """写路径校验（严格）：空→None；非空须经别名归入 CATEGORIES，否则 400。

    供店铺创建/修改、管理员归类接口调用，保证落库值永远规范。
    """
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    value = canonicalize(raw)
    if value not in CATEGORY_SET:
        raise ValidationError(
            message=f'分类必须为可选值之一：{" / ".join(CATEGORIES)}', code=4000
        )
    return value


def normalize_category_payload(data: dict) -> dict:
    """把 schema.load 后的 dict 中 category 字段就地规范（含字段置空）。

    通常不直接调用，改用 normalize_shop_payload 一并处理 zone。
    """
    if 'category' not in data:
        return data
    data['category'] = coerce_category(data.get('category'))
    return data


def canonicalize_zone(raw) -> str:
    """大分类读路径归一（宽容）：None/空→''；否则 strip 后原样返回。

    不复用 canonicalize()：后者带 lower() 与 ALIASES 查表，那是细分分类的语义，
    对三值封闭枚举反而会引入误命中。非规范值不报错，筛不到即自然降级。
    """
    if raw is None:
        return ''
    return str(raw).strip()


def coerce_zone(raw) -> Optional[str]:
    """大分类写路径校验（严格）：空→None；非空须 ∈ ZONES，否则 400。

    供店铺创建/修改调用，保证落库值永远规范（角标色值映射依赖它）。
    """
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    value = str(raw).strip()
    if value not in ZONE_SET:
        raise ValidationError(
            message=f'大分类必须为可选值之一：{" / ".join(ZONES)}', code=4000
        )
    return value


def normalize_zone_payload(data: dict) -> dict:
    """把 schema.load 后的 dict 中 zone 字段就地规范（含字段置空）。"""
    if 'zone' not in data:
        return data
    data['zone'] = coerce_zone(data.get('zone'))
    return data


def normalize_shop_payload(data: dict) -> dict:
    """店铺写路径的统一入口：一次规范 category 与 zone。

    4 个店铺写方法共用：MerchantService/ContributeService 的 create/update。
    """
    data = normalize_category_payload(data)
    return normalize_zone_payload(data)


def family_of(canonical) -> tuple:
    """返回该规范分类所属粗粒度族（含自身）；无族返回空元组。"""
    for members in FAMILIES.values():
        if canonical in members:
            return members
    return ()
