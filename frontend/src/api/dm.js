import request from './request'

// 我的私信会话列表
export const getConversations = () => request.get('/dm/conversations')

// 与某人的私信历史，params: { page, page_size, before_id }
export const getPeerMessages = (peerId, params) =>
  request.get(`/dm/conversations/${peerId}`, { params })

// 发送私信，data: { recipient_id, content }
export const sendDm = (data) => request.post('/dm/send', data)

// 把某人的消息标记为已读
export const markPeerRead = (peerId) => request.post(`/dm/conversations/${peerId}/read`)

// 我收到的未读私信总数
export const getUnreadCount = () => request.get('/dm/unread-count')

// 推荐可私聊对象（官方助手 / 管理员 / 最近关注），items 带 reason 标签
export const getSuggestions = () => request.get('/dm/suggestions')
