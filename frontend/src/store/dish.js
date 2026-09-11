import { defineStore } from 'pinia'

import * as dishApi from '@/api/dish'

export const useDishStore = defineStore('dish', {
  state: () => ({
    shopDishes: [],
    shopDishesShopId: null, // shopDishes 属于哪家店：换店时据此清空，避免闪上一家店的菜
    dishDetail: null,
    recommendList: [],
    loading: false,
    // 首页推荐专用的加载态：与 loading 分开，免得店铺详情页的菜品请求点亮首页的骨架屏
    recommendLoading: false,
    recommendSchoolId: null, // recommendList 属于哪所学校：换校时据此清空，避免闪上一所学校的推荐
  }),
  actions: {
    // 店铺下的菜品列表，shopId + params
    async fetchShopDishes(shopId, params = {}) {
      // 换店时先清空：否则会先把上一家店的菜品渲染到新店页面上再被替换（观感上就是"闪一下"）
      if (this.shopDishesShopId !== shopId) {
        this.shopDishes = []
        this.shopDishesShopId = shopId
      }
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
      // 切到另一道菜时先清掉上一道：详情页直接渲染 store 里的数据，
      // 不清就会先把上一道菜的名字/价格/图片渲染出来再替换（观感上就是"闪一下"）。
      // 同一道菜重复请求（如返回后重挂载）不清，内容原地复用。
      if (this.dishDetail?.id !== id) this.dishDetail = null
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
      // 换学校时先清空：否则会先把上一所学校的推荐渲染到新学校的标题下再被替换（观感上就是"闪一下"）。
      // 同一所学校重复请求（如返回首页）不清，数据原地复用，不白一次
      if (this.recommendSchoolId !== (params.school_id ?? null)) {
        this.recommendList = []
        this.recommendSchoolId = params.school_id ?? null
      }
      this.recommendLoading = true
      try {
        const res = await dishApi.getDishRecommend(params)
        this.recommendList = res.data.data.items || []
        return this.recommendList
      } finally {
        this.recommendLoading = false
      }
    },
  },
})
