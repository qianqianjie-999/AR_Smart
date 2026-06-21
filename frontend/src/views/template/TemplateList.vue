<template>
  <div class="template-container">
    <h2 class="page-title">催款模板管理</h2>

    <!-- 表格 -->
    <div class="table-container">
      <div class="table-header">
        <span class="table-title">模板列表</span>
        <div>
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增模板</el-button>
        </div>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="模板名称" min-width="160" />
        <el-table-column prop="template_type" label="模板类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.template_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="默认" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_default ? 'success' : 'info'" size="small">{{ row.is_default ? '默认' : '普通' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" link :icon="View" @click="handleView(row)">预览</el-button>
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
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
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
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px" class="dialog-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入模板名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模板类型" prop="template_type">
              <el-select v-model="form.template_type" style="width: 100%">
                <el-option v-for="t in templateTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="默认模板">
          <el-switch v-model="form.is_default" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="邮件标题" prop="subject">
          <el-input v-model="form.subject" placeholder="请输入模板标题，支持变量 {{客户名称}}" />
        </el-form-item>
        <el-form-item label="模板内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="10" placeholder="请输入模板内容，支持变量：{{客户名称}}、{{合同名称}}、{{欠款金额}}、{{逾期天数}}、{{日期}}、{{联系人}}、{{联系电话}}" />
        </el-form-item>
        <div class="variable-hint">
          <span class="hint-label">可用变量：</span>
          <el-tag v-for="v in variables" :key="v" size="small" effect="plain" style="margin: 2px; cursor: pointer" @click="insertVariable(v)">{{ v }}</el-tag>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewVisible" title="模板预览" width="600px">
      <div class="preview-content">
        <h3 class="preview-subject">{{ previewData.subject }}</h3>
        <div class="preview-body" v-html="previewContent"></div>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import { getTemplateList, getTemplateDetail, createTemplate, updateTemplate, deleteTemplate, getTemplateTypes } from '@/api/template'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const previewVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEdit = ref(false)
const editId = ref(null)
const previewData = ref({})
const templateTypes = ref(['催款函', '律师函', '对账单', '提醒函', '其他'])

const variables = ['{{客户名称}}', '{{合同名称}}', '{{合同编号}}', '{{欠款金额}}', '{{逾期天数}}', '{{日期}}', '{{联系人}}', '{{联系电话}}', '{{公司名称}}']

const form = reactive({
  name: '',
  template_type: '催款函',
  is_default: 0,
  subject: '',
  content: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const dialogTitle = computed(() => isEdit.value ? '编辑模板' : '新增模板')

const previewContent = computed(() => {
  return previewData.value.content?.replace(/\n/g, '<br>') || ''
})

const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  template_type: [{ required: true, message: '请选择模板类型', trigger: 'change' }],
  subject: [{ required: true, message: '请输入邮件标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入模板内容', trigger: 'blur' }]
}

function insertVariable(v) {
  form.content = (form.content || '') + v
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getTemplateList({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleView(row) {
  getTemplateDetail(row.id).then(res => {
    previewData.value = res.data || row
    previewVisible.value = true
  }).catch(() => {
    previewData.value = row
    previewVisible.value = true
  })
}

function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  getTemplateDetail(row.id).then(res => {
    const data = res.data || row
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) form[key] = data[key]
    })
    dialogVisible.value = true
  }).catch(() => {
    Object.keys(form).forEach(key => {
      if (row[key] !== undefined) form[key] = row[key]
    })
    dialogVisible.value = true
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除模板「${row.name}」吗？`, '删除确认', { type: 'warning' })
    await deleteTemplate(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // canceled
  }
}

function resetForm() {
  form.name = ''
  form.template_type = '催款函'
  form.is_default = 0
  form.subject = ''
  form.content = ''
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
      await updateTemplate(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createTemplate(data)
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
  fetchData()
  getTemplateTypes().then(res => {
    if (res.data) templateTypes.value = res.data
  }).catch(() => {})
})
</script>

<style scoped>
.table-total {
  color: #909399;
  font-size: 13px;
}

.variable-hint {
  margin-top: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.hint-label {
  font-size: 12px;
  color: #909399;
  margin-right: 4px;
}

.preview-content {
  padding: 16px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.preview-subject {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

.preview-body {
  line-height: 2;
  white-space: pre-wrap;
}
</style>