<template>
  <div class="auth-page">
    <div class="auth-card">
      <h2 class="auth-title">注册账号</h2>
      <p class="auth-subtitle">加入校园美食社区</p>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="用于登录，2-50 个字符" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="展示给其他用户的昵称" :prefix-icon="Postcard" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="6-50 个字符"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>
        <div v-if="schoolStore.hasSchool" class="register-school">
          <el-icon><School /></el-icon>
          <span>注册后将绑定「{{ schoolStore.currentSchool.name }}」</span>
        </div>
        <el-form-item>
          <el-button type="primary" class="auth-submit" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <router-link to="/login" class="auth-link">去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Postcard, School, User } from '@element-plus/icons-vue'

import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const schoolStore = useSchoolStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  nickname: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2-50 个字符', trigger: 'blur' },
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度为 6-50 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }

  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      password: form.password,
      nickname: form.nickname,
      school_id: schoolStore.hasSchool ? schoolStore.currentSchool.id : undefined,
    })
    ElMessage.success('注册成功，已自动登录')
    const redirect = route.query.redirect
    router.push(typeof redirect === 'string' ? redirect : '/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 160px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fdf6ec 0%, #ecf5ff 100%);
}
.auth-card {
  width: 380px;
  padding: 40px 36px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}
.auth-title {
  margin: 0 0 8px;
  text-align: center;
  color: #303133;
  font-size: 22px;
}
.auth-subtitle {
  margin: 0 0 28px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}
.register-school {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: -6px 0 14px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 13px;
}
.auth-submit {
  width: 100%;
  margin-top: 8px;
}
.auth-footer {
  margin-top: 20px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}
.auth-link {
  color: var(--el-color-primary);
  text-decoration: none;
}
.auth-link:hover {
  text-decoration: underline;
}
</style>
