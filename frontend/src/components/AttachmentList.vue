<template>
  <div class="attachment-list">
    <!-- 上传按钮 -->
    <div v-if="!readonly" class="upload-area">
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :multiple="true"
        :show-file-list="false"
        :before-upload="handleBeforeUpload"
        :on-success="handleSuccess"
        :on-error="handleError"
        :accept="acceptStr"
      >
        <el-button type="primary" :icon="Plus" :loading="uploading">上传附件</el-button>
        <template #tip>
          <div class="upload-tip">支持 PDF、Word、Excel、图片等格式，单个文件不超过 10MB</div>
        </template>
      </el-upload>
    </div>

    <!-- 文件列表 -->
    <div v-if="files.length" class="file-list">
      <div v-for="(file, idx) in files" :key="idx" class="file-item">
        <el-icon class="file-icon"><Document /></el-icon>
        <span class="file-name" :title="file.name || file.url">{{ file.name || file.url }}</span>
        <span class="file-actions">
          <el-button link type="primary" size="small" :icon="View" @click="$emit('preview', file)">预览</el-button>
          <el-button v-if="!readonly" link type="danger" size="small" :icon="Delete" @click="handleDelete(idx)">删除</el-button>
        </span>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="暂无附件" :image-size="80" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, View, Delete, Document } from '@element-plus/icons-vue'

const props = defineProps({
  files: { type: Array, default: () => [] },
  readonly: { type: Boolean, default: false },
  maxSize: { type: Number, default: 10 },
  accept: { type: Array, default: () => ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'] }
})

const emit = defineEmits(['upload', 'delete', 'preview'])

const uploadRef = ref(null)
const uploading = ref(false)

const uploadUrl = computed(() => '/api/upload/')
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}))
const acceptStr = computed(() => props.accept.join(','))

function handleBeforeUpload(file) {
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

function handleSuccess(response) {
  uploading.value = false
  const data = response.data || response
  let newFiles = []
  if (Array.isArray(data) && data.length > 0) {
    newFiles = data.map(d => ({ url: d.url || d.filename, name: d.original_name || d.filename }))
  } else if (data.url || data.filename) {
    newFiles = [{ url: data.url || data.filename, name: data.original_name || data.filename }]
  }
  if (newFiles.length) {
    emit('upload', newFiles)
  }
}

function handleError() {
  uploading.value = false
  ElMessage.error('上传失败，请重试')
}

function handleDelete(idx) {
  emit('delete', idx)
}
</script>

<style scoped>
.attachment-list {
  padding: 8px 4px;
}

.upload-area {
  margin-bottom: 16px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.2s;
}

.file-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.file-icon {
  color: #409eff;
  margin-right: 8px;
  font-size: 18px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

.file-actions {
  display: flex;
  gap: 4px;
}
</style>
