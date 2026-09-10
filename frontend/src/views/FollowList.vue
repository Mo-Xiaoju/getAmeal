<template>
  <div class="follow-list">
    <div class="list-head">
      <el-page-header :content="mode === 'following' ? '我的关注' : '我的粉丝'" @back="router.back()" />
    </div>

    <div v-loading="postStore.loading" class="user-grid">
      <div v-for="u in items" :key="u.id" class="user-card">
        <el-avatar
          class="user-link"
          :size="48"
          :src="u.avatar_url || undefined"
          @click="goUser(u.id)"
        >
          {{ (u.nickname || u.username || 'U').charAt(0) }}
        </el-avatar>
        <div class="user-info">
          <div class="user-name">{{ u.nickname || u.username }}</div>
          <div class="user-sub">
            @{{ u.username }}<template v-if="u.school_name"> · {{ u.school_name }}</template>
          </div>
        </div>
        <div class="row-actions">
          <!-- 商户不可关注他人/发起私信（后端 require_consumer），仅保留关系展示 -->
          <template v-if="!userStore.isMerchant">
            <el-button
              v-if="mode === 'followers'"
              size="small"
              :type="u.is_following ? 'info' : 'primary'"
              plain
              @click="handleFollow(u)"
            >
              {{ u.is_following ? '已关注' : '关注' }}
            </el-button>
            <span v-else class="following-badge">已关注</span>
            <el-button v-if="u.id !== myId" size="small" type="primary" plain @click="sendDm(u)">
              发私信
            </el-button>
          </template>
        </div>
      </div>
    </div>
    <el-empty v-if="!postStore.loading && !items.length" :description="emptyText" />

    <Pagination
      v-if="postStore.pagination.total_pages > 1"
      :current-page="postStore.pagination.page"
      :total-pages="postStore.pagination.total_pages"
      :total="postStore.pagination.total"
      @change="loadPage"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import Pagination from '@/components/Pagination.vue'
import { useUserNav } from '@/composables/useUserNav'
import { usePostStore } from '@/store/post'
import { useUserStore } from '@/store/user'

const props = defineProps({
  mode: { type: String, default: 'following' }, // following | followers
})

const router = useRouter()
const postStore = usePostStore()
const userStore = useUserStore()
const { goUser } = useUserNav()

const myId = computed(() => userStore.userInfo?.id)

const items = ref([])
const emptyText = computed(() =>
  props.mode === 'following' ? '还没有关注任何人' : '还没有粉丝'
)

const loadPage = async (page = 1) => {
  const params = { page, page_size: 12 }
  const data =
    props.mode === 'following'
      ? await postStore.fetchFollowing(params)
      : await postStore.fetchFollowers(params)
  items.value = data?.items || []
  return data
}

const handleFollow = async (u) => {
  const res = await postStore.follow(u.id)
  if (res?.following === false) {
    // 取关后从粉丝列表移除
    items.value = items.value.filter((x) => x.id !== u.id)
  } else {
    u.is_following = true
  }
}

// 发起私信：跳转私信页并带上对端资料，便于首屏会话头展示
const sendDm = (u) => {
  const peer = JSON.stringify({
    nickname: u.nickname || u.username,
    username: u.username,
    avatar_url: u.avatar_url,
  })
  router.push({ path: `/messages/${u.id}`, query: { peer } })
}

onMounted(() => loadPage(1))
</script>

<style scoped>
.follow-list {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.list-head {
  margin-bottom: 16px;
}
.user-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 120px;
}
.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
}
.user-info {
  flex: 1;
  min-width: 0;
}
/* 头像可点进对方主页 */
.user-link {
  cursor: pointer;
  flex-shrink: 0;
}
.user-link:hover {
  opacity: 0.85;
}
.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.user-sub {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.following-badge {
  font-size: 13px;
  color: #909399;
}
.row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
