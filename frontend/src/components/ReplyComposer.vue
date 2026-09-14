<template>
  <div class="reply-composer">
    <el-input
      v-model="text"
      type="textarea"
      :rows="2"
      maxlength="200"
      show-word-limit
      :disabled="guestLocked"
      :placeholder="placeholder"
    />
    <LoginHint v-if="guestLocked" text="登录后即可回复" />
    <div class="rc-actions">
      <el-button size="small" @click="$emit('cancel')">取消</el-button>
      <el-button
        size="small"
        type="primary"
        :disabled="guestLocked"
        :loading="submitting"
        @click="submit"
      >
        回复
      </el-button>
    </div>
  </div>
</template>

<script setup>
// 内联回复框。评价 / 笔记评论共用一份，避免在「回复评价」和「回复某条回复」两处
// 各写一遍（本组件不碰接口，提交只往上抛事件）。
import { computed, ref } from 'vue'

import LoginHint from '@/components/LoginHint.vue'

const props = defineProps({
  // 被回复人昵称；为空表示回复的是评价/评论本身
  nickname: { type: String, default: '' },
  guestLocked: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
})
const emit = defineEmits(['submit', 'cancel'])

const text = ref('')
const placeholder = computed(() =>
  props.guestLocked
    ? '登录后即可回复'
    : props.nickname
      ? `回复 @${props.nickname}`
      : '写下你的回复…',
)

function submit() {
  emit('submit', text.value)
}
</script>

<style scoped>
.reply-composer {
  margin-top: 8px;
}
.rc-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}
</style>
