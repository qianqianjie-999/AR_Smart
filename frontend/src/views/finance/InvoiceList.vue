<template>
  <div class="invoice-container">
    <h2 class="page-title">开票管理</h2>

    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="合同">
          <el-input v-model="searchForm.contractNo" placeholder="合同编号" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="发票号码">
          <el-input v-model="searchForm.invoiceNo" placeholder="发票号码" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="开票日期">
          <el-date-picker v-model="searchForm.dateRange" type="daterange" range-separator="至"
            start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" style="width: 260px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <div class="table-header">
        <span class="table-title">开票列表</span>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增开票</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="invoice_no" label="发票号码" width="150" />
        <el-table-column prop="invoice_type" label="发票类型" width="140" />
        <el-table-column prop="amount" label="开票金额(万元)" width="140" align="right">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="invoice_date" label="开票日期" width="120" />
        <el-table-column prop="tax_rate" label="税率" width="80" align="center">
          <template #default="{ row }">{{ row.tax_rate }}%</template>
        </el-table-column>
        <el-table-column label="附件" width="180">
          <template #default="{ row }">
            <div v-if="parseFiles(row.invoice_file).length">
              <el-button link type="primary" size="small" v-for="(f, i) in parseFiles(row.invoice_file).slice(0, 3)" :key="i" @click="previewFile(f)">
                文件{{ i + 1 }}
              </el-button>
              <el-tag v-if="parseFiles(row.invoice_file).length > 3" size="small" type="info">+{{ parseFiles(row.invoice_file).length - 3 }}</el-tag>
            </div>
            <span v-else style="color:#909399">无</span>
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
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-form-item label="合同" prop="contract_id">
          <el-select v-model="form.contract_id" placeholder="请选择合同" filterable style="width: 100%">
            <el-option v-for="c in contractOptions" :key="c.id" :label="`${c.contract_no} - ${c.project_name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="发票号码" prop="invoice_no">
          <el-input v-model="form.invoice_no" placeholder="请输入发票号码" />
        </el-form-item>
        <el-form-item label="发票类型" prop="invoice_type">
          <el-select v-model="form.invoice_type" style="width: 100%">
            <el-option label="增值税专用发票" value="增值税专用发票" />
            <el-option label="增值税普通发票" value="增值税普通发票" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="开票金额(元)" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="开票日期" prop="invoice_date">
          <el-date-picker v-model="form.invoice_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="税率(%)" prop="tax_rate">
          <el-input-number v-model="form.tax_rate" :min="0" :max="100" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="发票附件">
          <AttachmentInput v-model="form.invoice_file" placeholder="上传或输入发票附件路径" />
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
import { getInvoiceList, createInvoice, updateInvoice, deleteInvoice } from '@/api/invoice'
import { getContractList } from '@/api/contract'
import AttachmentInput from '@/components/AttachmentInput.vue'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const contractOptions = ref([])

const searchForm = reactive({ contractNo: '', invoiceNo: '', dateRange: null })
const form = reactive({ contract_id: '', invoice_no: '', invoice_type: '增值税专用发票', amount: 0, invoice_date: '', tax_rate: 13, remark: '', invoice_file: '[]' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const dialogTitle = computed(() => isEdit.value ? '编辑开票' : '新增开票')
const rules = {
  contract_id: [{ required: true, message: '请选择合同', trigger: 'change' }],
  invoice_no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  invoice_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  invoice_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

function parseFiles(val) {
  if (!val) return []
  if (Array.isArray(val)) return val
  try {
    const parsed = JSON.parse(val)
    return Array.isArray(parsed) ? parsed : [{ url: val }]
  } catch {
    return [{ url: val }]
  }
}

function previewFile(f) {
  const url = typeof f === 'object' ? (f.url || f.filename) : f
  if (!url) return
  const fullUrl = url.startsWith('/api/') || url.startsWith('http') ? url : `/api/upload/${url}`
  const token = localStorage.getItem('token') || ''
  const separator = fullUrl.includes('?') ? '&' : '?'
  window.open(`${fullUrl}${separator}token=${encodeURIComponent(token)}`, '_blank')
}

async function fetchContracts() {
  try { const res = await getContractList({ page: 1, page_size: 999 }); contractOptions.value = res.data?.list || res.data?.items || [] }
  catch { contractOptions.value = [] }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getInvoiceList({
      page: pagination.page, page_size: pagination.pageSize,
      contract_no: searchForm.contractNo || undefined, invoice_no: searchForm.invoiceNo || undefined,
      start_date: searchForm.dateRange?.[0] || undefined, end_date: searchForm.dateRange?.[1] || undefined
    })
    tableData.value = res.data?.list || res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch { tableData.value = [] } finally { loading.value = false }
}

function handleSearch() { pagination.page = 1; fetchData() }
function handleReset() { searchForm.contractNo = ''; searchForm.invoiceNo = ''; searchForm.dateRange = null; handleSearch() }
function handleAdd() {
  isEdit.value = false; editId.value = null
  form.contract_id = ''; form.invoice_no = ''; form.invoice_type = '增值税专用发票'; form.amount = 0; form.invoice_date = ''; form.tax_rate = 13; form.remark = ''; form.invoice_file = '[]'
  dialogVisible.value = true
}
function handleEdit(row) { isEdit.value = true; editId.value = row.id; Object.keys(form).forEach(k => { if (row[k] !== undefined) form[k] = row[k] }); dialogVisible.value = true }
async function handleDelete(row) {
  try { await ElMessageBox.confirm('确定删除吗？', '删除确认', { type: 'warning' }); await deleteInvoice(row.id); ElMessage.success('删除成功'); fetchData() } catch { /* canceled */ }
}
async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form }
    if (isEdit.value) { await updateInvoice(editId.value, data); ElMessage.success('更新成功') }
    else { await createInvoice(data); ElMessage.success('创建成功') }
    dialogVisible.value = false; fetchData()
  } catch { /* handled */ } finally { submitLoading.value = false }
}

onMounted(() => { fetchContracts(); fetchData() })
</script>

<style scoped>
.amount-positive { color: #909399; font-size: 13px; }
</style>
