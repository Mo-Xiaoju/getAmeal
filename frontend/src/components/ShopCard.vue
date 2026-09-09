<template>
  <div class="shop-card" @click="goDetail">
    <div class="shop-cover">
      <img
        v-if="shop.image_url"
        :src="shop.image_url"
        :alt="shop.name"
        loading="lazy"
        @error="imageFailed = true"
        @click.stop="openImage([shop.image_url], 0)"
      />
      <div v-else-if="imageFailed" class="cover-fallback">
        <el-icon><Food /></el-icon>
      </div>
      <div v-else class="cover-fallback">
        <el-icon><Food /></el-icon>
      </div>
      <el-tag v-if="shop.category" class="category-tag" effect="light">{{ shop.category }}</el-tag>
    </div>

    <div class="shop-info">
      <h3 class="shop-name">{{ shop.name }}</h3>
      <div class="shop-rating">
        <RatingStars :rating="shop.avg_rating || 0" />
        <span class="rating-count">({{ shop.rating_count || 0 }})</span>
      </div>
      <div class="shop-meta">
        <span v-if="shop.price_range" class="meta-item">{{ shop.price_range }}</span>
        <span v-if="shop.school_name" class="meta-item">{{ shop.school_name }}</span>
      </div>
      <p v-if="shop.address" class="shop-address">
        <el-icon><Location /></el-icon>{{ shop.address }}
      </p>
      <div v-if="shop.rec_reason && shop.rec_reason.length" class="rec-reason">
        <el-tag v-for="(r, i) in shop.rec_reason" :key="i" type="warning" size="small" effect="plain">{{ r }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Food, Location } from '@element-plus/icons-vue'

import RatingStars from '@/components/RatingStars.vue'

import { openImage } from '@/composables/useImageViewer'

// 店铺卡片：店铺列表 / 收藏列表 / 推荐区复用
const props = defineProps({
  shop: { type: Object, required: true },
})

const router = useRouter()
const imageFailed = ref(false)

const goDetail = () => {
  if (props.shop.id) router.push(`/shops/${props.shop.id}`)
}
</script>

<style scoped>
.shop-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
}
.shop-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}
.shop-cover {
  position: relative;
  height: 150px;
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
  font-size: 44px;
  color: var(--el-color-primary-light-5);
}
.category-tag {
  position: absolute;
  top: 8px;
  left: 8px;
}
.shop-info {
  padding: 14px 16px 16px;
}
.shop-name {
  margin: 0 0 6px;
  font-size: 16px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.shop-rating {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.rating-count {
  font-size: 13px;
  color: #909399;
}
.shop-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}
.meta-item {
  font-size: 13px;
  color: #606266;
}
.shop-address {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  font-size: 13px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rec-reason {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
</style>
