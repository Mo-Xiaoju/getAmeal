<template>
  <div class="home">
    <!-- 滚动 Banner：首屏为欢迎语与入口，其余屏为功能介绍面板 -->
    <section class="hero-banner" @mouseenter="pauseAutoPlay" @mouseleave="resumeAutoPlay">
      <el-carousel
        ref="carouselRef"
        height="340px"
        :autoplay="false"
        indicator-position="none"
        arrow="hover"
        @change="onSlideChange"
      >
        <el-carousel-item>
          <div class="slide">
            <h1 class="hero-title">校园美食，从这里开始</h1>
            <p class="hero-desc">
              发现食堂与周边美食 · 真实评价 · 探店笔记 · 美食圈子
            </p>

            <!-- 学校上下文 -->
            <div class="school-context">
              <template v-if="schoolStore.hasSchool">
                <el-icon class="school-icon"><School /></el-icon>
                <span class="school-name">{{ schoolStore.currentSchool.name }}</span>
              </template>
              <span v-else class="school-tip">选择你的学校，浏览专属美食</span>
            </div>

            <!-- 未登录访客的首屏入口已去掉（导航栏常驻登录/注册/选校），首屏只做展示 -->
            <div v-if="userStore.isMerchant" class="hero-actions">
              <el-button
                type="primary"
                size="large"
                :icon="Plus"
                @click="router.push('/merchant')"
              >
                发布店铺 / 管理菜单
              </el-button>
            </div>
          </div>
        </el-carousel-item>

        <el-carousel-item v-for="feature in features" :key="feature.title">
          <div class="slide slide-feature">
            <div class="feature-icon" :style="{ color: feature.color }">
              <el-icon><component :is="feature.icon" /></el-icon>
            </div>
            <h3 class="feature-title">{{ feature.title }}</h3>
            <p class="feature-desc">{{ feature.desc }}</p>
          </div>
        </el-carousel-item>
      </el-carousel>

      <!-- 进度式指示条：当前段的填充条即"距离自动翻页还剩多久"，鼠标悬停 banner 会暂停 -->
      <div ref="indicatorsRef" class="banner-indicators">
        <button
          v-for="(label, index) in slideLabels"
          :key="label"
          type="button"
          class="indicator"
          :class="{ active: index === activeIndex }"
          :aria-label="`切换到：${label}`"
          @click="goTo(index)"
        >
          <span v-if="index === activeIndex" class="indicator-fill" />
        </button>
      </div>
    </section>

    <!-- 商户发布引导：选择学校后常驻，让"发布店铺/菜单"在最直观的位置可见 -->
    <section v-if="userStore.isMerchant && schoolStore.hasSchool" class="merchant-cta">
      <div class="cta-text">
        <el-icon class="cta-icon"><Shop /></el-icon>
        <div>
          <h3 class="cta-title">在「{{ schoolStore.currentSchool.name }}」发布你的店铺与菜单</h3>
          <p class="cta-desc">
            提交店铺与菜品后，经管理员审核即可被本校学生浏览、评分与收藏。
          </p>
        </div>
      </div>
      <el-button type="primary" size="large" :icon="Plus" @click="router.push('/merchant')">
        进入商户中心
      </el-button>
    </section>

    <!-- 推荐店铺 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 推荐店铺</h2>
        <el-button text type="primary" @click="router.push('/shops')">查看全部 →</el-button>
      </div>
      <!-- 推荐区三栏统一做法：加载中且还没有数据时用骨架卡片占位（避免"空白闪一下 → 卡片整块冒出"），
           已有数据时直接渲染 —— 从详情页返回首页不会重新白一次，只在原地刷新 -->
      <div class="shop-grid">
        <template v-if="shopStore.recommendLoading && !shopStore.recommendList.length">
          <el-skeleton
            v-for="i in 4"
            :key="`shop-skeleton-${i}`"
            animated
            class="skeleton-card"
          >
            <template #template>
              <el-skeleton-item variant="image" class="skeleton-card-cover" />
              <div class="skeleton-card-body">
                <el-skeleton-item variant="text" style="width: 70%" />
                <el-skeleton-item variant="text" style="width: 45%; margin-top: 8px" />
              </div>
            </template>
          </el-skeleton>
        </template>
        <template v-else>
          <ShopCard v-for="shop in shopStore.recommendList" :key="shop.id" :shop="shop" />
        </template>
      </div>
      <el-empty
        v-if="!shopStore.recommendLoading && !shopStore.recommendList.length"
        description="暂无推荐店铺"
      />
    </section>

    <!-- 推荐菜品 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 热门菜品</h2>
      </div>
      <div class="dish-grid">
        <template v-if="dishStore.recommendLoading && !dishStore.recommendList.length">
          <el-skeleton
            v-for="i in 6"
            :key="`dish-skeleton-${i}`"
            animated
            class="skeleton-card"
          >
            <template #template>
              <el-skeleton-item variant="image" class="skeleton-card-cover" />
              <div class="skeleton-card-body">
                <el-skeleton-item variant="text" style="width: 70%" />
                <el-skeleton-item variant="text" style="width: 40%; margin-top: 8px" />
              </div>
            </template>
          </el-skeleton>
        </template>
        <template v-else>
          <DishCard v-for="d in dishStore.recommendList" :key="d.id" :dish="d" />
        </template>
      </div>
      <el-empty
        v-if="!dishStore.recommendLoading && !dishStore.recommendList.length"
        description="暂无热门菜品"
      />
    </section>

    <!-- 推荐笔记 -->
    <section v-if="schoolStore.hasSchool" class="recommend">
      <div class="recommend-head">
        <h2 class="section-title">{{ schoolStore.currentSchool.name }} · 推荐探店笔记</h2>
        <el-button text type="primary" @click="router.push('/posts')">查看全部 →</el-button>
      </div>
      <!-- 笔记骨架按 PostCard 复刻（头像行 / 标题 / 两行正文 / 150px 封面 / 数据栏贴底） -->
      <div class="post-grid">
        <template v-if="postStore.loading && !postStore.postList.length">
          <el-skeleton
            v-for="i in 3"
            :key="`post-skeleton-${i}`"
            animated
            class="skeleton-card skeleton-post"
          >
            <template #template>
              <div class="skeleton-head">
                <el-skeleton-item variant="circle" class="skeleton-avatar" />
                <div class="skeleton-author">
                  <el-skeleton-item variant="text" style="width: 40%" />
                  <el-skeleton-item variant="text" style="width: 65%; margin-top: 6px" />
                </div>
              </div>
              <el-skeleton-item variant="h3" style="width: 70%" />
              <el-skeleton-item variant="text" style="width: 100%; margin: 10px 0 4px" />
              <el-skeleton-item variant="text" style="width: 85%" />
              <el-skeleton-item variant="image" class="skeleton-cover" />
              <div class="skeleton-foot">
                <el-skeleton-item variant="text" style="width: 70px" />
                <el-skeleton-item variant="text" style="width: 90px" />
              </div>
            </template>
          </el-skeleton>
        </template>
        <template v-else>
          <PostCard v-for="post in postStore.postList" :key="post.id" :post="post" />
        </template>
      </div>
      <el-empty
        v-if="!postStore.loading && !postStore.postList.length"
        description="还没有探店笔记"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, EditPen, Plus, School, Shop } from '@element-plus/icons-vue'

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

// Banner 中滚动展示的三张功能面板
const features = [
  {
    icon: Shop,
    title: '发现美食',
    desc: '按学校浏览食堂窗口与周边店铺，查看菜品与真实评分。',
    color: 'var(--el-color-primary)',
  },
  {
    icon: EditPen,
    title: '分享探店',
    desc: '发布探店笔记，配图配文，安利你心中的校园好味道。',
    color: 'var(--el-color-success)',
  },
  {
    icon: ChatDotRound,
    title: '互动交流',
    desc: '点赞收藏、评论互动、关注博主、加入美食圈子。',
    color: 'var(--el-color-warning)',
  },
]

/* ---------- Banner 自动翻页 + 进度预览 ---------- */
// 自动翻页间隔：下方的进度条按同一时长填充，翻页前即可预估剩余时间
const AUTO_PLAY_MS = 5000

const carouselRef = ref(null)
const indicatorsRef = ref(null)
const activeIndex = ref(0)
const paused = ref(false)

const slideLabels = computed(() => ['校园美食，从这里开始', ...features.map((f) => f.title)])
const slideCount = slideLabels.value.length

// 进度条宽度与翻页时刻由同一条时钟驱动：每帧读同一个"已播放时长"，
// 既判断该不该翻页，也决定填充宽度，两者不可能对不上，
// 也就不会出现"进度条走完还要干等一会儿才翻页"的空档。
// 时长按真实时间戳推算而非逐帧累加，主线程卡顿不会把这 5 秒拖长
let cycleStart = 0
let pausedAt = 0
let pausedTotal = 0
let rafId = null
let fillEl = null
let paintedWidth = -1

function elapsedMs() {
  const end = paused.value ? pausedAt : performance.now()
  return Math.max(0, end - cycleStart - pausedTotal)
}

function paint() {
  if (!fillEl || !fillEl.isConnected) {
    // 当前段的填充条元素随 activeIndex 变化被重建，缓存失效后重新取
    fillEl = indicatorsRef.value?.querySelector('.indicator-fill') ?? null
    paintedWidth = -1
  }
  if (!fillEl) return
  const width = Math.min(elapsedMs() / AUTO_PLAY_MS, 1) * 100
  if (width === paintedWidth) return
  paintedWidth = width
  fillEl.style.width = `${width}%`
}

// 重新开始计时：切屏后调用
function resetProgress() {
  cycleStart = performance.now()
  pausedTotal = 0
  if (paused.value) pausedAt = cycleStart
  // 立刻清空旧段，避免 Vue 换到新段之前残留满格
  if (fillEl) fillEl.style.width = '0%'
  fillEl = null
  paintedWidth = -1
}

function frame() {
  if (!paused.value && elapsedMs() >= AUTO_PLAY_MS) {
    goTo(activeIndex.value + 1)
  }
  paint()
  rafId = requestAnimationFrame(frame)
}

// 唯一的切屏入口：自己先把状态改掉，不依赖 change 事件回来补
function goTo(index) {
  const next = (index + slideCount) % slideCount
  activeIndex.value = next
  resetProgress()
  // 手动翻页视为"继续播放"：否则悬停中点击会停在 0%，看上去像进度条消失了
  paused.value = false
  carouselRef.value?.setActiveItem(next)
}

// 兜住箭头等轮播自身发起的切换（自己发起的在 goTo 里已经处理过）
function onSlideChange(index) {
  if (index === activeIndex.value) return
  activeIndex.value = index
  resetProgress()
  paused.value = false
}

// 悬停暂停：时钟与进度条同时冻结，移开后从原处继续
function pauseAutoPlay() {
  if (paused.value) return
  pausedAt = performance.now()
  paused.value = true
}

function resumeAutoPlay() {
  if (!paused.value) return
  pausedTotal += performance.now() - pausedAt
  paused.value = false
}

onMounted(async () => {
  rafId = requestAnimationFrame(frame)
  if (!schoolStore.schoolList.length) {
    await schoolStore.fetchSchools()
  }
  if (schoolStore.hasSchool) {
    shopStore.fetchRecommend({ school_id: schoolStore.currentSchool.id, page_size: 6 })
    dishStore.fetchRecommend({ school_id: schoolStore.currentSchool.id, limit: 6 })
    postStore.fetchList({ school_id: schoolStore.currentSchool.id, page_size: 3, sort: 'recommend' })
  }
})

onUnmounted(() => cancelAnimationFrame(rafId))
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}
.hero-banner {
  padding: 8px 0 0;
  background: linear-gradient(135deg, var(--el-color-primary-light-9), #ecf5ff);
  border-radius: 16px;
  overflow: hidden;
}
.slide {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
  text-align: center;
  box-sizing: border-box;
}
/* 功能面板：铺满整屏，与 banner 背景融为一体（不做成悬浮卡片） */
.slide-feature {
  padding: 0 40px;
}
.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.12);
  font-size: 32px;
}
.feature-title {
  margin: 0 0 10px;
  font-size: 24px;
  color: #303133;
}
.feature-desc {
  margin: 0;
  max-width: 560px;
  font-size: 15px;
  line-height: 1.7;
  color: #606266;
}
.hero-title {
  margin: 0 0 12px;
  font-size: 32px;
  color: #303133;
}
.hero-desc {
  margin: 0 0 24px;
  font-size: 15px;
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
}
.hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
/* 进度式指示条 */
.banner-indicators {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 0 18px;
}
.indicator {
  width: 28px;
  height: 6px;
  padding: 0;
  border: 0;
  border-radius: 3px;
  background: rgba(64, 158, 255, 0.25);
  cursor: pointer;
  overflow: hidden;
  transition: width 0.3s;
}
.indicator.active {
  width: 96px;
}
/* 宽度由 JS 每帧写入，与自动翻页共用同一条时钟 */
.indicator-fill {
  display: block;
  width: 0;
  height: 100%;
  background: var(--el-color-primary);
}
/* 商户发布引导横幅 */
.merchant-cta {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--el-color-success-light-9), #fff);
  border: 1px solid var(--el-color-success-light-7);
  border-radius: 12px;
  flex-wrap: wrap;
}
.cta-text {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.cta-icon {
  font-size: 34px;
  color: var(--el-color-success);
  flex-shrink: 0;
}
.cta-title {
  margin: 0 0 4px;
  font-size: 16px;
  color: #303133;
}
.cta-desc {
  margin: 0;
  font-size: 13px;
  color: #909399;
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
/* 骨架屏：店铺/菜品骨架按 ShopCard、DishCard 复刻（封面同为 150px、圆角与内边距一致） */
.skeleton-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.skeleton-card-cover {
  height: 150px;
}
.skeleton-card-body {
  padding: 14px 16px 16px;
  flex: 1;
}
/* 笔记骨架：卡片是竖排的（头像行 → 标题 → 正文 → 封面 → 数据栏），单独一套 */
.skeleton-post {
  padding: 16px 18px;
}
.skeleton-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.skeleton-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  flex-shrink: 0;
}
.skeleton-author {
  flex: 1;
  min-width: 0;
}
.skeleton-cover {
  height: 150px;
  border-radius: 8px;
  margin: 10px 0;
}
.skeleton-foot {
  display: flex;
  justify-content: space-between;
  margin-top: auto;
}
</style>
