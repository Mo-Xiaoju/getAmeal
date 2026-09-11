<template>
  <div class="post-detail">
    <div class="page-head">
      <el-page-header content="笔记详情" @back="router.back()" />
    </div>

    <!-- 详情拿不到（笔记已删除 / 不存在）：骨架屏不能一直转下去，给明确空态与返回入口 -->
    <div v-if="notFound" class="not-found">
      <el-empty description="笔记不存在或已被删除">
        <el-button type="primary" plain @click="router.push('/posts')">返回笔记列表</el-button>
      </el-empty>
    </div>

    <!-- 首次进入 / 切换笔记时先渲染骨架：避免"空白 → 整页白遮罩闪一下 → 内容整块冒出"。
         同一篇重复请求时 store 里数据还在（fetchDetail 不清），直接渲染，不经过骨架。
         容器复用 .post-main（白卡片），骨架与内容同宽同内边距，切换时不跳 -->
    <el-skeleton v-else-if="!postStore.postDetail" animated class="post-main">
      <template #template>
        <div class="author-row">
          <el-skeleton-item variant="circle" class="skeleton-avatar" />
          <div class="author-info">
            <el-skeleton-item variant="text" style="width: 30%" />
            <el-skeleton-item variant="text" style="width: 45%; margin-top: 6px" />
          </div>
        </div>
        <el-skeleton-item variant="h1" style="width: 60%" />
        <el-skeleton-item variant="text" style="width: 100%; margin: 18px 0 10px" />
        <el-skeleton-item variant="text" style="width: 94%; margin-bottom: 10px" />
        <el-skeleton-item variant="text" style="width: 68%" />
        <div class="skeleton-actions">
          <el-skeleton-item variant="button" />
          <el-skeleton-item variant="button" />
        </div>
        <div class="comment-section">
          <el-skeleton-item variant="h3" style="width: 120px; margin-bottom: 16px" />
          <div class="comment-list">
            <el-skeleton :rows="3" animated />
          </div>
        </div>
      </template>
    </el-skeleton>

    <div v-else class="post-main">
      <!-- 作者行 -->
      <div class="author-row">
        <el-avatar
          class="user-link"
          :size="44"
          :src="post.author?.avatar_url || undefined"
          @click="goUser(post.user_id)"
        >
          {{ (post.author?.nickname || 'U').charAt(0) }}
        </el-avatar>
        <div class="author-info">
          <span class="author-name user-link" @click="goUser(post.user_id)">
            {{ post.author?.nickname || '匿名用户' }}
          </span>
          <span class="post-time">{{ formatDate(post.created_at) }}</span>
        </div>
        <el-button
          v-if="canFollow"
          size="small"
          :type="post.is_following ? 'info' : 'primary'"
          :plain="post.is_following"
          @click="handleFollow"
        >
          {{ post.is_following ? '已关注' : '+ 关注' }}
        </el-button>
      </div>

      <!-- 标题与标签 -->
      <h1 class="post-title">{{ post.title }}</h1>
      <div v-if="post.tags && post.tags.length" class="post-tags">
        <el-tag v-for="t in post.tags" :key="t" type="warning" effect="light">{{ t }}</el-tag>
      </div>

      <!-- 关联店铺 -->
      <div v-if="post.shop_id" class="post-shop">
        <el-icon><Shop /></el-icon>
        <span>笔记关联：</span>
        <el-link type="primary" @click="router.push(`/shops/${post.shop_id}`)">{{ post.shop_name }}</el-link>
      </div>

      <!-- 正文 -->
      <p class="post-content">{{ post.content }}</p>

      <!-- 图片 -->
      <div v-if="post.images && post.images.length" class="post-images">
        <img
          v-for="(img, i) in post.images"
          :key="i"
          :src="img"
          :alt="`图片${i + 1}`"
          loading="lazy"
          @error="$event.target.style.display = 'none'"
          @click="openImage(post.images, i)"
        />
      </div>

      <!-- 互动栏：商户只读，不渲染点赞/收藏（后端 4031，评论区同理见下） -->
      <div v-if="!userStore.isMerchant" class="action-bar">
        <!-- 点赞 = 大拇指、收藏 = 五角星，两个图形不再撞车。
             两种状态都靠"描边 → 实心 + 变色"表示（图标走默认插槽，才能把 filled 传进去；
             :icon 只能给组件本身，传不了 props）。
             颜色沿用按钮类型：已点赞 danger 红、已收藏 warning 黄，与列表卡片一致 -->
        <el-button
          :type="post.liked ? 'danger' : 'default'"
          @click="handleLike"
        >
          <el-icon><ThumbUpIcon :filled="!!post.liked" /></el-icon>
          点赞 {{ post.like_count || 0 }}
        </el-button>
        <el-button
          :type="post.favorited ? 'warning' : 'default'"
          @click="handleFavorite"
        >
          <el-icon><StarIcon :filled="!!post.favorited" /></el-icon>
          收藏 {{ post.favorite_count || 0 }}
        </el-button>
        <el-button
          v-if="isMine"
          type="danger"
          plain
          @click="handleDelete"
        >
          删除笔记
        </el-button>
      </div>

      <!-- 评论区 -->
      <section class="comment-section">
        <h2 class="section-title">评论（{{ post.comment_count || 0 }}）</h2>
        <div v-if="!userStore.isMerchant" class="comment-form">
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="2"
            maxlength="200"
            show-word-limit
            placeholder="说说你的看法…"
          />
          <div class="comment-actions">
            <el-button type="primary" :loading="commenting" @click="handleComment">发表评论</el-button>
          </div>
        </div>

        <!-- 只在"没有任何评论可显示"时用骨架占位，已有列表时不再盖一层白遮罩 -->
        <div v-if="commentsLoading && !postStore.comments.length" class="comment-list">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else class="comment-list">
          <el-empty v-if="!postStore.comments.length" description="暂无评论，抢个沙发" />
          <div v-for="c in postStore.comments" :key="c.id" class="comment-item">
            <el-avatar
              class="user-link"
              :size="34"
              :src="c.avatar_url || undefined"
              @click="goUser(c.user_id)"
            >
              {{ (c.nickname || 'U').charAt(0) }}
            </el-avatar>
            <div class="comment-body">
              <div class="comment-head">
                <span class="comment-nickname">{{ c.nickname || '匿名用户' }}</span>
                <span class="comment-time">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="comment-content">{{ c.content }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Shop } from '@element-plus/icons-vue'

import StarIcon from '@/components/StarIcon.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { openImage } from '@/composables/useImageViewer'
import { useUserNav } from '@/composables/useUserNav'
import { usePostStore } from '@/store/post'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const userStore = useUserStore()
const { goUser } = useUserNav()

const postId = computed(() => Number(route.params.id))
const post = computed(() => postStore.postDetail || {})
const commentText = ref('')
const commenting = ref(false)
// 初始即 true：评论要等详情返回后才请求，先按"加载中"渲染，避免闪一下"暂无评论"
const commentsLoading = ref(true)
// 详情请求失败（笔记已删除 / 不存在）：页面切空态而不是停在骨架屏上
const notFound = ref(false)

const isMine = computed(() => userStore.userInfo?.id === post.value.user_id)
// 关注同样仅学生账号可用（后端 require_consumer），商户不渲染
const canFollow = computed(
  () => userStore.isLoggedIn && !userStore.isMerchant && !isMine.value && !!post.value.user_id,
)

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

const requireLogin = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return false
  }
  return true
}

const handleFollow = async () => {
  if (!requireLogin()) return
  const res = await postStore.follow(post.value.user_id)
  post.value.is_following = res.following
  ElMessage.success(res.following ? '关注成功' : '已取消关注')
}

const handleLike = async () => {
  if (!requireLogin()) return
  const res = await postStore.like(postId.value)
  post.value.liked = res.liked
  post.value.like_count = res.like_count
}

const handleFavorite = async () => {
  if (!requireLogin()) return
  const res = await postStore.favorite(postId.value)
  post.value.favorited = res.favorited
  post.value.favorite_count = res.favorite_count
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定删除这篇笔记吗？', '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await postStore.removePost(postId.value)
  ElMessage.success('删除成功')
  router.replace('/posts')
}

const loadComments = async () => {
  commentsLoading.value = true
  try {
    await postStore.fetchComments(postId.value, { page: 1, page_size: 20 })
  } finally {
    commentsLoading.value = false
  }
}

const handleComment = async () => {
  if (!requireLogin()) return
  const text = commentText.value.trim()
  if (!text) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  commenting.value = true
  try {
    await postStore.comment(postId.value, text)
    commentText.value = ''
    post.value.comment_count = (post.value.comment_count || 0) + 1
    ElMessage.success('评论成功')
    loadComments()
  } finally {
    commenting.value = false
  }
}

onMounted(async () => {
  let detail
  try {
    detail = await postStore.fetchDetail(postId.value)
  } catch (e) {
    // 笔记已删除 / 不存在：接口层已提示，这里切空态并解除评论骨架
    notFound.value = true
    commentsLoading.value = false
    return
  }
  if (!detail) {
    // 详情没拿到（接口返回空）：解除评论骨架，交给空态文案
    commentsLoading.value = false
    return
  }
  loadComments()
})
</script>

<style scoped>
.post-detail {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  min-height: 60vh;
}
.page-head {
  margin-bottom: 16px;
}
.post-main {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 28px 32px;
}
/* 空态：与详情卡同一套外观（白底卡片），页面不至于只是一片空白 */
.not-found {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
}
/* 骨架屏：容器类复用真实布局（author-row / author-info / comment-section），
   这里只补头像尺寸和互动栏那一行的间距 */
.skeleton-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  flex-shrink: 0;
}
.skeleton-actions {
  display: flex;
  gap: 12px;
  margin: 22px 0 28px;
}
.author-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}
.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.author-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
/* 头像 / 昵称可点进对方主页 */
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
.author-name.user-link:hover {
  color: var(--el-color-primary);
}
.post-time {
  font-size: 12px;
  color: #c0c4cc;
}
.post-title {
  margin: 0 0 12px;
  font-size: 26px;
  color: #303133;
  line-height: 1.4;
}
.post-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.post-shop {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #909399;
}
.post-content {
  margin: 0 0 18px;
  font-size: 16px;
  color: #303133;
  line-height: 1.9;
  white-space: pre-wrap;
}
.post-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}
.post-images img {
  width: 100%;
  border-radius: 8px;
  cursor: zoom-in;
}
.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 28px;
}
.comment-section {
  border-top: 1px solid #f2f3f5;
  padding-top: 20px;
}
.section-title {
  margin: 0 0 14px;
  font-size: 18px;
  color: #303133;
}
.comment-form {
  margin-bottom: 20px;
}
.comment-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
.comment-list {
  min-height: 60px;
}
.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f2f3f5;
}
.comment-item:last-child {
  border-bottom: none;
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.comment-nickname {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.comment-time {
  font-size: 12px;
  color: #c0c4cc;
}
.comment-content {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
}
</style>
