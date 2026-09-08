<template>
  <div class="post-create">
    <div class="page-head">
      <el-page-header content="发布探店笔记" @back="router.back()" />
    </div>

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

        <el-form-item label="图片（本地上传优先，URL 备择；支持多张）">
          <div class="image-inputs">
            <div v-for="(img, i) in form.images" :key="i" class="image-input-row">
              <ImageField v-model="form.images[i]" :size="76" />
              <el-button :icon="Delete" circle type="danger" plain @click="removeImage(i)" />
            </div>
            <el-button :icon="Plus" plain @click="addImage">添加图片</el-button>
          </div>
        </el-form-item>

        <div class="form-actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">发布笔记</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'

import ImageField from '@/components/ImageField.vue'
import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useShopStore } from '@/store/shop'

const router = useRouter()
const postStore = usePostStore()
const schoolStore = useSchoolStore()
const shopStore = useShopStore()

const submitting = ref(false)
const shopList = ref([])

const form = reactive({
  title: '',
  content: '',
  tags: '',
  shop_id: null,
  images: [''],
})

const addImage = () => form.images.push('')
const removeImage = (i) => {
  form.images.splice(i, 1)
  if (!form.images.length) form.images.push('')
}

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
    router.replace(`/posts/${post.id}`)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (!schoolStore.schoolList.length) await schoolStore.fetchSchools()
  if (schoolStore.hasSchool) {
    const data = await shopStore.fetchShopList({ school_id: schoolStore.currentSchool.id, page_size: 50 })
    shopList.value = data.items || []
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
.create-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  padding: 28px 32px;
}
.image-inputs {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.image-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.image-input-row .el-input {
  flex: 1;
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
