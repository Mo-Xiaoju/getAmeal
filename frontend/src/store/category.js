import { defineStore } from 'pinia'

import * as shopApi from '@/api/shop'

// 店铺规范分类（受控词表，来源后端 /shops/categories，跨表单/筛选共用一份缓存）
export const useCategoryStore = defineStore('category', {
  state: () => ({
    categories: [],
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
  },
})
