<template>
  <!-- 点赞图标。Element Plus 图标集里没有大拇指（最接近的 Pointer 是一只指向别处的手，
       放在"点赞"旁边反而更像跳转），所以这里直接内联 Material 的 thumb_up。
       filled=false 描边、filled=true 实心：与 StarIcon 同一套规则，
       "未点赞 / 已点赞"除了颜色还有形状差异，不依赖颜色也能分辨。
       fill="currentColor"：塞进 el-icon / el-button 后颜色跟着父级走 -->
  <svg class="thumb-up-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path
      v-if="filled"
      d="M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"
    />
    <path
      v-else
      d="M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.58 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2zm-2 2l-3.02 7H9V9l4.34-4.34L12.23 10H21v2z"
    />
  </svg>
</template>

<script setup>
defineProps({
  // 已点赞：实心
  filled: { type: Boolean, default: false },
})
</script>

<style scoped>
/* 与 el-icon 内置图标的尺寸规则保持一致（1em，随字号缩放） */
.thumb-up-icon {
  width: 1em;
  height: 1em;
  display: block;
}
</style>
