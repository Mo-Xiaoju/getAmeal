<template>
  <p class="login-hint">
    {{ text }}
    <el-link type="primary" :underline="false" @click="goLogin">去登录</el-link>
  </p>
</template>

<script setup>
// 游客态提示：置灰的输入框 / 按钮旁给一条明确出路，带 redirect 回跳当前页
import { useLoginGate } from '@/composables/useLoginGate'

defineProps({
  text: { type: String, default: '登录后即可参与互动' },
})

const { goLogin } = useLoginGate()
</script>

<style scoped>
.login-hint {
  margin: 8px 0 0;
  font-size: 13px;
  color: #909399;
}
</style>
