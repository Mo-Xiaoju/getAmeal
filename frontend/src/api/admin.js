import request from './request'

// ========== 用户管理 ==========
export const getAdminUsers = (params) => request.get('/admin/users', { params })
export const updateUser = (userId, data) => request.put(`/admin/users/${userId}`, data)

// ========== 店铺管理 ==========
export const getAdminShops = (params) => request.get('/admin/shops', { params })
export const addShop = (data) => request.post('/admin/shops', data)
export const updateShop = (shopId, data) => request.put(`/admin/shops/${shopId}`, data)
export const deleteShop = (shopId) => request.delete(`/admin/shops/${shopId}`)
