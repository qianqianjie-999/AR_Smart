<template>
  <div class="file-upload-container">
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :on-success="handleSuccess"
      :on-error="handleError"
      :on-remove="handleRemove"
      :before-upload="beforeUpload"
      :file-list="fileList"
      :multiple="multiple"
      :disabled="disabled"
      drag
      list-type="text"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          上传文件大小不超过 {{ maxSize }}MB，支持 {{ allowedTypes.join(', ') }} 格式
        </div>
      </template>
    </el-upload>

    <!-- 文件预览列表 -->
    <div v-if="fileList.length > 0" class="preview-list">
      <div class="preview-header">已上传文件 ({{ fileList.length }})</div>
      <div v-for="(file, index) in fileList" :key="file.uid || index" class="preview-item">
        <el-icon><Document /></el-icon>
        <span class="preview-name">{{ file.name }}</span>
        <el-button link type="primary" size="small" :icon="View" @click="previewFile(file)">预览</el-button>
        <el-button link type="danger" size="small" :icon="Delete" @click="removeFile(file)">删除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, View, Delete, Document } from '@element-plus/icons-vue'

const props = defineProps({
  contractId: { type: [String, Number], default: '' },
  files: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false },
  maxSize: { type: Number, default: 10 },
  allowedTypes: { type: Array, default: () => ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png', 'zip'] }
})

const emit = defineEmits(['upload', 'delete'])

const uploadRef = ref(null)
const fileList = ref([])

const uploadUrl = computed(() => `/api/contracts/${props.contractId}/files`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))

watch(() => props.files, (newFiles) => {
  fileList.value = (newFiles || []).map(f => ({
    name: f.name || f.filename || f.file_name || 'unknown',
    url: f.url || f.path || '',
    uid: f.id || f.uid || Date.now(),
    status: 'success'
  }))
}, { immediate: true })

function isImageFile(file) {
  const ext = (file.name || '').split('.').pop()?.toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)
}

function previewFile(file) {
  let url = file.url || file.response?.url || file.response?.data?.url || ''
  if (!url) return ElMessage.warning('无法获取文件地址')

  if (url.startsWith('/api/')) {
    url = url
  } else if (!url.startsWith('http')) {
    url = `/api/upload/${url}`
  }

  if (isImageFile(file)) {
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(`<html><head><title>图片预览</title><style>body{margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#1a1a1a}img{max-width:100%;max-height:100vh;object-fit:contain}</style></head><body><img src="${url}" onerror="this.parentElement.innerHTML='<p style=color:#fff>加载失败</p>'" /></body></html>`)
    }
  } else {
    const token = localStorage.getItem('token') || ''
    const separator = url.includes('?') ? '&' : '?'
    window.open(`${url}${separator}token=${encodeURIComponent(token)}`, '_blank')
  }
}

function removeFile(file) {
  const idx = fileList.value.findIndex(f => f.uid === file.uid)
  if (idx > -1) {
    fileList.value.splice(idx, 1)
    emit('delete', idx)
  }
}

function beforeUpload(file) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (props.allowedTypes.length && !props.allowedTypes.includes(ext)) {
    ElMessage.error(`不支持的文件类型: .${ext}，仅支持 ${props.allowedTypes.join(', ')}`)
    return false
  }
  const isLt = file.size / 1024 / 1024 < props.maxSize
  if (!isLt) {
    ElMessage.error(`文件大小不能超过 ${props.maxSize}MB`)
    return false
  }
  return true
}

function handleSuccess(response, file) {
  ElMessage.success(`${file.name} 上传成功`)
  emit('upload', response.data || response)
}

function handleError(error, file) {
  ElMessage.error(`${file.name} 上传失败`)
}

function handleRemove(file) {
  const idx = fileList.value.findIndex(f => f.uid === file.uid)
  if (idx > -1) {
    fileList.value.splice(idx, 1)
    emit('delete', idx)
  }
}
</script>

<style scoped>
.file-upload-container {
  padding: 10px 0;
}

.preview-list {
  margin-top: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.preview-header {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  color: #606266;
}

.preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
