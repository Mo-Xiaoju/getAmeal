<template>
  <div class="home">
    <section class="hero">
      <h1 class="hero-title">校园美食，从这里开始</h1>
      <p class="hero-desc">
        发现食堂与周边美食 · 真实评价 · 探店笔记 · 美食圈子
      </p>

      <!-- 学校上下文 -->
      <div class="school-context">
        <template v-if="schoolStore.hasSchool">
          <el-icon class="school-icon"><School /></el-icon>
          <span class="school-name">{{ schoolStore.currentSchool.name }}</span>
          <el-button size="small" text type="primary" @click="router.push('/choose-school')">切换学校</el-button>
        </template>
        <template v-else>
          <span class="school-tip">选择你的学校，浏览专属美食</span>
          <el-button type="primary" size="large" @click="router.push('/choose-school')">选择学校</el-button>
        </template>
      </div>

      <div class="hero-actions">
        <template v-if="userStore.isLoggedIn">
          <el-button type="primary" size="large" @click="router.push('/shops')">逛一逛店铺</el-button>
          <el-button size="large" @click="router.push('/profile')">进入个人中心</el-button>
        </template>
        <template v-else>
          <el-button type="primary" size="large" @click="router.push('/register')">立即注册</el-button>
          <el-button size="large" @click="router.push('/login')">登录</el-button>
        </template>
      </div>
    </section>

    <!-- 推荐店铺 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 推荐店铺</h2>
        <el-button text type="primary" @click="router.push('/shops')">查看全部 →</el-button>
      </div>
      <div v-loading="shopStore.loading" class="shop-grid">
        <ShopCard v-for="shop in shopStore.recommendList" :key="shop.id" :shop="shop" />
      </div>
      <el-empty
        v-if="!shopStore.loading && !shopStore.recommendList.length"
        description="暂无推荐店铺"
      />
    </section>

    <!-- 推荐菜品 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 热门菜品</h2>
      </div>
      <div v-loading="dishStore.loading" class="dish-grid">
        <DishCard v-for="d in dishStore.recommendList" :key="d.id" :dish="d" />
      </div>
      <el-empty
        v-if="!dishStore.loading && !dishStore.recommendList.length"
        description="暂无热门菜品"
      />
    </section>

    <!-- 最新笔记 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 最新探店笔记</h2>
        <el-button text type="primary" @click="router.push('/posts')">查看全部 →</el-button>
      </div>
      <div v-loading="postStore.loading" class="post-grid">
        <PostCard v-for="post in postStore.postList" :key="post.id" :post="post" />
      </div>
      <el-empty
        v-if="!postStore.loading && !postStore.postList.length"
        description="还没有探店笔记"
      />
    </section>

    <section class="features">
      <div class="feature-card">
        <el-icon class="feature-icon"><Shop /></el-icon>
        <h3>发现美食</h3>
        <p>按学校浏览食堂窗口与周边店铺，查看菜品与真实评分。</p>
      </div>
      <div class="feature-card">
        <el-icon class="feature-icon"><EditPen /></el-icon>
        <h3>分享探店</h3>
        <p>发布探店笔记，配图配文，安利你心中的校园好味道。</p>
      </div>
      <div class="feature-card">
        <el-icon class="feature-icon"><ChatDotRound /></el-icon>
        <h3>互动交流</h3>
        <p>点赞收藏、评论互动、关注博主、加入美食圈子。</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, EditPen, School, Shop } from '@element-plus/icons-vue'

import DishCard from '@/components/DishCard.vue'
import PostCard from '@/components/PostCard.vue'
import ShopCard from '@/components/ShopCard.vue'
import { useDishStore } from '@/store/dish'
import { usePostStore } from '@/store/post'
import { useSchoolStore } from '@/store/school'
import { useShopStore } from '@/store/shop'
import { useUserStore } from '@/store/user'

const router = useRouter()
const schoolStore = useSchoolStore()
const shopStore = useShopStore()
const dishStore = useDishStore()
const postStore = usePostStore()
const userStore = useUserStore()

onMounted(async () => {
  if (!schoolStore.schoolList.length) {
    await schoolStore.fetchSchools()
  }
  if (schoolStore.hasSchool) {
    shopStore.fetchRecommend({ school_id: schoolStore.currentSchool.id, page_size: 6 })
    dishStore.fetchRecommend({ school_id: schoolStore.currentSchool.id, limit: 6 })
    postStore.fetchList({ school_id: schoolStore.currentSchool.id, page_size: 3 })
  }
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}
.hero {
  text-align: center;
  padding: 60px 20px 40px;
  background: linear-gradient(135deg, var(--el-color-primary-light-9), #ecf5ff);
  border-radius: 16px;
}
.hero-title {
  margin: 0 0 12px;
  font-size: 34px;
  color: #303133;
}
.hero-desc {
  margin: 0 0 24px;
  font-size: 16px;
  color: #606266;
}
.school-context {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}
.school-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}
.school-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-color-primary);
}
.school-tip {
  font-size: 15px;
  color: #606266;
  margin-right: 8px;
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
.recommend {
  margin-top: 36px;
}
.recommend-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-title {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
.shop-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}
.dish-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}
.features {
  margin-top: 40px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}
.feature-card {
  padding: 28px 24px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  text-align: center;
}
.feature-icon {
  font-size: 36px;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}
.feature-card h3 {
  margin: 0 0 8px;
  color: #303133;
}
.feature-card p {
  margin: 0;
  color: #909399;
  font-size: 14px;
  line-height: 1.6;
}
</style>
