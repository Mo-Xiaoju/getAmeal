import { defineStore } from 'pinia'

import * as postApi from '@/api/post'

// 列表结果的"查询范围"指纹：范围一变，store 里那份 postList 就不再属于当前查询，必须先清掉，
// 否则会先把上一份结果渲染出来再被替换（观感上就是"闪一下"）。
// 只认"换了一份列表"：换页签（全部 / 我的）、换学校、首页推荐 vs 笔记列表。
// 排序 / 关键词 / 页码都不算 —— 最新↔热门来回切时，两份数据本来就是同一批笔记，
// 清空再铺骨架会让整块网格白一下；旧卡片原地留着等新数据替换即可。
// page_size 要计入：个人中心统计只取 1 条、首页推荐只取 3 条，都会写进同一个 postList。
const listScopeKey = (params = {}) =>
  JSON.stringify({
    school_id: params.school_id ?? null,
    user_id: params.user_id ?? null,
    page_size: params.page_size ?? null,
  })

export const usePostStore = defineStore('post', {
  state: () => ({
    postList: [],
    postListKey: '', // postList 属于哪一份查询（首页推荐 / 笔记列表 / 我的笔记）
    listSeq: 0, // 列表请求序号：并发时只认最后一次请求的响应
    postDetail: null,
    comments: [],
    commentTotal: 0,
    followingList: [],
    followerList: [],
    pagination: { page: 1, page_size: 10, total: 0, total_pages: 0 },
    // 列表类请求专用：详情请求不置这个位，否则会连带触发列表页的加载态
    loading: false,
  }),
  actions: {
    // 列表请求前的公共准备：查询范围变了先清空旧结果，并领一个请求号
    beginList(key) {
      if (this.postListKey !== key) {
        this.postList = []
        this.postListKey = key
      }
      this.listSeq += 1
      return this.listSeq
    },
    // 笔记列表，params: { school_id, keyword, sort, page, page_size }
    async fetchList(params) {
      const seq = this.beginList(listScopeKey(params))
      this.loading = true
      try {
        const res = await postApi.getPostList(params)
        const data = res.data.data
        // 期间又发起了新查询：这份响应已经过期，丢弃，否则会把新查询的结果覆盖掉
        if (seq !== this.listSeq) return data
        this.postList = data.items || []
        this.pagination = data
        return data
      } finally {
        // 只有最后一次请求才有资格解除加载态，否则会把仍在加载的列表提前"解除"
        if (seq === this.listSeq) this.loading = false
      }
    },
    // 笔记详情
    async fetchDetail(id) {
      // 切到另一篇笔记时先清掉上一篇的详情与评论：详情页直接渲染 store 里的数据，
      // 不清就会先把上一篇的标题/正文渲染出来再替换（观感上就是"闪一下"）。
      // 同一篇重复请求（如返回后重挂载）不清，内容原地复用。
      if (this.postDetail?.id !== id) {
        this.postDetail = null
        this.comments = []
        this.commentTotal = 0
      }
      const res = await postApi.getPostDetail(id)
      this.postDetail = res.data.data
      return this.postDetail
    },
    // 发布笔记
    async create(data) {
      const res = await postApi.createPost(data)
      return res.data.data
    },
    // 我的笔记列表
    async fetchMine(params = {}) {
      // 与"全部笔记"不是同一份结果，用 mine 前缀区分查询范围
      const seq = this.beginList(`mine:${listScopeKey(params)}`)
      this.loading = true
      try {
        const res = await postApi.getMyPosts(params)
        const data = res.data.data
        if (seq !== this.listSeq) return data
        this.postList = data.items || []
        this.pagination = data
        return data
      } finally {
        if (seq === this.listSeq) this.loading = false
      }
    },
    // 删除笔记
    async removePost(id) {
      await postApi.deletePost(id)
    },
    // 点赞/取消点赞
    async like(id) {
      const res = await postApi.toggleLike(id)
      return res.data.data
    },
    // 收藏/取消收藏笔记
    async favorite(id) {
      const res = await postApi.toggleFavorite(id)
      return res.data.data
    },
    // 评论列表
    async fetchComments(id, params = {}) {
      const res = await postApi.getComments(id, params)
      const data = res.data.data
      // 期间已经切到别的笔记（postDetail 换了 id）：这份评论不再属于当前详情页，
      // 丢弃，否则慢请求回来会把新笔记的评论区刷成上一篇的
      if (this.postDetail?.id !== id) return data
      this.comments = data.items || []
      this.commentTotal = data.total || 0
      return data
    },
    // 发表评论
    async comment(id, content) {
      const res = await postApi.addComment(id, { content })
      return res.data.data
    },
    // 关注/取关用户
    async follow(userId) {
      const res = await postApi.toggleFollow(userId)
      return res.data.data
    },
    // 我的关注/粉丝
    async fetchFollowing(params = {}) {
      const res = await postApi.getFollowing(params)
      this.followingList = res.data.data.items || []
      return res.data.data
    },
    async fetchFollowers(params = {}) {
      const res = await postApi.getFollowers(params)
      this.followerList = res.data.data.items || []
      return res.data.data
    },
  },
})
