<template>
  <span class="rating-stars">
    <template v-for="i in 5" :key="i">
      <el-icon v-if="i <= rounded" class="star filled"><StarFilled /></el-icon>
      <el-icon v-else class="star"><Star /></el-icon>
    </template>
    <span v-if="showValue" class="rating-value">{{ rating.toFixed(1) }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { Star, StarFilled } from '@element-plus/icons-vue'

// 评分展示：根据 rating 渲染星星
const props = defineProps({
  rating: { type: Number, required: true, default: 0 },
  showValue: { type: Boolean, default: false },
})

const rounded = computed(() => Math.round(props.rating))
</script>

<style scoped>
.rating-stars {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}
.star {
  font-size: 16px;
  color: #c0c4cc;
}
.star.filled {
  color: #f7ba2a;
}
.rating-value {
  margin-left: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #f56c6c;
}
</style>
