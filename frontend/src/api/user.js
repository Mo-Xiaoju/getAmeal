import request from './request'

// 获取个人信息
export const getProfile = () => request.get('/user/profile')

// 更新个人信息，data: { nickname, avatar_url }
export const updateProfile = (data) => request.put('/user/profile', data)

// 我的收藏列表（店铺/笔记），params: { type: shop|post|all, page, page_size }
export const getFavorites = (params) => request.get('/user/favorites', { params })

// 我的点赞列表，params: { page, page_size }
export const getMyLikes = (params) => request.get('/user/likes', { params })

// 我的浏览记录（店铺/菜品/笔记），params: { type: shop|dish|post|all, page, page_size }
export const getViewHistory = (params) => request.get('/user/history', { params })

// 我的评价列表，params: { page, page_size }
export const getMyReviews = (params) => request.get('/user/reviews', { params })

// 删除我的某条评价
export const deleteReview = (reviewId) => request.delete(`/user/reviews/${reviewId}`)

// 他人公开主页资料（游客可见；带登录态时 data.is_following 生效）
export const getUserProfile = (userId) => request.get(`/user/${userId}/profile`)
