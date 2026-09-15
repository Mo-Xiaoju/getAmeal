<template>
  <div class="price-range-field">
    <div class="prf-row">
      <el-input-number
        v-model="min"
        class="prf-input"
        :min="PRICE_MIN"
        :max="PRICE_MAX"
        :step="1"
        :precision="0"
        :controls="false"
        :disabled="disabled"
        placeholder="最低"
        aria-label="人均最低价（整数元）"
      />
      <span class="prf-sep">~</span>
      <el-input-number
        v-model="max"
        class="prf-input"
        :min="PRICE_MIN"
        :max="PRICE_MAX"
        :step="1"
        :precision="0"
        :controls="false"
        :disabled="disabled"
        placeholder="最高"
        aria-label="人均最高价（整数元）"
      />
      <span class="prf-unit">元</span>
    </div>
    <p v-if="error" class="prf-error">{{ error }}</p>
    <p v-else class="prf-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
// 人均区间输入：两个整数输入框（最低 / 最高），v-model 值是 { min, max } 的整数区间。
// 硬性约束——只有两端都填且 min<=max 时才对外产出值，避免半填或倒挂的区间流到提交接口；
// 与后端 string 的互转统一走 utils/priceRange。
import { computed, nextTick, ref, watch } from 'vue'

import { PRICE_MAX, PRICE_MIN, formatPriceRange } from '@/utils/priceRange'

const props = defineProps({
  // { min: number|null, max: number|null }
  modelValue: { type: Object, default: () => ({ min: null, max: null }) },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const min = ref(null)
const max = ref(null)
// 外部回填与内部改动共用同一组 ref，用标志位隔断回声，避免循环 emit
let syncing = false

const norm = (v) => (v === null || v === undefined || v === '' ? null : Math.trunc(Number(v)))

watch(
  () => [norm(props.modelValue?.min), norm(props.modelValue?.max)],
  ([m, x]) => {
    if (m === min.value && x === max.value) return
    syncing = true
    min.value = m
    max.value = x
    nextTick(() => {
      syncing = false
    })
  },
  { immediate: true },
)

watch([min, max], () => {
  if (syncing) return
  emit('update:modelValue', { min: norm(min.value), max: norm(max.value) })
})

const error = computed(() => {
  const m = norm(min.value)
  const x = norm(max.value)
  if (m === null && x === null) return ''
  if (m === null || x === null) return '最低价与最高价需同时填写'
  if (m > x) return '最低价不能高于最高价'
  return ''
})

const hint = computed(() => {
  const text = formatPriceRange({ min: min.value, max: max.value })
  return text ? `展示为「${text}」` : '留空则不在店铺中展示人均'
})
</script>

<style scoped>
.price-range-field {
  width: 100%;
}
.prf-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.prf-input {
  flex: 1;
  min-width: 0;
}
.prf-input :deep(.el-input__inner) {
  text-align: center;
}
.prf-sep {
  color: #909399;
}
.prf-unit {
  font-size: 13px;
  color: #909399;
}
.prf-error {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-color-danger);
}
.prf-hint {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #909399;
}
</style>
