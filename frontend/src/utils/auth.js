// token 与学校选择的存取工具（localStorage）
const TOKEN_KEY = 'campus_food_token'
const SCHOOL_KEY = 'campus_food_school'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

// ---- 学校上下文（跟随账号生命周期，登出/失效即清除，避免残留给下一个账号） ----

export function getSchool() {
  try {
    return JSON.parse(localStorage.getItem(SCHOOL_KEY) || 'null')
  } catch (e) {
    return null
  }
}

export function setSchool(school) {
  if (school) {
    localStorage.setItem(SCHOOL_KEY, JSON.stringify(school))
  } else {
    localStorage.removeItem(SCHOOL_KEY)
  }
}

export function removeSchool() {
  localStorage.removeItem(SCHOOL_KEY)
}
