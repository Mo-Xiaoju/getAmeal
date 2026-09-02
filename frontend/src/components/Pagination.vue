<template>
  <div v-if="totalPages > 1" class="pagination">
    <el-pagination
      background
      layout="prev, pager, next, total"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      @current-change="(page) => emit('change', page)"
    />
  </div>
</template>

<script setup>
// 通用分页组件：列表页 / 收藏列表复用
defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, default: 0 },
  pageSize: { type: Number, default: 10 },
})

const emit = defineEmits(['change'])
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
