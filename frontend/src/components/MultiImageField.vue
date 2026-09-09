<template>
  <div class="multi-image-field">
    <div class="mif-tiles">
      <!-- 填满末尾空槽后自动在右侧补一个新空槽（未达上限时） -->
      <ImageField
        v-for="(url, i) in slots"
        :key="i"
        :model-value="url"
        :size="size"
        :tip="url ? '' : tip"
        @update:model-value="onChange(i, $event)"
      />
    </div>
    <p v-if="filledCount() >= max" class="mif-limit">最多上传 {{ max }} 张</p>
  </div>
</template>

<script setup>
// 多图上传：v-model 为已上传图片 URL 数组。内部维护 [已填…, 末尾一个空槽] 的不变量：
// 上传一张后右侧自动补一个空上传位；移除某张即删除该槽并把空槽补回最右。
import { ref, watch } from 'vue'

import ImageField from '@/components/ImageField.vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 9 },
  size: { type: Number, default: 88 }, // 每张预览框边长 px
  tip: { type: String, default: '添加图片' }, // 空上传槽的小字说明
})
const emit = defineEmits(['update:modelValue'])

function buildSlots(urls) {
  const list = [...urls].filter((u) => (u || '').trim()).map((u) => u.trim())
  if (list.length < props.max) list.push('')
  return list.slice(0, props.max)
}

function filledCount() {
  return slots.value.filter((u) => (u || '').trim()).length
}

const slots = ref(buildSlots(props.modelValue || []))

// 外部重置（如表单清空/回填）时同步槽位；用已填内容比较避免自己 emit 引发的回环
watch(
  () => props.modelValue,
  (val) => {
    const incoming = [...(val || [])].filter((u) => (u || '').trim())
    const current = slots.value.filter((u) => (u || '').trim())
    if (incoming.join('\n') !== current.join('\n')) {
      slots.value = buildSlots(incoming)
    }
  },
)

function emitValue() {
  emit('update:modelValue', slots.value.filter((u) => (u || '').trim()))
}

function ensureTrailing() {
  slots.value = slots.value.filter((u) => (u || '').trim())
  if (slots.value.length < props.max) slots.value.push('')
}

function onChange(i, val) {
  const url = (val || '').trim()
  if (!url) {
    // 右上角 ✕：移除该张
    slots.value.splice(i, 1)
    ensureTrailing()
    emitValue()
    return
  }
  slots.value[i] = url
  // 填满的是末尾空槽 → 右侧自动补一个空上传位
  if (i === slots.value.length - 1 && filledCount() < props.max) {
    slots.value.push('')
  }
  emitValue()
}
</script>

<style scoped>
.multi-image-field {
  width: 100%;
}
.mif-tiles {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.mif-limit {
  margin: 8px 0 0;
  font-size: 12px;
  color: #909399;
}
</style>
