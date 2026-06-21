<template>
  <div>
    <div class="flex-between mb-16">
      <span></span>
      <el-button type="warning" :icon="Warning" @click="handleInterrupt">中断时效</el-button>
    </div>
    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column prop="contract_no" label="合同编号" width="140" />
      <el-table-column prop="customer_name" label="客户" min-width="140" />
      <el-table-column prop="base_date" label="基准日期" width="120" />
      <el-table-column prop="due_date" label="时效到期日" width="120" />
      <el-table-column prop="remaining_days" label="剩余天数" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="remainingDaysType(row.remaining_days)" size="small">
            {{ row.remaining_days }}天
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="limitationStatusType(row.status)" size="small">{{ limitationStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="interrupt_count" label="中断次数" width="80" align="center" />
      <el-table-column prop="last_interrupt_date" label="最后中断日" width="130">
        <template #default="{ row }">{{ row.last_interrupt_date || '-' }}</template>
      </el-table-column>
    </el-table>

    <!-- 中断时效弹窗 -->
    <el-dialog v-model="dialogVisible" title="中断时效" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="dialog-form">
        <el-form-item label="中断原因" prop="reason">
          <el-select v-model="form.reason" style="width: 100%">
            <el-option label="部分回款" value="部分回款" />
            <el-option label="书面承诺" value="书面承诺" />
            <el-option label="对账确认" value="对账确认" />
            <el-option label="催款函件" value="催款函件" />
            <el-option label="诉讼/仲裁" value="诉讼/仲裁" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="中断日期" prop="interrupt_date">
          <el-date-picker v-model="form.interrupt_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="新到期日" prop="new_due_date">
          <el-date-picker v-model="form.new_due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="补充说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确认中断</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { getLimitationList, interruptLimitation } from '@/api/limitation'

const props = defineProps({
  contractId: { type: [String, Number], required: true }
})

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)

const form = reactive({
  reason: '部分回款',
  interrupt_date: '',
  new_due_date: '',
  remark: ''
})

const rules = {
  reason: [{ required: true, message: '请选择中断原因', trigger: 'change' }],
  interrupt_date: [{ required: true, message: '请选择中断日期', trigger: 'change' }],
  new_due_date: [{ required: true, message: '请选择新到期日', trigger: 'change' }]
}

function remainingDaysType(days) {
  if (days == null) return 'info'
  if (days <= 7) return 'danger'
  if (days <= 90) return 'warning'
  return 'success'
}

function limitationStatusType(s) {
  const map = { '有效': 'success', '即将到期': 'warning', '已过期': 'danger' }
  return map[s] || 'info'
}

function limitationStatusText(s) {
  const map = { '有效': '有效', '即将到期': '即将到期', '已过期': '已过期' }
  return map[s] || s
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getLimitationList({ contract_id: props.contractId })
    tableData.value = res.data?.list || res.data?.items || res.data || []
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

function handleInterrupt() {
  form.reason = '部分回款'
  form.interrupt_date = ''
  form.new_due_date = ''
  form.remark = ''
  dialogVisible.value = true
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    await interruptLimitation({ ...form, contract_id: props.contractId })
    ElMessage.success('时效中断成功')
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ }
  finally { submitLoading.value = false }
}

fetchData()
</script>
