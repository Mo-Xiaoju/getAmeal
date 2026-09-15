// 人均区间工具：全站只允许「整数-整数元」一种落库格式（如 '10-20元'）。
// 读取时放宽（兼容 '10-20'、'10 ~ 20 元' 等历史写法），写入时收紧到唯一格式，
// 保证传给后端的 price_range 一定是一个整数区间，而不是自由文本。
export const PRICE_MIN = 0
export const PRICE_MAX = 9999

const PRICE_RANGE_RE = /^(\d{1,4})\s*[-~—]\s*(\d{1,4})\s*元?$/

// 空区间（两端都未填）——人均是选填项，合法
export function isEmptyPriceRange(range) {
  return toInt(range?.min) === null && toInt(range?.max) === null
}

// 字符串 → { min, max }；无法识别一律返回空区间（调用方据此提示/回填）
export function parsePriceRange(value) {
  const m = PRICE_RANGE_RE.exec(String(value || '').trim())
  if (!m) return { min: null, max: null }
  return { min: Number(m[1]), max: Number(m[2]) }
}

// { min, max } → '10-20元'；半填 / 越界 / 倒挂一律返回 ''（宁可不发，也不写非法区间）
export function formatPriceRange(range) {
  const min = toInt(range?.min)
  const max = toInt(range?.max)
  if (min === null || max === null) return ''
  if (min < PRICE_MIN || max > PRICE_MAX || min > max) return ''
  return `${min}-${max}元`
}

// 硬性约束的判定口径：空区间合法；其余必须能格式化出完整整数区间
export function isValidPriceRange(range) {
  return isEmptyPriceRange(range) || formatPriceRange(range) !== ''
}

// 归一化为整数或 null：小数截断，空串 / 非数字视为未填
function toInt(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? Math.trunc(n) : null
}
