<template>
  <div class="dish-card" @click="goDetail">
    <div class="dish-cover">
      <img
        v-if="dish.image_url"
        :src="dish.image_url"
        :alt="dish.name"
        loading="lazy"
        @error="imageFailed = true"
        @click.stop="openImage(dish.images && dish.images.length ? dish.images : [dish.image_url], 0)"
      />
      <div v-else class="cover-fallback">
        <el-icon><Food /></el-icon>
      </div>
    </div>

    <div class="dish-info">
      <h3 class="dish-name">{{ dish.name }}</h3>
      <div class="dish-meta">
        <span class="dish-price">¥{{ priceText }}</span>
        <span class="dish-rating">
          <el-icon class="star-icon"><StarFilled /></el-icon>
          <span>{{ dish.avg_rating || '0' }}</span>
        </span>
      </div>
      <div v-if="dish.tags && dish.tags.length" class="dish-tags">
        <el-tag v-for="t in dish.tags.slice(0, 3)" :key="t" size="small" effect="plain">{{ t }}</el-tag>
      </div>
      <div v-if="dish.rec_reason && dish.rec_reason.length" class="rec-reason">
        <el-tag v-for="(r, i) in dish.rec_reason" :key="i" type="warning" size="small" effect="plain">{{ r }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Food, StarFilled } from '@element-plus/icons-vue'

import { openImage } from '@/composables/useImageViewer'

// 菜品卡片：店铺详情 / 推荐区复用
const props = defineProps({
  dish: { type: Object, required: true },
})

const router = useRouter()
const imageFailed = ref(false)

// 价格展示：去掉多余的尾随 0（12.50 -> 12.5，38.00 -> 38）
const priceText = computed(() => String(Number(props.dish.price) || 0))

const goDetail = () => {
  if (props.dish.id) router.push(`/dishes/${props.dish.id}`)
}
</script>

<style scoped>
/* 与 ShopCard/PostCard 同一骨架：撑满格子 + 封面定高，混排时行内高度才对齐 */
.dish-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.dish-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}
.dish-cover {
  height: 150px;
  flex-shrink: 0;
  background: var(--el-color-primary-light-9);
}
.dish-cover img {
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
  font-size: 40px;
  color: var(--el-color-primary-light-5);
}
.dish-info {
  padding: 14px 16px 16px;
  flex: 1;
}
.dish-name {
  margin: 0 0 6px;
  font-size: 16px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dish-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.dish-price {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}
.dish-rating {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  color: #909399;
}
.star-icon {
  font-size: 14px;
  color: #f7ba2a;
}
.dish-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.rec-reason {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}
</style>
