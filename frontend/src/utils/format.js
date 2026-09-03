// 时间显示工具：消息列表 / 会话列表共用
function pad(n) {
  return n < 10 ? `0${n}` : `${n}`
}

// 'YYYY-MM-DD HH:mm'（后端返回 UTC，需转本地）
export function formatDateTime(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 会话列表时间：今天只显时分，昨天显「昨天」，更早显日期
export function formatConversationTime(value) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const startOfDay = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  if (startOfDay === startOfToday) {
    return `${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  if (startOfDay === startOfToday - 86400000) return '昨天'
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
