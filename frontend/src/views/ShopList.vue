<template>
  <div class="shop-list">
    <div class="school-bar">
      <template v-if="schoolStore.hasSchool">
        <el-icon class="school-bar-icon"><School /></el-icon>
        <span class="school-bar-name">{{ schoolStore.currentSchool.name }}</span>
        <el-button size="small" text type="primary" @click="router.push('/choose-school')">切换学校</el-button>
      </template>
      <template v-else>
        <span class="school-bar-tip">尚未选择学校</span>
        <el-button size="small" type="primary" @click="router.push('/choose-school')">去选择学校</el-button>
      </template>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索店铺名称"
        clearable
        style="width: 220px"
        :prefix-icon="Search"
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-select v-model="filters.category" placeholder="全部分类" clearable style="width: 140px" @change="handleSearch">
        <el-option v-for="c in categoryStore.categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-select v-model="filters.zone" placeholder="全部位置" clearable style="width: 120px" @change="handleSearch">
        <el-option v-for="z in categoryStore.zones" :key="z" :label="z" :value="z" />
      </el-select>
      <el-select v-model="filters.sort" placeholder="排序" style="width: 130px" @change="handleSearch">
        <el-option label="评分最高" value="rating" />
        <el-option label="最新上架" value="newest" />
      </el-select>
      <el-button type="primary" @click="handleSearch">查询</el-button>
    </div>

    <div v-loading="shopStore.loading" class="shop-grid">
      <ShopCard v-for="shop in shopStore.shopList" :key="shop.id" :shop="shop" />
    </div>

    <el-empty v-if="!shopStore.loading && !shopStore.shopList.length" description="没有符合条件的店铺" />

    <Pagination
      v-if="shopStore.pagination.total_pages > 1"
      :current-page="shopStore.pagination.page"
      :total-pages="shopStore.pagination.total_pages"
      :total="shopStore.pagination.total"
      @change="handlePageChange"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { School, Search } from '@element-plus/icons-vue'

import Pagination from '@/components/Pagination.vue'
import ShopCard from '@/components/ShopCard.vue'
import { useCategoryStore } from '@/store/category'
import { useSchoolStore } from '@/store/school'
import { useShopStore } from '@/store/shop'

const router = useRouter()
const schoolStore = useSchoolStore()
const shopStore = useShopStore()
const categoryStore = useCategoryStore()

const filters = reactive({
  keyword: '',
  category: '',
  zone: '',
  sort: 'rating',
  page: 1,
})

const loadShops = async () => {
  const params = {
    page: filters.page,
    page_size: 12,
    sort: filters.sort,
  }
  if (filters.keyword.trim()) params.keyword = filters.keyword.trim()
  if (filters.category) params.category = filters.category
  if (filters.zone) params.zone = filters.zone
  if (schoolStore.hasSchool) params.school_id = schoolStore.currentSchool.id
  await shopStore.fetchShopList(params)
}

const handleSearch = () => {
  filters.page = 1
  loadShops()
}

const handlePageChange = (page) => {
  filters.page = page
  loadShops()
}

onMounted(async () => {
  if (!schoolStore.schoolList.length) {
    await schoolStore.fetchSchools()
  }
  if (!categoryStore.categories.length) categoryStore.fetchCategories()
  if (!categoryStore.zones.length) categoryStore.fetchZones()
  loadShops()
})
</script>

<style scoped>
.shop-list {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}
.school-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--el-color-primary-light-9);
  border-radius: 10px;
  margin-bottom: 16px;
}
.school-bar-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}
.school-bar-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.school-bar-tip {
  font-size: 14px;
  color: #909399;
}
.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.shop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
  min-height: 200px;
}
</style>
