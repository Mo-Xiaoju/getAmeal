<template>
  <div class="history-list">
    <div class="list-head">
      <el-page-header content="浏览记录" @back="router.back()" />
    </div>

    <el-radio-group v-model="activeType" class="type-tabs">
      <el-radio-button v-for="t in typeTabs" :key="t.value" :value="t.value">
        {{ t.label }}
      </el-radio-button>
    </el-radio-group>

    <div v-loading="loading" class="hist-grid">
      <div v-for="item in items" :key="item.id" class="hist-item">
        <div class="hist-meta">
          <el-tag size="small" effect="plain" :type="typeOf(item).tag">{{ typeOf(item).label }}</el-tag>
          <span class="hist-time">{{ formatTime(item.viewed_at) }}</span>
        </div>
        <ShopCard v-if="item.target_type === 'shop'" :shop="item.shop" />
        <DishCard v-else-if="item.target_type === 'dish'" :dish="item.dish" />
        <PostCard v-else :post="item.post" />
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

import DishCard from '@/components/DishCard.vue'
import Pagination from '@/components/Pagination.vue'
import PostCard from '@/components/PostCard.vue'
import ShopCard from '@/components/ShopCard.vue'
import { getViewHistory } from '@/api/user'

const router = useRouter()

const typeTabs = [
  { label: '全部', value: 'all' },
  { label: '店铺', value: 'shop' },
  { label: '菜品', value: 'dish' },
  { label: '笔记', value: 'post' },
]

const activeType = ref('all')
const items = ref([])
const loading = ref(false)
const pagination = ref({ page: 1, total: 0, total_pages: 0, page_size: 12 })

const emptyText = computed(() => {
  if (activeType.value === 'shop') return '还没有浏览过店铺'
  if (activeType.value === 'dish') return '还没有浏览过菜品'
  if (activeType.value === 'post') return '还没有浏览过笔记'
  return '暂无浏览记录，快去逛逛吧'
})

const typeOf = (item) => {
  const map = {
    shop: { label: '店铺', tag: 'info' },
    dish: { label: '菜品', tag: 'warning' },
    post: { label: '笔记', tag: 'primary' },
  }
  return map[item.target_type] || { label: item.target_type, tag: 'info' }
}

const formatTime = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const loadPage = async (page = 1) => {
  loading.value = true
  try {
    const res = await getViewHistory({ type: activeType.value, page, page_size: 12 })
    const data = res.data.data
    items.value = data.items || []
    pagination.value = data
    return data
  } finally {
    loading.value = false
  }
}

watch(activeType, () => loadPage(1))
onMounted(() => loadPage(1))
</script>

<style scoped>
.history-list {
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
/* 不设 align-items: start —— 默认 stretch，同一行的店铺/菜品/笔记卡片才是等高 */
.hist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  min-height: 120px;
}
.hist-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
}
/* 卡片撑满格子的剩余高度（三种卡片根节点都带同名骨架样式） */
.hist-item :deep(.shop-card),
.hist-item :deep(.dish-card),
.hist-item :deep(.post-card) {
  flex: 1;
  min-height: 0;
}
.hist-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.hist-time {
  font-size: 12px;
  color: #909399;
}
</style>
