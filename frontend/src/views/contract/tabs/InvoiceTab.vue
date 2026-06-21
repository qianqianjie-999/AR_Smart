<template>
  <div>
    <div class="flex-between mb-16">
      <span></span>
      <el-button type="primary" :icon="Plus" @click="handleAdd">新增开票记录</el-button>
    </div>
    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="invoice_no" label="发票号码" width="150" />
      <el-table-column prop="invoice_type" label="发票类型" width="100" />
      <el-table-column prop="amount" label="开票金额(万元)" width="150" align="right">
        <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
      </el-table-column>
      <el-table-column prop="invoice_date" label="开票日期" width="130" />
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
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
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
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getInvoiceList, createInvoice, updateInvoice, deleteInvoice } from '@/api/invoice'
import AttachmentInput from '@/components/AttachmentInput.vue'

const props = defineProps({
  contractId: { type: [String, Number], required: true }
})

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)

const form = reactive({
  invoice_no: '',
  invoice_type: '增值税专用发票',
  amount: 0,
  invoice_date: '',
  tax_rate: 13,
  invoice_file: '[]',
  remark: ''
})

const dialogTitle = computed(() => isEdit.value ? '编辑开票记录' : '新增开票记录')

const rules = {
  invoice_no: [{ required: true, message: '请输入发票号码', trigger: 'blur' }],
  invoice_type: [{ required: true, message: '请选择发票类型', trigger: 'change' }],
  amount: [{ required: true, message: '请输入开票金额', trigger: 'blur' }],
  invoice_date: [{ required: true, message: '请选择开票日期', trigger: 'change' }]
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

async function fetchData() {
  loading.value = true
  try {
    const res = await getInvoiceList({ contract_id: props.contractId })
    tableData.value = res.data?.list || res.data?.items || res.data || []
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false; editId.value = null
  form.invoice_no = ''; form.invoice_type = '增值税专用发票'
  form.amount = 0; form.invoice_date = ''; form.tax_rate = 13; form.invoice_file = '[]'; form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.id
  Object.keys(form).forEach(key => { if (row[key] !== undefined) form[key] = row[key] })
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该开票记录吗？', '删除确认', { type: 'warning' })
    await deleteInvoice(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch { /* canceled */ }
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form, contract_id: props.contractId }
    if (isEdit.value) { await updateInvoice(editId.value, data); ElMessage.success('更新成功') }
    else { await createInvoice(data); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ }
  finally { submitLoading.value = false }
}

fetchData()
</script>
