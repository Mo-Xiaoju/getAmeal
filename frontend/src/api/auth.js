import request from './request'

// 登录，data: { username, password }
export const login = (data) => request.post('/auth/login', data)

// 注册，data: { username, password, nickname }
export const register = (data) => request.post('/auth/register', data)

// 登出
export const logout = () => request.post('/auth/logout')

// 获取当前用户信息
export const fetchMe = () => request.get('/auth/me')

// 更新当前用户信息，data: { nickname, avatar_url }
export const updateMe = (data) => request.put('/auth/me', data)

// 修改密码，data: { old_password, new_password }
export const changePassword = (data) => request.put('/auth/password', data)
