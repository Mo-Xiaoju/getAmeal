<template>
  <div class="image-field">
    <!-- 点击分流：有图 = 放大预览（只读检查）；无图 = 选文件上传 -->
    <div
      class="if-box"
      :class="{ 'is-circle': circle, 'has-img': !!modelValue }"
      :style="{ width: size + 'px', height: size + 'px' }"
      role="button"
      tabindex="0"
      :aria-disabled="disabled"
      :title="boxTitle"
      :aria-label="modelValue ? '点击图片放大预览' : '点击上传图片'"
      @click="onBoxClick"
      @keydown.enter="onBoxClick"
    >
      <!-- 有图：原生 img 铺满整框，方形/圆形裁切不变。点击=放大预览，绝不打开文件选择 -->
      <img
        v-if="modelValue && !uploading && !broken"
        :src="modelValue"
        class="if-img"
        alt=""
        loading="lazy"
        @click.stop="preview"
        @error="broken = true"
      />
      <!-- 图已损坏（如旧数据死链）：占位提示，点击框=更换 -->
      <div v-else-if="modelValue && !uploading" class="if-empty">
        <el-icon :size="26"><Picture /></el-icon>
      </div>

      <!-- 空占位：仅示意"点这里上传"，无任何多余按钮 -->
      <div v-else-if="!uploading" class="if-empty">
        <el-icon :size="26"><Camera /></el-icon>
        <span v-if="tip" class="if-tip">{{ tip }}</span>
      </div>

      <div v-if="uploading" class="if-mask">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      </div>

      <!-- 有图：悬停透出的独立"更换/上传"小按钮（点它才换图，不再整块即上传） -->
      <button
        v-if="modelValue && !uploading"
        class="if-replace"
        type="button"
        :disabled="disabled"
        title="更换图片"
        aria-label="更换图片"
        @click.stop="pickFile"
      >
        <el-icon :size="16"><Camera /></el-icon>
      </button>

      <!-- 右上角移除 -->
      <button
        v-if="modelValue && !uploading && closable"
        class="if-remove"
        type="button"
        :disabled="disabled"
        title="移除图片"
        @click.stop="remove"
      >
        <el-icon :size="12"><Close /></el-icon>
      </button>
    </div>

    <input ref="fileRef" type="file" accept="image/*" class="if-file" @change="onFile" />
  </div>
</template>

<script setup>
// 图片字段：有图时点击缩略图 = 放大预览，悬停透出"更换"小按钮换图；空框点击=上传。
// 无 URL 链接、无多余按钮。v-model 值为图片 URL 字符串，'' 表示无图。
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera, Close, Loading, Picture } from '@element-plus/icons-vue'

import { uploadImage } from '@/api/upload'
import { openImage } from '@/composables/useImageViewer'

const props = defineProps({
  modelValue: { type: String, default: '' },
  size: { type: Number, default: 100 }, // 预览框边长 px
  circle: { type: Boolean, default: false }, // 圆形预览（头像用）
  tip: { type: String, default: '' }, // 空占位里的小字说明
  closable: { type: Boolean, default: true }, // 是否显示右上角移除（头像常改由父级提供移除入口）
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const fileRef = ref(null)
const uploading = ref(false)
// 图片加载失败标记：死链（旧数据）时改占位并把点击改为"更换"，换 URL 后自动复位
const broken = ref(false)

watch(
  () => props.modelValue,
  () => {
    broken.value = false
  },
)

const boxTitle = computed(() => {
  if (props.disabled) return '不可用'
  if (uploading.value) return '上传中…'
  if (props.modelValue && !broken.value) return '点击图片放大预览'
  return '点击上传图片'
})

const MAX_SIZE = 16 * 1024 * 1024 // 与后端 MAX_CONTENT_LENGTH 一致
const ALLOWED = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

// 有图：点击放大预览（只读检查原图）；无图 / 图损坏：点击选文件
function onBoxClick() {
  if (props.disabled || uploading.value) return
  if (props.modelValue && !broken.value) preview()
  else pickFile()
}

function preview() {
  const u = (props.modelValue || '').trim()
  if (u) openImage([u], 0)
}

function pickFile() {
  if (props.disabled || uploading.value) return
  fileRef.value?.click()
}

async function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // 复位 input，保证同文件可再次选择
  if (!file) return
  if (!ALLOWED.includes(file.type)) {
    ElMessage.warning('仅支持 png / jpg / jpeg / gif / webp 图片')
    return
  }
  if (file.size > MAX_SIZE) {
    ElMessage.warning('图片大小不能超过 16MB')
    return
  }
  uploading.value = true
  try {
    // 成功返回相对 URL；业务/网络失败已由 axios 拦截器统一提示，此处无需重复 toast
    const res = await uploadImage(file)
    emit('update:modelValue', res.data.data?.url || '')
  } catch (err) {
    // 无额外处理（拦截器已提示）
  } finally {
    uploading.value = false
  }
}

function remove() {
  if (props.disabled) return
  emit('update:modelValue', '')
}
</script>

<style scoped>
.image-field {
  display: inline-block;
  max-width: 100%;
  line-height: 0;
}
.if-box {
  position: relative;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fafafa;
  transition: border-color 0.15s;
}
.if-box.is-circle {
  border-radius: 50%;
}
.if-box.has-img {
  border-style: solid;
}
.if-box:hover,
.if-box:focus-visible {
  border-color: var(--el-color-primary);
  outline: none;
}
.if-box[aria-disabled='true'] {
  cursor: not-allowed;
  opacity: 0.7;
}
.if-box.has-img:not([aria-disabled='true']) {
  cursor: zoom-in;
}
.if-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.if-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  height: 100%;
  color: #909399;
  line-height: 1.2;
}
.if-tip {
  font-size: 12px;
}
.if-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.75);
  color: var(--el-color-primary);
}
/* 悬停透出的"更换/上传"小圆钮：默认透明且不拦截指针（避免隐形按钮吞掉点击预览），hover 才可用 */
.if-replace {
  position: absolute;
  left: 50%;
  bottom: 6px;
  transform: translateX(-50%);
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  cursor: pointer;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s, background 0.15s;
}
.if-box:hover .if-replace,
.if-replace:focus-visible {
  opacity: 1;
  pointer-events: auto;
}
.if-replace:hover {
  background: var(--el-color-primary);
}
.if-replace[disabled] {
  cursor: not-allowed;
}
/* 右上角移除按钮 */
.if-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  cursor: pointer;
  transition: background 0.15s;
}
.if-remove:hover {
  background: var(--el-color-danger);
}
.if-remove[disabled] {
  cursor: not-allowed;
}
.if-file {
  display: none;
}
</style>
