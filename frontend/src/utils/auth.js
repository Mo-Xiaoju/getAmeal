// token 与学校选择的存取工具。
//
// 为什么用 sessionStorage 而不用 localStorage：
//   localStorage 是同源所有标签页共享 —— A 标签页登录账号A、B 标签页再登录账号B，
//   会把共享 token 覆盖成 B，A 标签页下一次请求就被"顶号"。
//   同浏览器双开不同账号需要的是标签页级隔离，这正是 sessionStorage 的语义：
//   每个标签页各自持有一份 token/学校，互不覆盖。
// 取舍：登录态跟随标签页生命周期 —— 刷新/路由跳转仍在，关闭标签页后需重新登录。
const TOKEN_KEY = 'campus_food_token'
const SCHOOL_KEY = 'campus_food_school'

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  sessionStorage.removeItem(TOKEN_KEY)
}

// ---- 学校上下文（跟随账号生命周期，登出/失效即清除，避免残留给下一个账号） ----

export function getSchool() {
  try {
    return JSON.parse(sessionStorage.getItem(SCHOOL_KEY) || 'null')
  } catch (e) {
    return null
  }
}

export function setSchool(school) {
  if (school) {
    sessionStorage.setItem(SCHOOL_KEY, JSON.stringify(school))
  } else {
    sessionStorage.removeItem(SCHOOL_KEY)
  }
}

export function removeSchool() {
  sessionStorage.removeItem(SCHOOL_KEY)
}
