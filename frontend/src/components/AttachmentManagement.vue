<template>
  <div class="attachment-management">
    <!-- 顶部概览 -->
    <div class="overview-row">
      <div class="overview-card overview-primary">
        <div class="overview-icon"><el-icon :size="26"><FolderOpened /></el-icon></div>
        <div class="overview-content">
          <div class="overview-label">附件总数</div>
          <div class="overview-value">{{ totalCount }}</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon small"><el-icon><Document /></el-icon></div>
        <div class="overview-content small">
          <div class="overview-label">合同文件</div>
          <div class="overview-value small">{{ groupStats.contract }}</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon small success"><el-icon><CircleCheck /></el-icon></div>
        <div class="overview-content small">
          <div class="overview-label">验收资料</div>
          <div class="overview-value small">{{ groupStats.acceptance }}</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon small warning"><el-icon><Money /></el-icon></div>
        <div class="overview-content small">
          <div class="overview-label">结算资料</div>
          <div class="overview-value small">{{ groupStats.settlement }}</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon small info"><el-icon><Tickets /></el-icon></div>
        <div class="overview-content small">
          <div class="overview-label">发票附件</div>
          <div class="overview-value small">{{ groupStats.invoice }}</div>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon small danger"><el-icon><BellFilled /></el-icon></div>
        <div class="overview-content small">
          <div class="overview-label">催款函附件</div>
          <div class="overview-value small">{{ groupStats.collection }}</div>
        </div>
      </div>
    </div>

    <!-- 卡片网格：合同附件组 -->
    <div class="category-grid">
      <!-- 合同文件 -->
      <div class="category-card">
        <div class="card-header card-header-blue">
          <div class="card-title-block">
            <div class="card-title"><el-icon><Document /></el-icon> 合同文件</div>
            <div class="card-subtitle">如合同扫描件、补充协议等</div>
          </div>
          <div class="card-action">
            <span class="count-badge">{{ fileGroups.contract.length }} 个文件</span>
          </div>
        </div>
        <div class="card-body">
          <div class="file-list" v-if="fileGroups.contract.length">
            <div v-for="(f, i) in fileGroups.contract" :key="i" class="file-item">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-info">
                <div class="file-name" :title="f.name">{{ f.name }}</div>
              </div>
              <div class="file-actions">
                <button class="icon-btn" @click="handlePreview(f)" title="预览">
                  <el-icon><ZoomIn /></el-icon>
                </button>
                <button v-if="!readonly" class="icon-btn danger" @click="handleDelete('contract', i)" title="删除">
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无文件，点击下方按钮上传" :image-size="60" />
        </div>
        <div class="card-footer" v-if="!readonly">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :multiple="true"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :on-success="(response) => handleUploadSuccess('contract', response)"
            :on-error="handleUploadError"
          >
            <el-button type="primary" :icon="Plus" :loading="uploadingMap.contract">上传附件</el-button>
            <template #tip>
              <div class="upload-tip">支持 PDF、Word、Excel、图片等格式，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </div>
      </div>

      <!-- 验收资料 -->
      <div class="category-card">
        <div class="card-header card-header-green">
          <div class="card-title-block">
            <div class="card-title"><el-icon><CircleCheck /></el-icon> 验收资料</div>
            <div class="card-subtitle">竣工验收单、验收报告</div>
          </div>
          <div class="card-action">
            <span class="count-badge">{{ fileGroups.acceptance.length }} 个文件</span>
          </div>
        </div>
        <div class="card-body">
          <div class="file-list" v-if="fileGroups.acceptance.length">
            <div v-for="(f, i) in fileGroups.acceptance" :key="i" class="file-item">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-info">
                <div class="file-name" :title="f.name">{{ f.name }}</div>
              </div>
              <div class="file-actions">
                <button class="icon-btn" @click="handlePreview(f)" title="预览">
                  <el-icon><ZoomIn /></el-icon>
                </button>
                <button v-if="!readonly" class="icon-btn danger" @click="handleDelete('acceptance', i)" title="删除">
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无文件，点击下方按钮上传" :image-size="60" />
        </div>
        <div class="card-footer" v-if="!readonly">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :multiple="true"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :on-success="(response) => handleUploadSuccess('acceptance', response)"
            :on-error="handleUploadError"
          >
            <el-button type="primary" :icon="Plus" :loading="uploadingMap.acceptance">上传附件</el-button>
            <template #tip>
              <div class="upload-tip">支持 PDF、Word、Excel、图片等格式，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </div>
      </div>

      <!-- 结算资料 -->
      <div class="category-card">
        <div class="card-header card-header-orange">
          <div class="card-title-block">
            <div class="card-title"><el-icon><Money /></el-icon> 结算资料</div>
            <div class="card-subtitle">结算单、审计报告、价格汇总表</div>
          </div>
          <div class="card-action">
            <span class="count-badge">{{ fileGroups.settlement.length }} 个文件</span>
          </div>
        </div>
        <div class="card-body">
          <div class="file-list" v-if="fileGroups.settlement.length">
            <div v-for="(f, i) in fileGroups.settlement" :key="i" class="file-item">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-info">
                <div class="file-name" :title="f.name">{{ f.name }}</div>
              </div>
              <div class="file-actions">
                <button class="icon-btn" @click="handlePreview(f)" title="预览">
                  <el-icon><ZoomIn /></el-icon>
                </button>
                <button v-if="!readonly" class="icon-btn danger" @click="handleDelete('settlement', i)" title="删除">
                  <el-icon><Delete /></el-icon>
                </button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无文件，点击下方按钮上传" :image-size="60" />
        </div>
        <div class="card-footer" v-if="!readonly">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            :multiple="true"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :on-success="(response) => handleUploadSuccess('settlement', response)"
            :on-error="handleUploadError"
          >
            <el-button type="primary" :icon="Plus" :loading="uploadingMap.settlement">上传附件</el-button>
            <template #tip>
              <div class="upload-tip">支持 PDF、Word、Excel、图片等格式，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </div>
      </div>
    </div>

    <!-- 发票 + 催款函（横向并排） -->
    <div class="record-row">
      <!-- 发票附件区域 -->
      <div class="section-wrapper section-half">
        <div class="section-title section-title-info">
          <el-icon><Tickets /></el-icon>
          <span>发票附件</span>
          <el-tag size="small" type="info" effect="dark" round>{{ groupStats.invoice }} 个文件</el-tag>
        </div>

        <div v-if="invoiceFiles.length" class="record-grid-single">
          <div v-for="(item, idx) in invoiceFiles" :key="item.id" class="record-card">
            <div class="record-header record-header-info">
              <div class="record-title">发票 #{{ item.invoice_no }}</div>
              <el-tag size="small" type="info" effect="light">{{ item.files.length }} 个文件</el-tag>
            </div>
            <div class="record-date" v-if="item.invoice_date">开票日期：{{ item.invoice_date }}</div>
            <div class="record-body">
              <div v-for="(f, i) in item.files" :key="i" class="file-item">
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-info">
                  <div class="file-name" :title="f.name">{{ f.name }}</div>
                </div>
                <div class="file-actions">
                  <button class="icon-btn" @click="handlePreview(f)" title="预览">
                    <el-icon><ZoomIn /></el-icon>
                  </button>
                  <button v-if="!readonly" class="icon-btn danger" @click="handleInvoiceDelete(item.id, i)" title="删除">
                    <el-icon><Delete /></el-icon>
                  </button>
                </div>
              </div>
            </div>
            <div class="record-footer" v-if="!readonly">
              <el-upload
                :action="uploadUrl"
                :headers="uploadHeaders"
                :multiple="true"
                :show-file-list="false"
                :before-upload="handleBeforeUpload"
                :on-success="(response) => handleInvoiceUpload(item.id, response)"
                :on-error="handleUploadError"
              >
                <el-button type="primary" :icon="Plus" size="small">上传附件</el-button>
                <template #tip>
                  <div class="upload-tip">支持 PDF、Word、Excel、图片等格式</div>
                </template>
              </el-upload>
            </div>
          </div>
        </div>
        <div v-else class="empty-box">
          <el-empty description="暂无发票附件" :image-size="80" />
        </div>
      </div>

      <!-- 催款函附件区域 -->
      <div class="section-wrapper section-half">
        <div class="section-title section-title-danger">
          <el-icon><BellFilled /></el-icon>
          <span>催款函附件</span>
          <el-tag size="small" type="danger" effect="dark" round>{{ groupStats.collection }} 个文件</el-tag>
        </div>

        <div v-if="collectionFiles.length" class="record-grid-single">
          <div v-for="(item, idx) in collectionFiles" :key="item.id" class="record-card">
            <div class="record-header record-header-danger">
              <div class="record-title">{{ item.collection_type }}</div>
              <el-tag size="small" type="danger" effect="light">{{ item.files.length }} 个文件</el-tag>
            </div>
            <div class="record-date" v-if="item.collection_date">催款日期：{{ item.collection_date }}</div>
            <div class="record-body">
              <div v-for="(f, i) in item.files" :key="i" class="file-item">
                <el-icon class="file-icon"><Document /></el-icon>
                <div class="file-info">
                  <div class="file-name" :title="f.name">{{ f.name }}</div>
                </div>
                <div class="file-actions">
                  <button class="icon-btn" @click="handlePreview(f)" title="预览">
                    <el-icon><ZoomIn /></el-icon>
                  </button>
                  <button v-if="!readonly" class="icon-btn danger" @click="handleCollectionDelete(item.id, i)" title="删除">
                    <el-icon><Delete /></el-icon>
                  </button>
                </div>
              </div>
            </div>
            <div class="record-footer" v-if="!readonly">
              <el-upload
                :action="uploadUrl"
                :headers="uploadHeaders"
                :multiple="true"
                :show-file-list="false"
                :before-upload="handleBeforeUpload"
                :on-success="(response) => handleCollectionUpload(item.id, response)"
                :on-error="handleUploadError"
              >
                <el-button type="primary" :icon="Plus" size="small">上传附件</el-button>
                <template #tip>
                  <div class="upload-tip">支持 PDF、Word、Excel、图片等格式</div>
                </template>
              </el-upload>
            </div>
          </div>
        </div>
        <div v-else class="empty-box">
          <el-empty description="暂无催款函附件" :image-size="80" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Document, FolderOpened, CircleCheck, Money, Tickets,
  BellFilled, ZoomIn, Delete, Plus
} from '@element-plus/icons-vue'
import { getContractDetail, updateContract } from '@/api/contract'
import { getInvoiceList, updateInvoice } from '@/api/invoice'
import { getCollectionList, updateCollection } from '@/api/collection'

const props = defineProps({
  contractId: { type: [String, Number], required: true },
  readonly: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh'])

const contractInfo = ref({})
const invoiceRecords = ref([])
const collectionRecords = ref([])

// 通用上传相关
const uploadUrl = '/api/upload/'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))
const uploadingMap = ref({
  contract: false,
  acceptance: false,
  settlement: false
})

function handleBeforeUpload(file) {
  const maxSize = 10
  const isLt = file.size / 1024 / 1024 < maxSize
  if (!isLt) {
    ElMessage.error(`文件大小不能超过 ${maxSize}MB`)
    return false
  }
  return true
}

function parseUploadResponse(response) {
  const data = response.data || response
  let newFiles = []
  if (Array.isArray(data) && data.length > 0) {
    newFiles = data.map(d => ({ url: d.url || d.filename, name: d.original_name || d.filename }))
  } else if (data.url || data.filename) {
    newFiles = [{ url: data.url || data.filename, name: data.original_name || data.filename }]
  }
  return newFiles
}

async function handleUploadSuccess(group, response) {
  const newFiles = parseUploadResponse(response)
  if (!newFiles.length) return
  await handleUpload(group, newFiles)
}

function handleUploadError() {
  ElMessage.error('上传失败，请重试')
}

// 解析文件字段
function parseFiles(val) {
  if (!val) return []
  if (Array.isArray(val)) return val.map(v => typeof v === 'string' ? { url: v, name: v.split('/').pop() } : v)
  try {
    const parsed = JSON.parse(val)
    if (Array.isArray(parsed)) {
      return parsed.map(f => ({
        url: f.url || f.filename || f,
        name: f.name || (f.url || f.filename || f).split('/').pop()
      }))
    }
    return [{ url: val, name: val.split('/').pop() }]
  } catch {
    return [{ url: val, name: val.split('/').pop() }]
  }
}

function serializeFiles(files) {
  return JSON.stringify(files.map(f => ({ url: f.url, name: f.name })))
}

// 合同附件分组
const fileGroups = computed(() => ({
  contract: parseFiles(contractInfo.value.contract_file || ''),
  acceptance: parseFiles(contractInfo.value.acceptance_file || ''),
  settlement: parseFiles(contractInfo.value.settlement_file || '')
}))

// 发票附件按记录分组
const invoiceFiles = computed(() => {
  return invoiceRecords.value
    .map(item => ({
      id: item.id,
      invoice_no: item.invoice_no,
      invoice_date: item.invoice_date || '',
      files: parseFiles(item.invoice_file || '')
    }))
    .filter(item => item.files.length > 0)
})

// 催款函附件按记录分组
const collectionFiles = computed(() => {
  return collectionRecords.value
    .map(item => ({
      id: item.id,
      collection_type: item.collection_type || '电话',
      collection_date: item.collection_date || '',
      files: parseFiles(item.collection_file || '')
    }))
    .filter(item => item.files.length > 0)
})

// 统计
const groupStats = computed(() => ({
  contract: fileGroups.value.contract.length,
  acceptance: fileGroups.value.acceptance.length,
  settlement: fileGroups.value.settlement.length,
  invoice: invoiceFiles.value.reduce((sum, item) => sum + item.files.length, 0),
  collection: collectionFiles.value.reduce((sum, item) => sum + item.files.length, 0)
}))

const totalCount = computed(() => {
  return groupStats.value.contract +
    groupStats.value.acceptance +
    groupStats.value.settlement +
    groupStats.value.invoice +
    groupStats.value.collection
})

// 加载数据
async function loadData() {
  try {
    const [contractRes, invoiceRes, collectionRes] = await Promise.all([
      getContractDetail(props.contractId),
      getInvoiceList({ contract_id: props.contractId, page: 1, page_size: 999 }),
      getCollectionList({ contract_id: props.contractId, page: 1, page_size: 999 })
    ])
    contractInfo.value = contractRes.data || {}
    invoiceRecords.value = invoiceRes.data?.list || invoiceRes.data?.items || []
    collectionRecords.value = collectionRes.data?.list || collectionRes.data?.items || []
  } catch (err) {
    // error handled globally
  }
}

// 预览文件
function handlePreview(file) {
  const url = file.url
  if (!url) return
  const token = localStorage.getItem('token') || ''
  const fullUrl = url.startsWith('/api/') || url.startsWith('http') ? url : `/api/upload/${url}`
  const separator = fullUrl.includes('?') ? '&' : '?'
  window.open(`${fullUrl}${separator}token=${encodeURIComponent(token)}`, '_blank')
}

// 上传合同/验收/结算附件（主合同级别）
async function handleUpload(group, newFiles) {
  const fieldMap = {
    contract: 'contract_file',
    acceptance: 'acceptance_file',
    settlement: 'settlement_file'
  }
  const field = fieldMap[group]
  const currentFiles = fileGroups.value[group]
  const updated = [...currentFiles, ...newFiles]
  const serialized = serializeFiles(updated)

  try {
    await updateContract(props.contractId, { [field]: serialized })
    ElMessage.success('上传成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

async function handleDelete(group, index) {
  const fieldMap = {
    contract: 'contract_file',
    acceptance: 'acceptance_file',
    settlement: 'settlement_file'
  }
  const field = fieldMap[group]
  const currentFiles = fileGroups.value[group]
  const updated = currentFiles.filter((_, i) => i !== index)
  const serialized = serializeFiles(updated)

  try {
    await updateContract(props.contractId, { [field]: serialized })
    ElMessage.success('删除成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

// 上传/删除发票附件
async function handleInvoiceUpload(invoiceId, response) {
  const newFiles = parseUploadResponse(response)
  if (!newFiles.length) return
  const record = invoiceRecords.value.find(r => r.id === invoiceId)
  if (!record) return
  const currentFiles = parseFiles(record.invoice_file || '')
  const updated = [...currentFiles, ...newFiles]
  const serialized = serializeFiles(updated)

  try {
    await updateInvoice(invoiceId, { invoice_file: serialized })
    ElMessage.success('上传成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

async function handleInvoiceDelete(invoiceId, index) {
  const record = invoiceRecords.value.find(r => r.id === invoiceId)
  if (!record) return
  const currentFiles = parseFiles(record.invoice_file || '')
  const updated = currentFiles.filter((_, i) => i !== index)
  const serialized = serializeFiles(updated)

  try {
    await updateInvoice(invoiceId, { invoice_file: serialized })
    ElMessage.success('删除成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

// 上传/删除催款函附件
async function handleCollectionUpload(collectionId, response) {
  const newFiles = parseUploadResponse(response)
  if (!newFiles.length) return
  const record = collectionRecords.value.find(r => r.id === collectionId)
  if (!record) return
  const currentFiles = parseFiles(record.collection_file || '')
  const updated = [...currentFiles, ...newFiles]
  const serialized = serializeFiles(updated)

  try {
    await updateCollection(collectionId, { collection_file: serialized })
    ElMessage.success('上传成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

async function handleCollectionDelete(collectionId, index) {
  const record = collectionRecords.value.find(r => r.id === collectionId)
  if (!record) return
  const currentFiles = parseFiles(record.collection_file || '')
  const updated = currentFiles.filter((_, i) => i !== index)
  const serialized = serializeFiles(updated)

  try {
    await updateCollection(collectionId, { collection_file: serialized })
    ElMessage.success('删除成功')
    await loadData()
    emit('refresh')
  } catch { /* handled */ }
}

onMounted(() => {
  loadData()
})

watch(() => props.contractId, () => {
  loadData()
})
</script>

<style scoped>
.attachment-management {
  padding: 0;
  background: #eef2f7;
  border-radius: 0 0 8px 8px;
}

/* 顶部概览 */
.overview-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #dcdfe6;
}

.overview-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #dcdfe6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.overview-card.overview-primary {
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 60%, #60a5fa 100%);
  color: #fff;
  border: none;
  padding: 18px;
  box-shadow: 0 4px 14px rgba(29, 78, 216, 0.35);
}

.overview-card.overview-primary .overview-icon {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.overview-card.overview-primary .overview-label {
  color: rgba(255, 255, 255, 0.92);
}

.overview-card.overview-primary .overview-value {
  color: #fff;
}

.overview-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: #dbeafe;
  color: #1e40af;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.overview-icon.small { width: 36px; height: 36px; border-radius: 6px; font-size: 16px; }
.overview-icon.small.success { background: #dcfce7; color: #166534; }
.overview-icon.small.warning { background: #fef3c7; color: #92400e; }
.overview-icon.small.info { background: #e5e7eb; color: #374151; }
.overview-icon.small.danger { background: #fee2e2; color: #991b1b; }

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.overview-content.small {
  gap: 0;
}

.overview-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.overview-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.overview-value.small {
  font-size: 18px;
  font-weight: 700;
}

/* 类别卡片网格 */
.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 0 24px 16px;
}

.category-card {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #dcdfe6;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s, transform 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.category-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.card-header {
  padding: 16px 18px;
  border-bottom: 2px solid;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-blue {
  background: linear-gradient(to right, #dbeafe 0%, #eff6ff 40%, #fff 100%);
  border-bottom-color: #3b82f6;
}

.card-header-green {
  background: linear-gradient(to right, #dcfce7 0%, #f0fdf4 40%, #fff 100%);
  border-bottom-color: #16a34a;
}

.card-header-orange {
  background: linear-gradient(to right, #fef3c7 0%, #fffbeb 40%, #fff 100%);
  border-bottom-color: #d97706;
}

.card-title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-header-blue .card-title { color: #1e40af; }
.card-header-green .card-title { color: #166534; }
.card-header-orange .card-title { color: #92400e; }

.card-subtitle {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.count-badge {
  background: rgba(0, 0, 0, 0.06);
  color: #111827;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.card-header-blue .count-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #1e40af;
  border-color: rgba(59, 130, 246, 0.25);
}

.card-header-green .count-badge {
  background: rgba(22, 163, 74, 0.15);
  color: #166534;
  border-color: rgba(22, 163, 74, 0.25);
}

.card-header-orange .count-badge {
  background: rgba(217, 119, 6, 0.15);
  color: #92400e;
  border-color: rgba(217, 119, 6, 0.25);
}

.card-body {
  flex: 1;
  padding: 14px 16px;
  min-height: 120px;
  max-height: 280px;
  overflow-y: auto;
  background: #fff;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  transition: background 0.15s;
  border: 1px solid #e5e7eb;
}

.file-item:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.file-icon {
  color: #2563eb;
  font-size: 18px;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  color: #111827;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 14px;
}

.icon-btn:hover {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.icon-btn.danger:hover {
  background: #dc2626;
  border-color: #dc2626;
  color: #fff;
}

.card-footer {
  padding: 12px 16px 16px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

/* 横向并排容器 */
.record-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 0 24px 24px;
}

/* 记录区（发票/催款函） */
.section-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 18px 20px 20px;
  border: 1px solid #dcdfe6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;
}

.section-wrapper:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.section-half {
  display: flex;
  flex-direction: column;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px 14px;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  border-bottom: 2px solid #374151;
  margin-bottom: 16px;
}

.section-title .el-icon {
  color: #374151;
  font-size: 18px;
}

.section-title-info {
  border-bottom-color: #2563eb;
}

.section-title-info .el-icon {
  color: #2563eb;
}

.section-title-danger {
  border-bottom-color: #dc2626;
}

.section-title-danger .el-icon {
  color: #dc2626;
}

.record-grid-single {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-card {
  background: #fff;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.record-card:hover {
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.record-header {
  padding: 14px 16px;
  background: #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #d1d5db;
}

.record-header-info {
  background: linear-gradient(to right, #dbeafe 0%, #eff6ff 50%, #fff 100%);
  border-bottom-color: #2563eb;
}

.record-header-danger {
  background: linear-gradient(to right, #fee2e2 0%, #fef2f2 50%, #fff 100%);
  border-bottom-color: #dc2626;
}

.record-title {
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.record-date {
  padding: 8px 16px;
  font-size: 12px;
  color: #4b5563;
  background: #fff;
  border-bottom: 1px dashed #d1d5db;
  font-weight: 500;
}

.record-body {
  padding: 12px 16px;
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #fff;
}

.record-footer {
  padding: 10px 16px 16px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.empty-box {
  background: #fff;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 30px;
}

.empty-box :deep(.el-empty__description) {
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
}

/* 上传提示 */
.upload-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 8px;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 1400px) {
  .overview-row {
    grid-template-columns: repeat(3, 1fr);
  }
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1100px) {
  .record-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .overview-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .category-grid,
  .record-grid,
  .record-grid-single {
    grid-template-columns: 1fr;
  }
}
</style>
