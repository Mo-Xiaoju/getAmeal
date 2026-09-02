import { defineStore } from 'pinia'

import * as dishApi from '@/api/dish'

export const useDishStore = defineStore('dish', {
  state: () => ({
    shopDishes: [],
    dishDetail: null,
    recommendList: [],
    loading: false,
  }),
  actions: {
    // 店铺下的菜品列表，shopId + params
    async fetchShopDishes(shopId, params = {}) {
      this.loading = true
      try {
        const res = await dishApi.getShopDishes(shopId, params)
        this.shopDishes = res.data.data.items || []
        return res.data.data
      } finally {
        this.loading = false
      }
    },
    // 菜品详情，id: 菜品ID
    async fetchDishDetail(id) {
      this.loading = true
      try {
        const res = await dishApi.getDishDetail(id)
        this.dishDetail = res.data.data
        return this.dishDetail
      } finally {
        this.loading = false
      }
    },
    // 推荐菜品，params: { school_id, limit }
    async fetchRecommend(params = {}) {
      const res = await dishApi.getDishRecommend(params)
      this.recommendList = res.data.data.items || []
      return this.recommendList
    },
  },
})
