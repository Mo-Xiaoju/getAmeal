// 全站点图放大统一入口（模块级单例状态）。
// ImageViewer.vue（App 根挂载一次）与本文件的调用点共享同一份状态；
// openImage(urls, index) 任意处调用即弹全屏查看器：传数组支持左右翻，传单值亦可。
import { ref } from 'vue'

const visible = ref(false)
const urlList = ref([])
const initialIndex = ref(0)

export function openImage(urls, index = 0) {
  const list = (Array.isArray(urls) ? urls : [urls])
    .map((u) => (u || '').trim())
    .filter(Boolean)
  if (!list.length) return
  urlList.value = list
  initialIndex.value = Math.min(Math.max(index || 0, 0), list.length - 1)
  visible.value = true
}

export function useImageViewer() {
  return {
    visible,
    urlList,
    initialIndex,
    openImage,
    close: () => {
      visible.value = false
    },
  }
}
