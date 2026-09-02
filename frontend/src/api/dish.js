import request from './request'

// 店铺下的菜品列表，params: { page, page_size }
export const getShopDishes = (shopId, params) => request.get(`/shops/${shopId}/dishes`, { params })

// 菜品列表（可选 school_id / shop_id 过滤、分页）
export const getDishList = (params) => request.get('/dishes', { params })

// 推荐菜品，params: { school_id, limit }
export const getDishRecommend = (params) => request.get('/dishes/recommend', { params })

// 菜品详情
export const getDishDetail = (dishId) => request.get(`/dishes/${dishId}`)
