<template>
  <div v-if="replyCount" class="reply-thread">
    <div v-for="r in replies" :key="r.id" class="reply-row">
      <el-avatar
        class="user-link"
        :size="26"
        :src="r.avatar_url || undefined"
        @click="goUser(r.user_id)"
      >
        {{ (r.nickname || 'U').charAt(0) }}
      </el-avatar>
      <div class="reply-body">
        <div class="reply-head">
          <span class="reply-nickname">{{ r.nickname || '匿名用户' }}</span>
          <!-- 回复某条回复时显示 @对象。服务端从父评论作者派生，前端只展示 -->
          <span v-if="r.reply_to_nickname" class="reply-to">回复 @{{ r.reply_to_nickname }}</span>
          <span class="reply-time">{{ formatDate(r.created_at) }}</span>
        </div>
        <p class="reply-content">{{ r.content }}</p>
        <div class="reply-ops">
          <span
            class="op"
            :class="{ 'is-liked': r.liked, 'is-locked': guestLocked || !canReply }"
            @click="onLike(r)"
          >
            <el-icon><ThumbUpIcon :filled="!!r.liked" /></el-icon>
            {{ r.like_count || 0 }}
          </span>
          <span v-if="canReply" class="op" @click="$emit('reply', r)">回复</span>
        </div>

        <!-- 子回复：回复固定两层，这里不会再往下嵌套 -->
        <div v-if="r.replies && r.replies.length" class="reply-children">
          <div v-for="c in r.replies" :key="c.id" class="reply-row">
            <el-avatar
              class="user-link"
              :size="22"
              :src="c.avatar_url || undefined"
              @click="goUser(c.user_id)"
            >
              {{ (c.nickname || 'U').charAt(0) }}
            </el-avatar>
            <div class="reply-body">
              <div class="reply-head">
                <span class="reply-nickname">{{ c.nickname || '匿名用户' }}</span>
                <span v-if="c.reply_to_nickname" class="reply-to">回复 @{{ c.reply_to_nickname }}</span>
                <span class="reply-time">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="reply-content">{{ c.content }}</p>
              <div class="reply-ops">
                <span
                  class="op"
                  :class="{ 'is-liked': c.liked, 'is-locked': guestLocked || !canReply }"
                  @click="onLike(c)"
                >
                  <el-icon><ThumbUpIcon :filled="!!c.liked" /></el-icon>
                  {{ c.like_count || 0 }}
                </span>
                <span v-if="canReply" class="op" @click="$emit('reply', c)">回复</span>
              </div>
              <ReplyComposer
                v-if="isComposing(c)"
                :nickname="c.nickname"
                :guest-locked="guestLocked"
                :submitting="submitting"
                @submit="(text) => $emit('submit', { target: c, content: text })"
                @cancel="$emit('cancel')"
              />
            </div>
          </div>
        </div>

        <!-- 回复框挂在被点的那条下面（回复子回复时也挂在它自己下方，服务端归一化到根） -->
        <ReplyComposer
          v-if="isComposing(r)"
          :nickname="r.nickname"
          :guest-locked="guestLocked"
          :submitting="submitting"
          @submit="(text) => $emit('submit', { target: r, content: text })"
          @cancel="$emit('cancel')"
        />
      </div>
    </div>

    <div v-if="hasMore" class="reply-more">
      <el-button text type="primary" :loading="loading" @click="$emit('load-more')">
        查看全部 {{ replyCount }} 条回复
      </el-button>
    </div>
  </div>
</template>

<script setup>
// 回复区（纯展示组件：props 进、事件出，自己不碰接口也不碰 store 的数据）。
// 评价卡与笔记评论卡共用，所以两边的回复行为天然一致。
//
// 数据形状由后端决定：每条根回复自带最多 3 条子回复预览，reply_count 是
// 「根回复 + 子回复」的总数，展开全部走 GET /<review|comment>/<id>/replies。
import { computed } from 'vue'

import ReplyComposer from '@/components/ReplyComposer.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { useUserNav } from '@/composables/useUserNav'

const props = defineProps({
  replies: { type: Array, default: () => [] },
  replyCount: { type: Number, default: 0 },
  // 正在展开更多回复（按钮转圈）
  loading: { type: Boolean, default: false },
  // 正在提交回复（回复框的按钮转圈）
  submitting: { type: Boolean, default: false },
  // 当前展开回复框的目标：null 关闭，{ id } 命中哪条就挂在哪条下面
  replyTo: { type: Object, default: null },
  guestLocked: { type: Boolean, default: false },
  // 商户只读（后端 4031），由父级按 userStore.isMerchant 传进来
  canReply: { type: Boolean, default: true },
})
const emit = defineEmits(['reply', 'like', 'load-more', 'submit', 'cancel'])

const { goUser } = useUserNav()

// 已加载的回复条数 = 根回复 + 各自带的子回复。
// 拿它跟 reply_count 比，而不是跟 replies.length 比 —— reply_count 把子回复也算进去了，
// 两个口径不同的话按钮会在展开后仍然赖着不走。
const loadedCount = computed(
  () =>
    props.replies.length +
    props.replies.reduce((n, r) => n + ((r.replies && r.replies.length) || 0), 0),
)
const hasMore = computed(() => props.replyCount > loadedCount.value)

const isComposing = (reply) => !!props.replyTo && props.replyTo.id === reply.id

function onLike(reply) {
  if (props.guestLocked || !props.canReply) return
  emit('like', reply)
}

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.reply-thread {
  margin-top: 10px;
  padding-left: 12px;
  border-left: 2px solid #f2f3f5;
}
.reply-row {
  display: flex;
  gap: 10px;
  padding: 8px 0;
}
.reply-body {
  flex: 1;
  min-width: 0;
}
.reply-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 2px;
}
.reply-nickname {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.reply-to {
  font-size: 12px;
  color: var(--el-color-primary);
}
.reply-time {
  font-size: 12px;
  color: #c0c4cc;
}
.reply-content {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.reply-ops {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 2px;
}
.op {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
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
/* 游客 / 商户：不可点，连 hover 变色也一并去掉，免得看着像能点 */
.op.is-locked {
  cursor: not-allowed;
}
.op.is-locked:hover {
  color: #909399;
}
.op.is-liked.is-locked:hover {
  color: var(--el-color-danger);
}
.reply-children {
  margin-top: 4px;
  padding-left: 10px;
  border-left: 2px solid #f7f8fa;
}
.reply-more {
  padding: 4px 0 0;
}
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
</style>
