<template>
  <div class="chat-panel">
    <div ref="scrollEl" class="chat-scroll">
      <div v-loading="loading && !messages.length" class="chat-list">
        <div v-if="!loading && !messages.length" class="chat-empty">
          <el-empty :image-size="80" description="还没有消息，来打个招呼吧～" />
        </div>

        <template v-else>
          <div v-if="!noMore" class="chat-load-earlier">
            <el-button size="small" text type="primary" :loading="loadingEarlier" @click="loadEarlier">
              加载更早的消息
            </el-button>
          </div>

          <div
            v-for="m in messages"
            :key="m.id"
            :class="['msg-row', isMine(m) ? 'mine' : '']"
          >
            <div class="msg-main">
              <div class="msg-meta">
                <span v-if="!isMine(m)" class="msg-name">
                  {{ m.author?.nickname || `用户${m.user_id}` }}
                </span>
                <span class="msg-time">{{ formatDateTime(m.created_at) }}</span>
              </div>
              <div class="msg-bubble">{{ m.content }}</div>
            </div>
            <el-avatar :size="34" :src="m.author?.avatar_url || undefined" class="msg-avatar">
              {{ (m.author?.nickname || 'U').charAt(0) }}
            </el-avatar>
          </div>
        </template>
      </div>
    </div>

    <MessageInput @send="handleSendText" />
  </div>
</template>

<script setup>
// 通用聊天面板：圈子群聊 / 全校群聊 / 私信三处复用。
// props.channel = { type: 'circle' | 'school' | 'dm', id }
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import * as chatApi from '@/api/chat'
import * as circleApi from '@/api/circle'
import * as dmApi from '@/api/dm'
import MessageInput from '@/components/MessageInput.vue'
import { useChatStore } from '@/store/chat'
import { useUserStore } from '@/store/user'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  channel: { type: Object, required: true }, // { type, id }
})

const PAGE_SIZE = 30
const userStore = useUserStore()
const chatStore = useChatStore()

const messages = ref([])
const loading = ref(false)
const loadingEarlier = ref(false)
const noMore = ref(false)
const scrollEl = ref(null)

const myId = () => userStore.userInfo?.id

// 按渠道挑选历史消息 API
function historyApi(params) {
  const { type, id } = props.channel
  if (type === 'circle') return circleApi.getCircleMessages(id, params)
  if (type === 'dm') return dmApi.getPeerMessages(id, params)
  return chatApi.getSchoolMessages({ ...params, school_id: id })
}

function isMine(m) {
  return m.user_id === myId()
}

function scrollToBottom(smooth = false) {
  const el = scrollEl.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
}

async function loadLatest() {
  loading.value = true
  try {
    const res = await historyApi({ page: 1, page_size: PAGE_SIZE })
    const data = res.data.data
    messages.value = data.items || []
    noMore.value = messages.value.length >= (data.total || 0)
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

async function loadEarlier() {
  const oldest = messages.value[0]
  if (!oldest || loadingEarlier.value) return
  loadingEarlier.value = true
  try {
    const el = scrollEl.value
    const prevHeight = el ? el.scrollHeight : 0
    const res = await historyApi({ page: 1, page_size: PAGE_SIZE, before_id: oldest.id })
    const older = res.data.data.items || []
    messages.value = [...older, ...messages.value]
    noMore.value = older.length === 0
    // 保持视口位置：插入旧消息后补偿高度差
    requestAnimationFrame(() => {
      if (el) el.scrollTop = el.scrollHeight - prevHeight
    })
  } finally {
    loadingEarlier.value = false
  }
}

function appendMessage(m) {
  if (!m || messages.value.some((x) => x.id === m.id)) return
  const nearBottom = scrollEl.value && scrollEl.value.scrollHeight - scrollEl.value.scrollTop - scrollEl.value.clientHeight < 90
  messages.value.push(m)
  if (nearBottom) scrollToBottom(true)
}

// 订阅服务端实时消息（与当前会话渠道匹配才接收）
function handleIncoming(channel, message) {
  const cur = props.channel
  if (!channel || channel.type !== cur.type || channel.id !== cur.id) return
  appendMessage(message)
  // 主动打开私信会话时，实时把对方新消息标记为已读
  if (cur.type === 'dm' && message.author?.id !== myId()) {
    dmApi.markPeerRead(cur.id).catch(() => {})
    chatStore.refreshUnread()
  }
}

// 发送：优先实时 socket，失败走对应 REST 兜底
async function handleSendText(text) {
  const { type, id } = props.channel
  const channel = { type, id }
  try {
    const ack = await chatStore.sendLive(channel, text)
    if (!ack || ack.ok === false) {
      throw new Error(ack?.message || '发送失败')
    }
    // 发送成功：回显消息会经 socket message 事件收到，无需本地追加
  } catch (err) {
    // socket 离线/超时 → REST 兜底（circle 无专用端点则用群消息 REST）
    try {
      let res
      if (type === 'circle') res = await circleApi.sendCircleMessage(id, { content: text })
      else if (type === 'dm') res = await dmApi.sendDm({ recipient_id: id, content: text })
      else res = await chatApi.sendSchoolMessage({ content: text })
      const msg = res.data.data
      appendMessage(msg)
    } catch (restErr) {
      ElMessage.error(restErr?.message || '发送失败，请检查网络后重试')
    }
  }
}

// 会话切换时重新拉历史
watch(
  () => `${props.channel?.type}:${props.channel?.id}`,
  () => {
    if (props.channel?.id) loadLatest()
  },
)

let unsubscribe = null
onMounted(() => {
  unsubscribe = chatStore.subscribe(handleIncoming)
  loadLatest()
})
onBeforeUnmount(() => {
  if (unsubscribe) unsubscribe()
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: #f5f7fa;
}
.chat-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 0;
}
.chat-list {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}
.chat-empty {
  margin: auto;
}
.chat-load-earlier {
  text-align: center;
  padding: 4px 0;
}
.msg-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 16px;
}
.msg-row.mine {
  flex-direction: row-reverse;
}
.msg-avatar {
  flex-shrink: 0;
}
.msg-main {
  max-width: 62%;
  display: flex;
  flex-direction: column;
}
.msg-row.mine .msg-main {
  align-items: flex-end;
}
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 3px;
}
.msg-row.mine .msg-meta {
  flex-direction: row-reverse;
}
.msg-name {
  font-size: 12px;
  color: #909399;
}
.msg-time {
  font-size: 11px;
  color: #c0c4cc;
}
.msg-bubble {
  background: #fff;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
  word-break: break-word;
  white-space: pre-wrap;
}
.msg-row.mine .msg-bubble {
  background: var(--el-color-primary);
  color: #fff;
}
</style>
