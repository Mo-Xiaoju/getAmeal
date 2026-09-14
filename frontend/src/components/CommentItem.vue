<template>
  <div class="comment-item">
    <el-avatar
      class="user-link"
      :size="34"
      :src="comment.avatar_url || undefined"
      @click="goUser(comment.user_id)"
    >
      {{ (comment.nickname || 'U').charAt(0) }}
    </el-avatar>
    <div class="comment-body">
      <div class="comment-head">
        <span class="comment-nickname">{{ comment.nickname || '匿名用户' }}</span>
        <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
      </div>
      <p class="comment-content">{{ comment.content }}</p>

      <!-- 互动栏：商户只读（后端 4031），不渲染 -->
      <div v-if="canInteract" class="comment-ops">
        <span
          class="op"
          :class="{ 'is-liked': comment.liked, 'is-locked': guestLocked }"
          @click="handleLike"
        >
          <el-icon><ThumbUpIcon :filled="!!comment.liked" /></el-icon>
          {{ comment.like_count || 0 }}
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
        :replies="comment.replies || []"
        :reply-count="comment.reply_count || 0"
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
// 一条笔记评论（含点赞、回复区）。结构与 ReviewItem 一一对应，差别只是没有
// 评分 / 图片 / 关联菜品 —— 那三样属于评价。
//
// 与 ReviewItem 一样自己调 store：就地改 comment 对象，绝不重载评论列表
// （重载会回到第一页并把已展开的回复收回去）。
import { computed, ref } from 'vue'

import ReplyComposer from '@/components/ReplyComposer.vue'
import ReplyThread from '@/components/ReplyThread.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { useLoginGate } from '@/composables/useLoginGate'
import { useUserNav } from '@/composables/useUserNav'
import { usePostStore } from '@/store/post'
import { useUserStore } from '@/store/user'

const props = defineProps({
  comment: { type: Object, required: true },
})

const postStore = usePostStore()
const userStore = useUserStore()
const { goUser } = useUserNav()
const { guestLocked, requireLogin } = useLoginGate()

// 商户不能点赞/回复（后端 4031），控件直接不渲染
const canInteract = computed(() => !userStore.isMerchant)

const replyTo = ref(null) // null=关闭；{ id: null }=回复评论本身；{ id }=回复某条回复
const replySubmitting = ref(false)
const repliesLoading = ref(false)

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

const handleLike = async () => {
  if (guestLocked.value) return
  if (!requireLogin()) return
  const res = await postStore.commentLike(props.comment.id)
  props.comment.liked = res.liked
  props.comment.like_count = res.like_count
}

const handleReplyLike = async (reply) => {
  if (guestLocked.value) return
  if (!requireLogin()) return
  const res = await postStore.commentLike(reply.id)
  reply.liked = res.liked
  reply.like_count = res.like_count
}

function openReply(target) {
  if (guestLocked.value) return
  if (!requireLogin()) return
  replyTo.value = target ? { id: target.id } : { id: null }
}

const submitReply = async (target, text) => {
  if (!requireLogin()) return
  const content = (text || '').trim()
  if (!content) return
  const postId = props.comment.post_id
  replySubmitting.value = true
  try {
    // 顶层评论与回复走同一个接口，回复多带一个 parent_id
    const reply = await postStore.comment(postId, content, target?.id ?? null)
    if (target) {
      // 挂在承载它的那条根评论下面；找不到就不插（见 ReviewItem 里同样的取舍）
      const root = findRoot(target.id)
      if (root) {
        if (!root.replies) root.replies = []
        root.replies.push(reply)
      }
    } else {
      if (!props.comment.replies) props.comment.replies = []
      props.comment.replies.push(reply)
    }
    props.comment.reply_count = (props.comment.reply_count || 0) + 1
    replyTo.value = null
  } finally {
    replySubmitting.value = false
  }
}

function findRoot(targetId) {
  const replies = props.comment.replies || []
  return (
    replies.find((r) => r.id === targetId) ||
    replies.find((r) => (r.replies || []).some((c) => c.id === targetId)) ||
    null
  )
}

const loadMoreReplies = async () => {
  repliesLoading.value = true
  try {
    const data = await postStore.fetchCommentReplies(props.comment.id, { page: 1, page_size: 50 })
    props.comment.replies = data.items || []
  } finally {
    repliesLoading.value = false
  }
}
</script>

<style scoped>
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
  margin: 0 0 6px;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.comment-ops {
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
/* 头像可点进评论者主页 */
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
</style>
