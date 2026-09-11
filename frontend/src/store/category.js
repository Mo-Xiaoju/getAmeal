import { defineStore } from 'pinia'

import * as shopApi from '@/api/shop'

// 店铺受控词表（来源后端 /shops/categories 与 /shops/zones，跨表单/筛选共用一份缓存）
export const useCategoryStore = defineStore('category', {
  state: () => ({
    categories: [], // 细分分类：食堂/奶茶/火锅…
    zones: [], // 大分类：校内/周边/外卖
    loading: false,
  }),
  actions: {
    async fetchCategories() {
      if (this.categories.length) return this.categories
      this.loading = true
      try {
        const res = await shopApi.getCategories()
        this.categories = res.data.data?.categories || []
        return this.categories
      } finally {
        this.loading = false
      }
    },
    async fetchZones() {
      if (this.zones.length) return this.zones
      this.loading = true
      try {
        const res = await shopApi.getZones()
        this.zones = res.data.data?.zones || []
        return this.zones
      } finally {
        this.loading = false
      }
    },
  },
})
