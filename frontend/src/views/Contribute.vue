<template>
  <div class="contribute">
    <div class="page-head">
      <div>
        <h1 class="page-title">提交商户 / 菜单</h1>
        <p class="page-desc">
          商户未入驻时，可代为提交食堂与菜单；提交内容将进入审核流程（
          <span class="pending-tip">待审核中</span>
          ）
        </p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openShopDialog()">新建商户</el-button>
    </div>

    <div v-if="!schoolStore.hasSchool" class="no-school">
      <el-empty description="请先选择所在学校，才能提交商户">
        <el-button type="primary" @click="router.push('/choose-school')">去选择学校</el-button>
      </el-empty>
    </div>

    <template v-else>
      <div v-loading="loading" class="shop-grid">
        <div v-for="shop in shops" :key="shop.id" class="shop-card">
          <div class="shop-card-head">
            <img v-if="shop.image_url" :src="shop.image_url" class="shop-cover" alt="" />
            <div v-else class="shop-cover placeholder"><el-icon><Shop /></el-icon></div>
            <el-tag size="small" :type="statusTagType(shop.status)" effect="light">
              {{ statusText(shop.status) }}
            </el-tag>
          </div>
          <h3 class="shop-name">{{ shop.name }}</h3>
          <div class="shop-meta">
            <span v-if="shop.category">{{ shop.category }}</span>
            <span v-if="shop.price_range">{{ shop.price_range }}</span>
            <span>{{ (shop.dishes || []).length }} 道菜</span>
          </div>
          <div class="shop-address">{{ shop.address }}</div>
          <p v-if="shop.status === 'rejected'" class="reject-reason">驳回原因：{{ shop.reject_reason || '未填写' }}</p>
          <div class="shop-actions">
            <el-button size="small" type="primary" plain @click="openDishDrawer(shop)">管理菜单</el-button>
            <el-button size="small" @click="openShopDialog(shop)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDeleteShop(shop)">删除</el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !shops.length" description="还没有提交记录，点击右上角「新建商户」提交" />

      <!-- 我在他人/社区店补充的菜品（仍走审核） -->
      <div v-if="contributedDishes.length" class="contributed-block">
        <h2 class="block-title">我补充的菜品</h2>
        <p class="block-desc">你在其它店铺提交的菜品；编辑后同样需重新审核</p>
        <div class="contributed-list">
          <div v-for="dish in contributedDishes" :key="dish.id" class="contributed-item">
            <div class="dish-info">
              <div class="dish-name">
                {{ dish.name }}
                <el-tag size="small" :type="statusTagType(dish.status)" effect="light">
                  {{ statusText(dish.status) }}
                </el-tag>
                <el-tag v-if="dish.shop_status !== 'approved'" size="small" type="info" effect="plain">
                  所属店铺重新审核中
                </el-tag>
              </div>
              <div class="dish-sub">
                <span class="dish-price">¥{{ Number(dish.price).toFixed(2) }}</span>
                <span v-if="dish.shop_name"> · 所属店铺：{{ dish.shop_name }}</span>
                <span v-if="dish.tags.length"> · {{ dish.tags.join(' / ') }}</span>
              </div>
              <div v-if="dish.description" class="dish-desc">{{ dish.description }}</div>
              <p v-if="dish.status === 'rejected'" class="reject-reason">驳回原因：{{ dish.reject_reason || '未填写' }}</p>
            </div>
            <div class="dish-ops">
              <el-button size="small" text type="primary" @click="openContributedEdit(dish)">编辑</el-button>
              <el-button size="small" text type="danger" @click="handleDeleteContributed(dish)">删除</el-button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 新建/编辑提交 -->
    <el-dialog v-model="shopDialog.show" :title="shopDialog.form.id ? '编辑提交' : '新建商户'" width="520px">
      <el-alert
        v-if="shopDialog.form.id && shopDialog.form.status === 'approved'"
        type="warning"
        show-icon
        :closable="false"
        title="修改后将重新进入待审核，审核通过前暂停公开展示"
        class="review-alert"
      />
      <el-form label-position="top">
        <el-form-item label="商户名称" required>
          <el-input v-model="shopDialog.form.name" maxlength="100" placeholder="例如：北区奶茶店" />
        </el-form-item>
        <el-form-item label="地址" required>
          <el-input v-model="shopDialog.form.address" maxlength="200" placeholder="例如：校园内学三食堂一楼" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="shopDialog.form.category" placeholder="例如：食堂 / 奶茶饮品 / 面食" />
        </el-form-item>
        <el-form-item label="人均区间">
          <el-input v-model="shopDialog.form.price_range" placeholder="例如：10-20元" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="shopDialog.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="封面图">
          <ImageField v-model="shopDialog.form.image_url" :size="120" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shopDialog.show = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveShop">提交</el-button>
      </template>
    </el-dialog>

    <!-- 菜单管理 -->
    <el-drawer v-model="dishDrawer.show" :title="dishDrawer.shop ? `${dishDrawer.shop.name} · 菜单管理` : ''" size="480px">
      <div class="dish-add">
        <h4>添加菜品</h4>
        <el-alert
          v-if="editingApprovedDish"
          type="warning"
          show-icon
          :closable="false"
          title="修改后将重新进入待审核，通过前不公开展示"
          class="review-alert"
        />
        <el-form label-position="top">
          <div class="dish-form-row">
            <el-form-item label="菜品名" required>
              <el-input v-model="dishForm.name" placeholder="例如：招牌盖饭" />
            </el-form-item>
            <el-form-item label="价格（元）" required>
              <el-input-number v-model="dishForm.price" :min="0" :precision="2" :step="1" style="width: 100%" />
            </el-form-item>
          </div>
          <el-form-item label="描述">
            <el-input v-model="dishForm.description" maxlength="500" />
          </el-form-item>
          <el-form-item label="菜品图">
            <ImageField v-model="dishForm.image_url" :size="72" />
          </el-form-item>
          <el-form-item label="标签（逗号分隔）">
            <el-input v-model="dishForm.tags" placeholder="例如：招牌,下饭" />
          </el-form-item>
          <el-button type="primary" plain :loading="saving" @click="handleAddDish">添加</el-button>
        </el-form>
      </div>

      <el-divider />

      <div class="dish-list">
        <div v-for="dish in drawerDishes" :key="dish.id" class="dish-item">
          <div class="dish-info">
            <div class="dish-name">
              {{ dish.name }}
              <el-tag size="small" :type="statusTagType(dish.status)" effect="light">
                {{ statusText(dish.status) }}
              </el-tag>
            </div>
            <div class="dish-sub">
              <span class="dish-price">¥{{ Number(dish.price).toFixed(2) }}</span>
              <span v-if="dish.tags.length"> · {{ dish.tags.join(' / ') }}</span>
            </div>
            <div v-if="dish.description" class="dish-desc">{{ dish.description }}</div>
            <p v-if="dish.status === 'rejected'" class="reject-reason">驳回原因：{{ dish.reject_reason || '未填写' }}</p>
          </div>
          <div class="dish-ops">
            <el-button size="small" text type="primary" @click="openDishEdit(dish)">编辑</el-button>
            <el-button size="small" text type="danger" @click="handleDeleteDish(dish)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="!drawerDishes.length" description="暂无菜品，先添加一道吧" />
      </div>
    </el-drawer>

    <!-- 编辑我在别家店提交的菜品 -->
    <el-dialog v-model="contributedDialog.show" title="编辑补充的菜品" width="480px">
      <el-alert
        v-if="contributedDialog.form.status === 'approved'"
        type="warning"
        show-icon
        :closable="false"
        title="修改后将重新进入待审核，通过前不公开展示"
        class="review-alert"
      />
      <el-form label-position="top">
        <div class="dish-form-row">
          <el-form-item label="菜品名" required>
            <el-input v-model="contributedDialog.form.name" maxlength="100" placeholder="例如：招牌盖饭" />
          </el-form-item>
          <el-form-item label="价格（元）" required>
            <el-input-number v-model="contributedDialog.form.price" :min="0" :precision="2" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
        <el-form-item label="描述">
          <el-input v-model="contributedDialog.form.description" maxlength="500" />
        </el-form-item>
        <el-form-item label="菜品图">
          <ImageField v-model="contributedDialog.form.image_url" :size="72" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="contributedDialog.form.tags" placeholder="例如：招牌,下饭" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="contributedDialog.show = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveContributed">保存并重新提交审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Shop } from '@element-plus/icons-vue'

import {
  deleteSubmittedDish,
  deleteSubmittedShop,
  getMyContributions,
  submitDish,
  submitShop,
  updateSubmittedDish,
  updateSubmittedShop,
} from '@/api/contribute'
import ImageField from '@/components/ImageField.vue'
import { useSchoolStore } from '@/store/school'

const router = useRouter()
const schoolStore = useSchoolStore()

const loading = ref(false)
const saving = ref(false)
const shops = ref([])
const contributedDishes = ref([]) // 我在他人/社区店补充的菜品
const dishTotal = ref(0)

const emptyShopForm = () => ({
  id: null,
  name: '',
  address: '',
  category: '',
  price_range: '',
  description: '',
  image_url: '',
})
const shopDialog = reactive({ show: false, form: emptyShopForm() })

const openShopDialog = (shop) => {
  shopDialog.form = shop
    ? { ...shop }
    : { ...emptyShopForm(), image_url: `https://picsum.photos/seed/c${Date.now()}/400/300` }
  shopDialog.show = true
}

const statusText = (s) => ({ approved: '已发布', pending: '待审核', rejected: '已驳回' }[s] || s || '-')
const statusTagType = (s) => ({ approved: 'success', pending: 'warning', rejected: 'danger' }[s] || 'info')

const loadMy = async () => {
  loading.value = true
  try {
    const data = await getMyContributions({ page: 1, page_size: 50 })
    shops.value = data.data.items || []
    contributedDishes.value = data.data.contributed_dishes || []
    dishTotal.value = data.data.dish_total || 0
  } finally {
    loading.value = false
  }
}

const handleSaveShop = async () => {
  const form = shopDialog.form
  if (!form.name.trim() || !form.address.trim()) {
    ElMessage.warning('商户名称和地址不能为空')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      address: form.address.trim(),
      category: form.category?.trim() || undefined,
      price_range: form.price_range?.trim() || undefined,
      description: form.description?.trim() || undefined,
      // '' 可清除已存封面（后端 update 仅在值非 None 时 setattr）
      image_url: form.image_url?.trim() || '',
    }
    if (form.id) {
      await updateSubmittedShop(form.id, payload)
      ElMessage.success('已更新，重新提交审核')
    } else {
      await submitShop({ school_id: schoolStore.currentSchool.id, ...payload })
      ElMessage.success('提交成功，等待审核')
    }
    shopDialog.show = false
    loadMy()
  } finally {
    saving.value = false
  }
}

const handleDeleteShop = async (shop) => {
  try {
    await ElMessageBox.confirm(`确定删除提交「${shop.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await deleteSubmittedShop(shop.id)
  ElMessage.success('已删除')
  loadMy()
}

// ---- 菜单管理（数据来自 list_my 内嵌 dishes，操作后整体刷新）----
const dishDrawer = reactive({ show: false, shop: null })
const dishForm = reactive({ name: '', price: 0, description: '', tags: '', image_url: '', editId: null })

const drawerDishes = computed(() => {
  if (!dishDrawer.shop) return []
  const cur = shops.value.find((s) => s.id === dishDrawer.shop.id)
  return cur ? cur.dishes || [] : []
})

// 正在编辑的菜此前已发布（编辑后将重新审核，抽屉内显示提示）
const editingApprovedDish = computed(() => {
  if (!dishForm.editId) return false
  const cur = drawerDishes.value.find((d) => d.id === dishForm.editId)
  return !!cur && cur.status === 'approved'
})

const openDishDrawer = (shop) => {
  dishDrawer.shop = shop
  dishDrawer.show = true
  resetDishForm()
}

const resetDishForm = () => {
  dishForm.name = ''
  dishForm.price = 0
  dishForm.description = ''
  dishForm.tags = ''
  dishForm.image_url = ''
  dishForm.editId = null
}

const handleAddDish = async () => {
  if (!dishForm.name.trim()) {
    ElMessage.warning('请输入菜品名')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: dishForm.name.trim(),
      price: dishForm.price,
      description: dishForm.description?.trim() || undefined,
      // '' 可清除已存菜品图（后端 update 仅在值非 None 时 setattr）
      image_url: dishForm.image_url?.trim() || '',
      tags: dishForm.tags ? dishForm.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean) : [],
    }
    if (dishForm.editId) {
      await updateSubmittedDish(dishForm.editId, payload)
      ElMessage.success('已更新，重新提交审核')
    } else {
      await submitDish(dishDrawer.shop.id, payload)
      ElMessage.success('菜品已提交，等待审核')
    }
    resetDishForm()
    loadMy()
  } finally {
    saving.value = false
  }
}

const openDishEdit = (dish) => {
  dishForm.editId = dish.id
  dishForm.name = dish.name
  dishForm.price = Number(dish.price)
  dishForm.description = dish.description || ''
  dishForm.tags = (dish.tags || []).join(',')
  dishForm.image_url = dish.image_url || ''
}

const handleDeleteDish = async (dish) => {
  try {
    await ElMessageBox.confirm(`确定删除菜品「${dish.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await deleteSubmittedDish(dish.id)
  ElMessage.success('已删除')
  loadMy()
}

// ---- 我在他人/社区店补充的菜品：编辑 / 删除 ----
const emptyContributedForm = () => ({
  editId: null,
  status: null,
  name: '',
  price: 0,
  description: '',
  tags: '',
  image_url: '',
})
const contributedDialog = reactive({ show: false, form: emptyContributedForm() })

const openContributedEdit = (dish) => {
  contributedDialog.form = {
    editId: dish.id,
    status: dish.status,
    name: dish.name,
    price: Number(dish.price),
    description: dish.description || '',
    tags: (dish.tags || []).join(','),
    image_url: dish.image_url || '',
  }
  contributedDialog.show = true
}

const handleSaveContributed = async () => {
  const form = contributedDialog.form
  if (!form.name.trim()) {
    ElMessage.warning('请输入菜品名')
    return
  }
  saving.value = true
  try {
    await updateSubmittedDish(form.editId, {
      name: form.name.trim(),
      price: form.price,
      description: form.description?.trim() || undefined,
      image_url: form.image_url?.trim() || '',
      tags: form.tags ? form.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean) : [],
    })
    ElMessage.success('已更新，重新提交审核')
    contributedDialog.show = false
    loadMy()
  } finally {
    saving.value = false
  }
}

const handleDeleteContributed = async (dish) => {
  try {
    await ElMessageBox.confirm(`确定删除菜品「${dish.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await deleteSubmittedDish(dish.id)
  ElMessage.success('已删除')
  loadMy()
}

onMounted(() => {
  if (!schoolStore.schoolList.length) schoolStore.fetchSchools()
  loadMy()
})
</script>

<style scoped>
.contribute {
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
.pending-tip {
  color: #e6a23c;
}
.no-school {
  padding: 40px 0;
}
.shop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
  min-height: 120px;
}
.shop-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 14px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}
.shop-card:hover {
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}
.shop-card-head {
  position: relative;
  height: 140px;
}
.shop-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.shop-cover.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-size: 40px;
}
.shop-card-head .el-tag {
  position: absolute;
  top: 10px;
  right: 10px;
}
.shop-name {
  margin: 14px 16px 6px;
  font-size: 17px;
  color: #303133;
}
.shop-meta {
  display: flex;
  gap: 8px;
  margin: 0 16px;
  font-size: 13px;
  color: #909399;
}
.shop-address {
  margin: 8px 16px 0;
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.shop-actions {
  display: flex;
  gap: 8px;
  padding: 14px 16px;
}
.dish-add {
  padding: 0 4px;
}
.dish-add h4 {
  margin: 0 0 12px;
  color: #303133;
}
.dish-form-row {
  display: grid;
  grid-template-columns: 1fr 140px;
  gap: 12px;
}
.dish-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 80px;
}
.dish-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
}
.dish-info {
  flex: 1;
  min-width: 0;
}
.dish-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dish-sub {
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}
.dish-price {
  color: #f56c6c;
  font-weight: 600;
}
.dish-desc {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
}
.dish-ops {
  display: flex;
  flex-shrink: 0;
}
.reject-reason {
  margin: 8px 16px 0;
  font-size: 12px;
  line-height: 1.5;
  color: #f56c6c;
}
.dish-info .reject-reason,
.contributed-item .reject-reason {
  margin: 4px 0 0;
}
.review-alert {
  margin-bottom: 14px;
}
.contributed-block {
  margin-top: 28px;
}
.block-title {
  margin: 0 0 6px;
  font-size: 18px;
  color: #303133;
}
.block-desc {
  margin: 0 0 14px;
  font-size: 13px;
  color: #909399;
}
.contributed-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.contributed-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #fff;
}
.contributed-item .dish-info {
  flex: 1;
  min-width: 0;
}
.contributed-item .dish-name {
  flex-wrap: wrap;
}
</style>
