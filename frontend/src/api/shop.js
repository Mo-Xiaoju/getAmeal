import request from './request'

// 店铺列表，params: { keyword, category, zone, sort, page, page_size, longitude, latitude }
export const getShopList = (params) => request.get('/shops', { params })

// 店铺规范分类列表（表单下拉 / 筛选取值）
export const getCategories = () => request.get('/shops/categories')

// 店铺大分类词表（校内/周边/外卖，表单下拉 / 筛选取值）
export const getZones = () => request.get('/shops/zones')

// 推荐店铺，params: { longitude, latitude, page, page_size }
export const getRecommend = (params) => request.get('/shops/recommend', { params })

// 店铺详情
export const getShopDetail = (shopId) => request.get(`/shops/${shopId}`)

// 店铺评价列表，params: { page, page_size }
export const getShopReviews = (shopId, params) => request.get(`/shops/${shopId}/reviews`, { params })

// 发表评价，data: { rating, content, images }
export const addReview = (shopId, data) => request.post(`/shops/${shopId}/reviews`, data)

// 收藏店铺
export const addFavorite = (shopId) => request.post(`/shops/${shopId}/favorite`)

// 取消收藏
export const removeFavorite = (shopId) => request.delete(`/shops/${shopId}/favorite`)
