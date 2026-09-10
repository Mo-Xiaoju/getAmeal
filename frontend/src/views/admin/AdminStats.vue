<template>
  <div class="admin-stats">
    <div class="pane-head">
      <span class="pane-hint">埋点事件聚合：提交与审核趋势、事件类型与学校分布</span>
      <el-button size="small" :icon="Refresh" @click="refreshAll">刷新</el-button>
    </div>

    <!-- KPI 概览 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col v-for="kpi in kpiCards" :key="kpi.label" :span="4">
        <el-card shadow="never" class="kpi-card">
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-label">{{ kpi.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 提交 / 审核趋势 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="panel-head">
          <span>提交 / 审核趋势</span>
          <el-select v-model="days" size="small" style="width: 110px" @change="loadStats">
            <el-option :value="7" label="近 7 天" />
            <el-option :value="14" label="近 14 天" />
            <el-option :value="30" label="近 30 天" />
          </el-select>
        </div>
      </template>
      <div ref="trendRef" class="chart"></div>
    </el-card>

    <!-- 类型分布 + 学校分布 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span>事件类型分布</span></template>
          <div ref="typeRef" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <template #header><span>按学校分布</span></template>
          <div ref="schoolRef" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 事件明细 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="panel-head">
          <span>事件明细</span>
          <el-select
            v-model="eventTypeFilter"
            size="small"
            clearable
            placeholder="全部类型"
            style="width: 150px"
            @change="loadEvents(1)"
          >
            <el-option v-for="(label, val) in EVENT_LABELS" :key="val" :value="val" :label="label" />
          </el-select>
        </div>
      </template>

      <el-table v-loading="loadingEvents" :data="events" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="事件" width="130">
          <template #default="{ row }">
            <el-tag :type="eventTagType(row.event_type)" size="small">
              {{ EVENT_LABELS[row.event_type] || row.event_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作者" min-width="150">
          <template #default="{ row }">
            <span>{{ row.actor_nickname || '-' }}</span>
            <span v-if="row.actor_role" class="role-tag">{{ roleLabel(row.actor_role) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="对象" min-width="140">
          <template #default="{ row }">{{ row.extra?.name || row.extra?.title || '-' }}</template>
        </el-table-column>
        <el-table-column label="学校" min-width="130">
          <template #default="{ row }">{{ row.school_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="totalEvents"
          :page-size="pageSize"
          :current-page="pageEvents"
          @current-change="loadEvents"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { Refresh } from '@element-plus/icons-vue'

import { getAdminStats, getAdminEvents } from '@/api/admin'

// 事件类型 → 中文标签（后端受控词表见 EventLog 模型）
const EVENT_LABELS = {
  shop_submit: '提交店铺',
  dish_submit: '提交菜品',
  shop_approve: '店铺通过',
  shop_reject: '店铺驳回',
  dish_approve: '菜品通过',
  dish_reject: '菜品驳回',
  post_create: '发布笔记',
}

const days = ref(14)
const summary = ref({})
const trend = ref([])
const byType = ref([])
const bySchool = ref([])

const events = ref([])
const pageEvents = ref(1)
const totalEvents = ref(0)
const pageSize = 20
const loadingEvents = ref(false)
const eventTypeFilter = ref('')

const trendRef = ref()
const typeRef = ref()
const schoolRef = ref()
let trendChart = null
let typeChart = null
let schoolChart = null

const kpiCards = computed(() => {
  const s = summary.value
  const rate = s.approval_rate == null ? '-' : `${(s.approval_rate * 100).toFixed(1)}%`
  return [
    { label: '总事件', value: s.total_events ?? 0 },
    { label: '提交', value: s.total_submits ?? 0 },
    { label: '通过', value: s.total_approves ?? 0 },
    { label: '驳回', value: s.total_rejects ?? 0 },
    { label: '通过率', value: rate },
    { label: '店铺', value: s.total_shops ?? 0 },
  ]
})

const loadStats = async () => {
  try {
    const res = await getAdminStats({ days: days.value })
    const d = res.data?.data || {}
    summary.value = d.summary || {}
    trend.value = d.trend || []
    byType.value = d.by_type || []
    bySchool.value = d.by_school || []
    renderTrend()
    renderType()
    renderSchool()
  } catch (e) {
    console.error('stats API error:', e)
  }
}

const loadEvents = async (p = pageEvents.value) => {
  loadingEvents.value = true
  try {
    const params = { page: p, page_size: pageSize }
    if (eventTypeFilter.value) params.event_type = eventTypeFilter.value
    const res = await getAdminEvents(params)
    const d = res.data?.data || {}
    pageEvents.value = d.page || p
    totalEvents.value = d.total || 0
    events.value = d.items || []
  } catch (e) {
    console.error('events API error:', e)
  } finally {
    loadingEvents.value = false
  }
}

const refreshAll = () => {
  loadStats()
  loadEvents(1)
}

// ---- 图表渲染（配色取自 dataviz 验证调色板）----
const axisText = { color: '#909399' }
const splitLine = { lineStyle: { color: '#ebeef5' } }

const renderTrend = () => {
  if (!trendRef.value) return
  if (!trendChart) trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    color: ['#2a78d6', '#1baf7a', '#e34948'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['提交', '通过', '驳回'], top: 0 },
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trend.value.map((d) => d.date),
      axisLabel: axisText,
      axisLine: { lineStyle: { color: '#dcdfe6' } },
    },
    yAxis: { type: 'value', minInterval: 1, axisLabel: axisText, splitLine },
    series: [
      { name: '提交', type: 'line', smooth: true, symbolSize: 6, data: trend.value.map((d) => d.submits) },
      { name: '通过', type: 'line', smooth: true, symbolSize: 6, data: trend.value.map((d) => d.approves) },
      { name: '驳回', type: 'line', smooth: true, symbolSize: 6, data: trend.value.map((d) => d.rejects) },
    ],
  })
}

const renderType = () => {
  if (!typeRef.value) return
  if (!typeChart) typeChart = echarts.init(typeRef.value)
  const data = [...byType.value].reverse()
  typeChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', minInterval: 1, axisLabel: axisText, splitLine },
    yAxis: {
      type: 'category',
      data: data.map((d) => EVENT_LABELS[d.event_type] || d.event_type),
      axisLabel: { color: '#606266' },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 20,
        data: data.map((d) => d.count),
        itemStyle: { color: '#2a78d6', borderRadius: [0, 4, 4, 0] },
      },
    ],
  })
}

const renderSchool = () => {
  if (!schoolRef.value) return
  if (!schoolChart) schoolChart = echarts.init(schoolRef.value)
  const data = [...bySchool.value].reverse()
  schoolChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
    xAxis: { type: 'value', minInterval: 1, axisLabel: axisText, splitLine },
    yAxis: {
      type: 'category',
      data: data.map((d) => d.name || `学校 ${d.school_id}`),
      axisLabel: { color: '#606266' },
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 20,
        data: data.map((d) => d.count),
        itemStyle: { color: '#eb6834', borderRadius: [0, 4, 4, 0] },
      },
    ],
  })
}

const onResize = () => {
  trendChart?.resize()
  typeChart?.resize()
  schoolChart?.resize()
}

const eventTagType = (et) => {
  if (et.endsWith('_approve')) return 'success'
  if (et.endsWith('_reject')) return 'danger'
  if (et === 'post_create') return 'info'
  return 'primary'
}

const roleLabel = (r) => ({ student: '学生', merchant: '商户', admin: '管理员' }[r] || '')

const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadStats()
  loadEvents(1)
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  trendChart?.dispose()
  typeChart?.dispose()
  schoolChart?.dispose()
})
</script>

<style scoped>
.admin-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.pane-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.pane-hint {
  font-size: 13px;
  color: #909399;
}
.kpi-card {
  text-align: center;
}
.kpi-value {
  font-size: 26px;
  font-weight: 600;
  color: #303133;
  font-variant-numeric: tabular-nums;
}
.kpi-label {
  margin-top: 6px;
  font-size: 13px;
  color: #909399;
}
.chart-card {
  width: 100%;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chart {
  width: 100%;
  height: 300px;
}
.role-tag {
  margin-left: 6px;
  font-size: 12px;
  color: #909399;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
