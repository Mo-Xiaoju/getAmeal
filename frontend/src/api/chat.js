import request from './request'

// 历史消息，params: { page, page_size }
export const getMessages = (params) => request.get('/chat/messages', { params })

// 发送消息，content: 消息文本
export const sendMessage = (content) => request.post('/chat/messages', { content })
