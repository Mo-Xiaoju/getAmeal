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
              <div v-if="m.content" class="msg-bubble">{{ m.content }}</div>
              <!-- 店铺关联标注：纯店卡消息无文字气泡，只渲染店铺卡 -->
              <div v-if="m.shop" class="msg-shop" @click="goShop(m.shop)">
                <img v-if="m.shop.image_url" :src="m.shop.image_url" class="msg-shop-cover" alt="" />
                <div v-else class="msg-shop-cover msg-shop-cover-fallback">
                  <el-icon><Shop /></el-icon>
                </div>
                <div class="msg-shop-info">
                  <div class="msg-shop-name">{{ m.shop.name }}</div>
                  <div class="msg-shop-cat">{{ m.shop.category || '校园店铺' }}</div>
                </div>
                <el-icon class="msg-shop-arrow"><ArrowRight /></el-icon>
              </div>
            </div>
            <el-avatar :size="34" :src="m.author?.avatar_url || undefined" class="msg-avatar">
              {{ (m.author?.nickname || 'U').charAt(0) }}
            </el-avatar>
          </div>
        </template>
      </div>
    </div>

    <!-- 商户账号：仅校园群聊可发言；圈子/私信直接以只读态展示，而非点击后再报错 -->
    <template v-if="canSpeak">
      <!-- 店铺关联标注：校园/圈子群聊提供，私信不提供 -->
      <div v-if="canAnnotate && chatSchoolId" class="shop-pick-row">
        <span class="shop-pick-label">关联店铺</span>
        <el-select
          v-model="selectedShop"
          :loading="shopLoading"
          class="shop-pick"
          filterable
          clearable
          placeholder="选择同校店铺（可选）"
        >
          <el-option v-for="s in shopOptions" :key="s.id" :label="s.name" :value="s" />
        </el-select>
        <span v-if="selectedShop" class="shop-pick-hint">将随消息展示店铺卡片</span>
      </div>
      <MessageInput :allow-empty="!!selectedShop" @send="handleSendText" />
    </template>
    <div v-else class="merchant-readonly">
      <el-icon><Lock /></el-icon>
      <span>商户账号可在校园群聊发言，暂不参与私信 / 圈子群聊</span>
    </div>
  </div>
</template>

<script setup>
// 通用聊天面板：圈子群聊 / 全校群聊 / 私信三处复用。
// props.channel = { type: 'circle' | 'school' | 'dm', id }
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowRight, Lock, Shop } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import * as chatApi from '@/api/chat'
import * as circleApi from '@/api/circle'
import * as dmApi from '@/api/dm'
import * as shopApi from '@/api/shop'
import MessageInput from '@/components/MessageInput.vue'
import { useChatStore } from '@/store/chat'
import { useUserStore } from '@/store/user'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  channel: { type: Object, required: true }, // { type, id }
  schoolId: { type: Number, default: null }, // 圈子群聊所属学校；校园群聊自身即学校，用不到
})
const router = useRouter()

const PAGE_SIZE = 30
const userStore = useUserStore()
const chatStore = useChatStore()

const messages = ref([])
const loading = ref(false)
const loadingEarlier = ref(false)
const noMore = ref(false)
const scrollEl = ref(null)

const myId = () => userStore.userInfo?.id

// 商户：仅校园群聊可发言（圈子/私信只读）
const canSpeak = computed(() => !userStore.isMerchant || props.channel?.type === 'school')
// 店铺关联标注：校园群聊 / 圈子群聊提供，私信不提供
const canAnnotate = computed(() => props.channel?.type === 'school' || props.channel?.type === 'circle')
// 店铺选项所属学校：校园群聊的 channel.id 即学校；圈子用父组件传入 schoolId
const chatSchoolId = computed(() =>
  props.channel?.type === 'school' ? props.channel.id : (props.schoolId || null),
)

// 同校 approved 店铺（供关联标注选择）
const shopOptions = ref([])
const shopLoading = ref(false)
const selectedShop = ref(null)

async function loadShopOptions() {
  if (!canAnnotate.value || !chatSchoolId.value) {
    shopOptions.value = []
    return
  }
  shopLoading.value = true
  try {
    const res = await shopApi.getShopList({ school_id: chatSchoolId.value, page_size: 50 })
    shopOptions.value = res.data.data?.items || []
  } catch (e) {
    shopOptions.value = []
  } finally {
    shopLoading.value = false
  }
}

function goShop(shop) {
  if (shop?.id) router.push(`/shops/${shop.id}`)
}

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
  // nextTick：等 Vue 把刚 push 的消息渲染进 DOM 后再滚，否则 scrollHeight 还是旧值，滚不到位
  nextTick(() => {
    const el = scrollEl.value
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
  })
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
  const isOwn = isMine(m)
  messages.value.push(m)
  // 别人发的消息：正处在底部（正常聊天状态）就自动跟随下滑；在翻历史则不打扰
  // 自己发的消息：一律滑到底，确保发送内容可见（REST 兜底回显与 socket 回显都走这里）
  if (nearBottom || isOwn) scrollToBottom(true)
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
// 纯店卡消息：text 为空但选中了店铺（allowEmpty）→ 仅携带 shop_id
async function handleSendText(text) {
  const { type, id } = props.channel
  const channel = { type, id }
  const shopId = selectedShop.value?.id || null
  if (!text.trim() && !shopId) {
    ElMessage.warning('请输入内容或关联店铺')
    return
  }
  try {
    const ack = await chatStore.sendLive(channel, text, shopId)
    if (!ack || ack.ok === false) {
      throw new Error(ack?.message || '发送失败')
    }
    // 发送成功：回显消息会经 socket message 事件收到，无需本地追加
    selectedShop.value = null
  } catch (err) {
    // socket 离线/超时 → REST 兜底（dm 不支持店铺标注，不带 shop_id）
    try {
      let res
      if (type === 'circle') res = await circleApi.sendCircleMessage(id, { content: text, shop_id: shopId })
      else if (type === 'dm') res = await dmApi.sendDm({ recipient_id: id, content: text })
      else res = await chatApi.sendSchoolMessage({ content: text, shop_id: shopId })
      const msg = res.data.data
      appendMessage(msg)
      selectedShop.value = null
    } catch (restErr) {
      ElMessage.error(restErr?.message || '发送失败，请检查网络后重试')
    }
  }
}

// 会话切换时重新拉历史 + 重载店铺选择
watch(
  () => `${props.channel?.type}:${props.channel?.id}:${chatSchoolId.value}`,
  () => {
    if (props.channel?.id) loadLatest()
    selectedShop.value = null
    loadShopOptions()
  },
)

let unsubscribe = null
onMounted(() => {
  unsubscribe = chatStore.subscribe(handleIncoming)
  loadLatest()
  loadShopOptions()
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
/* 店铺关联标注卡片：气泡下方，可点击跳店铺详情 */
.msg-shop {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
  max-width: 100%;
  padding: 8px 10px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.msg-shop:hover {
  border-color: var(--el-color-primary);
}
.msg-row.mine .msg-shop {
  background: #f0f7ff;
  border-color: var(--el-color-primary-light-5);
}
.msg-shop-cover {
  width: 42px;
  height: 42px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}
.msg-shop-cover-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #c0c4cc;
  font-size: 20px;
}
.msg-shop-info {
  flex: 1;
  min-width: 0;
}
.msg-shop-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-shop-cat {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.msg-shop-arrow {
  color: #c0c4cc;
  flex-shrink: 0;
}
/* 关联店铺选择行 */
.shop-pick-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px 0;
  background: #fff;
}
.shop-pick-label {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
.shop-pick {
  flex: 1;
  min-width: 0;
}
.shop-pick-hint {
  font-size: 12px;
  color: var(--el-color-success);
  white-space: nowrap;
}
/* 商户只读态：替掉输入框，说明身份限制 */
.merchant-readonly {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  font-size: 13px;
  color: #a0a4ab;
  background: #fff;
  border-top: 1px solid #ebeef5;
}
</style>
