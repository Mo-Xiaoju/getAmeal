<template>
  <div v-if="zone" class="zone-ribbon" :style="{ background: color }">
    <span>{{ zone }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// 大分类（校内/周边/外卖）角标，覆盖在封面右上角的直角三角形。
// 与封面左上角的 category 标签互补：那个说「卖什么」（食堂/奶茶…），这个说「在哪买/怎么买」。
// zone 为空（含本次改动前的全部存量店铺）时整个角标不渲染。
const props = defineProps({
  zone: { type: String, default: '' },
})

// 用 -dark-2 档而非基础色：白字在 #67c23a / #e6a23c 这类基础色上对比度只有 2 出头
const ZONE_COLORS = {
  校内: 'var(--el-color-success-dark-2)',
  周边: 'var(--el-color-primary-dark-2)',
  外卖: 'var(--el-color-warning-dark-2)',
}
const color = computed(() => ZONE_COLORS[props.zone] || 'var(--el-color-info-dark-2)')
</script>

<style scoped>
.zone-ribbon {
  position: absolute;
  top: 0;
  right: 0;
  width: 64px;
  height: 64px;
  /* 右上角直角三角形：斜边自左上顶点 (0,0) 连到右下顶点 (64,64) */
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  /* 纯装饰：封面图挂着「点击放大」，角标不能吃掉点击事件 */
  pointer-events: none;
  z-index: 1;
}
.zone-ribbon span {
  /* 文字块整体绕自身中心旋转 45° 后与斜边平行，落在三角形内（clip-path 会兜底裁剪） */
  margin: 16px 4px 0 0;
  transform: rotate(45deg);
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 1px;
  color: #fff;
  white-space: nowrap;
}
</style>
