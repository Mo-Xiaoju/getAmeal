<template>
  <div class="circle-chat-page">
    <div v-loading="loading && !circleStore.detail" class="chat-card">
      <template v-if="circleStore.detail">
        <div class="chat-head">
          <div class="head-left">
            <el-button text :icon="ArrowLeft" @click="router.push('/circles')">圈子</el-button>
            <el-avatar :size="40" shape="square" :src="circleStore.detail.cover_url || undefined">
              <el-icon><ChatRound /></el-icon>
            </el-avatar>
            <div class="head-info">
              <div class="head-name">
                {{ circleStore.detail.name }}
                <el-tag v-if="isOwner" size="small" type="warning" effect="plain">我创建的</el-tag>
              </div>
              <div class="head-sub">
                {{ circleStore.detail.member_count }} 名成员
                <template v-if="circleStore.detail.creator">
                  · 创建者 {{ circleStore.detail.creator.nickname }}
                </template>
              </div>
            </div>
          </div>

          <div class="head-actions">
            <el-button size="small" :icon="User" @click="openMembers">成员</el-button>
            <template v-if="isOwner">
              <el-button size="small" :icon="EditPen" @click="openEdit">编辑</el-button>
              <el-button size="small" type="danger" plain :icon="Delete" @click="handleDissolve">
                解散圈子
              </el-button>
            </template>
            <el-button
              v-else-if="circleStore.detail.joined"
              size="small"
              type="info"
              plain
              @click="handleLeave"
            >
              退出圈子
            </el-button>
          </div>
        </div>

        <!-- 已加入：圈内实时群聊 -->
        <ChatPanel
          v-if="circleStore.detail.joined"
          :channel="{ type: 'circle', id: circleStore.detail.id }"
          class="chat-body"
        />

        <!-- 未加入：展示简介，引导加入（非成员不可见聊天记录） -->
        <div v-else class="join-panel">
          <el-empty :image-size="90" description="加入圈子后即可参与圈内群聊">
            <div class="join-desc">
              {{ circleStore.detail.description || '这个圈子还没有简介，进圈聊聊就知道啦～' }}
            </div>
            <el-button type="primary" size="large" :loading="joining" @click="handleJoin">
              加入圈子
            </el-button>
          </el-empty>
        </div>
      </template>
    </div>

    <!-- 成员列表 -->
    <el-drawer v-model="membersVisible" :title="`成员 · ${circleStore.detail?.member_count || ''}`" size="340px">
      <div class="member-list">
        <div v-for="m in circleStore.members" :key="m.id" class="member-row">
          <el-avatar :size="36" :src="m.avatar_url || undefined">
            {{ (m.nickname || 'U').charAt(0) }}
          </el-avatar>
          <span class="member-name">{{ m.nickname }}</span>
          <el-tag v-if="m.id === circleStore.detail?.creator?.id" size="small" type="warning">创建者</el-tag>
        </div>
      </div>
    </el-drawer>

    <!-- 编辑圈子（仅创建者） -->
    <el-dialog v-model="editVisible" title="编辑圈子" width="440px">
      <el-form label-width="72px" @submit.prevent>
        <el-form-item label="圈子名称" required>
          <el-input v-model="editForm.name" maxlength="60" show-word-limit />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="封面图">
          <el-input v-model="editForm.cover_url" placeholder="图片 URL（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 圈子详情/群聊页：/circles/:id，需登录（未加入者先加入再看聊天）
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, ChatRound, Delete, EditPen, User,
} from '@element-plus/icons-vue'

import ChatPanel from '@/components/ChatPanel.vue'
import { useChatStore } from '@/store/chat'
import { useCircleStore } from '@/store/circle'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const circleStore = useCircleStore()
const chatStore = useChatStore()
const userStore = useUserStore()

const loading = ref(false)
const joining = ref(false)
const savingEdit = ref(false)
const membersVisible = ref(false)
const editVisible = ref(false)
const editForm = reactive({ name: '', description: '', cover_url: '' })

const detailId = computed(() => Number(route.params.id))
const isOwner = computed(
  () =>
    circleStore.detail?.creator?.id &&
    userStore.userInfo?.id === circleStore.detail.creator.id,
)

async function loadDetail() {
  loading.value = true
  try {
    await circleStore.fetchDetail(detailId.value)
  } catch (e) {
    ElMessage.error(e?.message || '圈子不存在')
    router.replace('/circles')
  } finally {
    loading.value = false
  }
}

async function handleJoin() {
  if (!userStore.isLoggedIn) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  joining.value = true
  try {
    await circleStore.join(detailId.value, (joined) => chatStore.emitCircleJoin(joined, detailId.value))
    ElMessage.success('已加入圈子')
  } catch (e) {
    ElMessage.error(e?.message || '加入失败')
  } finally {
    joining.value = false
  }
}

async function handleLeave() {
  try {
    await ElMessageBox.confirm('退出后将不再看到圈内消息，确定退出吗？', '退出圈子', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch (e) {
    return
  }
  try {
    await circleStore.join(detailId.value, (joined) => chatStore.emitCircleJoin(joined, detailId.value))
    ElMessage.success('已退出圈子')
  } catch (e) {
    ElMessage.error(e?.message || '退出失败')
  }
}

async function handleDissolve() {
  try {
    await ElMessageBox.confirm('解散后聊天记录不再可见且无法恢复，确定解散吗？', '解散圈子', {
      confirmButtonText: '解散',
      cancelButtonText: '取消',
      type: 'error',
    })
  } catch (e) {
    return
  }
  try {
    await circleStore.remove(detailId.value)
    ElMessage.success('已解散圈子')
    router.replace('/circles')
  } catch (e) {
    ElMessage.error(e?.message || '解散失败')
  }
}

function openMembers() {
  membersVisible.value = true
  circleStore.fetchMembers(detailId.value, { page_size: 60 }).catch(() => {})
}

function openEdit() {
  const d = circleStore.detail || {}
  Object.assign(editForm, {
    name: d.name,
    description: d.description || '',
    cover_url: d.cover_url || '',
  })
  editVisible.value = true
}

async function handleEdit() {
  if (!editForm.name.trim()) {
    ElMessage.warning('请填写圈子名称')
    return
  }
  savingEdit.value = true
  try {
    await circleStore.update(detailId.value, {
      name: editForm.name.trim(),
      description: editForm.description.trim(),
      cover_url: editForm.cover_url.trim() || undefined,
    })
    editVisible.value = false
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    savingEdit.value = false
  }
}

onMounted(loadDetail)
onBeforeUnmount(() => {
  circleStore.detail = null
})
</script>

<style scoped>
.circle-chat-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px;
}
.chat-card {
  height: calc(100vh - 180px);
  min-height: 420px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.head-info {
  min-width: 0;
}
.head-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.head-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}
.head-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.chat-body {
  flex: 1;
  min-height: 0;
}
.join-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}
.join-desc {
  max-width: 360px;
  color: #909399;
  font-size: 13px;
  margin: 4px auto 18px;
  white-space: pre-wrap;
  word-break: break-word;
}
.member-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.member-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 8px;
}
.member-row:hover {
  background: #f5f7fa;
}
.member-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
}
</style>
