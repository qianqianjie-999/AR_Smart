<template>
  <div>
    <div class="flex-between mb-16">
      <span></span>
      <el-button type="primary" :icon="Plus" @click="handleAdd">新增回款记录</el-button>
    </div>
    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column type="index" label="序号" width="60" align="center" />
      <el-table-column prop="payment_no" label="回款次数" width="80" align="center" />
      <el-table-column prop="amount" label="回款金额(万元)" width="150" align="right">
        <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
      </el-table-column>
      <el-table-column prop="payment_date" label="回款日期" width="130" />
      <el-table-column prop="payment_method" label="回款方式" width="100" />
      <el-table-column prop="bank_account" label="银行账号" min-width="160" />
      <el-table-column label="中断时效" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.interrupt_limitation ? 'warning' : 'info'" size="small">{{ row.interrupt_limitation ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="150" />
      <el-table-column label="操作" width="120" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="dialog-form">
        <el-form-item label="回款金额(元)" prop="amount">
          <el-input-number v-model="form.amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="回款日期" prop="payment_date">
          <el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="回款方式" prop="payment_method">
          <el-select v-model="form.payment_method" style="width: 100%">
            <el-option label="银行转账" value="银行转账" />
            <el-option label="现金" value="现金" />
            <el-option label="承兑汇票" value="承兑汇票" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="回款次数" prop="payment_no">
          <el-input-number v-model="form.payment_no" :min="1" :step="1" style="width: 100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="银行账号" prop="bank_account">
          <el-input v-model="form.bank_account" placeholder="请输入回款银行账号" />
        </el-form-item>
        <el-form-item label="中断时效">
          <el-switch v-model="form.interrupt_limitation" :active-value="1" :inactive-value="0" active-text="是" inactive-text="否" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { getPaymentList, createPayment, updatePayment, deletePayment } from '@/api/payment'

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
  amount: 0,
  payment_date: '',
  payment_method: '银行转账',
  payment_no: 1,
  bank_account: '',
  interrupt_limitation: 1,
  remark: ''
})

const dialogTitle = computed(() => isEdit.value ? '编辑回款记录' : '新增回款记录')

const rules = {
  amount: [{ required: true, message: '请输入回款金额', trigger: 'blur' }],
  payment_date: [{ required: true, message: '请选择回款日期', trigger: 'change' }],
  payment_method: [{ required: true, message: '请选择回款方式', trigger: 'change' }]
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getPaymentList({ contract_id: props.contractId })
    tableData.value = res.data?.list || res.data?.items || res.data || []
  } catch { tableData.value = [] }
  finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  editId.value = null
  form.amount = 0
  form.payment_date = ''
  form.payment_method = '银行转账'
  form.payment_no = 1
  form.bank_account = ''
  form.interrupt_limitation = 1
  form.remark = ''
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.keys(form).forEach(key => { if (row[key] !== undefined) form[key] = row[key] })
  dialogVisible.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定删除该回款记录吗？', '删除确认', { type: 'warning' })
    await deletePayment(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch { /* canceled */ }
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    const data = { ...form, contract_id: props.contractId }
    if (isEdit.value) {
      await updatePayment(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createPayment(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ }
  finally { submitLoading.value = false }
}

fetchData()
</script>
