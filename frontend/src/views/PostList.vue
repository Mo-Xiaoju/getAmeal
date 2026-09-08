<template>
  <div class="post-list">
    <div class="list-head">
      <div>
        <h1 class="page-title">{{ isMine ? '我的笔记' : '探店笔记' }}</h1>
        <p class="page-desc">{{ isMine ? '你发布的探店内容' : '分享你发现的校园好味道' }}</p>
      </div>
      <!-- 商户不开放发布探店笔记（后端 4031），页内给出商户中心入口 -->
      <el-button v-if="userStore.isMerchant" type="success" :icon="Shop" @click="router.push('/merchant')">
        商户中心
      </el-button>
      <el-button v-else type="primary" :icon="EditPen" @click="handleCreate">发布笔记</el-button>
    </div>

    <!-- 筛选栏（我的笔记页隐藏） -->
    <div v-if="!isMine" class="filter-bar">
      <el-radio-group v-model="sort" @change="handleChange">
        <el-radio-button label="newest">最新</el-radio-button>
        <el-radio-button label="hot">热门</el-radio-button>
      </el-radio-group>
      <el-input
        v-model="keyword"
        class="search-input"
        placeholder="搜索笔记标题 / 内容"
        :prefix-icon="Search"
        clearable
        @keyup.enter="handleChange"
        @clear="handleChange"
      />
    </div>

    <div v-loading="postStore.loading" class="post-grid">
      <PostCard v-for="post in postStore.postList" :key="post.id" :post="post" />
    </div>
    <el-empty
      v-if="!postStore.loading && !postStore.postList.length"
      :description="isMine ? '你还没有发布笔记' : '还没有笔记，来发布第一篇吧'"
    />

    <Pagination
      v-if="postStore.pagination.total_pages > 1"
      :current-page="postStore.pagination.page"
      :total-pages="postStore.pagination.total_pages"
      :total="postStore.pagination.total"
      @change="loadList"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { EditPen, Search, Shop } from '@element-plus/icons-vue'

import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const schoolStore = useSchoolStore()
const userStore = useUserStore()

const sort = ref('newest')
const keyword = ref('')
// ?mine=1 时进入"我的笔记"模式
const isMine = computed(() => route.query.mine === '1')

const loadList = async (page = 1) => {
  if (isMine.value) {
    await postStore.fetchMine({ page, page_size: 12 })
    return
  }
  const params = { page, page_size: 12, sort: sort.value }
  if (keyword.value.trim()) params.keyword = keyword.value.trim()
  if (schoolStore.hasSchool) params.school_id = schoolStore.currentSchool.id
  await postStore.fetchList(params)
}

const handleChange = () => loadList(1)

const handleCreate = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录再发布笔记')
    router.push({ path: '/login', query: { redirect: '/posts/create' } })
    return
  }
  router.push('/posts/create')
}

onMounted(() => {
  if (!schoolStore.schoolList.length) schoolStore.fetchSchools()
  loadList(1)
})
</script>

<style scoped>
.post-list {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  margin: 0 0 6px;
  font-size: 26px;
  color: #303133;
}
.page-desc {
  margin: 0;
  font-size: 14px;
  color: #909399;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.search-input {
  max-width: 320px;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
  min-height: 120px;
}
</style>
