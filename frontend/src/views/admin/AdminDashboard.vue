<template>
  <div class="admin-dashboard">
    <div class="page-head">
      <div>
        <h1 class="page-title">管理后台</h1>
        <p class="page-desc">用户角色 / 状态管理</p>
      </div>
      <el-button :icon="Refresh" plain @click="loadUsers(1)">刷新</el-button>
    </div>

    <el-card shadow="never" class="panel">
      <template #header>
        <div class="panel-head">
          <span>用户管理</span>
          <span class="panel-hint">可直接修改角色（学生 / 商户 / 管理员）或停用账号</span>
        </div>
      </template>

      <el-table v-loading="loading" :data="users" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="140" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <el-select
              :model-value="row.role"
              :disabled="row.id === userStore.userInfo?.id"
              size="small"
              @change="(v) => handleRoleChange(row, v)"
            >
              <el-option label="学生" value="student" />
              <el-option label="商户" value="merchant" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="school_name" label="学校" min-width="120">
          <template #default="{ row }">{{ row.school_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :disabled="row.id === userStore.userInfo?.id"
              size="small"
              @change="(v) => handleActiveChange(row, v)"
            />
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="loadUsers"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import { getAdminUsers, updateUser } from '@/api/admin'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const loading = ref(false)
const users = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)

const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const loadUsers = async (p = page.value) => {
  loading.value = true
  try {
    const data = await getAdminUsers({ page: p, page_size: pageSize })
    page.value = data.data.page || p
    total.value = data.data.total || 0
    users.value = data.data.items || []
  } finally {
    loading.value = false
  }
}

const handleRoleChange = async (row, role) => {
  try {
    await updateUser(row.id, { role })
    ElMessage.success(`已将「${row.username}」设为${roleName(role)}`)
  } catch (e) {
    loadUsers() // 失败回滚
  }
}

const handleActiveChange = async (row, active) => {
  try {
    await updateUser(row.id, { is_active: active })
    ElMessage.success(active ? '账号已启用' : '账号已停用')
  } catch (e) {
    loadUsers() // 失败回滚
  }
}

const roleName = (r) => ({ student: '学生', merchant: '商户', admin: '管理员' }[r] || r)

onMounted(() => loadUsers(1))
</script>

<style scoped>
.admin-dashboard {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  margin: 0 0 6px;
  font-size: 26px;
  color: #303133;
}
.page-desc {
  margin: 0;
  font-size: 14px;
  color: #909399;
}
.panel-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.panel-hint {
  font-size: 13px;
  color: #909399;
  font-weight: 400;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
