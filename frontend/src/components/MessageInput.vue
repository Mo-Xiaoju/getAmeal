<template>
  <div class="message-input">
    <textarea
      ref="textareaRef"
      v-model="draft"
      class="message-input-area"
      rows="1"
      :placeholder="placeholder"
      :disabled="disabled"
      @keydown="onKeydown"
    />
    <el-button type="primary" :disabled="disabled || !canSend" @click="handleSend">发送</el-button>
  </div>
</template>

<script setup>
// 消息输入框：Enter 发送，Shift+Enter 换行；发送后自动聚焦
import { computed, nextTick, ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: '输入消息，Enter 发送，Shift+Enter 换行…' },
})
const emit = defineEmits(['send'])

const draft = ref('')
const textareaRef = ref(null)
const canSend = computed(() => draft.value.trim().length > 0 && !props.disabled)

const onKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleSend = () => {
  const text = draft.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  draft.value = ''
  nextTick(() => textareaRef.value?.focus())
}
</script>

<style scoped>
.message-input {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 10px 14px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
.message-input-area {
  flex: 1;
  resize: none;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 8px 12px;
  font: inherit;
  font-size: 14px;
  line-height: 20px;
  outline: none;
  max-height: 100px;
  color: #303133;
}
.message-input-area:focus {
  border-color: var(--el-color-primary);
}
.message-input-area:disabled {
  background: #f5f7fa;
  cursor: not-allowed;
}
</style>
