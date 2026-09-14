import request from './request'

// ---- 商户：我的店铺 ----
export const getMyShops = (params) => request.get('/merchant/shops', { params })
export const createShop = (data) => request.post('/merchant/shops', data)
export const updateShop = (shopId, data) => request.put(`/merchant/shops/${shopId}`, data)
export const deleteShop = (shopId) => request.delete(`/merchant/shops/${shopId}`)

// ---- 商户：认领未入驻店铺（提交申请，需管理员审核）----
export const getClaimableShops = (params) => request.get('/merchant/shops/claimable', { params })
// 提交认领申请，data: { reason? }；审核通过后店铺才归到自己名下
export const applyClaim = (shopId, data) => request.post(`/merchant/shops/${shopId}/claim`, data)
// 我的认领申请列表（含审核状态与驳回原因）
export const getMyClaims = (params) => request.get('/merchant/claims', { params })
// 撤回待审的认领申请
export const cancelClaim = (claimId) => request.delete(`/merchant/claims/${claimId}`)

// ---- 商户：店铺菜单 ----
export const getShopDishes = (shopId, params) => request.get(`/merchant/shops/${shopId}/dishes`, { params })
export const createDish = (shopId, data) => request.post(`/merchant/shops/${shopId}/dishes`, data)
export const updateDish = (dishId, data) => request.put(`/merchant/dishes/${dishId}`, data)
export const deleteDish = (dishId) => request.delete(`/merchant/dishes/${dishId}`)
