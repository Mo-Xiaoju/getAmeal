<template>
  <header class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="navbar-brand">
        <el-icon class="navbar-logo"><Bowl /></el-icon>
        <span class="navbar-title">校园美食</span>
      </router-link>

      <nav class="navbar-menu">
        <router-link to="/" class="nav-link" :class="{ active: isActive('/') }">首页</router-link>
        <router-link to="/shops" class="nav-link" :class="{ active: isActive('/shops') }">店铺</router-link>
        <router-link to="/posts" class="nav-link" :class="{ active: isActive('/posts') }">笔记</router-link>
        <router-link to="/circles" class="nav-link" :class="{ active: isActive('/circles') }">圈子</router-link>
        <router-link to="/chat" class="nav-link" :class="{ active: isActive('/chat') }">校园群聊</router-link>
        <!-- 商户常驻入口：让"发布/管理店铺"始终可见，不依赖头像下拉 -->
        <router-link
          v-if="userStore.isMerchant"
          to="/merchant"
          class="nav-link nav-link-merchant"
          :class="{ active: isActive('/merchant') }"
        >
          <el-icon><Shop /></el-icon><span>商户中心</span>
        </router-link>
      </nav>

      <div class="navbar-right">
        <!-- 当前学校 -->
        <router-link
          v-if="schoolStore.hasSchool"
          to="/choose-school"
          class="school-chip"
          title="切换学校"
        >
          <el-icon><School /></el-icon>
          <span class="school-chip-name">{{ schoolStore.currentSchool.name }}</span>
        </router-link>
        <router-link v-else to="/choose-school" class="school-chip school-chip-empty">
          选择学校
        </router-link>

        <!-- 未登录 -->
        <template v-if="!userStore.isLoggedIn">
          <router-link to="/login"><el-button type="primary" plain class="login-btn">登录</el-button></router-link>
          <router-link to="/register"><el-button type="primary">注册</el-button></router-link>
        </template>

        <!-- 已登录 -->
        <template v-else>
          <router-link
            to="/messages"
            class="dm-link"
            :class="{ active: isActive('/messages') }"
            title="私信"
          >
            <el-badge :value="chatStore.unreadCount" :hidden="!chatStore.unreadCount" :max="99">
              <el-icon class="dm-icon"><ChatLineRound /></el-icon>
            </el-badge>
          </router-link>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-trigger">
              <el-avatar :size="30" :src="userStore.userInfo?.avatar_url || undefined">
                {{ (userStore.nickname || 'U').charAt(0) }}
              </el-avatar>
              <span class="user-name">{{ userStore.nickname || userStore.userInfo?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人中心
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isMerchant" command="merchant">
                  <el-icon><Shop /></el-icon>商户中心
                </el-dropdown-item>
                <el-dropdown-item v-if="!userStore.isMerchant" command="contribute">
                  <el-icon><EditPen /></el-icon>提交商户 / 菜单
                </el-dropdown-item>
                <el-dropdown-item v-if="!userStore.isMerchant" command="favorites">
                  <!-- 与列表卡片 / 详情页同一对图标：全站"点赞 = 大拇指，收藏 = 五角星"；
                       这里是入口不是状态，两枚都用描边款 -->
                  <el-icon><StarIcon /></el-icon>我的收藏
                </el-dropdown-item>
                <el-dropdown-item v-if="!userStore.isMerchant" command="likes">
                  <el-icon><ThumbUpIcon /></el-icon>我的点赞
                </el-dropdown-item>
                <el-dropdown-item v-if="!userStore.isMerchant" command="history">
                  <el-icon><Clock /></el-icon>浏览记录
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" command="admin">
                  <el-icon><Setting /></el-icon>管理后台
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown, Bowl, ChatLineRound, Clock, EditPen, School, Setting, Shop,
  SwitchButton, User,
} from '@element-plus/icons-vue'

import StarIcon from '@/components/StarIcon.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { useChatStore } from '@/store/chat'
import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const schoolStore = useSchoolStore()
const chatStore = useChatStore()

const isActive = (path) => (path === '/' ? route.path === '/' : route.path.startsWith(path))

// 登录期间轮询未读私信，驱动私信入口红点
let unreadTimer = null
const stopUnreadTimer = () => {
  if (unreadTimer) {
    clearInterval(unreadTimer)
    unreadTimer = null
  }
}
watch(
  () => userStore.isLoggedIn,
  (logged) => {
    if (logged) {
      chatStore.refreshUnread()
      stopUnreadTimer()
      unreadTimer = setInterval(() => chatStore.refreshUnread(), 15000)
    } else {
      stopUnreadTimer()
      chatStore.unreadCount = 0
    }
  },
  { immediate: true },
)
onMounted(() => {
  // 挂载时兜底一次（覆盖 watch immediate 时 token 未就绪的边缘情况）
  if (userStore.isLoggedIn) chatStore.refreshUnread()
})
onBeforeUnmount(stopUnreadTimer)

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'merchant') {
    router.push('/merchant')
  } else if (command === 'contribute') {
    router.push('/contribute')
  } else if (command === 'favorites') {
    router.push('/profile/favorites')
  } else if (command === 'likes') {
    router.push('/profile/likes')
  } else if (command === 'history') {
    router.push('/profile/history')
  } else if (command === 'admin') {
    router.push('/admin')
  } else if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
    } catch (e) {
      return
    }
    await userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.navbar {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 100;
}
.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 28px;
}
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: #303133;
}
.navbar-logo {
  font-size: 26px;
  color: var(--el-color-primary);
}
.navbar-title {
  font-size: 18px;
  font-weight: 700;
}
.navbar-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.nav-link {
  padding: 6px 12px;
  border-radius: 6px;
  color: #606266;
  text-decoration: none;
  font-size: 15px;
  transition: all 0.2s;
}
.nav-link:hover {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.nav-link.active {
  color: var(--el-color-primary);
  font-weight: 600;
}
.nav-link-merchant {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--el-color-primary);
  color: #fff;
  border-radius: 16px;
  padding: 5px 14px;
  font-weight: 600;
}
.nav-link-merchant:hover {
  background: var(--el-color-primary-light-3);
  color: #fff;
}
.nav-link-merchant.active {
  background: var(--el-color-primary-dark-2);
  color: #fff;
}
.navbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
/* 登录按钮悬停不再填成实心主色（会与"注册"完全一样），改为淡底加深、文字保持主色，
   与 school-chip 悬停同一套色阶；覆盖 Element 的 --el-button-hover-* 变量 */
.navbar-right .login-btn.el-button {
  --el-button-hover-text-color: var(--el-color-primary);
  --el-button-hover-bg-color: var(--el-color-primary-light-7);
  --el-button-hover-border-color: var(--el-color-primary-light-5);
}
.dm-link {
  display: inline-flex;
  align-items: center;
  color: #606266;
  padding: 4px 2px;
  border-radius: 6px;
}
.dm-link.active {
  color: var(--el-color-primary);
}
.dm-link:hover {
  color: var(--el-color-primary);
}
.dm-icon {
  font-size: 20px;
}
.school-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 16px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 13px;
  text-decoration: none;
  transition: all 0.2s;
  max-width: 160px;
}
.school-chip:hover {
  background: var(--el-color-primary-light-7);
}
.school-chip-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.school-chip-empty {
  background: #fff;
  border: 1px dashed var(--el-color-primary);
  color: var(--el-color-primary);
  font-weight: 600;
}
.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  outline: none;
}
.user-trigger:hover {
  background: var(--el-color-primary-light-9);
}
.user-name {
  font-size: 14px;
  color: #303133;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
