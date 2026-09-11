<template>
  <div class="likes-list">
    <div class="list-head">
      <el-page-header content="我的点赞" @back="router.back()" />
    </div>

    <div v-loading="loading" class="post-grid">
      <div v-for="item in items" :key="item.id" class="like-item">
        <PostCard :post="item.post" />
        <div class="item-actions">
          <!-- 点赞用大拇指（星星留给收藏 / 评分），与卡片和详情页同一枚图标；
               这页列的都是"已点赞"，所以用实心款，和列表里卡片上的状态图标对得上 -->
          <el-button text type="danger" size="small" @click="unlike(item)">
            <el-icon><ThumbUpIcon filled /></el-icon>取消点赞
          </el-button>
        </div>
      </div>
    </div>
    <el-empty v-if="!loading && !items.length" description="还没有点赞过的笔记" />

    <Pagination
      v-if="pagination.total_pages > 1"
      :current-page="pagination.page"
      :total-pages="pagination.total_pages"
      :total="pagination.total"
      :page-size="pagination.page_size"
      @change="loadPage"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import { getMyLikes } from '@/api/user'
import { usePostStore } from '@/store/post'

const router = useRouter()
const postStore = usePostStore()

const items = ref([])
const loading = ref(false)
const pagination = ref({ page: 1, total: 0, total_pages: 0, page_size: 12 })

const loadPage = async (page = 1) => {
  loading.value = true
  try {
    const res = await getMyLikes({ page, page_size: 12 })
    const data = res.data.data
    items.value = data.items || []
    pagination.value = data
    return data
  } finally {
    loading.value = false
  }
}

// 取消点赞：服务端 toggle 幂等（当前已点赞 -> 取消）
const unlike = async (item) => {
  await postStore.like(item.post.id)
  const page = pagination.value.page
  if (items.value.length === 1 && page > 1) {
    await loadPage(page - 1)
  } else {
    await loadPage(page)
  }
}

onMounted(() => loadPage(1))
</script>

<style scoped>
.likes-list {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.list-head {
  margin-bottom: 20px;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  min-height: 120px;
}
.like-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
}
/* 卡片撑满格子的剩余高度，有无配图的笔记卡片才会等高 */
.like-item :deep(.post-card) {
  flex: 1;
  min-height: 0;
}
.item-actions {
  display: flex;
  justify-content: flex-end;
}
.item-actions :deep(.el-button) {
  padding: 2px 6px;
}
</style>
