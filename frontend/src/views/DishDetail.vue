<template>
  <div class="dish-detail">
    <div class="page-head">
      <el-page-header content="菜品详情" @back="router.back()" />
    </div>

    <!-- 详情拿不到（菜品不存在 / 已下架）：骨架屏不能一直转下去，给明确空态 -->
    <div v-if="notFound" class="not-found">
      <el-empty description="菜品不存在或已下架">
        <el-button type="primary" plain @click="router.back()">返回上一页</el-button>
      </el-empty>
    </div>

    <!-- 首次进入 / 切换菜品时先渲染骨架：避免"空白 → 整页白遮罩闪一下 → 内容整块冒出"。
         同一道菜重复请求时 store 里数据还在（fetchDishDetail 不清），直接渲染，不经过骨架 -->
    <el-skeleton v-else-if="!dishStore.dishDetail" animated>
      <template #template>
        <!-- 容器复用真实布局的类（dish-hero / dish-info / review-section），保证同形同高 -->
        <div class="dish-hero">
          <el-skeleton-item variant="image" class="skeleton-cover" />
          <div class="dish-info">
            <el-skeleton-item variant="text" style="width: 30%" />
            <el-skeleton-item variant="h1" style="width: 55%; margin: 10px 0 12px" />
            <el-skeleton-item variant="text" style="width: 25%" />
            <el-skeleton-item variant="text" style="width: 70%; margin-top: 12px" />
          </div>
        </div>
        <div class="review-section">
          <div class="section-title">
            <el-skeleton-item variant="text" style="width: 160px" />
          </div>
          <div class="review-list">
            <el-skeleton :rows="3" animated />
          </div>
        </div>
      </template>
    </el-skeleton>

    <div v-else class="dish-main">
      <!-- 菜品信息 -->
      <div class="dish-hero">
        <div class="dish-media">
          <div class="dish-cover">
            <!-- 大图预览：点击可进入 Element 全屏查看（图集内左右翻） -->
            <el-image
              v-if="images.length"
              :src="images[activeIdx]"
              :preview-src-list="images"
              :initial-index="activeIdx"
              :preview-teleported="true"
              fit="cover"
              class="dish-main-img"
            >
              <template #error>
                <div class="cover-fallback"><el-icon><Food /></el-icon></div>
              </template>
            </el-image>
            <div v-else class="cover-fallback">
              <el-icon><Food /></el-icon>
            </div>
          </div>
          <!-- 缩略图栏：点击切换大图 -->
          <div v-if="images.length > 1" class="dish-thumbs">
            <div
              v-for="(img, i) in images"
              :key="i"
              class="dish-thumb"
              :class="{ active: i === activeIdx }"
              @click="activeIdx = i"
            >
              <img :src="img" :alt="`${dish.name} ${i + 1}`" />
            </div>
          </div>
        </div>
        <div class="dish-info">
          <div class="dish-tags">
            <el-tag v-for="t in dish.tags || []" :key="t" type="warning" effect="light">{{ t }}</el-tag>
          </div>
          <h1 class="dish-name">{{ dish.name }}</h1>
          <div class="dish-price">¥{{ priceText }}</div>
          <div class="dish-rating">
            <RatingStars :rating="dish.avg_rating || 0" :show-value="true" />
            <span class="rating-count">{{ dish.rating_count || 0 }} 人评价</span>
          </div>
          <p v-if="dish.description" class="dish-desc">{{ dish.description }}</p>
          <div class="dish-shop">
            <el-icon><Shop /></el-icon>
            <span class="shop-label">在售于</span>
            <el-link type="primary" @click="router.push(`/shops/${dish.shop_id}`)">{{ dish.shop_name }}</el-link>
          </div>
        </div>
      </div>

      <!-- 菜品评价：在店铺页写评价时关联了本菜品的那些。
           菜品页只读（写评价的入口在店铺页，那里才有评分和关联菜品选择），
           但点赞与回复照常可用 —— 只读不等于不能互动 -->
      <section class="review-section">
        <h2 class="section-title">菜品评价</h2>
        <!-- 只在"没有任何评价可显示"时用骨架占位，已有列表时不再盖一层白遮罩 -->
        <div v-if="reviewsLoading && !reviews.length" class="review-list">
          <el-skeleton :rows="3" animated />
        </div>
        <div v-else class="review-list">
          <el-empty v-if="!reviews.length" description="这道菜还没有评价">
            <el-button type="primary" plain @click="router.push(`/shops/${dish.shop_id}`)">
              去店铺页写一条
            </el-button>
          </el-empty>
          <ReviewItem v-for="review in reviews" :key="review.id" :review="review" :show-dish="false" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Food, Shop } from '@element-plus/icons-vue'

import RatingStars from '@/components/RatingStars.vue'
import ReviewItem from '@/components/ReviewItem.vue'
import { useDishStore } from '@/store/dish'

const route = useRoute()
const router = useRouter()
const dishStore = useDishStore()

const dishId = computed(() => Number(route.params.id))
const dish = computed(() => dishStore.dishDetail || {})
// 图集：优先接口返回的 images；历史/单图菜品回退为 [image_url]
const images = computed(() => {
  const imgs = dish.value.images || []
  if (imgs.length) return imgs
  return dish.value.image_url ? [dish.value.image_url] : []
})
const activeIdx = ref(0) // 当前大图索引
// 切换到其它菜品时回到第一张
watch(
  () => dishStore.dishDetail?.id,
  () => {
    activeIdx.value = 0
  },
)
// 初始即 true：评价要等详情返回后才请求，先按"加载中"渲染，避免闪一下"暂无评价"
const reviewsLoading = ref(true)
// 详情请求失败（菜品不存在 / 已下架）：页面切空态而不是停在骨架屏上
const notFound = ref(false)
// 本地 ref 而不是写进 store：每个菜品页一份，写进 store 会和店铺页那份 reviews 互相污染
const reviews = ref([])

const priceText = computed(() => String(Number(dish.value.price) || 0))

onMounted(async () => {
  try {
    await dishStore.fetchDishDetail(dishId.value)
  } catch (e) {
    // 菜品不存在 / 已下架：接口层已提示，这里切空态并解除评论骨架
    notFound.value = true
    reviewsLoading.value = false
    return
  }
  try {
    const data = await dishStore.fetchDishReviews(dishId.value, { page: 1, page_size: 20 })
    reviews.value = data.items || []
  } finally {
    reviewsLoading.value = false
  }
})
</script>

<style scoped>
.dish-detail {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  min-height: 60vh;
}
/* 空态：与详情卡同一套外观（白底卡片），页面不至于只是一片空白 */
.not-found {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
}
/* 骨架屏：容器类复用真实布局（dish-hero / dish-info / review-section），这里只补封面尺寸 */
.skeleton-cover {
  flex: 0 0 320px;
  height: 200px;
  border-radius: 12px;
}
.page-head {
  margin-bottom: 16px;
}
.dish-hero {
  display: flex;
  gap: 24px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 20px;
}
.dish-media {
  flex: 0 0 320px;
}
.dish-cover {
  width: 320px;
  height: 200px;
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-color-primary-light-9);
}
.dish-main-img {
  width: 100%;
  height: 100%;
  display: block;
}
.dish-cover :deep(.el-image__inner) {
  width: 100%;
  height: 100%;
}
.cover-fallback {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  color: var(--el-color-primary-light-5);
}
.dish-thumbs {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.dish-thumb {
  width: 56px;
  height: 56px;
  border: 2px solid transparent;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fff;
  transition: border-color 0.15s;
}
.dish-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.dish-thumb.active {
  border-color: var(--el-color-primary);
}
.dish-info {
  flex: 1;
  min-width: 0;
}
.dish-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.dish-name {
  margin: 0 0 10px;
  font-size: 26px;
  color: #303133;
}
.dish-price {
  font-size: 26px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 10px;
}
.dish-rating {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.rating-count {
  font-size: 13px;
  color: #909399;
}
.dish-desc {
  margin: 0 0 14px;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
}
.dish-shop {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}
.shop-label {
  color: #909399;
}
.review-section {
  margin-top: 28px;
}
.section-title {
  margin: 0 0 16px;
  font-size: 18px;
  color: #303133;
}
.review-list {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 8px 18px;
  min-height: 120px;
}
/* 单条评价的样式在 ReviewItem.vue（店铺页与菜品页共用），这里只留列表容器 */
</style>
