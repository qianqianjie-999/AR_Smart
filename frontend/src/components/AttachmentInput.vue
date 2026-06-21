<template>
  <div class="attachment-input">
    <el-upload
      ref="uploadRef"
      v-model:file-list="fileList"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :multiple="true"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :disabled="disabled"
      :accept="acceptStr"
    >
      <el-button :disabled="disabled" :icon="Upload" :loading="uploading">
        {{ uploading ? '上传中...' : '上传附件' }}
      </el-button>
    </el-upload>

    <div v-if="files.length" class="attachment-files">
      <div v-for="(f, idx) in files" :key="idx" class="attachment-item">
        <el-tag type="success" size="small" effect="plain" class="attachment-tag">
          <el-icon><Document /></el-icon>
          {{ getFileName(f.url || f.filename || f) }}
        </el-tag>
        <el-button link type="primary" size="small" :icon="View" @click="previewFile(f)">预览</el-button>
        <el-button link type="danger" size="small" :icon="Delete" :disabled="disabled" @click="removeFile(idx)">移除</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { View, Upload, Delete, Document } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: [String, Array], default: '' },
  disabled: { type: Boolean, default: false },
  maxSize: { type: Number, default: 10 },
  accept: { type: Array, default: () => ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'] }
})

const emit = defineEmits(['update:modelValue'])

const uploadRef = ref(null)
const uploading = ref(false)
const fileList = ref([])

const uploadUrl = '/api/upload/'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))
const acceptStr = computed(() => props.accept.join(','))

const files = computed(() => {
  if (!props.modelValue) return []
  if (Array.isArray(props.modelValue)) return props.modelValue
  try {
    const parsed = JSON.parse(props.modelValue)
    return Array.isArray(parsed) ? parsed : [{ url: props.modelValue }]
  } catch {
    return [{ url: props.modelValue }]
  }
})

function emitUpdate(arr) {
  emit('update:modelValue', JSON.stringify(arr))
}

function getFileName(path) {
  if (!path) return ''
  const parts = String(path).split('/')
  return parts[parts.length - 1] || path
}

function resolveUrl(raw) {
  const url = typeof raw === 'object' ? (raw.url || raw.filename) : raw
  if (!url) return ''
  if (url.startsWith('/api/') || url.startsWith('http')) return url
  return `/api/upload/${url}`
}

function isImageFile(path) {
  if (!path) return false
  const ext = String(path).split('.').pop()?.toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)
}

function previewFile(f) {
  const url = resolveUrl(f)
  if (!url) return

  if (isImageFile(url)) {
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(`
        <html><head><title>图片预览</title>
        <style>body{margin:0;display:flex;justify-content:center;align-items:center;min-height:100vh;background:#1a1a1a}
        img{max-width:100%;max-height:100vh;object-fit:contain}</style></head>
        <body><img src="${url}" onerror="this.parentElement.innerHTML='<p style=color:#fff>加载失败</p>'" /></body></html>
      `)
    }
  } else {
    const token = localStorage.getItem('token') || ''
    const separator = url.includes('?') ? '&' : '?'
    window.open(`${url}${separator}token=${encodeURIComponent(token)}`, '_blank')
  }
}

function beforeUpload(file) {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (props.accept.length && !props.accept.includes(ext)) {
    ElMessage.error(`不支持的文件类型: ${ext}，仅支持 ${props.accept.join(', ')}`)
    return false
  }
  const isLt = file.size / 1024 / 1024 < props.maxSize
  if (!isLt) {
    ElMessage.error(`文件大小不能超过 ${props.maxSize}MB`)
    return false
  }
  uploading.value = true
  return true
}

function handleUploadSuccess(response) {
  uploading.value = false
  const data = response.data || response
  let newFiles = []
  if (Array.isArray(data) && data.length > 0) {
    newFiles = data.map(d => ({ url: d.url || d.filename, name: d.original_name || d.filename }))
  } else if (data.url || data.filename) {
    newFiles = [{ url: data.url || data.filename, name: data.original_name || data.filename }]
  }
  if (newFiles.length) {
    const updated = [...files.value, ...newFiles]
    emitUpdate(updated)
    ElMessage.success(`上传成功: ${newFiles.length} 个文件`)
  }
}

function handleUploadError() {
  uploading.value = false
  ElMessage.error('上传失败，请重试')
}

function removeFile(idx) {
  const updated = files.value.filter((_, i) => i !== idx)
  emitUpdate(updated)
}
</script>

<style scoped>
.attachment-input {
  width: 100%;
}

.attachment-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.attachment-tag {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
