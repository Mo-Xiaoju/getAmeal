import request from './request'

// 评论的点赞 / 回复展开。评论的发表与列表在 api/post.js
// （POST/GET /posts/<id>/comments）；评价回复的发表在 api/review.js

// 点赞/取消点赞评论或回复
export const toggleCommentLike = (commentId) => request.post(`/comments/${commentId}/like`)

// 某条评论的二级回复列表（展开「查看全部 N 条回复」用），params: { page, page_size }
export const getCommentReplies = (commentId, params) =>
  request.get(`/comments/${commentId}/replies`, { params })
