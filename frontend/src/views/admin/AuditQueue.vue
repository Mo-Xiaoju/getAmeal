<template>
  <div class="audit-queue">
    <el-tabs v-model="tab">
      <!-- 待审店铺：含该店全部待审菜品，可整店通过/驳回 -->
      <el-tab-pane :label="`待审店铺`" name="shops" lazy>
        <div class="pane-head">
          <span class="pane-hint">学生提交的店铺，可整店（含待审菜品）通过或驳回</span>
          <el-button size="small" :icon="Refresh" @click="loadShops(1)">刷新</el-button>
        </div>
        <div v-loading="shopsLoading" class="shop-list">
          <el-empty v-if="!shopsLoading && !shopList.length" description="暂无待审店铺" />
          <div v-for="shop in shopList" :key="shop.id" class="audit-shop">
            <div class="audit-shop-main">
              <div class="shop-line">
                <span class="shop-name">{{ shop.name }}</span>
                <el-tag v-if="shop.school_name" size="small" type="info" effect="plain">{{ shop.school_name }}</el-tag>
                <el-tag v-if="shop.category" size="small" type="primary" effect="light">{{ shop.category }}</el-tag>
                <el-tag v-if="shop.price_range" size="small" type="warning" effect="plain">{{ shop.price_range }}</el-tag>
              </div>
              <div class="shop-addr">{{ shop.address }}</div>
              <div class="shop-meta">
                提交者：{{ submitterText(shop.submitter) }} · {{ formatTime(shop.created_at) }}
              </div>
              <div class="pending-dishes">
                <template v-if="shop.pending_dishes.length">
                  <div class="pending-title">本店待审菜品（{{ shop.pending_dishes.length }} 道，将随整店操作一并处理）：</div>
                  <div v-for="d in shop.pending_dishes" :key="d.id" class="pending-dish">
                    <span class="pd-name">{{ d.name }}</span>
                    <span class="pd-price">¥{{ Number(d.price).toFixed(2) }}</span>
                    <span v-if="d.submitter" class="pd-by">由 {{ d.submitter.nickname }} 提交</span>
                  </div>
                </template>
                <div v-else class="no-dishes">本店暂无待审菜品</div>
              </div>
            </div>
            <div class="audit-ops">
              <el-button size="small" type="success" :loading="actingShop === shop.id" @click="bulkApprove(shop)">
                整店通过
              </el-button>
              <el-button size="small" type="danger" plain :loading="actingShop === shop.id" @click="bulkReject(shop)">
                驳回
              </el-button>
            </div>
          </div>
        </div>
        <div v-if="shopTotal > pageSize" class="pagination-wrap">
          <el-pagination
            background
            layout="prev, pager, next, total"
            :total="shopTotal"
            :page-size="pageSize"
            :current-page="shopPage"
            @current-change="loadShops"
          />
        </div>
      </el-tab-pane>

      <!-- 待审菜品：父店已通过，逐条单独审核 -->
      <el-tab-pane :label="`待审菜品`" name="dishes" lazy>
        <div class="pane-head">
          <span class="pane-hint">店铺已通过审核，同学补充/提交的菜品在此逐条审核</span>
          <el-button size="small" :icon="Refresh" @click="loadDishes(1)">刷新</el-button>
        </div>
        <el-table v-loading="dishesLoading" :data="dishList" stripe size="small">
          <el-table-column label="菜品" min-width="160">
            <template #default="{ row }">
              <span class="dish-cell">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="所属店铺" min-width="150">
            <template #default="{ row }">{{ row.shop_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="价格" width="100">
            <template #default="{ row }"><span class="price">¥{{ Number(row.price).toFixed(2) }}</span></template>
          </el-table-column>
          <el-table-column label="提交者" min-width="120">
            <template #default="{ row }">{{ submitterText(row.submitter) }}</template>
          </el-table-column>
          <el-table-column label="提交时间" width="150">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="success" :loading="actingDish === row.id" @click="approveDish(row)">
                通过
              </el-button>
              <el-button size="small" type="danger" plain :loading="actingDish === row.id" @click="rejectDish(row)">
                驳回
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!dishesLoading && !dishList.length" description="暂无待审菜品" />
        <div v-if="dishTotal > pageSize" class="pagination-wrap">
          <el-pagination
            background
            layout="prev, pager, next, total"
            :total="dishTotal"
            :page-size="pageSize"
            :current-page="dishPage"
            @current-change="loadDishes"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

import {
  bulkReviewShop,
  getAuditDishes,
  getAuditShops,
  reviewDish,
} from '@/api/admin'

const tab = ref('shops')
const pageSize = 10

// ---- 店铺队列 ----
const shopsLoading = ref(false)
const shopList = ref([])
const shopTotal = ref(0)
const shopPage = ref(1)
const actingShop = ref(null)

const loadShops = async (p = shopPage.value) => {
  shopsLoading.value = true
  try {
    const res = await getAuditShops({ status: 'pending', page: p, page_size: pageSize })
    const data = res.data.data
    shopList.value = data.items || []
    shopTotal.value = data.total || 0
    shopPage.value = data.page || p
  } finally {
    shopsLoading.value = false
  }
}

// ---- 菜品队列 ----
const dishesLoading = ref(false)
const dishList = ref([])
const dishTotal = ref(0)
const dishPage = ref(1)
const actingDish = ref(null)

const loadDishes = async (p = dishPage.value) => {
  dishesLoading.value = true
  try {
    const res = await getAuditDishes({ status: 'pending', page: p, page_size: pageSize })
    const data = res.data.data
    dishList.value = data.items || []
    dishTotal.value = data.total || 0
    dishPage.value = data.page || p
  } finally {
    dishesLoading.value = false
  }
}

const submitterText = (s) => (s ? `${s.nickname}${s.school_name ? ' · ' + s.school_name : ''}` : '未知')
const formatTime = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return (
    d.toLocaleDateString('zh-CN') +
    ' ' +
    d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  )
}

// 驳回需填写原因
const promptReason = () =>
  ElMessageBox.prompt('请填写驳回原因，提交者将看到该说明', '驳回', {
    confirmButtonText: '确定驳回',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputValidator: (v) => (v && v.trim() ? true : '请填写驳回原因'),
    inputPlaceholder: '例如：信息不完整 / 图片不清晰 / 与已有店铺重复',
  }).then(({ value }) => value.trim())

const bulkApprove = async (shop) => {
  const n = shop.pending_dishes?.length || 0
  actingShop.value = shop.id
  try {
    const res = await bulkReviewShop(shop.id, { action: 'approve' })
    const affected = res.data.data?.affected_dishes || 0
    ElMessage.success(affected ? `已通过店铺及 ${affected} 道待审菜品` : '已通过店铺')
    loadShops()
  } finally {
    actingShop.value = null
  }
}

const bulkReject = async (shop) => {
  let reason
  try {
    reason = await promptReason()
  } catch (e) {
    return // 用户取消
  }
  actingShop.value = shop.id
  try {
    const res = await bulkReviewShop(shop.id, { action: 'reject', reason })
    const affected = res.data.data?.affected_dishes || 0
    ElMessage.success(affected ? `已驳回店铺及 ${affected} 道待审菜品` : '已驳回店铺')
    loadShops()
  } finally {
    actingShop.value = null
  }
}

const approveDish = async (row) => {
  actingDish.value = row.id
  try {
    await reviewDish(row.id, { action: 'approve' })
    ElMessage.success(`已通过菜品「${row.name}」`)
    loadDishes()
  } finally {
    actingDish.value = null
  }
}

const rejectDish = async (row) => {
  let reason
  try {
    reason = await promptReason()
  } catch (e) {
    return
  }
  actingDish.value = row.id
  try {
    await reviewDish(row.id, { action: 'reject', reason })
    ElMessage.success(`已驳回菜品「${row.name}」`)
    loadDishes()
  } finally {
    actingDish.value = null
  }
}

onMounted(loadShops)

watch(tab, (newTab) => {
  if (newTab === 'dishes' && !dishList.value.length && !dishesLoading.value) {
    loadDishes()
  }
})
</script>

<style scoped>
.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.pane-hint {
  font-size: 13px;
  color: #909399;
}
.shop-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 80px;
}
.audit-shop {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 10px;
}
.audit-shop-main {
  flex: 1;
  min-width: 0;
}
.shop-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.shop-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.shop-addr {
  font-size: 13px;
  color: #606266;
}
.shop-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.pending-dishes {
  margin-top: 8px;
  padding: 8px 10px;
  background: #fafafa;
  border-radius: 8px;
}
.pending-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.pending-dish {
  display: flex;
  gap: 8px;
  align-items: baseline;
  font-size: 13px;
}
.pd-name {
  color: #303133;
}
.pd-price {
  color: #f56c6c;
  font-weight: 600;
}
.pd-by {
  font-size: 12px;
  color: #909399;
}
.no-dishes {
  font-size: 12px;
  color: #c0c4cc;
}
.audit-ops {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
.dish-cell {
  font-weight: 600;
  color: #303133;
}
.price {
  color: #f56c6c;
  font-weight: 600;
}
</style>
