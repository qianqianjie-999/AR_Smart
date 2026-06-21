<template>
  <div class="payment-container">
    <h2 class="page-title">回款管理</h2>

    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="合同">
          <el-input v-model="searchForm.contractNo" placeholder="合同编号" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="searchForm.customerName" placeholder="客户名称" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="回款日期">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <div class="table-header">
        <span class="table-title">回款列表</span>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增回款</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="customer_name" label="客户" min-width="140" />
        <el-table-column prop="amount" label="回款金额(万元)" width="140" align="right">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="payment_date" label="回款日期" width="120" />
        <el-table-column prop="payment_method" label="回款方式" width="100" />
        <el-table-column prop="bank_account" label="银行账号" min-width="150" />
        <el-table-column prop="interrupt_limitation" label="中断时效" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.interrupt_limitation ? 'success' : 'info'" size="small">
              {{ row.interrupt_limitation ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column label="操作" width="140" fixed="right" align="center">
          <template #default="{ row }">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-form-item label="合同" prop="contract_id">
          <el-select v-model="form.contract_id" placeholder="请选择合同" filterable style="width: 100%">
            <el-option v-for="c in contractOptions" :key="c.id" :label="`${c.contract_no} - ${c.project_name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="回款金额(元)" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="回款日期" prop="payment_date">
          <el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="回款方式" prop="payment_method">
          <el-select v-model="form.payment_method" style="width: 100%">
            <el-option label="银行转账" value="银行转账" />
            <el-option label="现金" value="现金" />
            <el-option label="承兑汇票" value="承兑汇票" />
          </el-select>
        </el-form-item>
        <el-form-item label="银行账号">
          <el-input v-model="form.bank_account" placeholder="回款银行账号" />
        </el-form-item>
        <el-form-item label="中断时效">
          <el-switch v-model="form.interrupt_limitation" active-text="是" inactive-text="否" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { getPaymentList, createPayment, updatePayment, deletePayment } from '@/api/payment'
import { getContractList } from '@/api/contract'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const contractOptions = ref([])

const searchForm = reactive({
  contractNo: '',
  customerName: '',
  dateRange: null
})

const form = reactive({
  contract_id: '',
  amount: 0,
  payment_date: '',
  payment_method: '银行转账',
  bank_account: '',
  interrupt_limitation: true,
  remark: ''
})

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const dialogTitle = computed(() => isEdit.value ? '编辑回款' : '新增回款')
const rules = {
  contract_id: [{ required: true, message: '请选择合同', trigger: 'change' }],
  amount: [{ required: true, message: '请输入回款金额', trigger: 'blur' }],
  payment_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  payment_method: [{ required: true, message: '请选择方式', trigger: 'change' }]
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

async function fetchContracts() {
  try {
    const res = await getContractList({ page: 1, page_size: 999 })
    contractOptions.value = res.data?.list || res.data?.items || []
  } catch { contractOptions.value = [] }
}

async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      contract_no: searchForm.contractNo || undefined,
      customer_name: searchForm.customerName || undefined,
      start_date: searchForm.dateRange?.[0] || undefined,
      end_date: searchForm.dateRange?.[1] || undefined
    }
    const res = await getPaymentList(params)
    tableData.value = res.data?.list || res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch { tableData.value = [] } finally { loading.value = false }
}

function handleSearch() { pagination.page = 1; fetchData() }
function handleReset() {
  searchForm.contractNo = ''; searchForm.customerName = ''; searchForm.dateRange = null
  handleSearch()
}

function handleAdd() {
  isEdit.value = false; editId.value = null
  form.contract_id = ''; form.amount = 0; form.payment_date = ''
  form.payment_method = '银行转账'; form.bank_account = ''; form.interrupt_limitation = true; form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.id
  Object.keys(form).forEach(k => { if (row[k] !== undefined) form[k] = row[k] })
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该回款记录吗？', '删除确认', { type: 'warning' })
    await deletePayment(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch { /* canceled */ }
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form }
    if (isEdit.value) { await updatePayment(editId.value, data); ElMessage.success('更新成功') }
    else { await createPayment(data); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ } finally { submitLoading.value = false }
}

onMounted(() => { fetchContracts(); fetchData() })
</script>

<style scoped>
.amount-positive { color: #909399; font-size: 13px; }
</style>
