import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/store/user'

/**
 * 未登录访客的交互闸门。
 *
 * 需要登录才能用的输入框 / 按钮统一绑 `guestLocked` 置灰：游客一眼看到「这里要登录」，
 * 而不是先被引导着输入一遍，点提交时才被跳走、内容白写。
 *
 * `requireLogin` 保留作兜底（如页面打开期间 token 失效），不再是主要的拦截手段。
 */
export function useLoginGate() {
  const route = useRoute()
  const router = useRouter()
  const userStore = useUserStore()

  const isLoggedIn = computed(() => userStore.isLoggedIn)
  // 绑到 :disabled —— 未登录时输入框不可聚焦、按钮不可点
  const guestLocked = computed(() => !userStore.isLoggedIn)
  // 登录后回跳当前页
  const loginTo = computed(() => ({ path: '/login', query: { redirect: route.fullPath } }))
  const goLogin = () => router.push(loginTo.value)

  const requireLogin = () => {
    if (userStore.isLoggedIn) return true
    ElMessage.warning('请先登录')
    goLogin()
    return false
  }

  return { isLoggedIn, guestLocked, loginTo, goLogin, requireLogin }
}
