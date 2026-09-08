import { defineStore } from 'pinia'

import * as schoolApi from '@/api/school'
import { useChatStore } from '@/store/chat'
import { useUserStore } from '@/store/user'
import { getSchool, setSchool } from '@/utils/auth'

export const useSchoolStore = defineStore('school', {
  state: () => ({
    schoolList: [],
    currentSchool: getSchool(), // { id, name, address, logo_url, shop_count }
    loading: false,
  }),
  getters: {
    hasSchool: (state) => !!state.currentSchool,
  },
  actions: {
    _persist() {
      setSchool(this.currentSchool)
    },
    async fetchSchools() {
      if (this.schoolList.length) return this.schoolList
      this.loading = true
      try {
        const res = await schoolApi.getSchoolList()
        this.schoolList = res.data.data || []
        // 本地缓存的当前学校若已不在名单中（例如数据重导后 id 变化），清除避免失效引用
        if (this.currentSchool && !this.schoolList.find((s) => s.id === this.currentSchool.id)) {
          this.clearSchool()
        }
        return this.schoolList
      } finally {
        this.loading = false
      }
    },
    // 选择学校：写入本地；若已登录则同步绑定到账号，并把 socket 切到该校群聊房间
    async selectSchool(school) {
      const oldId = this.currentSchool?.id
      this.currentSchool = school
      this._persist()
      const userStore = useUserStore()
      if (userStore.isLoggedIn) {
        try {
          await userStore.updateProfile({ school_id: school.id })
          // 绑定成功后让实时连接加入新学校房间（并离开旧学校房间）
          useChatStore().emitSchoolChange(school.id, oldId)
        } catch (e) {
          // 绑定失败不阻断浏览，个人中心可再改
        }
      }
      return school
    },
    // 登录/拉取账号资料后：以账号绑定的学校覆盖浏览器残留的上下文（账号已绑定，无需再调 updateProfile）
    applyAccountSchool(school) {
      if (!school || !school.id) return null
      this.currentSchool = { ...school }
      this._persist()
      return this.currentSchool
    },
    clearSchool() {
      this.currentSchool = null
      this._persist()
    },
  },
})
