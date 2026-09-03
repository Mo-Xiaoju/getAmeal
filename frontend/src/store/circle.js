import { defineStore } from 'pinia'

import * as circleApi from '@/api/circle'

export const useCircleStore = defineStore('circle', {
  state: () => ({
    list: [],
    joinedList: [],
    detail: null,
    members: [],
    pagination: { page: 1, page_size: 10, total: 0, total_pages: 0 },
    loading: false,
  }),
  actions: {
    // 圈子列表，params: { school_id, keyword, page, page_size }
    async fetchList(params) {
      this.loading = true
      try {
        const res = await circleApi.getCircleList(params)
        const data = res.data.data
        this.list = data.items || []
        this.pagination = data
        return data
      } finally {
        this.loading = false
      }
    },
    // 我加入的圈子
    async fetchJoined(params = {}) {
      const res = await circleApi.getMyCircles(params)
      const data = res.data.data
      this.joinedList = data.items || []
      return data
    },
    // 圈子详情
    async fetchDetail(id) {
      this.loading = true
      try {
        const res = await circleApi.getCircleDetail(id)
        this.detail = res.data.data
        return this.detail
      } finally {
        this.loading = false
      }
    },
    // 成员列表
    async fetchMembers(id, params = {}) {
      const res = await circleApi.getCircleMembers(id, params)
      const data = res.data.data
      this.members = data.items || []
      return data
    },
    // 创建圈子
    async create(data) {
      const res = await circleApi.createCircle(data)
      return res.data.data
    },
    // 更新圈子
    async update(id, data) {
      const res = await circleApi.updateCircle(id, data)
      this.detail = res.data.data
      return this.detail
    },
    // 解散圈子
    async remove(id) {
      await circleApi.deleteCircle(id)
    },
    // 加入/退出圈子；加入成功时通过 joinSocket 订阅实时房间
    async join(id, joinSocket) {
      const res = await circleApi.toggleJoinCircle(id)
      const data = res.data.data
      if (this.detail && this.detail.id === id) {
        this.detail.joined = data.joined
        this.detail.member_count = data.member_count
      }
      const item = this.list.find((c) => c.id === id)
      if (item) {
        item.joined = data.joined
        item.member_count = data.member_count
      }
      if (typeof joinSocket === 'function') joinSocket(data.joined, id)
      return data
    },
  },
})
