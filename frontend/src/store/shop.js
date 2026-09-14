import { defineStore } from 'pinia'

import * as commentApi from '@/api/comment'
import * as reviewApi from '@/api/review'
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
    // 首页推荐专用的加载态：与 loading 分开，免得列表页/详情页的请求点亮首页的骨架屏
    recommendLoading: false,
    recommendSchoolId: null, // recommendList 属于哪所学校：换校时据此清空，避免闪上一所学校的推荐
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
      // 切到另一家店时先清掉上一家的详情与评价：详情页/评价区都直接渲染 store 里的数据，
      // 不清就会先把上一家店的内容渲染出来、等接口回来再替换（观感上就是"闪一下"）。
      // 返回同一家店（详情页 → 菜品页 → 返回）时不清，数据原样复用，页面不会重新白一次。
      if (this.shopDetail?.id !== id) {
        this.shopDetail = null
        this.reviews = []
      }
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
    // store=false：只取数据不写 this.reviews。菜品详情页只要 3 条预览，
    // 写进去会污染店铺详情页的完整列表（返回同一家店时会先渲染出这 3 条再被替换）
    async fetchReviews(shopId, params = {}, { store = true } = {}) {
      const res = await shopApi.getShopReviews(shopId, params)
      const data = res.data.data
      if (store) this.reviews = data.items || []
      return data
    },
    // 发表评价，shopId + payload: { rating, content, images, dish_id }
    async addReview(shopId, payload) {
      const res = await shopApi.addReview(shopId, payload)
      return res.data.data
    },
    // ---- 评价互动（纯 HTTP 包装，不写 state）----
    // 点赞态与回复列表分别落在店铺页的 store.reviews 和菜品页的本地点赞数组里，
    // store 侧的 mutation helper 够不到后者，所以统一由视图拿到返回值后就地更新。
    // 同 postStore.like。
    async reviewLike(id) {
      const res = await reviewApi.toggleReviewLike(id)
      return res.data.data
    },
    // 评价下面的回复点赞走 /api/comments/<id>/like：comments 是一张表，
    // 评价回复与笔记评论共用同一个点赞入口（postStore.commentLike 是同一个接口的另一份包装）
    async commentLike(id) {
      const res = await commentApi.toggleCommentLike(id)
      return res.data.data
    },
    async addReviewReply(id, content, parentId = null) {
      // 只发 parent_id：被回复人由服务端从父评论作者派生（客户端传了也无效）
      const payload = parentId ? { content, parent_id: parentId } : { content }
      const res = await reviewApi.addReviewReply(id, payload)
      return res.data.data
    },
    async fetchReviewReplies(id, params = {}) {
      const res = await reviewApi.getReviewReplies(id, params)
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
      // 换学校时先清空：否则会先把上一所学校的推荐渲染到新学校的标题下再被替换（观感上就是"闪一下"）。
      // 同一所学校重复请求（如返回首页）不清，数据原地复用，不白一次
      if (this.recommendSchoolId !== (params.school_id ?? null)) {
        this.recommendList = []
        this.recommendSchoolId = params.school_id ?? null
      }
      this.recommendLoading = true
      try {
        const res = await shopApi.getRecommend(params)
        this.recommendList = res.data.data.items || []
        return this.recommendList
      } finally {
        this.recommendLoading = false
      }
    },
  },
})
