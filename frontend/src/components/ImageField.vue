<template>
  <div class="image-field">
    <!-- 预览 / 空占位（点击唤起本地选择） -->
    <div
      class="if-box"
      :class="{ circle: circle }"
      :style="{ width: size + 'px', height: size + 'px' }"
      @click="pickFile"
    >
      <img v-if="modelValue && !uploading" :src="modelValue" class="if-img" alt="" />
      <div v-else-if="!uploading" class="if-empty">
        <el-icon :size="20"><Plus /></el-icon>
        <span>图片</span>
      </div>
      <div v-if="uploading" class="if-mask">
        <el-icon class="is-loading" :size="22"><Loading /></el-icon>
      </div>
      <!-- 已有图：悬停快捷操作 -->
      <div v-if="modelValue && !uploading" class="if-box-ops">
        <el-button circle size="small" type="primary" plain @click.stop="pickFile">
          <el-icon><RefreshRight /></el-icon>
        </el-button>
        <el-button circle size="small" type="danger" plain @click.stop="remove">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 主按钮组：无图＝上传；有图＝更换/移除；URL 仅作备择 -->
    <div class="if-actions">
      <el-button size="small" :type="modelValue ? 'default' : 'primary'" plain :loading="uploading" :disabled="disabled" @click="pickFile">
        <el-icon><Upload /></el-icon>
        {{ modelValue ? '更换图片' : '上传本地图片' }}
      </el-button>
      <el-button v-if="modelValue" size="small" text type="danger" :disabled="disabled" @click="remove">
        移除
      </el-button>
      <el-button size="small" text :disabled="disabled" @click="toggleLink">
        {{ showLink ? '收起链接' : '使用图片链接' }}
      </el-button>
    </div>

    <!-- 备择：直接填图片 URL -->
    <div v-if="showLink" class="if-link">
      <el-input
        v-model="linkDraft"
        size="small"
        placeholder="https://… 或 /api/uploads/…"
        clearable
        @keyup.enter="applyLink"
      />
      <el-button size="small" type="primary" plain :disabled="disabled" @click="applyLink">确定</el-button>
    </div>

    <input ref="fileRef" type="file" accept="image/*" class="if-file" @change="onFile" />
  </div>
</template>

<script setup>
// 图片字段：本地上传优先，URL 作备择。v-model 值为图片 URL 字符串，'' 表示无图。
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Loading, Plus, RefreshRight, Upload } from '@element-plus/icons-vue'

import { uploadImage } from '@/api/upload'

const props = defineProps({
  modelValue: { type: String, default: '' },
  size: { type: Number, default: 100 }, // 预览框边长 px
  circle: { type: Boolean, default: false }, // 圆形预览（头像用）
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const fileRef = ref(null)
const uploading = ref(false)
const showLink = ref(false)
const linkDraft = ref('')

const MAX_SIZE = 16 * 1024 * 1024 // 与后端 MAX_CONTENT_LENGTH 一致
const ALLOWED = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

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

function toggleLink() {
  showLink.value = !showLink.value
  if (showLink.value && props.modelValue) linkDraft.value = props.modelValue
}

function applyLink() {
  const url = linkDraft.value.trim()
  if (!url) {
    ElMessage.warning('请输入图片链接')
    return
  }
  emit('update:modelValue', url)
  showLink.value = false
}

function remove() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.image-field {
  display: inline-block;
  max-width: 100%;
}
.if-box {
  position: relative;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #fafafa;
}
.if-box.circle {
  border-radius: 50%;
}
.if-box:hover {
  border-color: var(--el-color-primary);
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
  font-size: 12px;
}
.if-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
  color: var(--el-color-primary);
}
.if-box-ops {
  position: absolute;
  right: 4px;
  bottom: 4px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}
.if-box:hover .if-box-ops {
  opacity: 1;
}
.if-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}
.if-link {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}
.if-file {
  display: none;
}
</style>
