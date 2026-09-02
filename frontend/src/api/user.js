import request from './request'

// 获取个人信息
export const getProfile = () => request.get('/user/profile')

// 更新个人信息，data: { nickname, avatar_url }
export const updateProfile = (data) => request.put('/user/profile', data)

// 我的收藏列表，params: { page, page_size }
export const getFavorites = (params) => request.get('/user/favorites', { params })

// 我的评价列表，params: { page, page_size }
export const getMyReviews = (params) => request.get('/user/reviews', { params })

// 删除我的某条评价
export const deleteReview = (reviewId) => request.delete(`/user/reviews/${reviewId}`)
