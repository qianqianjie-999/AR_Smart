<template>
  <div class="limitation-list">
    <h2 class="page-title">时效列表</h2>

    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="有效" value="effective" />
            <el-option label="即将到期" value="expiring" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期日">
          <el-date-picker v-model="searchForm.dateRange" type="daterange"
            range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width: 260px" />
        </el-form-item>
        <el-form-item label="客户/合同">
          <el-input v-model="searchForm.keyword" placeholder="客户名称/合同编号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <div class="table-header"><span class="table-title">时效列表</span></div>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="customer_name" label="客户" min-width="150" />
        <el-table-column prop="base_date" label="基准日期" width="120" />
        <el-table-column prop="due_date" label="时效到期日" width="120" />
        <el-table-column prop="remaining_days" label="剩余天数" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="remainingDaysType(row.remaining_days)" size="small">{{ row.remaining_days }}天</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="interrupt_count" label="中断次数" width="80" align="center" />
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="warning" link @click="handleInterrupt(row)">中断</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="flex-between mt-16">
        <span class="table-total">共 {{ pagination.total }} 条记录</span>
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="中断时效" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="dialog-form">
        <el-form-item label="中断原因" prop="reason">
          <el-select v-model="form.reason" style="width: 100%">
            <el-option label="部分回款" value="部分回款" />
            <el-option label="书面承诺" value="书面承诺" />
            <el-option label="对账确认" value="对账确认" />
            <el-option label="催款函件" value="催款函件" />
            <el-option label="诉讼/仲裁" value="诉讼/仲裁" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="中断日期" prop="interrupt_date">
          <el-date-picker v-model="form.interrupt_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="新到期日" prop="new_due_date">
          <el-date-picker v-model="form.new_due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { getLimitationList, interruptLimitation } from '@/api/limitation'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const currentRow = ref(null)

const searchForm = reactive({ status: '', dateRange: null, keyword: '' })
const form = reactive({ reason: '部分回款', interrupt_date: '', new_due_date: '', remark: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const rules = {
  reason: [{ required: true, message: '请选择原因', trigger: 'change' }],
  interrupt_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  new_due_date: [{ required: true, message: '请选择新到期日', trigger: 'change' }]
}

function remainingDaysType(d) {
  if (d == null) return 'info'
  if (d <= 7) return 'danger'
  if (d <= 90) return 'warning'
  return 'success'
}

function statusType(s) {
  const map = { 'effective': 'success', 'expiring': 'warning', 'expired': 'danger' }
  return map[s] || 'info'
}

function statusText(s) {
  const map = { 'effective': '有效', 'expiring': '即将到期', 'expired': '已过期' }
  return map[s] || s
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getLimitationList({
      page: pagination.page, page_size: pagination.pageSize,
      status: searchForm.status || undefined, keyword: searchForm.keyword || undefined,
      start_date: searchForm.dateRange?.[0] || undefined, end_date: searchForm.dateRange?.[1] || undefined
    })
    tableData.value = res.data?.list || res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch { tableData.value = [] } finally { loading.value = false }
}

function handleSearch() { pagination.page = 1; fetchData() }
function handleReset() { searchForm.status = ''; searchForm.dateRange = null; searchForm.keyword = ''; handleSearch() }

function handleInterrupt(row) {
  currentRow.value = row
  form.reason = '部分回款'; form.interrupt_date = ''; form.new_due_date = ''; form.remark = ''
  dialogVisible.value = true
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    await interruptLimitation({ ...form, limitation_id: currentRow.value?.id })
    ElMessage.success('时效中断成功')
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ } finally { submitLoading.value = false }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
</style>
