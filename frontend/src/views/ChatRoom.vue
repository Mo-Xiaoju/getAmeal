<template>
  <div class="school-chat-page">
    <div class="chat-card">
      <!-- 未选择学校：引导先选校 -->
      <div v-if="!schoolStore.hasSchool" class="no-school">
        <el-empty description="请先选择学校，再进入本校校园群聊">
          <el-button type="primary" @click="router.push('/choose-school')">去选择学校</el-button>
        </el-empty>
      </div>

      <template v-else>
        <div class="chat-head">
          <div class="chat-title">
            <el-icon class="chat-title-icon"><ChatDotRound /></el-icon>
            <span>{{ schoolStore.currentSchool.name }} · 校园群聊</span>
            <el-tag v-if="chatStore.connected" size="small" type="success" effect="light">实时在线</el-tag>
            <el-tag v-else size="small" type="info" effect="light">未连接</el-tag>
          </div>
          <span class="chat-sub">全校同学的公共群聊，文明发言～</span>
        </div>
        <ChatPanel
          :key="`school-${schoolStore.currentSchool.id}`"
          :channel="{ type: 'school', id: schoolStore.currentSchool.id }"
          class="chat-body"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
// 校园群聊（全校大群，按学校隔离）：/chat，需登录
import { useRouter } from 'vue-router'
import { ChatDotRound } from '@element-plus/icons-vue'

import ChatPanel from '@/components/ChatPanel.vue'
import { useChatStore } from '@/store/chat'
import { useSchoolStore } from '@/store/school'

const router = useRouter()
const schoolStore = useSchoolStore()
const chatStore = useChatStore()
</script>

<style scoped>
.school-chat-page {
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
.no-school {
  margin: auto;
}
.chat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.chat-title-icon {
  color: var(--el-color-primary);
  font-size: 20px;
}
.chat-sub {
  font-size: 13px;
  color: #909399;
}
.chat-body {
  flex: 1;
  min-height: 0;
}
</style>
