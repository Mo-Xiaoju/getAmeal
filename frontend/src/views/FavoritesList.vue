<template>
  <div class="favorites-list">
    <div class="list-head">
      <el-page-header content="我的收藏" @back="router.back()" />
    </div>

    <el-radio-group v-model="activeType" class="type-tabs">
      <el-radio-button v-for="t in typeTabs" :key="t.value" :value="t.value">
        {{ t.label }}
      </el-radio-button>
    </el-radio-group>

    <div v-loading="loading" class="fav-grid">
      <div v-for="item in items" :key="item.id" class="fav-item">
        <ShopCard v-if="item.type === 'shop'" :shop="item.shop" />
        <PostCard v-else :post="item.post" />
        <div class="item-actions">
          <el-button text type="danger" size="small" @click="unfavorite(item)">
            <el-icon><Delete /></el-icon>取消收藏
          </el-button>
        </div>
      </div>
    </div>
    <el-empty v-if="!loading && !items.length" :description="emptyText" />

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
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Delete } from '@element-plus/icons-vue'

import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import ShopCard from '@/components/ShopCard.vue'
import { removeFavorite } from '@/api/shop'
import { getFavorites } from '@/api/user'
import { usePostStore } from '@/store/post'

const router = useRouter()
const postStore = usePostStore()

const typeTabs = [
  { label: '全部', value: 'all' },
  { label: '店铺', value: 'shop' },
  { label: '笔记', value: 'post' },
]

const activeType = ref('all')
const items = ref([])
const loading = ref(false)
const pagination = ref({ page: 1, total: 0, total_pages: 0, page_size: 12 })

const emptyText = computed(() => {
  if (activeType.value === 'shop') return '还没有收藏的店铺，去店铺逛逛吧'
  if (activeType.value === 'post') return '还没有收藏的笔记'
  return '还没有收藏任何内容'
})

const loadPage = async (page = 1) => {
  loading.value = true
  try {
    const res = await getFavorites({ type: activeType.value, page, page_size: 12 })
    const data = res.data.data
    items.value = data.items || []
    pagination.value = data
    return data
  } finally {
    loading.value = false
  }
}

// 取消收藏：店铺走 DELETE，笔记走幂等 toggle（当前已收藏 -> 取消）
const unfavorite = async (item) => {
  if (item.type === 'shop') await removeFavorite(item.shop.id)
  else await postStore.favorite(item.post.id)
  const page = pagination.value.page
  if (items.value.length === 1 && page > 1) {
    await loadPage(page - 1)
  } else {
    await loadPage(page)
  }
}

watch(activeType, () => loadPage(1))
onMounted(() => loadPage(1))
</script>

<style scoped>
.favorites-list {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.list-head {
  margin-bottom: 16px;
}
.type-tabs {
  margin-bottom: 20px;
}
.fav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  align-items: start;
  min-height: 120px;
}
.fav-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.item-actions {
  display: flex;
  justify-content: flex-end;
}
.item-actions :deep(.el-button) {
  padding: 2px 6px;
}
</style>
