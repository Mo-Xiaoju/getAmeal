import request from './request'

// 用户列表，params: { page, page_size }
export const getAdminUsers = (params) => request.get('/admin/users', { params })

// 变更用户角色/停用，data: { role?, is_active? }
export const updateUser = (userId, data) => request.put(`/admin/users/${userId}`, data)
