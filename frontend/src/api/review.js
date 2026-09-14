import request from './request'

// 评价的点赞 / 回复。评价本身的发表与列表在 api/shop.js（POST/GET /shops/<id>/reviews）

// 点赞/取消点赞评价
export const toggleReviewLike = (reviewId) => request.post(`/reviews/${reviewId}/like`)

// 评价的回复列表，params: { page, page_size }
export const getReviewReplies = (reviewId, params) =>
  request.get(`/reviews/${reviewId}/replies`, { params })

// 回复评价；回复某条回复时带 parent_id（被回复人由服务端派生，前端不传）
export const addReviewReply = (reviewId, data) => request.post(`/reviews/${reviewId}/replies`, data)
