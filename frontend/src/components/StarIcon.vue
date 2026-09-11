<template>
  <!-- 收藏图标。与 ThumbUpIcon 同源（同一套 Material 图形、同样的 1em 尺寸与笔画粗细）：
       两个图标会在卡片的同一行里并排出现，混用 Element Plus 的 Star 会让两颗星的观感对不齐。
       filled=false 描边、filled=true 实心 —— 收藏状态除了颜色还有形状差异。
       注意：评分（RatingStars / DishCard）仍用 el-icon 的 Star，那是"打了几分"，
       和"我收藏了没"是两回事，不复用这套 -->
  <svg class="star-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path
      v-if="filled"
      d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"
    />
    <path
      v-else
      d="M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4z"
    />
  </svg>
</template>

<script setup>
defineProps({
  // 已收藏：实心
  filled: { type: Boolean, default: false },
})
</script>

<style scoped>
.star-icon {
  width: 1em;
  height: 1em;
  display: block;
}
</style>
