import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { useSchoolStore } from '@/store/school'
import { getToken, removeToken, setToken } from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    userInfo: null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.userInfo?.role === 'admin',
    nickname: (state) => state.userInfo?.nickname || '',
  },
  actions: {
    // 登录，payload: { username, password }
    async login(payload) {
      const res = await authApi.login(payload)
      const data = res.data.data
      this.token = data.access_token
      this.userInfo = data.user
      setToken(data.access_token)
      // 以账号绑定的学校为准，覆盖浏览器里可能残留的学校上下文
      useSchoolStore().applyAccountSchool(data.user?.school)
      return data
    },
    // 注册，payload: { username, password, nickname }
    async register(payload) {
      const res = await authApi.register(payload)
      const data = res.data.data
      // 注册成功即登录
      this.token = data.access_token
      this.userInfo = data.user
      setToken(data.access_token)
      return data
    },
    // 登出
    async logout() {
      try {
        await authApi.logout()
      } catch (e) {
        // 忽略登出接口异常，本地清理登录态
      } finally {
        this.token = ''
        this.userInfo = null
        removeToken()
        // 登出即清除学校上下文，避免残留给下一个注册/登录的账号
        useSchoolStore().clearSchool()
      }
    },
    // 拉取当前用户信息
    async fetchUserInfo() {
      if (!this.token) return null
      const res = await authApi.fetchMe()
      this.userInfo = res.data.data
      useSchoolStore().applyAccountSchool(this.userInfo?.school)
      return this.userInfo
    },
    // 更新个人信息，payload: { nickname, avatar_url }
    async updateProfile(payload) {
      const res = await authApi.updateMe(payload)
      this.userInfo = res.data.data
      return this.userInfo
    },
  },
})
