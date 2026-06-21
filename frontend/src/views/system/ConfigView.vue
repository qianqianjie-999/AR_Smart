<template>
  <div class="config-container">
    <h2 class="page-title">系统配置</h2>

    <el-form :model="configForm" label-width="200px" v-loading="loading" style="max-width:700px">
      <el-divider content-position="left">时效预警设置</el-divider>
      <el-form-item label="90天预警天数">
        <el-input-number v-model="configForm.limitation_warning_90" :min="30" :max="180" /> 天
        <span class="tip">到期前N天发送90天预警通知</span>
      </el-form-item>
      <el-form-item label="30天预警天数">
        <el-input-number v-model="configForm.limitation_warning_30" :min="7" :max="90" /> 天
      </el-form-item>
      <el-form-item label="7天预警天数">
        <el-input-number v-model="configForm.limitation_warning_7" :min="1" :max="30" /> 天
      </el-form-item>

      <el-divider content-position="left">分页与文件</el-divider>
      <el-form-item label="默认分页大小">
        <el-input-number v-model="configForm.page_size_default" :min="10" :max="100" :step="10" />
      </el-form-item>
      <el-form-item label="上传文件最大大小">
        <el-input-number v-model="configForm.file_max_size" :min="1048576" :max="209715200" :step="1048576" />
        <span class="tip">字节 (当前: {{ (configForm.file_max_size / 1048576).toFixed(0) }}MB)</span>
      </el-form-item>

      <el-divider content-position="left">数据备份</el-divider>
      <el-form-item label="备份保留天数">
        <el-input-number v-model="configForm.backup_retention_days" :min="7" :max="365" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
        <el-button @click="loadConfig">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, updateConfig } from '@/api/system'

const loading = ref(false)
const saving = ref(false)
const configForm = reactive({
  limitation_warning_90: 90,
  limitation_warning_30: 30,
  limitation_warning_7: 7,
  page_size_default: 20,
  file_max_size: 52428800,
  backup_retention_days: 30,
})

async function loadConfig() {
  loading.value = true
  try {
    const res = await getConfig()
    const data = res.data || {}
    // 将后端返回的数组格式转为对象
    if (Array.isArray(data)) {
      data.forEach(item => {
        const key = item.config_key
        if (key in configForm) {
          configForm[key] = Number(item.config_value) || item.config_value
        }
      })
    } else {
      Object.assign(configForm, data)
    }
  } catch (e) { /* ignore */ }
  loading.value = false
}

async function saveConfig() {
  saving.value = true
  try {
    const payload = {}
    Object.keys(configForm).forEach(k => { payload[k] = String(configForm[k]) })
    await updateConfig(payload)
    ElMessage.success('配置已保存')
  } catch (e) { /* ignore */ }
  saving.value = false
}

onMounted(loadConfig)
</script>

<style scoped>
.tip { color: #909399; font-size: 12px; margin-left: 12px; }
</style>
