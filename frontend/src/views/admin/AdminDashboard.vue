<template>
  <div class="admin-dashboard">
    <div class="page-head">
      <div>
        <h1 class="page-title">管理后台</h1>
        <p class="page-desc">用户、店铺与内容审核统一管理</p>
      </div>
    </div>


    <el-tabs v-model="activeTab" type="border-card">
      <!-- 用户管理 -->
      <el-tab-pane label="用户管理" name="users">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span>用户列表</span>
              <span class="panel-hint">可直接修改角色（学生 / 商户 / 管理员）或停用账号</span>
              <el-button class="panel-refresh" size="small" :icon="Refresh" @click="loadUsers(1)">刷新</el-button>
            </div>
          </template>

          <el-table v-loading="loadingUsers" :data="users" :key="'users-' + users.length" stripe>
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
              :total="totalUsers"
              :page-size="pageSize"
              :current-page="pageUsers"
              @current-change="loadUsers"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 店铺管理 -->
      <el-tab-pane label="店铺管理" name="shops">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-head">
              <span>店铺列表</span>
              <div class="panel-actions">
                <el-button size="small" :icon="Refresh" @click="loadShops(1)">刷新</el-button>
                <el-button type="primary" size="small" @click="openShopDialog()">新增店铺</el-button>
              </div>
            </div>
          </template>


          <el-table v-loading="loadingShops" :data="shops" :key="'shops-' + shops.length" stripe>
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="name" label="店名" min-width="140" />
            <el-table-column prop="school_name" label="学校" min-width="120">
              <template #default="{ row }">{{ row.school_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column label="大分类" width="90">
              <!-- 「未设置」即迁移时未回填的存量店，是管理员需要补值的待办清单 -->
              <template #default="{ row }">
                <span :class="{ 'zone-missing': !row.zone }">{{ row.zone || '未设置' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="price_range" label="人均" width="100" />
            <el-table-column prop="avg_rating" label="评分" width="80" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '营业中' : '已下架' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button link size="small" @click="openShopDialog(row)">编辑</el-button>
                <el-button link size="small" type="danger" @click="handleDeleteShop(row)">下架</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              background
              layout="prev, pager, next, total"
              :total="totalShops"
              :page-size="pageSize"
              :current-page="pageShops"
              @current-change="loadShops"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 内容审核 -->
      <el-tab-pane label="内容审核" name="audit">
        <AuditQueue />
      </el-tab-pane>

      <!-- 数据统计（埋点看板） -->
      <el-tab-pane label="数据统计" name="stats" lazy>
        <AdminStats />
      </el-tab-pane>
    </el-tabs>

    <!-- 店铺编辑弹窗 -->
    <el-dialog v-model="shopDialogVisible" :title="shopForm.id ? '编辑店铺' : '新增店铺'" width="500px">
      <el-form :model="shopForm" label-width="80px">
        <el-form-item label="店名" required>
          <el-input v-model="shopForm.name" placeholder="请输入店名" />
        </el-form-item>
        <el-form-item label="学校ID" required>
          <el-input-number v-model="shopForm.school_id" :min="1" />
        </el-form-item>
        <el-form-item label="地址" required>
          <el-input v-model="shopForm.address" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="大分类">
          <el-select v-model="shopForm.zone" placeholder="请选择（校内/周边/外卖）" clearable style="width: 100%">
            <el-option v-for="z in categoryStore.zones" :key="z" :label="z" :value="z" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="shopForm.category" placeholder="如：食堂、奶茶、火锅" />
        </el-form-item>
        <el-form-item label="人均">
          <el-input v-model="shopForm.price_range" placeholder="如：10-20元" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="shopForm.description" type="textarea" rows="3" />
        </el-form-item>
        <el-form-item label="封面图">
          <el-input v-model="shopForm.image_url" placeholder="图片 URL" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shopDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitShop">确定</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import {
  getAdminUsers,
  updateUser,
  getAdminShops,
  addShop,
  updateShop,
  deleteShop,
} from '@/api/admin'
import { useCategoryStore } from '@/store/category'
import { useUserStore } from '@/store/user'

import AuditQueue from './AuditQueue.vue'
import AdminStats from './AdminStats.vue'

const userStore = useUserStore()
const categoryStore = useCategoryStore()
const adminTab = ref('users')

// ========== 标签页 ==========
const activeTab = ref('users')

// ========== 用户管理 ==========
const loadingUsers = ref(false)
const users = ref([])
const pageUsers = ref(1)
const totalUsers = ref(0)

// ========== 店铺管理 ==========
const loadingShops = ref(false)
const shops = ref([])
const pageShops = ref(1)
const totalShops = ref(0)
const shopDialogVisible = ref(false)
const shopForm = ref({
  id: null,
  school_id: null,
  name: '',
  address: '',
  description: '',
  category: '',
  zone: '',
  price_range: '',
  image_url: '',
})

const pageSize = 20

const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ---- 用户管理 ----
const loadUsers = async (p = pageUsers.value) => {
  loadingUsers.value = true
  try {
    const res = await getAdminUsers({ page: p, page_size: pageSize })
    const d = res.data?.data || {}
    pageUsers.value = d.page || p
    totalUsers.value = d.total || 0
    users.value = d.items || []
  } catch (e) {
    console.error('users API error:', e)
  } finally {
    loadingUsers.value = false
  }
}

const handleRoleChange = async (row, role) => {
  try {
    await updateUser(row.id, { role })
    ElMessage.success(`已将「${row.username}」设为${roleName(role)}`)
  } catch (e) {
    loadUsers()
  }
}

const handleActiveChange = async (row, active) => {
  try {
    await updateUser(row.id, { is_active: active })
    row.is_active = active
    ElMessage.success(active ? '账号已启用' : '账号已停用')
  } catch (e) {
    loadUsers()
  }
}

const roleName = (r) => ({ student: '学生', merchant: '商户', admin: '管理员' }[r] || r)

// ---- 店铺管理 ----
const loadShops = async (p = pageShops.value) => {
  loadingShops.value = true
  try {
    const res = await getAdminShops({ page: p, page_size: pageSize })
    console.log('shops API res:', res)
    console.log('shops res.data:', res.data)
    const d = res.data?.data || {}
    pageShops.value = d.page || p
    totalShops.value = d.total || 0
    shops.value = d.items || []
    console.log('shops.value:', shops.value)
  } catch (e) {
    console.error('shops API error:', e)
  } finally {
    loadingShops.value = false
  }
}

const openShopDialog = (row = null) => {
  if (row) {
    shopForm.value = { ...row }
  } else {
    shopForm.value = {
      id: null,
      school_id: null,
      name: '',
      address: '',
      description: '',
      category: '',
      zone: '',
      price_range: '',
      image_url: '',
    }
  }
  shopDialogVisible.value = true
}

const submitShop = async () => {
  const f = shopForm.value
  if (!f.name || !f.school_id || !f.address) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (f.id) {
      await updateShop(f.id, f)
      ElMessage.success('店铺已更新')
    } else {
      await addShop(f)
      ElMessage.success('店铺已创建')
    }
    shopDialogVisible.value = false
    loadShops()
  } catch (e) {
    // 错误由 request 拦截器统一提示
  }
}

const handleDeleteShop = async (row) => {
  try {
    await ElMessageBox.confirm(`确定下架「${row.name}」吗？`, '提示', { type: 'warning' })
    await deleteShop(row.id)
    ElMessage.success('店铺已下架')
    loadShops()
  } catch (e) {
    if (e !== 'cancel') {
      // 非取消的错误
    }
  }
}

onMounted(() => {
  if (!categoryStore.zones.length) categoryStore.fetchZones()
  loadUsers(1)
  loadShops(1)
})
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
.panel-refresh {
  margin-left: auto;
}
.panel-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.admin-tabs {
  margin-top: 4px;
}
.zone-missing {
  color: #c0c4cc;
}
</style>
