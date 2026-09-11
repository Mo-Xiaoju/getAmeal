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
      <el-button v-else type="primary" :icon="EditPen" :disabled="guestLocked" @click="handleCreate">
        发布笔记
      </el-button>
    </div>
    <LoginHint v-if="guestLocked" text="登录后即可发布探店笔记" />

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

    <!-- 换排序 / 翻页 / 搜索时旧卡片原地留着，等新数据回来直接替换（不铺骨架也不盖白遮罩）；
         只有"第一次进来"或"换了一份列表"（我的笔记↔全部、换学校）才铺骨架 -->
    <div class="post-grid">
      <template v-if="postStore.loading && !postStore.postList.length">
        <!-- 外层用 el-skeleton（不只是 el-skeleton-item）才能拿到动效：渐变动画挂在 is-animated 根节点上 -->
        <el-skeleton v-for="i in 6" :key="`post-skeleton-${i}`" animated class="skeleton-card">
          <template #template>
            <div class="skeleton-head">
              <el-skeleton-item variant="circle" class="skeleton-avatar" />
              <div class="skeleton-author">
                <el-skeleton-item variant="text" style="width: 40%" />
                <el-skeleton-item variant="text" style="width: 65%; margin-top: 6px" />
              </div>
            </div>
            <el-skeleton-item variant="h3" style="width: 70%" />
            <el-skeleton-item variant="text" style="width: 100%; margin: 10px 0 4px" />
            <el-skeleton-item variant="text" style="width: 85%" />
            <el-skeleton-item variant="image" class="skeleton-cover" />
            <div class="skeleton-foot">
              <el-skeleton-item variant="text" style="width: 70px" />
              <el-skeleton-item variant="text" style="width: 90px" />
            </div>
          </template>
        </el-skeleton>
      </template>
      <template v-else>
        <PostCard v-for="post in postStore.postList" :key="post.id" :post="post" />
      </template>
    </div>
    <el-empty
      v-if="!postStore.loading && !postStore.postList.length"
      :description="isMine ? '你还没有发布笔记' : '还没有笔记，来发布第一篇吧'"
    />

    <!-- 列表为空（首次进入 / 换筛选条件）时先不显示分页：此时 pagination 还是上一份查询的 -->
    <Pagination
      v-if="postStore.postList.length && postStore.pagination.total_pages > 1"
      :current-page="postStore.pagination.page"
      :total-pages="postStore.pagination.total_pages"
      :total="postStore.pagination.total"
      @change="loadList"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { EditPen, Search, Shop } from '@element-plus/icons-vue'

import LoginHint from '@/components/LoginHint.vue'
import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import { useLoginGate } from '@/composables/useLoginGate'
import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const postStore = usePostStore()
const schoolStore = useSchoolStore()
const userStore = useUserStore()
const { guestLocked, requireLogin } = useLoginGate()

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

// /posts ←→ /posts?mine=1 只是 query 变化，组件实例会被复用、不会重新挂载：
// 不重新拉列表的话，两种模式的标题变了、列表却还是对方的数据
watch(isMine, () => loadList(1))

// 游客按钮已置灰，requireLogin 只兜底（如页面停留期间 token 失效）
const handleCreate = () => {
  if (!requireLogin()) return
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
/* 骨架卡片：按 PostCard 的尺寸复刻（同一套圆角/内边距，封面同为 150px），
   单独定义而不复用 .post-card，免得占位块也带悬停上浮 */
.skeleton-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 16px 18px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.skeleton-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.skeleton-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}
.skeleton-author {
  flex: 1;
  min-width: 0;
}
.skeleton-cover {
  height: 150px;
  border-radius: 8px;
  margin: 10px 0;
}
.skeleton-foot {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
}
</style>
