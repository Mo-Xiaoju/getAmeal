import axios from 'axios'
import { ElMessage } from 'element-plus'

import { getToken, removeSchool, removeToken } from '@/utils/auth'

// axios 实例：统一 baseURL / 超时 / 凭证
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  withCredentials: true,
})

// 请求拦截器：附加 token
request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一解包业务码、401 时处理登录态失效
request.interceptors.response.use(
  (response) => {
    // 业务失败：HTTP 200 但业务码非 0
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body && body.code !== 0) {
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // token 过期 / 未登录：清除登录态与学校上下文并跳转登录页
      removeToken()
      removeSchool()
      const { pathname, search } = window.location
      ElMessage.error(error.response.data?.message || '登录已过期，请重新登录')
      if (!['/login', '/register'].includes(window.location.pathname)) {
        window.location.href = `/login?redirect=${encodeURIComponent(pathname + search)}`
      }
    } else if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else if (!error.response) {
      ElMessage.error('网络异常，请检查后端服务是否已启动')
    }
    return Promise.reject(error)
  },
)

export default request
