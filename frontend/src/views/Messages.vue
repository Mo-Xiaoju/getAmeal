<template>
  <div class="messages-page">
    <div class="messages-pane">
      <!-- 左：会话列表 -->
      <aside class="pane-left">
        <div class="conv-head">私信</div>
        <div class="conv-list">
          <div
            v-for="c in convs"
            :key="c.peer.id"
            :class="['conv-item', { active: activePeer?.id === c.peer.id }]"
            @click="openPeer(c.peer)"
          >
            <el-badge :value="c.unread_count" :hidden="!c.unread_count" :max="99" class="conv-badge">
              <!-- .stop：整行是「打开会话」，点头像要进对方主页 -->
              <el-avatar
                class="user-link"
                :size="40"
                :src="c.peer.avatar_url || undefined"
                @click.stop="goUser(c.peer.id)"
              >
                {{ (c.peer.nickname || 'U').charAt(0) }}
              </el-avatar>
            </el-badge>
            <div class="conv-main">
              <div class="conv-top">
                <span class="conv-name">{{ c.peer.nickname }}</span>
                <span class="conv-time">{{ formatConversationTime(c.last_message?.created_at) }}</span>
              </div>
              <div class="conv-preview">{{ previewOf(c) }}</div>
            </div>
          </div>

          <div v-if="!loadingConvs && !convs.length" class="conv-empty">
            <el-empty :image-size="60" description="还没有私信" />
          </div>
        </div>

        <!-- 推荐联系人：贴底常驻，有会话时也可见，随时能发起新私信 -->
        <div v-if="suggestions.length" class="conv-suggest">
          <div class="suggest-head">推荐联系人</div>
          <div class="suggest-list">
            <div
              v-for="s in suggestions"
              :key="s.id"
              :class="['suggest-item', { active: activePeer?.id === s.id }]"
              @click="openPeer(s)"
            >
              <el-avatar :size="34" :src="s.avatar_url || undefined">
                {{ (s.nickname || 'U').charAt(0) }}
              </el-avatar>
              <span class="suggest-name">{{ s.nickname || s.username }}</span>
              <el-tag size="small" type="info" effect="plain">{{ s.reason }}</el-tag>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右：会话窗口 -->
      <section class="pane-right">
        <template v-if="activePeer">
          <div class="conv-title">
            <el-avatar
              class="user-link"
              :size="30"
              :src="activePeer.avatar_url || undefined"
              @click="goUser(activePeer.id)"
            >
              {{ (activePeer.nickname || 'U').charAt(0) }}
            </el-avatar>
            <span>{{ activePeer.nickname }}</span>
          </div>
          <ChatPanel
            :key="`dm-${activePeer.id}`"
            :channel="{ type: 'dm', id: activePeer.id }"
            class="pane-body"
          />
        </template>
        <div v-else class="pane-empty">
          <el-empty description="选择一个会话开始聊天，或从关注/粉丝列表发起私信" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
// 私信页：/messages 与 /messages/:userId（双栏微信式）
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import * as dmApi from '@/api/dm'
import ChatPanel from '@/components/ChatPanel.vue'
import { useUserNav } from '@/composables/useUserNav'
import { useChatStore } from '@/store/chat'
import { useUserStore } from '@/store/user'
import { formatConversationTime } from '@/utils/format'

const route = useRoute()
const chatStore = useChatStore()
const userStore = useUserStore()
const { goUser } = useUserNav()

const convs = ref([])
const activePeer = ref(null)
const loadingConvs = ref(false)
const suggestions = ref([])

// 从路由解析发起会话的对端资料（/messages/:userId?peer=...）
function initialPeer() {
  const id = Number(route.params.userId)
  if (!id) return null
  let extra = {}
  try {
    if (route.query.peer) extra = JSON.parse(route.query.peer) || {}
  } catch (e) {
    extra = {}
  }
  return { id, nickname: extra.nickname || extra.username || `用户${id}`, avatar_url: extra.avatar_url || '' }
}

function previewOf(c) {
  const t = c.last_message?.content || ''
  return t.replace(/\s+/g, ' ')
}

async function refreshConvs() {
  loadingConvs.value = true
  try {
    const res = await dmApi.getConversations()
    convs.value = res.data.data.items || []
    // 若正在打开的是路由指定的新会话且尚未有消息，也能从列表补全昵称
    if (activePeer.value && route.params.userId) {
      const hit = convs.value.find((c) => c.peer.id === activePeer.value.id)
      if (hit) activePeer.value = { ...hit.peer }
    }
  } catch (e) {
    // 网络异常静默，等待下次轮询
  } finally {
    loadingConvs.value = false
  }
}

// 推荐联系人（官方助手 / 管理员 / 最近关注）：左栏空置时也能一键开聊
async function loadSuggestions() {
  try {
    const res = await dmApi.getSuggestions()
    suggestions.value = res.data.data?.items || []
  } catch (e) {
    suggestions.value = []
  }
}

async function openPeer(peer) {
  if (!peer || peer.id === userStore.userInfo?.id) return
  activePeer.value = { ...peer }
  try {
    await dmApi.markPeerRead(peer.id)
  } catch (e) {
    // 忽略已读标记失败
  }
  chatStore.refreshUnread()
  refreshConvs()
}

function handleIncoming(channel, message) {
  if (channel?.type !== 'dm') return
  // 非当前会话的私信实时刷新未读数；会话列表常驻刷新以更新预览
  if (!activePeer.value || channel.id !== activePeer.value.id) {
    chatStore.refreshUnread()
  }
  refreshConvs()
}

let unsubscribe = null
let timer = null

onMounted(() => {
  unsubscribe = chatStore.subscribe(handleIncoming)
  const peer = initialPeer()
  if (peer) openPeer(peer)
  refreshConvs()
  loadSuggestions()
  // 会话列表 / 未读数轮询兜底（覆盖 socket 异常断线场景）；推荐联系人一并刷新，
  // 这样刚聊过的人会从推荐区消失、新关注的人会自动出现
  timer = setInterval(() => {
    refreshConvs()
    loadSuggestions()
  }, 15000)
})
onBeforeUnmount(() => {
  if (unsubscribe) unsubscribe()
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.messages-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}
.messages-pane {
  height: calc(100vh - 180px);
  min-height: 440px;
  display: flex;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
}
.pane-left {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}
.conv-head {
  padding: 14px 16px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.conv-item:hover {
  background: #f0f2f5;
}
.conv-item.active {
  background: #e6f1fd;
}
.conv-badge {
  flex-shrink: 0;
}
.conv-main {
  flex: 1;
  min-width: 0;
}
.conv-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.conv-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-time {
  font-size: 11px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.conv-preview {
  font-size: 12px;
  color: #909399;
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-empty {
  padding: 40px 0;
}
/* 推荐联系人：贴底常驻。父级 .pane-left 是纵向 flex，.conv-list 吃满剩余高度，
   这里 flex-shrink:0 保证它不被会话列表挤走，自身超出时内部滚动。 */
.conv-suggest {
  flex-shrink: 0;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
.suggest-head {
  padding: 10px 16px 4px;
  font-size: 13px;
  font-weight: 600;
  color: #909399;
}
.suggest-list {
  max-height: 168px;
  overflow-y: auto;
}
.suggest-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.suggest-item:hover {
  background: #f0f2f5;
}
.suggest-item.active {
  background: #e6f1fd;
}
.suggest-name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* 头像可点进对方主页 */
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
.pane-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}
.conv-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.pane-body {
  flex: 1;
  min-height: 0;
}
.pane-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
