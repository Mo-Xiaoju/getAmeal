<template>
  <div class="review-item">
    <el-avatar
      class="user-link"
      :size="40"
      :src="review.avatar_url || undefined"
      @click="goUser(review.user_id)"
    >
      {{ (review.nickname || 'U').charAt(0) }}
    </el-avatar>
    <div class="review-body">
      <div class="review-head">
        <span class="review-nickname">{{ review.nickname || '匿名用户' }}</span>
        <RatingStars :rating="review.rating || 0" />
        <span class="review-time">{{ formatDate(review.created_at) }}</span>
      </div>

      <!-- 关联菜品：这条评价是冲着这道菜写的，点进去看菜品详情 -->
      <div v-if="showDish && review.dish_id" class="review-dish">
        <el-icon><Dish /></el-icon>
        <el-link type="primary" :underline="false" @click="router.push(`/dishes/${review.dish_id}`)">
          {{ review.dish_name || '关联菜品' }}
        </el-link>
      </div>

      <p v-if="review.content" class="review-content">{{ review.content }}</p>

      <!-- 图片九宫格：后端一直在发 images，此前前端从未渲染 -->
      <div v-if="images.length" class="review-images">
        <img
          v-for="(img, i) in images"
          :key="i"
          :src="img"
          :alt="`评价图片${i + 1}`"
          loading="lazy"
          @error="$event.target.style.display = 'none'"
          @click="openImage(images, i)"
        />
      </div>

      <!-- 互动栏：商户只读（后端 4031），不渲染 -->
      <div v-if="canInteract" class="review-ops">
        <span
          class="op"
          :class="{ 'is-liked': review.liked, 'is-locked': guestLocked }"
          @click="handleLike"
        >
          <el-icon><ThumbUpIcon :filled="!!review.liked" /></el-icon>
          {{ review.like_count || 0 }}
        </span>
        <span class="op" :class="{ 'is-locked': guestLocked }" @click="openReply(null)">回复</span>
      </div>

      <ReplyComposer
        v-if="replyTo && replyTo.id === null"
        :guest-locked="guestLocked"
        :submitting="replySubmitting"
        @submit="(text) => submitReply(null, text)"
        @cancel="replyTo = null"
      />

      <ReplyThread
        :replies="review.replies || []"
        :reply-count="review.reply_count || 0"
        :loading="repliesLoading"
        :submitting="replySubmitting"
        :reply-to="replyTo"
        :guest-locked="guestLocked"
        :can-reply="canInteract"
        @reply="openReply"
        @like="handleReplyLike"
        @load-more="loadMoreReplies"
        @submit="({ target, content }) => submitReply(target, content)"
        @cancel="replyTo = null"
      />
    </div>
  </div>
</template>

<script setup>
// 一条评价（含图片、关联菜品、点赞、回复区）。
//
// 自己调 store/接口，而不是把一堆事件抛给宿主视图：店铺页和菜品页要用的是完全相同的一套
// 互动行为，做成"纯展示 + 事件出"就得在两个视图里各写一遍（回复框状态、分页、就地更新），
// 迟早会漂移。ReplyThread 仍然保持纯展示，因为那个才真的会被两处复用。
//
// 所有成功后的更新都是**就地改 review 对象**、绝不重载列表：重载会重置分页、
// 把已经展开的「查看全部」全部收回去。店铺页的 review 来自 store（Pinia 深层响应式），
// 菜品页的来自本地 ref，两边就地改都能重渲染。
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import RatingStars from '@/components/RatingStars.vue'
import ReplyComposer from '@/components/ReplyComposer.vue'
import ReplyThread from '@/components/ReplyThread.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { useLoginGate } from '@/composables/useLoginGate'
import { openImage } from '@/composables/useImageViewer'
import { useUserNav } from '@/composables/useUserNav'
import { useShopStore } from '@/store/shop'
import { useUserStore } from '@/store/user'

const props = defineProps({
  review: { type: Object, required: true },
  // 菜品页的每一条都必然是这道菜的，再挂一个菜品 tag 是噪音
  showDish: { type: Boolean, default: true },
})

const router = useRouter()
const shopStore = useShopStore()
const userStore = useUserStore()
const { goUser } = useUserNav()
const { guestLocked, requireLogin } = useLoginGate()

// 商户不能点赞/回复（后端 4031），控件直接不渲染
const canInteract = computed(() => !userStore.isMerchant)
const images = computed(() => props.review.images || [])

const replyTo = ref(null) // null=关闭；{ id: null }=回复评价本身；{ id }=回复某条回复
const replySubmitting = ref(false)
const repliesLoading = ref(false)

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

const handleLike = async () => {
  if (guestLocked.value) return
  if (!requireLogin()) return
  const res = await shopStore.reviewLike(props.review.id)
  props.review.liked = res.liked
  props.review.like_count = res.like_count
}

const handleReplyLike = async (reply) => {
  if (guestLocked.value) return
  if (!requireLogin()) return
  // 评论点赞走 /api/comments/<id>/like：评价回复与笔记评论是同一张表
  const res = await shopStore.commentLike(reply.id)
  reply.liked = res.liked
  reply.like_count = res.like_count
}

function openReply(target) {
  if (guestLocked.value) return
  if (!requireLogin()) return
  // target 为 null 表示回复评价本身；已在别处展开时先关掉再开，等价于"切换目标"
  replyTo.value = target ? { id: target.id } : { id: null }
}

const submitReply = async (target, text) => {
  if (!requireLogin()) return
  const content = (text || '').trim()
  if (!content) return
  replySubmitting.value = true
  try {
    const reply = await shopStore.addReviewReply(props.review.id, content, target?.id ?? null)
    if (target) {
      // 回复某条回复：挂在它所在的那条根回复下面（服务端也把 parent_id 归一化到根，这里保持一致）。
      // 找不到承载它的根就不本地插入 —— 宁可只多一个计数，也不要把回复挂到不相干的根上。
      const root = findRoot(target.id)
      if (root) {
        if (!root.replies) root.replies = []
        root.replies.push(reply)
      }
    } else {
      if (!props.review.replies) props.review.replies = []
      props.review.replies.push(reply)
    }
    props.review.reply_count = (props.review.reply_count || 0) + 1
    replyTo.value = null
  } finally {
    replySubmitting.value = false
  }
}

// 在已加载的回复里找到承载 target 的那条根回复（target 自己就是根时返回它）
function findRoot(targetId) {
  const replies = props.review.replies || []
  return (
    replies.find((r) => r.id === targetId) ||
    replies.find((r) => (r.replies || []).some((c) => c.id === targetId)) ||
    null
  )
}

const loadMoreReplies = async () => {
  repliesLoading.value = true
  try {
    // 一次取满一页（预览只给了 3 条根回复）。极端情况下根回复超过 50 条时按钮会留着，
    // 这个量级在本项目里不会出现，不值得再搭一套分页 UI。
    const data = await shopStore.fetchReviewReplies(props.review.id, { page: 1, page_size: 50 })
    props.review.replies = data.items || []
  } finally {
    repliesLoading.value = false
  }
}
</script>

<style scoped>
.review-item {
  display: flex;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #f2f3f5;
}
.review-item:last-child {
  border-bottom: none;
}
.review-body {
  flex: 1;
  min-width: 0;
}
.review-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.review-nickname {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.review-time {
  font-size: 12px;
  color: #c0c4cc;
}
.review-dish {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #909399;
}
.review-content {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.review-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.review-images img {
  width: 92px;
  height: 92px;
  object-fit: cover;
  border-radius: 8px;
  cursor: zoom-in;
}
.review-ops {
  display: flex;
  align-items: center;
  gap: 16px;
}
.op {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
  cursor: pointer;
  transition: color 0.15s;
}
.op:hover {
  color: var(--el-color-primary);
}
.op.is-liked {
  color: var(--el-color-danger);
}
.op.is-locked {
  cursor: not-allowed;
}
.op.is-locked:hover {
  color: #909399;
}
.op.is-liked.is-locked:hover {
  color: var(--el-color-danger);
}
/* 头像可点进评价者主页 */
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
</style>
