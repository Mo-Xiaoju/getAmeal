import { defineStore } from 'pinia'

import * as shopApi from '@/api/shop'

export const useShopStore = defineStore('shop', {
  state: () => ({
    shopList: [],
    recommendList: [],
    shopDetail: null,
    reviews: [],
    favoriteCount: 0,
    pagination: { page: 1, page_size: 10, total: 0, total_pages: 0 },
    loading: false,
  }),
  getters: {
    isFavorited: (state) => !!state.shopDetail?.favorited,
  },
  actions: {
    // 店铺列表 + 筛选，params: { school_id, keyword, category, sort, page, page_size }
    async fetchShopList(params) {
      this.loading = true
      try {
        const res = await shopApi.getShopList(params)
        const data = res.data.data
        this.shopList = data.items || []
        this.pagination = data
        return data
      } finally {
        this.loading = false
      }
    },
    // 店铺详情，id: 店铺ID
    async fetchShopDetail(id) {
      this.loading = true
      try {
        const res = await shopApi.getShopDetail(id)
        this.shopDetail = res.data.data
        return this.shopDetail
      } finally {
        this.loading = false
      }
    },
    // 店铺评价列表，shopId + params
    async fetchReviews(shopId, params = {}) {
      const res = await shopApi.getShopReviews(shopId, params)
      const data = res.data.data
      this.reviews = data.items || []
      return data
    },
    // 发表评价，shopId + payload: { rating, content }
    async addReview(shopId, payload) {
      const res = await shopApi.addReview(shopId, payload)
      return res.data.data
    },
    // 切换收藏状态，shopId（返回当前是否已收藏）
    async toggleFavorite(shopId) {
      if (this.shopDetail?.favorited) {
        const res = await shopApi.removeFavorite(shopId)
        this.shopDetail.favorited = res.data.data.favorited
      } else {
        const res = await shopApi.addFavorite(shopId)
        if (this.shopDetail) this.shopDetail.favorited = res.data.data.favorited
        else this.favoriteCount = 1
      }
      return this.shopDetail?.favorited
    },
    // 获取推荐店铺
    async fetchRecommend(params = {}) {
      const res = await shopApi.getRecommend(params)
      this.recommendList = res.data.data.items || []
      return this.recommendList
    },
  },
})
