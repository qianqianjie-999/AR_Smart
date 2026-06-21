<template>
  <div class="pagination-wrapper flex-between">
    <span class="pagination-total">共 {{ total }} 条记录</span>
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="total"
      :page-sizes="pageSizes"
      :layout="layout"
      background
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  pageSizes: { type: Array, default: () => [10, 20, 50, 100] },
  layout: { type: String, default: 'total, sizes, prev, pager, next, jumper' }
})

const emit = defineEmits(['update:page', 'update:pageSize', 'change'])

const currentPage = ref(props.page)
const currentPageSize = ref(props.pageSize)

watch(() => props.page, (val) => { currentPage.value = val })
watch(() => props.pageSize, (val) => { currentPageSize.value = val })

function handleSizeChange(val) {
  emit('update:pageSize', val)
  emit('change', { page: currentPage.value, pageSize: val })
}

function handleCurrentChange(val) {
  emit('update:page', val)
  emit('change', { page: val, pageSize: currentPageSize.value })
}
</script>

<style scoped>
.pagination-wrapper {
  padding: 10px 0;
}
.pagination-total {
  color: #909399;
  font-size: 13px;
}
</style>
