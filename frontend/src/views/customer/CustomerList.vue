<template>
  <div class="customer-container">
    <h2 class="page-title">客户管理</h2>

    <!-- 搜索表单 -->
    <div class="search-form">
      <el-form :model="searchForm" inline>
        <el-form-item label="区域">
          <el-input v-model="searchForm.region" placeholder="如：汶上县" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item label="客户名称">
          <el-input v-model="searchForm.name" placeholder="请输入客户名称" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="信用等级">
          <el-select v-model="searchForm.creditLevel" placeholder="全部" clearable style="width: 140px">
            <el-option label="A级" value="A" />
            <el-option label="B级" value="B" />
            <el-option label="C级" value="C" />
            <el-option label="D级" value="D" />
          </el-select>
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
        <span class="table-title">客户列表</span>
        <div>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增客户</el-button>
          <el-button :icon="Download" @click="handleExport" :loading="exportLoading">导出Excel</el-button>
          <el-button :icon="Upload" @click="importDialogVisible = true">导入Excel</el-button>
        </div>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border style="width: 100%">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="region" label="区域" width="100" />
        <el-table-column prop="name" label="客户名称" min-width="160" />
        <el-table-column prop="business_contact" label="业务联系人" width="100" />
        <el-table-column prop="credit_level" label="信用等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="creditLevelType(row.credit_level)" size="small">
              {{ row.credit_level }}级
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="outstanding_amount" label="欠款金额(万元)" width="140" align="right">
          <template #default="{ row }">{{ formatMoney(row.outstanding_amount) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="handleView(row)">详情</el-button>
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
      width="700px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px" class="dialog-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区域" prop="region">
              <el-input v-model="form.region" placeholder="如：汶上县" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="信用等级" prop="credit_level">
              <el-select v-model="form.credit_level" placeholder="请选择" style="width: 100%">
                <el-option label="A级" value="A" />
                <el-option label="B级" value="B" />
                <el-option label="C级" value="C" />
                <el-option label="D级" value="D" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务联系人">
              <el-input v-model="form.business_contact" placeholder="请输入业务联系人" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="注册地址">
          <el-input v-model="form.registered_addr" placeholder="请输入客户注册地址" />
        </el-form-item>
        <el-form-item label="联系地址">
          <el-input v-model="form.contact_addr" placeholder="请输入客户联系地址" />
        </el-form-item>
        <el-form-item label="开票信息">
          <el-input v-model="form.billing_info" type="textarea" :rows="2" placeholder="请输入开票信息（税号、开户行、账号等）" />
        </el-form-item>

        <!-- 联系人子表 -->
        <el-divider content-position="left">联系人信息</el-divider>
        <div v-for="(contact, index) in form.contacts" :key="index" class="contact-row">
          <el-row :gutter="12">
            <el-col :span="4">
              <el-select v-model="contact.contact_type" placeholder="类型" style="width: 100%">
                <el-option label="商务" value="商务" />
                <el-option label="财务" value="财务" />
                <el-option label="技术" value="技术" />
                <el-option label="法务" value="法务" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-input v-model="contact.name" placeholder="姓名" />
            </el-col>
            <el-col :span="4">
              <el-input v-model="contact.position" placeholder="职位" />
            </el-col>
            <el-col :span="4">
              <el-input v-model="contact.phone" placeholder="电话" />
            </el-col>
            <el-col :span="4">
              <el-input v-model="contact.email" placeholder="邮箱" />
            </el-col>
            <el-col :span="3">
              <el-checkbox v-model="contact.is_primary" :true-value="1" :false-value="0" size="small">主要</el-checkbox>
            </el-col>
            <el-col :span="1">
              <el-button type="danger" :icon="Delete" circle size="small" @click="removeContact(index)" />
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" link :icon="Plus" @click="addContact">添加联系人</el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="客户详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="客户名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="区域">{{ detailData.region }}</el-descriptions-item>
        <el-descriptions-item label="信用等级">
          <el-tag :type="creditLevelType(detailData.credit_level)" size="small">{{ detailData.credit_level }}级</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="业务联系人">{{ detailData.business_contact }}</el-descriptions-item>
        <el-descriptions-item label="注册地址" :span="2">{{ detailData.registered_addr }}</el-descriptions-item>
        <el-descriptions-item label="联系地址" :span="2">{{ detailData.contact_addr }}</el-descriptions-item>
        <el-descriptions-item label="开票信息" :span="2">{{ detailData.billing_info }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="detailData.contacts?.length" class="mt-20">
        <div class="section-title">联系人列表</div>
        <el-table :data="detailData.contacts" size="small" border>
          <el-table-column prop="contact_type" label="类型" width="70" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="position" label="职位" width="100" />
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column prop="email" label="邮箱" min-width="160" />
          <el-table-column label="主要" width="60" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_primary ? 'success' : 'info'" size="small">{{ row.is_primary ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 导入Excel弹窗 -->
    <el-dialog v-model="importDialogVisible" title="批量导入客户" width="500px">
      <div class="import-tips">
        <p>请上传 Excel 文件（.xlsx / .xls），表头需包含以下列：</p>
        <el-tag size="small" effect="plain" style="margin: 2px">客户名称（必填）</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">区域</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">注册地址</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">联系地址</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">开票信息</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">业务联系人</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">信用等级</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">联系人姓名</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">联系人电话</el-tag>
        <el-tag size="small" effect="plain" style="margin: 2px">联系人邮箱</el-tag>
      </div>
      <el-upload
        ref="importUploadRef"
        :action="importUploadUrl"
        :headers="importUploadHeaders"
        :show-file-list="false"
        :before-upload="beforeImportUpload"
        :on-success="handleImportSuccess"
        :on-error="handleImportError"
        :accept="'.xlsx,.xls'"
        drag
        style="margin-top: 16px"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将 Excel 文件拖到此处，或<em>点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Download, Upload, View, Edit, Delete, UploadFilled } from '@element-plus/icons-vue'
import { getCustomerList, getCustomerDetail, createCustomer, updateCustomer, deleteCustomer, exportCustomers } from '@/api/customer'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const submitLoading = ref(false)
const exportLoading = ref(false)
const importDialogVisible = ref(false)
const importUploadRef = ref(null)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const detailData = ref({})

const searchForm = reactive({
  region: '',
  name: '',
  creditLevel: ''
})

const form = reactive({
  name: '',
  region: '',
  credit_level: 'A',
  business_contact: '',
  registered_addr: '',
  contact_addr: '',
  billing_info: '',
  contacts: []
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const dialogTitle = computed(() => isEdit.value ? '编辑客户' : '新增客户')

const importUploadUrl = '/api/customer/import'
const importUploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))

const formRules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  region: [{ required: true, message: '请输入区域', trigger: 'blur' }],
  credit_level: [{ required: true, message: '请选择信用等级', trigger: 'change' }]
}

function creditLevelType(level) {
  const map = { 'A': 'success', 'B': 'primary', 'C': 'warning', 'D': 'danger' }
  return map[level] || 'info'
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

function addContact() {
  form.contacts.push({ contact_type: '商务', name: '', position: '', phone: '', email: '', is_primary: 0 })
}

function removeContact(index) {
  form.contacts.splice(index, 1)
}

async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      region: searchForm.region || undefined,
      name: searchForm.name || undefined,
      credit_level: searchForm.creditLevel || undefined
    }
    const res = await getCustomerList(params)
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
  searchForm.region = ''
  searchForm.name = ''
  searchForm.creditLevel = ''
  handleSearch()
}

function handleAdd() {
  isEdit.value = false
  editId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleView(row) {
  getCustomerDetail(row.id).then(res => {
    detailData.value = res.data || row
    detailVisible.value = true
  }).catch(() => {
    detailData.value = row
    detailVisible.value = true
  })
}

function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  getCustomerDetail(row.id).then(res => {
    const data = res.data || row
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) form[key] = data[key]
    })
    if (!form.contacts?.length) form.contacts = []
    dialogVisible.value = true
  }).catch(() => {
    Object.keys(form).forEach(key => {
      if (row[key] !== undefined) form[key] = row[key]
    })
    if (!form.contacts?.length) form.contacts = []
    dialogVisible.value = true
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除客户「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteCustomer(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // canceled
  }
}

function resetForm() {
  form.name = ''
  form.region = ''
  form.credit_level = 'A'
  form.business_contact = ''
  form.registered_addr = ''
  form.contact_addr = ''
  form.billing_info = ''
  form.contacts = []
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
      await updateCustomer(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createCustomer(data)
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

async function handleExport() {
  exportLoading.value = true
  try {
    const params = {
      region: searchForm.region || undefined,
      name: searchForm.name || undefined,
      credit_level: searchForm.creditLevel || undefined
    }
    const res = await exportCustomers(params)
    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `客户列表_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    // handled by interceptor
  } finally {
    exportLoading.value = false
  }
}

function beforeImportUpload(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['xlsx', 'xls'].includes(ext)) {
    ElMessage.error('仅支持 .xlsx / .xls 格式')
    return false
  }
  return true
}

function handleImportSuccess(response) {
  const data = response.data || response
  ElMessage.success(data.message || `导入成功: ${data.success_count || 0} 条`)
  if (data.error_rows?.length) {
    ElMessage.warning(`部分行导入失败: ${data.error_rows.join('; ')}`)
  }
  importDialogVisible.value = false
  fetchData()
}

function handleImportError() {
  ElMessage.error('导入失败，请检查文件格式')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.contact-row {
  margin-bottom: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.table-total {
  color: #909399;
  font-size: 13px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.mt-20 {
  margin-top: 20px;
}
</style>
