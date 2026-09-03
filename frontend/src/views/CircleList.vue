<template>
  <div class="circle-list-page">
    <div v-if="!schoolStore.hasSchool" class="no-school">
      <el-empty description="请先选择学校，再浏览本校圈子">
        <el-button type="primary" @click="router.push('/choose-school')">去选择学校</el-button>
      </el-empty>
    </div>

    <template v-else>
      <div class="list-head">
        <div class="head-title">
          <el-icon class="head-icon"><ChatRound /></el-icon>
          <span>圈子 · {{ schoolStore.currentSchool.name }}</span>
        </div>
        <div class="head-actions">
          <el-input
            v-model="keyword"
            placeholder="搜索圈子名称"
            clearable
            class="search-input"
            @keyup.enter="loadList(1)"
            @clear="loadList(1)"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button type="primary" :icon="Plus" @click="openCreate">创建圈子</el-button>
        </div>
      </div>

      <div v-loading="circleStore.loading" class="circle-grid">
        <div
          v-for="c in circleStore.list"
          :key="c.id"
          class="circle-card"
          @click="router.push(`/circles/${c.id}`)"
        >
          <div class="cover" :style="coverStyle(c)">
            <div class="cover-joined" v-if="c.joined">已加入</div>
            <div class="cover-name">{{ c.name }}</div>
          </div>
          <div class="card-body">
            <div class="desc">{{ c.description || '这个圈子还没有简介' }}</div>
            <div class="card-foot">
              <span class="member">
                <el-icon><UserFilled /></el-icon>{{ c.member_count }} 人
              </span>
              <el-button
                v-if="!c.joined"
                size="small"
                type="primary"
                @click.stop="handleJoin(c)"
              >加入</el-button>
              <el-button v-else size="small" type="info" plain @click.stop="handleJoin(c)">
                退出
              </el-button>
            </div>
          </div>
        </div>
        <el-empty v-if="!circleStore.loading && !circleStore.list.length" description="还没有圈子，快来创建一个吧～" />
      </div>

      <Pagination
        v-if="circleStore.pagination.total_pages > 1"
        class="list-pagination"
        :current-page="circleStore.pagination.page"
        :total-pages="circleStore.pagination.total_pages"
        :total="circleStore.pagination.total"
        @change="loadList"
      />

      <!-- 创建圈子 -->
      <el-dialog v-model="createVisible" title="创建圈子" width="440px">
        <el-form label-width="72px" @submit.prevent>
          <el-form-item label="所在学校">
            <el-input :model-value="schoolStore.currentSchool.name" disabled />
          </el-form-item>
          <el-form-item label="圈子名称" required>
            <el-input v-model="form.name" maxlength="60" show-word-limit placeholder="给圈子起个名字" />
          </el-form-item>
          <el-form-item label="简介">
            <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit
                      placeholder="介绍下这个圈子是干嘛的" />
          </el-form-item>
          <el-form-item label="封面图">
            <el-input v-model="form.cover_url" placeholder="图片 URL（可选，留空用默认封面）" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="createVisible = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
        </template>
      </el-dialog>
    </template>
  </div>
</template>

<script setup>
// 圈子广场：/circles，按学校浏览可加入的群聊圈子
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatRound, Plus, Search, UserFilled } from '@element-plus/icons-vue'

import Pagination from '@/components/Pagination.vue'
import { useCircleStore } from '@/store/circle'
import { useSchoolStore } from '@/store/school'
import { useUserStore } from '@/store/user'
import { useChatStore } from '@/store/chat'

const router = useRouter()
const circleStore = useCircleStore()
const schoolStore = useSchoolStore()
const userStore = useUserStore()
const chatStore = useChatStore()

const keyword = ref('')
const createVisible = ref(false)
const creating = ref(false)
const form = reactive({ name: '', description: '', cover_url: '' })

const schoolId = () => schoolStore.currentSchool?.id

async function loadList(page = 1) {
  if (!schoolId()) return
  await circleStore.fetchList({ school_id: schoolId(), keyword: keyword.value.trim(), page, page_size: 12 })
}

function coverStyle(c) {
  return c.cover_url
    ? { backgroundImage: `url(${c.cover_url})` }
    : { background: 'linear-gradient(135deg, #f6c453, #f5a623)' }
}

function openCreate() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  Object.assign(form, { name: '', description: '', cover_url: '' })
  createVisible.value = true
}

async function handleJoin(c) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  try {
    await circleStore.join(c.id, (joined) => chatStore.emitCircleJoin(joined, c.id))
    ElMessage.success(c.joined ? '已加入圈子' : '已退出圈子')
  } catch (e) {
    ElMessage.error(e?.message || '操作失败')
  }
}

async function handleCreate() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写圈子名称')
    return
  }
  creating.value = true
  try {
    const circle = await circleStore.create({
      school_id: schoolId(),
      name: form.name.trim(),
      description: form.description.trim(),
      cover_url: form.cover_url.trim() || undefined,
    })
    createVisible.value = false
    ElMessage.success('创建成功，已自动加入')
    // 创建者已是成员，直接订阅该群实时房间（勿走 toggle 以免退群）
    chatStore.emitCircleJoin(true, circle.id)
    router.push(`/circles/${circle.id}`)
  } catch (e) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

onMounted(() => loadList(1))
</script>

<style scoped>
.circle-list-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.no-school {
  margin: 80px auto;
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.head-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.head-icon {
  color: var(--el-color-primary);
  font-size: 24px;
}
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.search-input {
  width: 220px;
}
.circle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 120px;
}
.circle-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}
.circle-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.cover {
  height: 110px;
  background-size: cover;
  background-position: center;
  position: relative;
}
.cover-joined {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 12px;
  color: #fff;
  background: rgba(0, 0, 0, 0.45);
  padding: 2px 8px;
  border-radius: 10px;
}
.cover-name {
  position: absolute;
  left: 12px;
  bottom: 10px;
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}
.card-body {
  padding: 12px 14px;
}
.desc {
  font-size: 13px;
  color: #909399;
  height: 36px;
  line-height: 18px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}
.member {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}
.list-pagination {
  margin-top: 24px;
}
</style>
