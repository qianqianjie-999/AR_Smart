<template>
  <div>
    <div class="flex-between mb-16">
      <span></span>
      <el-button type="primary" :icon="Plus" @click="handleAdd">新增催款记录</el-button>
    </div>

    <!-- 时间线展示 -->
    <el-timeline v-if="tableData.length > 0" class="mb-20">
      <el-timeline-item
        v-for="item in tableData"
        :key="item.id"
        :timestamp="item.created_at || item.collection_date"
        placement="top"
        :color="item.is_limitation_interrupt ? '#e6a23c' : '#409eff'"
      >
        <el-card shadow="hover">
          <div class="timeline-header">
            <el-tag :type="item.is_limitation_interrupt ? 'warning' : 'primary'" size="small">
              {{ item.is_limitation_interrupt ? '已中断时效' : '普通催款' }}
            </el-tag>
            <span class="timeline-method">{{ item.collection_type }}</span>
          </div>
          <p class="timeline-content">{{ item.collection_content || item.remark || '-' }}</p>
          <div class="timeline-footer">
            <span v-if="item.express_no">EMS: {{ item.express_no }}</span>
            <span>签收: <el-tag :type="item.sign_status === '已签收' ? 'success' : 'info'" size="small">{{ item.sign_status || '待签收' }}</el-tag></span>
            <div v-if="parseFiles(item.collection_file).length" class="file-list">
              <span>附件: </span>
              <el-button link type="primary" size="small" v-for="(f, i) in parseFiles(item.collection_file)" :key="i" @click="previewFile(f)">
                文件{{ i + 1 }}
              </el-button>
            </div>
            <el-button type="primary" link @click="handleEdit(item)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(item)">删除</el-button>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无催款记录" />

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="dialog-form">
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
          <el-input v-model="form.recipient" placeholder="收件人姓名" />
        </el-form-item>
        <el-form-item label="EMS单号">
          <el-input v-model="form.express_no" placeholder="EMS快递单号" />
        </el-form-item>
        <el-form-item label="签收状态" prop="sign_status">
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
import { getCollectionList, createCollection, updateCollection, deleteCollection } from '@/api/collection'
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
  collection_type: '电话',
  collection_date: '',
  recipient: '',
  express_no: '',
  sign_status: '待签收',
  is_limitation_interrupt: 1,
  collection_content: '',
  collection_file: '[]'
})

const dialogTitle = computed(() => isEdit.value ? '编辑催款记录' : '新增催款记录')

const rules = {
  collection_type: [{ required: true, message: '请选择催款方式', trigger: 'change' }],
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

async function fetchData() {
  loading.value = true
  try {
    const res = await getCollectionList({ contract_id: props.contractId })
    tableData.value = res.data?.list || res.data?.items || res.data || []
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false; editId.value = null
  form.collection_type = '电话'; form.collection_date = ''
  form.recipient = ''; form.express_no = ''
  form.sign_status = '待签收'; form.is_limitation_interrupt = 1
  form.collection_content = ''; form.collection_file = '[]'
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true; editId.value = row.id
  Object.keys(form).forEach(key => { if (row[key] !== undefined) form[key] = row[key] })
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该催款记录吗？', '删除确认', { type: 'warning' })
    await deleteCollection(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch { /* canceled */ }
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form, contract_id: props.contractId }
    if (isEdit.value) { await updateCollection(editId.value, data); ElMessage.success('更新成功') }
    else { await createCollection(data); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ }
  finally { submitLoading.value = false }
}

fetchData()
</script>

<style scoped>
.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.timeline-method {
  font-weight: 600;
  color: #333;
}
.timeline-content {
  margin: 8px 0;
  color: #666;
  line-height: 1.6;
}
.timeline-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #999;
}
</style>
