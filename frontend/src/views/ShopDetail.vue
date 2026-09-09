<template>
  <div v-loading="shopStore.loading" class="shop-detail">
    <!-- 店铺信息 -->
    <div v-if="shopStore.shopDetail" class="detail-main">
      <div class="shop-hero">
        <div class="shop-cover">
          <img
            v-if="shop.image_url"
            :src="shop.image_url"
            :alt="shop.name"
            @error="imageFailed = true"
            @click.stop="openImage([shop.image_url], 0)"
          />
          <div v-else class="cover-fallback">
            <el-icon><Food /></el-icon>
          </div>
        </div>
        <div class="shop-info">
          <div class="shop-tags">
            <el-tag v-if="shop.category" type="primary" effect="light">{{ shop.category }}</el-tag>
            <el-tag v-if="shop.price_range" type="warning" effect="plain">{{ shop.price_range }}</el-tag>
            <el-tag v-if="shop.school_name" type="info" effect="plain">{{ shop.school_name }}</el-tag>
          </div>
          <h1 class="shop-name">{{ shop.name }}</h1>
          <div class="shop-rating">
            <RatingStars :rating="shop.avg_rating || 0" :show-value="true" />
            <span class="rating-count">{{ shop.rating_count || 0 }} 条评价</span>
          </div>
          <p class="shop-address">
            <el-icon><Location /></el-icon>{{ shop.address || '暂无地址' }}
          </p>
          <p v-if="shop.description" class="shop-desc">{{ shop.description }}</p>
          <div class="shop-actions">
            <!-- 学生/游客/管理员：收藏 + 写评价（商户不开放，后端 4031） -->
            <template v-if="!userStore.isMerchant">
              <el-button
                :type="shopStore.isFavorited ? 'warning' : 'primary'"
                :plain="!shopStore.isFavorited"
                :icon="shopStore.isFavorited ? StarFilled : Star"
                @click="handleFavorite"
              >
                {{ shopStore.isFavorited ? '已收藏' : '收藏店铺' }}
              </el-button>
              <el-button type="success" plain :icon="EditPen" @click="scrollToReview">写评价</el-button>
              <!-- 菜单可能更新不及时：同学可代为补充菜品（走审核，同店同名去重） -->
              <el-button v-if="canContribute" plain :icon="Plus" @click="openDishDialog">补充菜品</el-button>
            </template>
            <!-- 仅本商户的店铺出现管理入口；非本商户的店铺不渲染任何管理按钮 -->
            <el-button v-else-if="isMyShop" type="primary" :icon="Shop" @click="router.push('/merchant')">
              管理本店 · 菜单
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 本店菜品 -->
    <section v-if="shopStore.shopDetail" class="dish-section">
      <h2 class="section-title">本店菜品</h2>
      <div v-loading="dishStore.loading" class="dish-grid">
        <DishCard v-for="d in dishStore.shopDishes" :key="d.id" :dish="d" />
      </div>
      <el-empty
        v-if="!dishStore.loading && !dishStore.shopDishes.length"
        :description="emptyDishesText"
      >
        <el-button v-if="canContribute" size="small" type="primary" plain :icon="Plus" @click="openDishDialog">
          补充菜品
        </el-button>
      </el-empty>
    </section>

    <!-- 评价区 -->
    <div class="review-section" ref="reviewSection">
      <!-- 商户不开放写评价（后端 4031），仅保留评价浏览 -->
      <template v-if="!userStore.isMerchant">
        <h2 class="section-title">发表评价</h2>
        <div class="review-form">
          <div class="form-rate">
            <span class="form-label">评分：</span>
            <el-rate v-model="form.rating" :texts="rateTexts" show-text />
          </div>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="分享你的用餐体验（选填）"
          />
          <div class="form-actions">
            <el-button type="primary" :loading="submitting" @click="handleSubmit">发布评价</el-button>
          </div>
        </div>
      </template>

      <h2 class="section-title">全部评价</h2>
      <div v-loading="reviewsLoading" class="review-list">
        <el-empty
          v-if="!reviewsLoading && !shopStore.reviews.length"
          description="还没有评价，来发表第一条吧"
        />
        <div v-for="review in shopStore.reviews" :key="review.id" class="review-item">
          <el-avatar :size="40" :src="review.avatar_url || undefined">
            {{ (review.nickname || 'U').charAt(0) }}
          </el-avatar>
          <div class="review-body">
            <div class="review-head">
              <span class="review-nickname">{{ review.nickname || '匿名用户' }}</span>
              <RatingStars :rating="review.rating || 0" />
              <span class="review-time">{{ formatDate(review.created_at) }}</span>
            </div>
            <p v-if="review.content" class="review-content">{{ review.content }}</p>
          </div>
        </div>
      </div>
      <Pagination
        v-if="reviewPagination.total_pages > 1"
        :current-page="reviewPagination.page"
        :total-pages="reviewPagination.total_pages"
        :total="reviewPagination.total"
        @change="loadReviews"
      />
    </div>

    <!-- 补充菜品（代已公开店铺补全菜单，审核后展示） -->
    <el-dialog v-model="dishDialog.show" title="补充菜品" width="480px">
      <p class="dish-tip">{{ dishDialogTip }}</p>
      <el-form label-position="top">
        <div class="dish-form-row">
          <el-form-item label="菜品名" required>
            <el-input v-model="dishDialog.form.name" maxlength="100" placeholder="例如：招牌盖饭" />
          </el-form-item>
          <el-form-item label="价格（元）" required>
            <el-input-number v-model="dishDialog.form.price" :min="0" :precision="2" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
        <el-form-item label="描述">
          <el-input v-model="dishDialog.form.description" maxlength="500" />
        </el-form-item>
        <el-form-item label="菜品图（可多张，最多 9 张）">
          <MultiImageField v-model="dishDialog.form.images" :size="76" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="dishDialog.form.tags" placeholder="例如：招牌,下饭" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dishDialog.show = false">取消</el-button>
        <el-button type="primary" :loading="dishDialog.submitting" @click="handleSubmitDish">提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { EditPen, Food, Location, Plus, Shop, Star, StarFilled } from '@element-plus/icons-vue'

import { submitDish } from '@/api/contribute'
import DishCard from '@/components/DishCard.vue'
import MultiImageField from '@/components/MultiImageField.vue'
import { openImage } from '@/composables/useImageViewer'
import Pagination from '@/components/Pagination.vue'
import RatingStars from '@/components/RatingStars.vue'
import { useDishStore } from '@/store/dish'
import { useShopStore } from '@/store/shop'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const shopStore = useShopStore()
const userStore = useUserStore()
const dishStore = useDishStore()

const shopId = computed(() => Number(route.params.id))
const imageFailed = ref(false)
const reviewsLoading = ref(false)
const submitting = ref(false)
const reviewSection = ref(null)
const reviewPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })

const rateTexts = ['很差', '较差', '一般', '不错', '超赞']
const form = reactive({ rating: 5, content: '' })

const shop = computed(() => shopStore.shopDetail || {})
// 当前登录商户是否为该店 owner（决定是否展示管理按钮）
const isMyShop = computed(
  () => userStore.isMerchant && shop.value.owner_id === userStore.userInfo?.id,
)
// 是否可向该店补充菜品：任何非商户用户都可代为补全已公开店铺的菜单（商家可能更新不及时，
// 提交仍走审核）；仅排除商户视角与自己提交的店铺（后者在「提交管理」页维护）。
const canContribute = computed(
  () => !userStore.isMerchant && shop.value.owner_id !== userStore.userInfo?.id,
)
// 弹窗/空态文案：社区店（尚无商户入驻）与商户入驻店分开表述
const dishDialogTip = computed(() =>
  shop.value.community_maintained
    ? '该店尚未有商户入驻，你补充的菜品将进入审核，通过后对外展示。'
    : '如果店铺菜单更新不及时或漏了菜，你可以帮忙补充；提交后进入审核，通过前不对外展示。',
)
const emptyDishesText = computed(() =>
  canContribute.value ? '本店暂未收录在售菜品，你可以帮店家补充' : '本店暂无在售菜品',
)

// ---- 补充菜品 ----
const dishDialog = reactive({
  show: false,
  submitting: false,
  form: { name: '', price: 0, description: '', tags: '', images: [] },
})

const resetDishForm = () => {
  dishDialog.form = { name: '', price: 0, description: '', tags: '', images: [] }
}

const openDishDialog = () => {
  if (!requireLogin()) return
  resetDishForm()
  dishDialog.show = true
}

const handleSubmitDish = async () => {
  const form = dishDialog.form
  if (!form.name.trim()) {
    ElMessage.warning('请输入菜品名')
    return
  }
  dishDialog.submitting = true
  try {
    await submitDish(shopId.value, {
      name: form.name.trim(),
      price: form.price,
      description: form.description?.trim() || undefined,
      images: form.images,
      tags: form.tags ? form.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean) : [],
    })
    ElMessage.success('菜品已提交，审核通过后展示')
    dishDialog.show = false
    dishStore.fetchShopDishes(shopId.value)
  } finally {
    dishDialog.submitting = false
  }
}

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

const loadReviews = async (page = 1) => {
  reviewsLoading.value = true
  try {
    const data = await shopStore.fetchReviews(shopId.value, { page, page_size: 10 })
    reviewPagination.page = data.page || page
    reviewPagination.total_pages = data.total_pages || 0
    reviewPagination.total = data.total || 0
  } finally {
    reviewsLoading.value = false
  }
}

const requireLogin = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return false
  }
  return true
}

const handleFavorite = async () => {
  if (!requireLogin()) return
  await shopStore.toggleFavorite(shopId.value)
  ElMessage.success(shopStore.isFavorited ? '收藏成功' : '已取消收藏')
}

const scrollToReview = () => {
  reviewSection.value?.scrollIntoView({ behavior: 'smooth' })
}

const handleSubmit = async () => {
  if (!requireLogin()) return
  if (!form.rating) {
    ElMessage.warning('请选择评分')
    return
  }
  submitting.value = true
  try {
    await shopStore.addReview(shopId.value, {
      rating: form.rating,
      content: form.content.trim() || undefined,
    })
    ElMessage.success('评价发布成功')
    form.content = ''
    form.rating = 5
    loadReviews(1)
    // 刷新详情以更新评分
    shopStore.fetchShopDetail(shopId.value)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  shopStore.fetchShopDetail(shopId.value)
  dishStore.fetchShopDishes(shopId.value)
  loadReviews(1)
})
</script>

<style scoped>
.shop-detail {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  min-height: 60vh;
}
.shop-hero {
  display: flex;
  gap: 24px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 20px;
}
.shop-cover {
  flex: 0 0 320px;
  height: 200px;
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-color-primary-light-9);
}
.shop-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
}
.cover-fallback {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  color: var(--el-color-primary-light-5);
}
.shop-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.shop-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.shop-name {
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}
.shop-rating {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.rating-count {
  font-size: 13px;
  color: #909399;
}
.shop-address {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0 0 10px;
  font-size: 14px;
  color: #606266;
}
.shop-desc {
  margin: 0 0 16px;
  font-size: 14px;
  color: #909399;
  line-height: 1.7;
}
.shop-actions {
  margin-top: auto;
}
.dish-section {
  margin-top: 28px;
}
.dish-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.review-section {
  margin-top: 28px;
}
.section-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: #303133;
}
.review-form {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 28px;
}
.form-rate {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.form-label {
  font-size: 14px;
  color: #606266;
  margin-right: 4px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
.review-list {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 8px 18px;
  min-height: 120px;
}
.review-item {
  display: flex;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #f2f3f5;
}
.review-item:last-child {
  border-bottom: none;
}
.review-body {
  flex: 1;
  min-width: 0;
}
.review-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.review-nickname {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.review-time {
  font-size: 12px;
  color: #c0c4cc;
}
.review-content {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
}
.dish-tip {
  margin: 0 0 14px;
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}
.dish-form-row {
  display: grid;
  grid-template-columns: 1fr 150px;
  gap: 12px;
}
</style>
