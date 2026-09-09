<template>
  <!-- 全屏图集查看器：v-if 保证每次打开都全新 mount，使 initial-index 生效（只在挂载时读取）；
       显式 teleported 挂到 body，弹层打开后才 mount 拿到更高的全局 z-index。 -->
  <el-image-viewer
    v-if="visible"
    :url-list="urlList"
    :initial-index="initialIndex"
    :hide-on-click-modal="true"
    :teleported="true"
    :close-on-press-escape="true"
    @close="close"
  />
</template>

<script setup>
import { useImageViewer } from '@/composables/useImageViewer'

const { visible, urlList, initialIndex, close } = useImageViewer()
</script>
