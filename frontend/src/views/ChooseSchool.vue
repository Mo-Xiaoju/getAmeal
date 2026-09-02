<template>
  <div class="choose-school">
    <h2 class="page-title">选择你的学校</h2>
    <p class="page-desc">
      全国 {{ schoolStore.schoolList.length || '—' }} 所高校（教育部全国高等学校名单）
      {{ userStore.isLoggedIn ? '，选择后同步绑定到你的账号' : '，注册时自动绑定到账号' }}
    </p>

    <div class="search-bar">
      <el-input
        v-model="keyword"
        placeholder="输入学校名称关键词，例如「北京」「师范」「理工」"
        clearable
        size="large"
        :prefix-icon="Search"
        @input="handleInput"
        @clear="handleInput"
      />
    </div>

    <div v-loading="schoolStore.loading" class="result-info">
      <template v-if="schoolStore.schoolList.length">
        <template v-if="keyword.trim()">
          共找到 <b>{{ filtered.length }}</b> 所匹配学校
          <span v-if="filtered.length > CAP" class="cap-hint">，仅显示前 {{ CAP }} 所，请细化关键词</span>
        </template>
        <template v-else>
          <span class="cap-hint">输入关键词筛选；以下为前 {{ CAP }} 所</span>
        </template>
      </template>
    </div>

    <div v-if="!schoolStore.loading && schoolStore.schoolList.length" class="school-grid">
      <div
        v-for="school in shown"
        :key="school.id"
        class="school-card"
        :class="{ selected: currentId === school.id }"
        @click="handleSelect(school)"
      >
        <div class="school-logo">
          <el-avatar :size="48" :src="school.logo_url || undefined" class="logo-avatar">
            {{ school.name.charAt(0) }}
          </el-avatar>
        </div>
        <div class="school-main">
          <h3 class="school-name">{{ school.name }}</h3>
          <p class="school-addr">
            <el-icon><Location /></el-icon>{{ school.address || '—' }}
          </p>
        </div>
        <div class="school-check">
          <el-icon v-if="currentId === school.id" class="checked-icon"><CircleCheckFilled /></el-icon>
          <span v-else class="enter-hint">进入 →</span>
        </div>
      </div>
    </div>

    <el-empty
      v-if="!schoolStore.loading && schoolStore.schoolList.length && !shown.length"
      :description="'没有找到与「' + keyword + '」匹配的学校'"
    />
    <el-empty
      v-else-if="!schoolStore.loading && !schoolStore.schoolList.length"
      description="暂无学校数据，请先执行 flask import-schools"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheckFilled, Location, Search } from '@element-plus/icons-vue'

import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'

const CAP = 36 // 每屏最多渲染的学校数，避免 3000+ DOM 节点

const router = useRouter()
const schoolStore = useSchoolStore()
const userStore = useUserStore()

const keyword = ref('')
const currentId = computed(() => schoolStore.currentSchool?.id)

// 客户端过滤（学校列表一次性加载，3000 条内存过滤即时完成）
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return schoolStore.schoolList
  return schoolStore.schoolList.filter((s) => s.name.toLowerCase().includes(kw))
})

const shown = computed(() => filtered.value.slice(0, CAP))

const handleInput = () => {
  // 供 el-input 事件绑定；过滤由 computed 自动完成
}

const handleSelect = async (school) => {
  await schoolStore.selectSchool(school)
  router.push('/')
}

onMounted(() => {
  if (!schoolStore.schoolList.length) {
    schoolStore.fetchSchools()
  }
})
</script>

<style scoped>
.choose-school {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}
.page-title {
  margin: 0 0 8px;
  text-align: center;
  color: #303133;
}
.page-desc {
  margin: 0 0 24px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}
.search-bar {
  margin-bottom: 12px;
}
.result-info {
  min-height: 24px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}
.cap-hint {
  color: #c0c4cc;
}
.school-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 12px;
}
.school-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.school-card:hover {
  border-color: var(--el-color-primary);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}
.school-card.selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
.school-logo {
  flex-shrink: 0;
}
.logo-avatar {
  font-size: 18px;
  background: var(--el-color-primary-light-7);
  color: #fff;
}
.school-main {
  flex: 1;
  min-width: 0;
}
.school-name {
  margin: 0 0 4px;
  font-size: 15px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.school-addr {
  display: flex;
  align-items: center;
  gap: 3px;
  margin: 0;
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.school-check {
  flex-shrink: 0;
  font-size: 13px;
}
.checked-icon {
  color: var(--el-color-primary);
  font-size: 20px;
}
.enter-hint {
  color: #c0c4cc;
}
</style>
