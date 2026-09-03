import request from './request'

// 本校全校群聊历史，params: { school_id, page, page_size, before_id }
export const getSchoolMessages = (params) => request.get('/chat/messages', { params })

// 发送全校群聊消息（socket 断开时 REST 兜底），data: { content }
export const sendSchoolMessage = (data) => request.post('/chat/messages', data)
