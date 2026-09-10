import { useRouter } from 'vue-router'

import { useUserStore } from '@/store/user'

/**
 * 统一的「点人」跳转：全站头像 / 昵称的点击都走这里。
 *
 * 点自己回个人中心——/user/:id 对本人展示关注/私信按钮没有意义，
 * 而且后端 toggle_follow 会直接拒绝关注自己。
 */
export function useUserNav() {
  const router = useRouter()
  const userStore = useUserStore()

  const goUser = (id) => {
    if (!id) return
    router.push(id === userStore.userInfo?.id ? '/profile' : `/user/${id}`)
  }

  return { goUser }
}
