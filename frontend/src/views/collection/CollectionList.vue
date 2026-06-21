<template>
  <div class="collection-container">
    <h2 class="page-title">催款管理</h2>

    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="催款方式">
          <el-select v-model="searchForm.collection_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="电话" value="电话" />
            <el-option label="邮件" value="邮件" />
            <el-option label="EMS" value="EMS" />
            <el-option label="上门" value="上门" />
            <el-option label="律师函" value="律师函" />
          </el-select>
        </el-form-item>
        <el-form-item label="合同">
          <el-input v-model="searchForm.contractNo" placeholder="合同编号" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="日期范围">
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
        <span class="table-title">催款列表</span>
        <el-button type="primary" :icon="Plus" @click="handleAdd">新增催款</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="project_name" label="合同" min-width="140" />
        <el-table-column prop="collection_type" label="催款方式" width="100" />
        <el-table-column prop="collection_date" label="催款日期" width="120" />
        <el-table-column prop="recipient" label="收件人" width="100" />
        <el-table-column prop="express_no" label="EMS单号" width="160" />
        <el-table-column prop="sign_status" label="签收状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.sign_status === '已签收' ? 'success' : 'info'" size="small">{{ row.sign_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_limitation_interrupt" label="中断时效" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_limitation_interrupt ? 'warning' : 'info'" size="small">
              {{ row.is_limitation_interrupt ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="collection_content" label="内容" min-width="180" show-overflow-tooltip />
        <el-table-column label="附件" width="180">
          <template #default="{ row }">
            <div v-if="parseFiles(row.collection_file).length">
              <el-button link type="primary" size="small" v-for="(f, i) in parseFiles(row.collection_file).slice(0, 3)" :key="i" @click="previewFile(f)">
                文件{{ i + 1 }}
              </el-button>
              <el-tag v-if="parseFiles(row.collection_file).length > 3" size="small" type="info">+{{ parseFiles(row.collection_file).length - 3 }}</el-tag>
            </div>
            <span v-else style="color:#909399">无</span>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="550px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="dialog-form">
        <el-form-item label="合同" prop="contract_id">
          <el-select v-model="form.contract_id" placeholder="请选择合同" filterable style="width: 100%">
            <el-option v-for="c in contractOptions" :key="c.id" :label="`${c.contract_no} - ${c.project_name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="催款方式" prop="collection_type">
          <el-select v-model="form.collection_type" style="width: 100%">
            <el-option label="电话" value="电话" />
            <el-option label="邮件" value="邮件" />
            <el-option label="EMS" value="EMS" />
            <el-option label="上门" value="上门" />
            <el-option label="律师函" value="律师函" />
          </el-select>
        </el-form-item>
        <el-form-item label="催款日期" prop="collection_date">
          <el-date-picker v-model="form.collection_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="收件人">
          <el-input v-model="form.recipient" placeholder="请输入收件人" />
        </el-form-item>
        <el-form-item label="EMS单号">
          <el-input v-model="form.express_no" placeholder="请输入EMS快递单号" />
        </el-form-item>
        <el-form-item label="签收状态">
          <el-select v-model="form.sign_status" style="width: 100%">
            <el-option label="待签收" value="待签收" />
            <el-option label="已签收" value="已签收" />
            <el-option label="拒收" value="拒收" />
          </el-select>
        </el-form-item>
        <el-form-item label="中断时效">
          <el-switch v-model="form.is_limitation_interrupt" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="催款内容">
          <el-input v-model="form.collection_content" type="textarea" :rows="3" placeholder="催款内容" />
        </el-form-item>
        <el-form-item label="附件">
          <AttachmentInput v-model="form.collection_file" placeholder="上传或输入催款函附件路径" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注" />
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
import { getCollectionList, createCollection, updateCollection, deleteCollection } from '@/api/collection'
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

const searchForm = reactive({ collection_type: '', contractNo: '', dateRange: null })
const form = reactive({
  contract_id: '',
  collection_type: '电话',
  collection_date: '',
  recipient: '',
  express_no: '',
  sign_status: '待签收',
  is_limitation_interrupt: 1,
  collection_content: '',
  collection_file: '[]',
  remark: ''
})
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const dialogTitle = computed(() => isEdit.value ? '编辑催款' : '新增催款')
const rules = {
  contract_id: [{ required: true, message: '请选择合同', trigger: 'change' }],
  collection_type: [{ required: true, message: '请选择方式', trigger: 'change' }],
  collection_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
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
    const res = await getCollectionList({
      page: pagination.page, page_size: pagination.pageSize,
      collection_type: searchForm.collection_type || undefined,
      contract_no: searchForm.contractNo || undefined,
      date_start: searchForm.dateRange?.[0] || undefined,
      date_end: searchForm.dateRange?.[1] || undefined
    })
    tableData.value = res.data?.list || res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch { tableData.value = [] } finally { loading.value = false }
}

function handleSearch() { pagination.page = 1; fetchData() }
function handleReset() { searchForm.collection_type = ''; searchForm.contractNo = ''; searchForm.dateRange = null; handleSearch() }
function handleAdd() {
  isEdit.value = false; editId.value = null
  form.contract_id = ''; form.collection_type = '电话'; form.collection_date = ''
  form.recipient = ''; form.express_no = ''; form.sign_status = '待签收'
  form.is_limitation_interrupt = 1; form.collection_content = ''; form.collection_file = '[]'; form.remark = ''
  dialogVisible.value = true
}
function handleEdit(row) { isEdit.value = true; editId.value = row.id; Object.keys(form).forEach(k => { if (row[k] !== undefined) form[k] = row[k] }); dialogVisible.value = true }
async function handleDelete(row) {
  try { await ElMessageBox.confirm('确定删除吗？', '删除确认', { type: 'warning' }); await deleteCollection(row.id); ElMessage.success('删除成功'); fetchData() } catch { /* canceled */ }
}
async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form }
    if (isEdit.value) { await updateCollection(editId.value, data); ElMessage.success('更新成功') }
    else { await createCollection(data); ElMessage.success('创建成功') }
    dialogVisible.value = false; fetchData()
  } catch { /* handled */ } finally { submitLoading.value = false }
}

onMounted(() => { fetchContracts(); fetchData() })
</script>

<style scoped>
.template-form { color: #909399; font-size: 13px; }
</style>