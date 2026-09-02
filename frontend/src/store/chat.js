import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],
    connectionStatus: 'disconnected', // disconnected | connecting | connected
  }),
  actions: {
    // 拉取历史消息，params: { page, page_size }
    async fetchHistory(params) {
      // TODO
    },
    // 发送消息，content: 消息文本
    async sendMessage(content) {
      // TODO
    },
    // 建立实时连接（SSE / WebSocket，占位）
    connect() {
      // TODO
    },
    // 断开实时连接
    disconnect() {
      // TODO
    },
  },
})
