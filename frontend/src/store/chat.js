import { defineStore } from 'pinia'
import { io } from 'socket.io-client'

import * as dmApi from '@/api/dm'
import { useUserStore } from '@/store/user'
import { getToken } from '@/utils/auth'

// socket 实例与消息订阅器放在 store 外的模块作用域：Pinia 状态不代理非纯对象
let socket = null
const listeners = new Set()

export const useChatStore = defineStore('chat', {
  state: () => ({
    connected: false,   // 当前 socket 是否在线
    unreadCount: 0,     // 未读私信总数（未读徽标）
  }),
  actions: {
    // 登录后建立实时连接；token 读取自本地缓存（与登录态同源）
    connect() {
      const token = getToken()
      if (socket || !token) return
      // 不指定 transports：websocket 直连会让 werkzeug 开发服务器在会话结束时误记 500，
      // 走默认的 轮询→升级 即可，最终仍落在 websocket 传输上。
      socket = io({ auth: { token } })

      socket.on('connect', () => {
        this.connected = true
        this.refreshUnread()
      })
      socket.on('disconnect', () => {
        this.connected = false
      })
      socket.on('connect_error', () => {
        this.connected = false
      })
      // 服务端 message 事件：{ channel:{type,id}, message }
      socket.on('message', (payload) => {
        const channel = payload?.channel
        const message = payload?.message
        if (!channel || !message) return
        // 收到他人私信时以服务端为准刷新未读数（含自己发送的回显则无需处理）
        if (channel.type === 'dm' && message.author?.id !== useUserStore().userInfo?.id) {
          this.refreshUnread()
        }
        listeners.forEach((cb) => cb(channel, message))
      })
    },
    // 登出时断开并清理订阅
    disconnect() {
      if (socket) {
        socket.removeAllListeners()
        socket.disconnect()
        socket = null
      }
      this.connected = false
      listeners.clear()
    },
    // 订阅消息流，返回退订函数
    subscribe(cb) {
      listeners.add(cb)
      return () => listeners.delete(cb)
    },
    // 实时发送（主路径）；离线/超时抛错，由调用方走 REST 兜底
    // shopId：店铺关联标注（校园/圈子群聊可选）
    async sendLive(channel, content, shopId) {
      if (!socket || !this.connected) throw new Error('实时通道未连接')
      const payload = { channel, content }
      if (shopId) payload.shop_id = shopId
      const ack = await socket.timeout(6000).emitWithAck('send', payload)
      return ack
    },
    // 加入/退出圈子后同步 socket 房间订阅
    emitCircleJoin(joined, circleId) {
      if (!socket || !this.connected) return
      socket.emit(joined ? 'circle:join' : 'circle:leave', { circle_id: circleId })
    },
    // 选择/切换学校后同步全校群聊房间订阅
    // （connect 时只按登录瞬间绑定的学校入房；登录后选校/换校必须补发，否则全校群聊收不到实时消息）
    emitSchoolChange(newSchoolId, oldSchoolId) {
      if (!socket || !this.connected) return
      if (oldSchoolId && oldSchoolId !== newSchoolId) socket.emit('school:leave', { school_id: oldSchoolId })
      if (newSchoolId) socket.emit('school:join', { school_id: newSchoolId })
    },
    // 以服务端为准刷新未读数
    async refreshUnread() {
      if (!getToken()) {
        this.unreadCount = 0
        return 0
      }
      try {
        const res = await dmApi.getUnreadCount()
        this.unreadCount = res.data.data?.total || 0
        return this.unreadCount
      } catch (e) {
        return this.unreadCount
      }
    },
  },
})
