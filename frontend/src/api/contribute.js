import request from './request'

// ---- 学生提交商户/菜单 ----
// 我的提交
export const getMyContributions = (params) => request.get('/contribute/my', { params })
// 提交店铺
export const submitShop = (data) => request.post('/contribute/shops', data)
export const updateSubmittedShop = (shopId, data) => request.put(`/contribute/shops/${shopId}`, data)
export const deleteSubmittedShop = (shopId) => request.delete(`/contribute/shops/${shopId}`)
// 给提交的店铺添加菜单
export const submitDish = (shopId, data) => request.post(`/contribute/shops/${shopId}/dishes`, data)
export const updateSubmittedDish = (dishId, data) => request.put(`/contribute/dishes/${dishId}`, data)
export const deleteSubmittedDish = (dishId) => request.delete(`/contribute/dishes/${dishId}`)
