import request from './request'

// ---- 商户：我的店铺 ----
export const getMyShops = (params) => request.get('/merchant/shops', { params })
export const createShop = (data) => request.post('/merchant/shops', data)
export const updateShop = (shopId, data) => request.put(`/merchant/shops/${shopId}`, data)
export const deleteShop = (shopId) => request.delete(`/merchant/shops/${shopId}`)

// ---- 商户：认领未入驻店铺 ----
export const getClaimableShops = (params) => request.get('/merchant/shops/claimable', { params })
export const claimShop = (shopId) => request.post(`/merchant/shops/${shopId}/claim`)

// ---- 商户：店铺菜单 ----
export const getShopDishes = (shopId, params) => request.get(`/merchant/shops/${shopId}/dishes`, { params })
export const createDish = (shopId, data) => request.post(`/merchant/shops/${shopId}/dishes`, data)
export const updateDish = (dishId, data) => request.put(`/merchant/dishes/${dishId}`, data)
export const deleteDish = (dishId) => request.delete(`/merchant/dishes/${dishId}`)
