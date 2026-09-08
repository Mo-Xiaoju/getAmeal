import request from './request'

// 用户列表，params: { page, page_size }
export const getAdminUsers = (params) => request.get('/admin/users', { params })

// 变更用户角色/停用，data: { role?, is_active? }
export const updateUser = (userId, data) => request.put(`/admin/users/${userId}`, data)

// ---- 内容审核（学生提交的店铺 / 菜品）----
// 店铺审核队列，params: { status, page, page_size }，status 默认 pending
export const getAuditShops = (params) => request.get('/admin/audits/shops', { params })
// 菜品审核队列（父店已通过的待审菜品），params 同上
export const getAuditDishes = (params) => request.get('/admin/audits/dishes', { params })
// 审核单家店铺，data: { action: 'approve'|'reject', reason? }
export const reviewShop = (shopId, data) => request.post(`/admin/audits/shops/${shopId}/review`, data)
// 整店审核：店铺与其全部待审菜品一并通过/驳回
export const bulkReviewShop = (shopId, data) => request.post(`/admin/audits/shops/${shopId}/bulk`, data)
// 审核单道菜品，data: { action, reason? }
export const reviewDish = (dishId, data) => request.post(`/admin/audits/dishes/${dishId}/review`, data)
