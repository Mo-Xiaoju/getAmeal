<template>
  <div class="message-input">
    <!-- 消息输入框：群聊页使用（占位） -->
  </div>
</template>

<script setup>
// 群聊消息输入：发送/禁态控制
defineProps({
  disabled: { type: Boolean, default: false },
})

// TODO: emit('send', content)
</script>
