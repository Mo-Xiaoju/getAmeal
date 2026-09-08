<template>
  <div class="app-container">
    <NavBar />
    <main class="app-main">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

<script setup>
// 根组件：整体布局（导航栏 + 页面内容 + 页脚）
import { watch } from 'vue'

import Footer from './components/Footer.vue'
import NavBar from './components/NavBar.vue'
import { useChatStore } from '@/store/chat'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const chatStore = useChatStore()

// 登录态变化时维护实时连接：登录即连接、登出即断开（含刷新后恢复）
watch(
  () => userStore.token,
  (token) => {
    if (token) {
      chatStore.connect()
      // 刷新后 userInfo 为空，用 token 拉回账号资料（登录流程已赋值则自动跳过）
      userStore.restoreSession()
    } else {
      chatStore.disconnect()
    }
  },
  { immediate: true },
)
</script>
