<template>
  <div class="post-create">
    <div class="page-head">
      <el-page-header content="发布探店笔记" @back="handleLeave" />
    </div>

    <el-alert v-if="draftRestored" class="draft-tip" type="info" show-icon :closable="false">
      <span>已恢复上次未发布的草稿，可以继续编辑发布。</span>
      <el-button link type="primary" @click="handleDiscardDraft">清空草稿</el-button>
    </el-alert>

    <div class="create-card">
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" maxlength="100" show-word-limit placeholder="取一个吸引人的标题" />
        </el-form-item>

        <el-form-item label="正文" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            maxlength="2000"
            show-word-limit
            placeholder="分享你的探店体验、口味测评、性价比…"
          />
        </el-form-item>

        <el-form-item label="标签（逗号分隔，可选）">
          <el-input v-model="form.tags" placeholder="例如：食堂,安利,平价" />
        </el-form-item>

        <el-form-item label="关联店铺（必填）" required>
          <template v-if="shopList.length">
            <el-select v-model="form.shop_id" placeholder="选择你探的这家店" style="width: 320px">
              <el-option v-for="s in shopList" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </template>
          <div v-else class="no-shop-tip">
            当前学校还没有店铺，请先
            <router-link to="/choose-school">选择学校</router-link>
            或返回，无法发布不关联店铺的笔记。
          </div>
        </el-form-item>

        <el-form-item label="图片（最多 9 张；上传一张后，右侧自动新增一个上传位）">
          <MultiImageField v-model="form.images" :size="96" />
        </el-form-item>

        <div class="form-actions">
          <el-button @click="handleLeave">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">发布笔记</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import MultiImageField from '@/components/MultiImageField.vue'
import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useShopStore } from '@/store/shop'

const router = useRouter()
const postStore = usePostStore()
const schoolStore = useSchoolStore()
const shopStore = useShopStore()

const submitting = ref(false)
const shopList = ref([])
const draftRestored = ref(false)

const form = reactive({
  title: '',
  content: '',
  tags: '',
  shop_id: null,
  images: [],
})

// ---- 草稿暂存 ----
// 与登录态同放 sessionStorage：登录态本身跟随标签页生命周期（关标签页即视为登出），
// 所以"本次登录内"保存草稿恰好对应 sessionStorage 的语义，登出后自然失效，
// 也不会像 localStorage 那样把 A 标签页的草稿泄给同浏览器登录的另一个账号。
const DRAFT_KEY = 'campus_food_post_draft'
const DRAFT_SAVE_DELAY = 400

function readDraft() {
  try {
    const draft = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || 'null')
    return draft && typeof draft === 'object' ? draft : null
  } catch (e) {
    return null
  }
}

function clearDraft() {
  sessionStorage.removeItem(DRAFT_KEY)
}

// 是否已有用户输入 —— 决定离开时要不要警示、要不要留草稿
const hasInput = computed(
  () =>
    !!form.title.trim() ||
    !!form.content.trim() ||
    !!form.tags.trim() ||
    !!form.shop_id ||
    form.images.length > 0,
)

function saveDraft() {
  if (!hasInput.value) {
    clearDraft()
    return
  }
  try {
    sessionStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({
        title: form.title,
        content: form.content,
        tags: form.tags,
        shop_id: form.shop_id,
        images: form.images,
      }),
    )
  } catch (e) {
    // 写入失败（如无痕模式配额为 0）时忽略：丢草稿不影响正常发布
  }
}

function restoreDraft() {
  const draft = readDraft()
  if (!draft) return
  form.title = draft.title || ''
  form.content = draft.content || ''
  form.tags = draft.tags || ''
  form.shop_id = draft.shop_id || null
  form.images = Array.isArray(draft.images) ? draft.images : []
  draftRestored.value = hasInput.value
}

let saveTimer = null
watch(
  form,
  () => {
    clearTimeout(saveTimer)
    saveTimer = setTimeout(saveDraft, DRAFT_SAVE_DELAY)
  },
  { deep: true },
)

// 离开本页（取消 / 返回 / 页面内跳转 / 浏览器后退）前，若有未发布内容就警示一次
const skipLeaveGuard = ref(false)

async function confirmLeave() {
  if (skipLeaveGuard.value || !hasInput.value) return true
  try {
    await ElMessageBox.confirm(
      '已填写的内容会保存为草稿，下次进入本页可以继续编辑。确定要离开吗？',
      '提示',
      { confirmButtonText: '离开', cancelButtonText: '继续编辑', type: 'warning' },
    )
  } catch (e) {
    return false
  }
  skipLeaveGuard.value = true
  clearTimeout(saveTimer)
  saveDraft()
  return true
}

async function handleLeave() {
  if (!(await confirmLeave())) return
  router.back()
}

async function handleDiscardDraft() {
  try {
    await ElMessageBox.confirm('清空后已填写的内容将无法恢复，确定要清空吗？', '提示', {
      confirmButtonText: '清空',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch (e) {
    return
  }
  clearTimeout(saveTimer)
  form.title = ''
  form.content = ''
  form.tags = ''
  form.shop_id = null
  form.images = []
  clearDraft()
  draftRestored.value = false
}

onBeforeRouteLeave(async () => confirmLeave())

onBeforeUnmount(() => clearTimeout(saveTimer))

const handleSubmit = async () => {
  const title = form.title.trim()
  const content = form.content.trim()
  if (!title) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!content) {
    ElMessage.warning('请填写正文')
    return
  }
  if (!form.shop_id) {
    ElMessage.warning('请选择关联店铺')
    return
  }
  submitting.value = true
  try {
    const images = form.images.map((s) => s.trim()).filter(Boolean)
    const post = await postStore.create({
      title,
      content,
      tags: form.tags.trim() || undefined,
      shop_id: form.shop_id,
      images,
    })
    ElMessage.success('发布成功')
    // 发布成功：草稿已完成使命，直接跳转且不再弹离开警示
    skipLeaveGuard.value = true
    draftRestored.value = false
    clearDraft()
    router.replace(`/posts/${post.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  restoreDraft()
  if (!schoolStore.schoolList.length) await schoolStore.fetchSchools()
  if (schoolStore.hasSchool) {
    const data = await shopStore.fetchShopList({ school_id: schoolStore.currentSchool.id, page_size: 50 })
    shopList.value = data.items || []
    // 草稿里的店铺可能来自别的学校（或已被下架），选不中就清掉让用户重选
    if (form.shop_id && !shopList.value.some((s) => s.id === form.shop_id)) {
      form.shop_id = null
    }
  }
})
</script>

<style scoped>
.post-create {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}
.page-head {
  margin-bottom: 16px;
}
.draft-tip {
  margin-bottom: 12px;
}
.create-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 28px 32px;
}
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}
.no-shop-tip {
  font-size: 13px;
  color: #e6a23c;
  line-height: 1.6;
}
.no-shop-tip a {
  color: var(--el-color-primary);
}
</style>
