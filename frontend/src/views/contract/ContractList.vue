<template>
  <div class="contract-container">
    <h2 class="page-title">合同管理</h2>

    <!-- 搜索表单 -->
    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="客户">
          <el-input v-model="searchForm.customerName" placeholder="请输入客户名称" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 140px">
            <el-option label="执行中" value="执行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已终止" value="已终止" />
          </el-select>
        </el-form-item>
        <el-form-item label="签订日期">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model="searchForm.projectName" placeholder="请输入" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格 -->
    <div class="table-container">
      <div class="table-header">
        <span class="table-title">合同列表</span>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增合同</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="contract_no" label="合同编号" width="150" />
        <el-table-column prop="project_name" label="项目名称" min-width="180" />
        <el-table-column prop="customer_name" label="客户" width="140" />
        <el-table-column prop="contract_amount" label="合同金额(万元)" width="140" align="right">
          <template #default="{ row }">{{ formatMoney(row.contract_amount) }}</template>
        </el-table-column>
        <el-table-column prop="audit_amount" label="审计金额(万元)" width="140" align="right">
          <template #default="{ row }">{{ formatMoney(row.audit_amount) }}</template>
        </el-table-column>
        <el-table-column prop="outstanding_amount" label="尚欠金额(万元)" width="140" align="right">
          <template #default="{ row }">
            <span style="color: #f56c6c; font-weight: 600;">{{ formatMoney(row.outstanding_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="due_amount" label="到期应付(万元)" width="140" align="right">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: 600;">{{ formatMoney(row.due_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="handleDetail(row)">详情</el-button>
            <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="flex-between mt-16">
        <span class="table-total">共 {{ pagination.total }} 条记录</span>
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="720px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px" class="dialog-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同编号" prop="contract_no">
              <el-input v-model="form.contract_no" placeholder="请输入合同编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_id">
              <el-select v-model="form.customer_id" placeholder="请选择客户" filterable style="width: 100%">
                <el-option
                  v-for="c in customerOptions"
                  :key="c.id"
                  :label="c.name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="form.project_name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同金额" prop="contract_amount">
              <div class="input-with-unit">
                <el-input-number v-model="form.contract_amount" :min="0" :precision="2" style="flex: 1" controls-position="right" />
                <span class="unit-text">(元)</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="审计金额" prop="audit_amount">
              <div class="input-with-unit">
                <el-input-number v-model="form.audit_amount" :min="0" :precision="2" style="flex: 1" controls-position="right" />
                <span class="unit-text">(元)</span>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="签订日期" prop="sign_date">
              <el-date-picker v-model="form.sign_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="验收日期">
              <el-date-picker v-model="form.acceptance_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择" style="width: 100%">
                <el-option label="执行中" value="执行中" />
                <el-option label="已完成" value="已完成" />
                <el-option label="已终止" value="已终止" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="付款方式">
          <el-input v-model="form.payment_method" type="textarea" :rows="2" placeholder="请输入付款方式说明" />
        </el-form-item>
        <el-form-item label="违约条款约定">
          <el-input v-model="form.breach_clause" type="textarea" :rows="2" placeholder="请输入违约条款约定" />
        </el-form-item>
        <el-form-item label="违约金利息">
          <el-input v-model="form.penalty_interest" placeholder="默认：日万分之五" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { getContractList, getContractDetail, createContract, updateContract, deleteContract } from '@/api/contract'
import { getCustomerList } from '@/api/customer'

const router = useRouter()
const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const customerOptions = ref([])

const searchForm = reactive({
  customerName: '',
  status: '',
  dateRange: null,
  projectName: ''
})

const form = reactive({
  contract_no: '',
  customer_id: '',
  project_name: '',
  contract_amount: 0,
  audit_amount: 0,
  sign_date: '',
  acceptance_date: '',
  status: '执行中',
  payment_method: '',
  breach_clause: '',
  penalty_interest: '日万分之五',
  remark: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const dialogTitle = computed(() => isEdit.value ? '编辑合同' : '新增合同')

const formRules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  contract_amount: [{ required: true, message: '请输入合同金额', trigger: 'blur' }],
  sign_date: [{ required: true, message: '请选择签订日期', trigger: 'change' }]
}

function statusType(status) {
  const map = { '执行中': 'primary', '已完成': 'success', '已终止': 'info' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { '执行中': '执行中', '已完成': '已完成', '已终止': '已终止' }
  return map[status] || status
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

async function fetchCustomers() {
  try {
    const res = await getCustomerList({ page: 1, page_size: 999 })
    customerOptions.value = res.data?.list || res.data?.items || []
  } catch {
    customerOptions.value = []
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      customer_name: searchForm.customerName || undefined,
      status: searchForm.status || undefined,
      project_name: searchForm.projectName || undefined,
      sign_date_start: searchForm.dateRange?.[0] || undefined,
      sign_date_end: searchForm.dateRange?.[1] || undefined
    }
    const res = await getContractList(params)
    tableData.value = res.data?.list || res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchData()
}

function handleReset() {
  searchForm.customerName = ''
  searchForm.status = ''
  searchForm.dateRange = null
  searchForm.projectName = ''
  handleSearch()
}

function handleAdd() {
  isEdit.value = false
  editId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleDetail(row) {
  router.push(`/contract/${row.id}`)
}

async function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  resetForm()
  try {
    const res = await getContractDetail(row.id)
    const info = res.data
    Object.keys(form).forEach(key => {
      if (info[key] !== undefined && info[key] !== null) {
        form[key] = info[key]
      }
    })
    if (!form.penalty_interest) form.penalty_interest = '日万分之五'
  } catch (e) {
    // 如果详情接口失败，回退为从列表行数据中取
    Object.keys(form).forEach(key => {
      if (row[key] !== undefined) form[key] = row[key]
    })
  }
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除合同「${row.project_name}」吗？`, '删除确认', { type: 'warning' })
    await deleteContract(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // canceled
  }
}

function resetForm() {
  form.contract_no = ''
  form.customer_id = ''
  form.project_name = ''
  form.contract_amount = 0
  form.audit_amount = 0
  form.sign_date = ''
  form.acceptance_date = ''
  form.status = '执行中'
  form.payment_method = ''
  form.breach_clause = ''
  form.penalty_interest = '日万分之五'
  form.remark = ''
}

function handleDialogClosed() {
  formRef.value?.resetFields()
  resetForm()
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitLoading.value = true
  try {
    const data = { ...form }
    if (isEdit.value) {
      await updateContract(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createContract(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // handled by interceptor
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  fetchCustomers()
  fetchData()
})
</script>

<style scoped>
.table-total {
  color: #909399;
  font-size: 13px;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.unit-text {
  color: #606266;
  font-size: 14px;
  white-space: nowrap;
}
</style>
