<template>
  <div class="log-container">
    <h2 class="page-title">操作日志</h2>

    <el-form :inline="true" :model="searchForm" class="search-bar">
      <el-form-item label="模块">
        <el-select v-model="searchForm.module" placeholder="全部" clearable style="width:130px">
          <el-option label="客户管理" value="客户管理" /><el-option label="合同管理" value="合同管理" />
          <el-option label="回款管理" value="回款管理" /><el-option label="开票管理" value="开票管理" />
          <el-option label="催款管理" value="催款管理" /><el-option label="时效管理" value="时效管理" />
          <el-option label="系统管理" value="系统管理" /><el-option label="认证" value="认证" />
        </el-select>
      </el-form-item>
      <el-form-item label="操作">
        <el-select v-model="searchForm.action" placeholder="全部" clearable style="width:110px">
          <el-option label="新增" value="新增" /><el-option label="编辑" value="编辑" />
          <el-option label="删除" value="删除" /><el-option label="登录" value="登录" />
          <el-option label="导出" value="导出" />
        </el-select>
      </el-form-item>
      <el-form-item label="日期">
        <el-date-picker v-model="searchForm.dateRange" type="daterange" range-separator="至"
          start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width:240px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadList"><el-icon><Search /></el-icon> 搜索</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="tableData" border stripe v-loading="loading" max-height="calc(100vh - 280px)">
      <el-table-column type="index" label="序号" width="60" />
      <el-table-column prop="username" label="操作用户" width="120" />
      <el-table-column prop="module" label="模块" width="100">
        <template #default="{row}"><el-tag size="small">{{ row.module }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="action" label="操作" width="80" />
      <el-table-column prop="content" label="内容" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP地址" width="140" />
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{row}">{{ row.created_at }}</template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="total, prev, pager, next" @current-change="loadList"
      style="margin-top:16px;justify-content:flex-end"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getOperationLogs } from '@/api/system'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchForm = reactive({ module: '', action: '', dateRange: null })

async function loadList() {
  loading.value = true
  try {
    const params = { page: page.value, pageSize: pageSize.value }
    if (searchForm.module) params.module = searchForm.module
    if (searchForm.action) params.action = searchForm.action
    if (searchForm.dateRange?.length === 2) {
      params.date_start = searchForm.dateRange[0]
      params.date_end = searchForm.dateRange[1]
    }
    const res = await getOperationLogs(params)
    tableData.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (e) { /* ignore */ }
  loading.value = false
}

onMounted(loadList)
</script>
