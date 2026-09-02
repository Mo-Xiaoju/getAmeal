import { defineStore } from 'pinia'

import * as postApi from '@/api/post'

export const usePostStore = defineStore('post', {
  state: () => ({
    postList: [],
    postDetail: null,
    comments: [],
    commentTotal: 0,
    followingList: [],
    followerList: [],
    pagination: { page: 1, page_size: 10, total: 0, total_pages: 0 },
    loading: false,
  }),
  actions: {
    // 笔记列表，params: { school_id, keyword, sort, page, page_size }
    async fetchList(params) {
      this.loading = true
      try {
        const res = await postApi.getPostList(params)
        const data = res.data.data
        this.postList = data.items || []
        this.pagination = data
        return data
      } finally {
        this.loading = false
      }
    },
    // 笔记详情
    async fetchDetail(id) {
      this.loading = true
      try {
        const res = await postApi.getPostDetail(id)
        this.postDetail = res.data.data
        return this.postDetail
      } finally {
        this.loading = false
      }
    },
    // 发布笔记
    async create(data) {
      const res = await postApi.createPost(data)
      return res.data.data
    },
    // 我的笔记列表
    async fetchMine(params) {
      this.loading = true
      try {
        const res = await postApi.getMyPosts(params)
        const data = res.data.data
        this.postList = data.items || []
        this.pagination = data
        return data
      } finally {
        this.loading = false
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
