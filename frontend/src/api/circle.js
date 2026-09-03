import request from './request'

// 圈子列表，params: { school_id, keyword, page, page_size }
export const getCircleList = (params) => request.get('/circles', { params })

// 圈子详情
export const getCircleDetail = (circleId) => request.get(`/circles/${circleId}`)

// 创建圈子，data: { school_id, name, cover_url, description }
export const createCircle = (data) => request.post('/circles', data)

// 更新圈子，data: { name, cover_url, description }
export const updateCircle = (circleId, data) => request.put(`/circles/${circleId}`, data)

// 解散圈子
export const deleteCircle = (circleId) => request.delete(`/circles/${circleId}`)

// 加入/退出圈子
export const toggleJoinCircle = (circleId) => request.post(`/circles/${circleId}/join`)

// 我加入的圈子，params: { page, page_size }
export const getMyCircles = (params) => request.get('/circles/joined', { params })

// 圈子成员，params: { page, page_size }
export const getCircleMembers = (circleId, params) =>
  request.get(`/circles/${circleId}/members`, { params })

// 圈内群聊历史，params: { page, page_size, before_id }
export const getCircleMessages = (circleId, params) =>
  request.get(`/circles/${circleId}/messages`, { params })

// 发送圈内消息（socket 断开时 REST 兜底），data: { content }
export const sendCircleMessage = (circleId, data) =>
  request.post(`/circles/${circleId}/messages`, data)
