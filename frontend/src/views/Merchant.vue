<template>
  <div class="merchant">
    <div class="page-head">
      <div>
        <h1 class="page-title">商户中心</h1>
        <p class="page-desc">发布和管理你的食堂与菜单（仅可操作自己的店铺）</p>
      </div>
      <div class="page-actions">
        <el-button
          :icon="Link"
          plain
          :disabled="!schoolStore.hasSchool"
          :title="schoolStore.hasSchool ? '认领校园内已公开但尚未入驻的店铺' : '请先选择所在学校'"
          @click="openClaimDialog"
        >
          认领已有店铺
        </el-button>
        <el-button type="primary" :icon="Plus" @click="openShopDialog()">新建店铺</el-button>
      </div>
    </div>

    <div v-if="!schoolStore.hasSchool" class="no-school">
      <el-empty description="请先选择所在学校，才能创建店铺">
        <el-button type="primary" @click="router.push('/choose-school')">去选择学校</el-button>
      </el-empty>
    </div>

    <template v-else>
      <div v-loading="loading" class="shop-grid">
        <div v-for="shop in shops" :key="shop.id" class="shop-card">
          <div class="shop-card-head">
            <img
              v-if="shop.image_url"
              :src="shop.image_url"
              class="shop-cover"
              alt=""
              @click.stop="openImage([shop.image_url], 0)"
            />
            <div v-else class="shop-cover placeholder"><el-icon><Shop /></el-icon></div>
            <el-tag size="small" :type="shop.status === 'approved' ? 'success' : 'warning'" effect="light">
              {{ statusText(shop.status) }}
            </el-tag>
          </div>
          <h3 class="shop-name">{{ shop.name }}</h3>
          <div class="shop-meta">
            <span v-if="shop.category">{{ shop.category }}</span>
            <span v-if="shop.price_range">{{ shop.price_range }}</span>
            <span>{{ shop.dish_count }} 道菜</span>
          </div>
          <div class="shop-address">{{ shop.address }}</div>
          <div v-if="shop.status === 'pending'" class="shop-status-note">
            待审核：通过前暂不对外公示，你仍可编辑与添加菜品
          </div>
          <div v-else-if="shop.status === 'rejected'" class="shop-status-note rejected">
            已驳回：暂不对外公示，可继续编辑保存
          </div>
          <div class="shop-actions">
            <el-button size="small" type="primary" plain @click="openDishDrawer(shop)">管理菜单</el-button>
            <el-button size="small" @click="openShopDialog(shop)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDeleteShop(shop)">删除</el-button>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !shops.length" description="还没有店铺，点击右上角「新建店铺」开始" />
    </template>

    <!-- 新建/编辑店铺 -->
    <el-dialog v-model="shopDialog.show" :title="shopDialog.form.id ? '编辑店铺' : '新建店铺'" width="520px">
      <el-form label-position="top">
        <el-form-item label="店铺名称" required>
          <el-input v-model="shopDialog.form.name" maxlength="100" placeholder="例如：北区奶茶店" />
        </el-form-item>
        <el-form-item label="地址" required>
          <el-input v-model="shopDialog.form.address" maxlength="200" placeholder="例如：校园内学三食堂一楼" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="shopDialog.form.category" placeholder="请选择分类" clearable style="width: 100%">
            <el-option v-for="c in categoryStore.categories" :key="c" :label="c" :value="c" />
          </el-select>
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
        <el-button type="primary" :loading="saving" @click="handleSaveShop">保存</el-button>
      </template>
    </el-dialog>

    <!-- 菜单管理 -->
    <el-drawer v-model="dishDrawer.show" :title="dishDrawer.shop ? `${dishDrawer.shop.name} · 菜单管理` : ''" size="480px">
      <div class="dish-add">
        <h4>添加菜品</h4>
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
          <el-form-item label="菜品图（可多张，最多 9 张）">
            <MultiImageField v-model="dishForm.images" :size="76" />
          </el-form-item>
          <el-form-item label="标签（逗号分隔）">
            <el-input v-model="dishForm.tags" placeholder="例如：招牌,下饭" />
          </el-form-item>
          <el-button type="primary" plain :loading="saving" @click="handleAddDish">添加</el-button>
        </el-form>
      </div>

      <el-divider />

      <div v-loading="dishLoading" class="dish-list">
        <div v-for="dish in dishes" :key="dish.id" class="dish-item">
          <div class="dish-info">
            <div class="dish-name">
              {{ dish.name }}
              <el-tag size="small" :type="dish.status === 'approved' ? 'success' : 'warning'" effect="light">
                {{ statusText(dish.status) }}
              </el-tag>
            </div>
            <div class="dish-sub">
              <span class="dish-price">¥{{ Number(dish.price).toFixed(2) }}</span>
              <span v-if="dish.tags.length"> · {{ dish.tags.join(' / ') }}</span>
            </div>
            <div v-if="dish.description" class="dish-desc">{{ dish.description }}</div>
          </div>
          <div class="dish-ops">
            <el-button size="small" text type="primary" @click="openDishEdit(dish)">编辑</el-button>
            <el-button size="small" text type="danger" @click="handleDeleteDish(dish)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="!dishLoading && !dishes.length" description="暂无菜品，先添加一道吧" />
      </div>
    </el-drawer>

    <!-- 认领已有店铺 -->
    <el-dialog v-model="claimDialog.show" title="认领已有店铺" width="680px">
      <p class="claim-tip">
        选择一家当前学校内「已公开且尚未有商户入驻」的店铺挂到你名下；认领后即可在商户中心直接管理其菜单。
        同学仍可向该店补充菜品，但会进入审核，管理员通过后才会对外展示。
      </p>
      <div v-loading="claimLoading" class="claim-list">
        <div v-for="shop in claimableShops" :key="shop.id" class="claim-item">
          <div class="claim-info">
            <img
              v-if="shop.image_url"
              :src="shop.image_url"
              class="claim-cover"
              alt=""
              @click.stop="openImage([shop.image_url], 0)"
            />
            <div v-else class="claim-cover placeholder"><el-icon><Shop /></el-icon></div>
            <div class="claim-text">
              <div class="claim-name">{{ shop.name }}</div>
              <div class="claim-meta">
                <span v-if="shop.category">{{ shop.category }}</span>
                <span v-if="shop.price_range">{{ shop.price_range }}</span>
                <span>{{ shop.address }}</span>
                <span>{{ shop.dish_count }} 道菜</span>
              </div>
            </div>
          </div>
          <el-button
            type="primary"
            plain
            size="small"
            :loading="claimingId === shop.id"
            @click="handleClaim(shop)"
          >
            认领
          </el-button>
        </div>
        <el-empty v-if="!claimLoading && !claimableShops.length" description="当前学校暂无待认领店铺" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Link, Plus, Shop } from '@element-plus/icons-vue'

import {
  claimShop,
  createDish,
  createShop,
  deleteDish,
  deleteShop,
  getClaimableShops,
  getMyShops,
  getShopDishes,
  updateDish,
  updateShop,
} from '@/api/merchant'
import ImageField from '@/components/ImageField.vue'
import MultiImageField from '@/components/MultiImageField.vue'
import { openImage } from '@/composables/useImageViewer'
import { useCategoryStore } from '@/store/category'
import { useSchoolStore } from '@/store/school'

const router = useRouter()
const schoolStore = useSchoolStore()
const categoryStore = useCategoryStore()

const loading = ref(false)
const saving = ref(false)
const shops = ref([])

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
    : { ...emptyShopForm(), image_url: `https://picsum.photos/seed/m${Date.now()}/400/300` }
  shopDialog.show = true
}

const statusText = (s) => ({ approved: '已发布', pending: '待审核', rejected: '已驳回' }[s] || s || '-')

const loadShops = async () => {
  loading.value = true
  try {
    const res = await getMyShops({ page: 1, page_size: 50 })
    shops.value = res.data.data.items || []
  } finally {
    loading.value = false
  }
}

const handleSaveShop = async () => {
  const form = shopDialog.form
  if (!form.name.trim() || !form.address.trim()) {
    ElMessage.warning('店铺名称和地址不能为空')
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
      await updateShop(form.id, payload)
      ElMessage.success('已更新')
    } else {
      await createShop({ school_id: schoolStore.currentSchool.id, ...payload })
      ElMessage.success('店铺创建成功')
    }
    shopDialog.show = false
    loadShops()
  } finally {
    saving.value = false
  }
}

const handleDeleteShop = async (shop) => {
  try {
    await ElMessageBox.confirm(`确定删除店铺「${shop.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await deleteShop(shop.id)
  ElMessage.success('已删除')
  loadShops()
}

// ---- 认领已有店铺 ----
const claimDialog = reactive({ show: false })
const claimLoading = ref(false)
const claimableShops = ref([])
const claimingId = ref(null)

const openClaimDialog = async () => {
  claimDialog.show = true
  claimLoading.value = true
  try {
    const params = schoolStore.hasSchool
      ? { school_id: schoolStore.currentSchool.id, page_size: 50 }
      : { page_size: 50 }
    const res = await getClaimableShops(params)
    claimableShops.value = res.data.data.items || []
  } finally {
    claimLoading.value = false
  }
}

const handleClaim = async (shop) => {
  claimingId.value = shop.id
  try {
    await claimShop(shop.id)
    ElMessage.success(`已认领「${shop.name}」`)
    claimableShops.value = claimableShops.value.filter((s) => s.id !== shop.id)
    loadShops()
  } finally {
    claimingId.value = null
  }
}

// ---- 菜单管理 ----
const dishDrawer = reactive({ show: false, shop: null })
const dishLoading = ref(false)
const dishes = ref([])
const dishForm = reactive({ name: '', price: 0, description: '', tags: '', images: [], editId: null })

const openDishDrawer = async (shop) => {
  dishDrawer.shop = shop
  dishDrawer.show = true
  resetDishForm()
  loadDishes(shop.id)
}

const resetDishForm = () => {
  dishForm.name = ''
  dishForm.price = 0
  dishForm.description = ''
  dishForm.tags = ''
  dishForm.images = []
  dishForm.editId = null
}

const loadDishes = async (shopId) => {
  dishLoading.value = true
  try {
    const res = await getShopDishes(shopId, { page: 1, page_size: 50 })
    dishes.value = res.data.data.items || []
  } finally {
    dishLoading.value = false
  }
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
      images: dishForm.images,
      tags: dishForm.tags ? dishForm.tags.split(/[,，]/).map((t) => t.trim()).filter(Boolean) : [],
    }
    if (dishForm.editId) {
      await updateDish(dishForm.editId, payload)
      ElMessage.success('已更新')
    } else {
      await createDish(dishDrawer.shop.id, payload)
      ElMessage.success('菜品已添加')
    }
    resetDishForm()
    loadDishes(dishDrawer.shop.id)
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
  dishForm.images = dish.images?.length ? [...dish.images] : dish.image_url ? [dish.image_url] : []
}

const handleDeleteDish = async (dish) => {
  try {
    await ElMessageBox.confirm(`确定删除菜品「${dish.name}」吗？`, '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  await deleteDish(dish.id)
  ElMessage.success('已删除')
  loadDishes(dishDrawer.shop.id)
}

onMounted(() => {
  if (!schoolStore.schoolList.length) schoolStore.fetchSchools()
  if (!categoryStore.categories.length) categoryStore.fetchCategories()
  loadShops()
})
</script>

<style scoped>
.merchant {
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
.page-actions {
  display: flex;
  align-items: center;
  gap: 10px;
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
.shop-status-note {
  margin: 6px 16px 0;
  font-size: 12px;
  color: #e6a23c;
  line-height: 1.5;
}
.shop-status-note.rejected {
  color: #f56c6c;
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
.claim-tip {
  margin: 0 0 14px;
  font-size: 13px;
  color: #909399;
  line-height: 1.7;
}
.claim-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 80px;
}
.claim-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
}
.claim-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.claim-cover {
  flex: 0 0 64px;
  width: 64px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
  background: #f2f3f5;
}
.claim-cover.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-color-primary);
  font-size: 20px;
}
.claim-text {
  min-width: 0;
}
.claim-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.claim-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
  font-size: 13px;
  color: #909399;
}
</style>
