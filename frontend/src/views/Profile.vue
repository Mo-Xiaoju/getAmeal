<template>
  <div class="profile">
    <div class="profile-card">
      <el-avatar :size="72" :src="userStore.userInfo?.avatar_url || undefined">
        {{ (userStore.nickname || 'U').charAt(0) }}
      </el-avatar>

      <h2 class="profile-name">{{ userStore.nickname || userStore.userInfo?.username }}</h2>
      <p class="profile-username">@{{ userStore.userInfo?.username }}</p>

      <div class="profile-meta">
        <el-tag v-if="userStore.isAdmin" type="warning" effect="light">管理员</el-tag>
        <el-tag v-else-if="userStore.isMerchant" type="success" effect="light">商户</el-tag>
        <el-tag v-else type="info" effect="light">学生</el-tag>
        <span class="profile-time">
          加入于 {{ formatDate(userStore.userInfo?.created_at) }}
        </span>
      </div>

      <!-- 关注 / 粉丝 / 笔记统计 -->
      <div class="profile-stats">
        <div class="stat-item" @click="router.push('/profile/following')">
          <span class="stat-num">{{ stats.following }}</span>
          <span class="stat-label">关注</span>
        </div>
        <div class="stat-item" @click="router.push('/profile/followers')">
          <span class="stat-num">{{ stats.followers }}</span>
          <span class="stat-label">粉丝</span>
        </div>
        <div class="stat-item" @click="router.push('/posts?mine=1')">
          <span class="stat-num">{{ stats.posts }}</span>
          <span class="stat-label">笔记</span>
        </div>
      </div>

      <div class="profile-actions" style="margin-top: 16px">
        <el-button type="primary" plain @click="router.push('/posts?mine=1')">我的笔记</el-button>
        <el-button plain @click="router.push('/posts/create')">发布笔记</el-button>
      </div>

      <el-divider />

      <!-- 绑定学校 -->
      <h3 class="section-title">绑定学校</h3>
      <div class="school-row">
        <el-icon v-if="boundSchool" class="school-icon"><School /></el-icon>
        <span v-if="boundSchool" class="school-value">{{ boundSchool.name }}</span>
        <span v-else class="school-value muted">尚未绑定学校</span>
        <el-button type="primary" plain size="small" @click="router.push('/choose-school')">
          {{ boundSchool ? '更改学校' : '去绑定' }}
        </el-button>
      </div>

      <el-divider />

      <h3 class="section-title">修改昵称</h3>
      <div class="edit-row">
        <el-input v-model="nickname" placeholder="输入新的昵称" style="max-width: 300px" />
        <el-button type="primary" :loading="saving" @click="handleUpdate">保存</el-button>
      </div>

      <div class="profile-actions">
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { School } from '@element-plus/icons-vue'

import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const schoolStore = useSchoolStore()
const postStore = usePostStore()

const nickname = ref(userStore.nickname)
const saving = ref(false)
const stats = ref({ following: 0, followers: 0, posts: 0 })

// 账号绑定的学校（优先本地已选学校，其次账号资料里的学校）
const boundSchool = computed(
  () => schoolStore.currentSchool || userStore.userInfo?.school || null
)

const formatDate = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  if (!schoolStore.schoolList.length) schoolStore.fetchSchools()
  // 统计关注/粉丝/笔记数
  const [fing, fers, mine] = await Promise.all([
    postStore.fetchFollowing({ page: 1, page_size: 1 }),
    postStore.fetchFollowers({ page: 1, page_size: 1 }),
    postStore.fetchMine({ page: 1, page_size: 1 }),
  ])
  stats.value = {
    following: fing?.total || 0,
    followers: fers?.total || 0,
    posts: mine?.total || 0,
  }
})

const handleUpdate = async () => {
  const value = (nickname.value || '').trim()
  if (!value) {
    ElMessage.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    await userStore.updateProfile({ nickname: value })
    ElMessage.success('昵称已更新')
  } finally {
    saving.value = false
  }
}

const handleLogout = async () => {
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.profile {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
}
.profile-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 40px;
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
}
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
  cursor: pointer;
}
.stat-item:hover .stat-num {
  color: var(--el-color-primary);
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
.section-title {
  margin: 0 0 12px;
  text-align: left;
  font-size: 16px;
  color: #303133;
}
.school-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.school-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}
.school-value {
  font-size: 15px;
  color: #303133;
  flex: 1;
  text-align: left;
}
.school-value.muted {
  color: #909399;
}
.edit-row {
  display: flex;
  gap: 10px;
}
.profile-actions {
  margin-top: 24px;
  text-align: left;
}
</style>
