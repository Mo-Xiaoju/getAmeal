import request from './request'

// 笔记列表，params: { school_id, keyword, sort, page, page_size }
export const getPostList = (params) => request.get('/posts', { params })

// 笔记详情
export const getPostDetail = (postId) => request.get(`/posts/${postId}`)

// 发布笔记，data: { title, content, images, shop_id, tags }
export const createPost = (data) => request.post('/posts', data)

// 我的笔记列表，params: { page, page_size }
export const getMyPosts = (params) => request.get('/posts/mine', { params })

// 删除笔记
export const deletePost = (postId) => request.delete(`/posts/${postId}`)

// 点赞/取消点赞
export const toggleLike = (postId) => request.post(`/posts/${postId}/like`)

// 收藏/取消收藏笔记
export const toggleFavorite = (postId) => request.post(`/posts/${postId}/favorite`)

// 笔记评论列表，params: { page, page_size }
export const getComments = (postId, params) => request.get(`/posts/${postId}/comments`, { params })

// 发表评论，data: { content }
export const addComment = (postId, data) => request.post(`/posts/${postId}/comments`, data)

// 关注/取关用户
export const toggleFollow = (userId) => request.post(`/user/${userId}/follow`)

// 我的关注/粉丝列表，params: { page, page_size }
export const getFollowing = (params) => request.get('/user/following', { params })
export const getFollowers = (params) => request.get('/user/followers', { params })
