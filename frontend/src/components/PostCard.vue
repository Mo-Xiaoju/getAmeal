<template>
  <div class="post-card" @click="goDetail">
    <div class="post-head">
      <!-- .stop：整张卡片是「进笔记详情」，点头像要进对方主页 -->
      <el-avatar
        class="post-avatar"
        :size="36"
        :src="post.author?.avatar_url || undefined"
        @click.stop="goUser(post.author?.id)"
      >
        {{ (post.author?.nickname || 'U').charAt(0) }}
      </el-avatar>
      <div class="post-author">
        <span class="post-nickname">{{ post.author?.nickname || '匿名用户' }}</span>
        <span class="post-time">{{ formatDate(post.created_at) }}</span>
      </div>
      <el-tag v-if="post.shop_name" type="info" size="small" effect="plain">@{{ post.shop_name }}</el-tag>
    </div>

    <h3 class="post-title">{{ post.title }}</h3>
    <p class="post-content">{{ post.content }}</p>

    <div v-if="post.images && post.images.length" class="post-cover">
      <img :src="post.images[0]" :alt="post.title" loading="lazy" @error="imageFailed = true" @click.stop="openImage(post.images, 0)" />
    </div>

    <div v-if="post.rec_reason && post.rec_reason.length" class="rec-reason">
      <el-tag v-for="(r, i) in post.rec_reason" :key="i" type="warning" size="small" effect="plain">{{ r }}</el-tag>
    </div>

    <div class="post-foot">
      <div v-if="post.tags && post.tags.length" class="post-tags">
        <el-tag v-for="t in post.tags.slice(0, 3)" :key="t" size="small" effect="plain">{{ t }}</el-tag>
      </div>
      <!-- 点赞用大拇指、收藏用五角星：两个都曾是星星，混在一排里分不清哪个是哪个。
           已点赞 / 已收藏除了整格变色（红 / 黄，与详情页按钮同色），图标也从描边变实心 -->
      <div class="post-stats">
        <span :class="{ 'is-liked': post.liked }">
          <el-icon><ThumbUpIcon :filled="!!post.liked" /></el-icon>{{ post.like_count || 0 }}
        </span>
        <span :class="{ 'is-favorited': post.favorited }">
          <el-icon><StarIcon :filled="!!post.favorited" /></el-icon>{{ post.favorite_count || 0 }}
        </span>
        <span><el-icon><ChatDotRound /></el-icon>{{ post.comment_count || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound } from '@element-plus/icons-vue'

import StarIcon from '@/components/StarIcon.vue'
import ThumbUpIcon from '@/components/ThumbUpIcon.vue'
import { openImage } from '@/composables/useImageViewer'
import { useUserNav } from '@/composables/useUserNav'

// 笔记卡片：笔记列表 / 首页最新笔记复用
const props = defineProps({
  post: { type: Object, required: true },
})

const router = useRouter()
const { goUser } = useUserNav()
const imageFailed = ref(false)

const formatDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
}

const goDetail = () => {
  if (props.post.id) router.push(`/posts/${props.post.id}`)
}
</script>

<style scoped>
/* 与 ShopCard/DishCard 同一骨架：撑满格子 + 封面定高，混排时行内高度才对齐 */
.post-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 16px 18px;
  cursor: pointer;
  transition: all 0.25s;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.post-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}
.post-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.post-avatar {
  cursor: pointer;
  flex-shrink: 0;
}
.post-avatar:hover {
  opacity: 0.85;
}
.post-author {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.post-nickname {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.post-time {
  font-size: 12px;
  color: #c0c4cc;
}
.post-title {
  margin: 0 0 6px;
  font-size: 16px;
  color: #303133;
  line-height: 1.4;
}
.post-content {
  margin: 0 0 10px;
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.post-cover {
  height: 150px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
  background: var(--el-color-primary-light-9);
}
.post-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
}
.rec-reason {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}
.post-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  /* 卡片被拉伸到与同行最高卡片齐平时，数据栏贴底 */
  margin-top: auto;
}
.post-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.post-stats {
  display: flex;
  gap: 14px;
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}
.post-stats span {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
/* 已点赞 / 已收藏：整格（图标 + 数字）跟着变色，取值与详情页按钮的按钮类型一致（danger / warning） */
.post-stats span.is-liked {
  color: var(--el-color-danger);
}
.post-stats span.is-favorited {
  color: var(--el-color-warning);
}
</style>
