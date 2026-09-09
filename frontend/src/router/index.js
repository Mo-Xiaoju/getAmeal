import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

import { getToken } from '@/utils/auth'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/shops',
    name: 'shop-list',
    component: () => import('../views/ShopList.vue'),
    meta: { title: '店铺列表' },
  },
  {
    path: '/shops/:id',
    name: 'shop-detail',
    component: () => import('../views/ShopDetail.vue'),
    meta: { title: '店铺详情' },
  },
  {
    path: '/posts',
    name: 'post-list',
    component: () => import('../views/PostList.vue'),
    meta: { title: '探店笔记' },
  },
  {
    path: '/posts/create',
    name: 'post-create',
    component: () => import('../views/PostCreate.vue'),
    meta: { title: '发布笔记', requiresAuth: true, requiresConsumer: true },
  },
  {
    path: '/posts/:id',
    name: 'post-detail',
    component: () => import('../views/PostDetail.vue'),
    meta: { title: '笔记详情' },
  },
  {
    path: '/dishes/:id',
    name: 'dish-detail',
    component: () => import('../views/DishDetail.vue'),
    meta: { title: '菜品详情' },
  },
  {
    path: '/choose-school',
    name: 'choose-school',
    component: () => import('../views/ChooseSchool.vue'),
    meta: { title: '选择学校' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '个人信息', requiresAuth: true },
  },
  {
    path: '/profile/following',
    name: 'following',
    component: () => import('../views/FollowList.vue'),
    meta: { title: '我的关注', requiresAuth: true },
    props: { mode: 'following' },
  },
  {
    path: '/profile/followers',
    name: 'followers',
    component: () => import('../views/FollowList.vue'),
    meta: { title: '我的粉丝', requiresAuth: true },
    props: { mode: 'followers' },
  },
  {
    path: '/profile/favorites',
    name: 'favorites',
    component: () => import('../views/FavoritesList.vue'),
    meta: { title: '我的收藏', requiresAuth: true },
  },
  {
    path: '/profile/likes',
    name: 'likes',
    component: () => import('../views/LikesList.vue'),
    meta: { title: '我的点赞', requiresAuth: true },
  },
  {
    path: '/profile/history',
    name: 'history',
    component: () => import('../views/HistoryList.vue'),
    meta: { title: '浏览记录', requiresAuth: true },
  },
  {
    path: '/merchant',
    name: 'merchant',
    component: () => import('../views/Merchant.vue'),
    meta: { title: '商户中心', requiresAuth: true, requiresMerchant: true },
  },
  {
    path: '/contribute',
    name: 'contribute',
    component: () => import('../views/Contribute.vue'),
    meta: { title: '提交商户/菜单', requiresAuth: true, requiresConsumer: true },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatRoom.vue'),
    meta: { title: '校园群聊', requiresAuth: true },
  },
  {
    path: '/circles',
    name: 'circle-list',
    component: () => import('../views/CircleList.vue'),
    meta: { title: '圈子', requiresAuth: true },
  },
  {
    path: '/circles/:id',
    name: 'circle-chat',
    component: () => import('../views/CircleChat.vue'),
    meta: { title: '圈子群聊', requiresAuth: true },
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('../views/Messages.vue'),
    meta: { title: '私信', requiresAuth: true },
  },
  {
    path: '/messages/:userId',
    name: 'messages-peer',
    component: () => import('../views/Messages.vue'),
    meta: { title: '私信', requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
    meta: { title: '注册', guestOnly: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/admin/AdminDashboard.vue'),
    meta: { title: '管理后台', requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局路由守卫
//  - requiresAuth：未登录跳转 /login?redirect=当前页
//  - requiresAdmin：非管理员跳转首页
//  - guestOnly：已登录访问登录/注册页时跳转首页
router.beforeEach(async (to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} · 校园美食` : '校园美食'

  const hasToken = !!getToken()
  if (to.meta.guestOnly && hasToken) {
    return next('/')
  }
  if (to.meta.requiresAuth && !hasToken) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  const needRole = to.meta.requiresAdmin || to.meta.requiresMerchant || to.meta.requiresConsumer
  if (needRole) {
    // 涉及角色权限的路由先确保账号资料已加载（刷新直达时 userInfo 可能为空）
    const userStore = useUserStore()
    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch (e) {
        // token 失效，重定向拦截器会处理
      }
    }
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      ElMessage.warning('需要管理员权限')
      return next('/')
    }
    if (to.meta.requiresMerchant && !userStore.isMerchant) {
      ElMessage.warning('需要商户权限')
      return next('/')
    }
    // 商户账号不提供学生向操作页面（发布探店笔记 / 提交商户菜单），直达链接同样拦截
    if (to.meta.requiresConsumer && userStore.isMerchant) {
      ElMessage.warning('商户账号仅可发布与管理自己的店铺与菜单')
      return next('/merchant')
    }
  }
  return next()
})

export default router
