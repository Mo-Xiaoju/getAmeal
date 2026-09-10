<template>
  <div v-loading="loading" class="user-profile">
    <el-empty v-if="notFound" description="用户不存在或已注销" />

    <template v-else-if="profile">
      <div class="profile-card">
        <el-avatar :size="88" :src="profile.avatar_url || undefined">
          {{ (profile.nickname || 'U').charAt(0) }}
        </el-avatar>

        <h2 class="profile-name">{{ profile.nickname || profile.username }}</h2>
        <p class="profile-username">@{{ profile.username }}</p>

        <div class="profile-meta">
          <el-tag :type="roleTag.type" effect="light">{{ roleTag.text }}</el-tag>
          <span v-if="profile.school_name" class="profile-school">{{ profile.school_name }}</span>
          <span class="profile-time">加入于 {{ formatDate(profile.created_at) }}</span>
        </div>

        <!-- 统计只读：/profile/following 等列表是「当前登录者」自己的，挂到别人身上会跳错页 -->
        <div class="profile-stats">
          <div class="stat-item">
            <span class="stat-num">{{ profile.following_count || 0 }}</span>
            <span class="stat-label">关注</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ profile.follower_count || 0 }}</span>
            <span class="stat-label">粉丝</span>
          </div>
          <div class="stat-item">
            <span class="stat-num">{{ profile.post_count || 0 }}</span>
            <span class="stat-label">笔记</span>
          </div>
        </div>

        <div class="profile-actions">
          <el-button v-if="isSelf" plain @click="router.push('/profile')">
            这是你的主页，去个人中心
          </el-button>
          <!-- 关注/私信均仅学生账号可用（后端 require_consumer），商户不渲染，与 FollowList 约定一致 -->
          <template v-else-if="!userStore.isMerchant">
            <el-button
              :type="profile.is_following ? 'info' : 'primary'"
              :plain="profile.is_following"
              @click="handleFollow"
            >
              {{ profile.is_following ? '已关注' : '+ 关注' }}
            </el-button>
            <el-button type="primary" plain @click="sendDm">发私信</el-button>
          </template>
        </div>
      </div>

      <section class="notes-section">
        <h3 class="section-title">TA 的笔记（{{ profile.post_count || 0 }}）</h3>
        <div v-loading="postsLoading" class="post-grid">
          <PostCard v-for="p in posts" :key="p.id" :post="p" />
        </div>
        <el-empty v-if="!postsLoading && !posts.length" description="还没有发布过笔记" />
        <Pagination
          v-if="pagination.total_pages > 1"
          :current-page="pagination.page"
          :total-pages="pagination.total_pages"
          :total="pagination.total"
          :page-size="pagination.page_size"
          @change="loadPosts"
        />
      </section>
    </template>
  </div>
</template>

<script setup>
// 他人公开主页：/user/:id（无需登录即可浏览，游客点关注/私信时引导登录）
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { getPostsByUser } from '@/api/post'
import { getUserProfile } from '@/api/user'
import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import { usePostStore } from '@/store/post'
import { useUserStore } from '@/store/user'

const PAGE_SIZE = 12

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const userStore = useUserStore()

const userId = computed(() => Number(route.params.id))
const profile = ref(null)
const loading = ref(false)
const notFound = ref(false)
const posts = ref([])
const postsLoading = ref(false)
const pagination = ref({ page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 })

const isSelf = computed(() => !!profile.value && userStore.userInfo?.id === profile.value.id)

const roleTag = computed(() => {
  const role = profile.value?.role
  if (role === 'admin') return { text: '管理员', type: 'warning' }
  if (role === 'merchant') return { text: '商户', type: 'success' }
  return { text: '学生', type: 'info' }
})

const formatDate = (iso) => (iso ? new Date(iso).toLocaleDateString('zh-CN') : '-')

const requireLogin = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return false
  }
  return true
}

async function loadProfile() {
  loading.value = true
  notFound.value = false
  try {
    const res = await getUserProfile(userId.value)
    profile.value = res.data.data
  } catch (e) {
    // 4045 用户不存在/已停用：接口层已提示，这里只切到空状态
    notFound.value = true
    profile.value = null
  } finally {
    loading.value = false
  }
}

async function loadPosts(page = 1) {
  postsLoading.value = true
  try {
    // 直接调 API 而非 postStore.fetchList：后者会覆盖笔记列表页共享的 postList 状态
    const res = await getPostsByUser(userId.value, { page, page_size: PAGE_SIZE })
    const data = res.data.data || {}
    posts.value = data.items || []
    pagination.value = {
      page: data.page || 1,
      page_size: data.page_size || PAGE_SIZE,
      total: data.total || 0,
      total_pages: data.total_pages || 0,
    }
  } catch (e) {
    posts.value = []
  } finally {
    postsLoading.value = false
  }
}

const handleFollow = async () => {
  if (!requireLogin()) return
  const res = await postStore.follow(profile.value.id)
  profile.value.is_following = res.following
  profile.value.follower_count = Math.max(
    (profile.value.follower_count || 0) + (res.following ? 1 : -1),
    0,
  )
  ElMessage.success(res.following ? '关注成功' : '已取消关注')
}

// 与 FollowList.sendDm 一致：把对端资料带在 query 里，私信页首屏即可显示会话头
const sendDm = () => {
  if (!requireLogin()) return
  const p = profile.value
  const peer = JSON.stringify({
    nickname: p.nickname || p.username,
    username: p.username,
    avatar_url: p.avatar_url,
  })
  router.push({ path: `/messages/${p.id}`, query: { peer } })
}

async function loadAll() {
  profile.value = null
  posts.value = []
  pagination.value = { page: 1, page_size: PAGE_SIZE, total: 0, total_pages: 0 }
  await loadProfile()
  if (!notFound.value) loadPosts(1)
}

onMounted(loadAll)
// 参数变化时组件会被复用（/user/1 → /user/2），需要重新拉取
watch(() => route.params.id, loadAll)
</script>

<style scoped>
.user-profile {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 20px 48px;
  min-height: 60vh;
}
.profile-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 36px;
  text-align: center;
}
.profile-name {
  margin: 16px 0 4px;
  font-size: 22px;
  color: #303133;
}
.profile-username {
  margin: 0 0 12px;
  color: #909399;
  font-size: 14px;
}
.profile-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
.profile-school,
.profile-time {
  color: #909399;
  font-size: 13px;
}
.profile-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-top: 18px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.stat-label {
  font-size: 13px;
  color: #909399;
}
.profile-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 8px;
}
.notes-section {
  margin-top: 28px;
}
.section-title {
  margin: 0 0 14px;
  font-size: 18px;
  color: #303133;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
  min-height: 80px;
}
</style>
