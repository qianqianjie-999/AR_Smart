<template>
  <div class="contract-detail-container">
    <!-- 顶部面包屑导航 -->
    <div class="detail-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
        <div class="divider-line"></div>
        <div class="title-block">
          <h1 class="page-title">{{ contractInfo.project_name || '加载中...' }}</h1>
          <div class="subtitle-info">
            <span><el-icon><Document /></el-icon> 合同编号：{{ contractInfo.contract_no || '-' }}</span>
            <span class="dot-sep">·</span>
            <span><el-icon><User /></el-icon> 客户：{{ contractInfo.customer_name || '-' }}</span>
            <span class="dot-sep">·</span>
            <el-tag :type="statusType(contractInfo.status)" size="small" effect="light">
              {{ statusText(contractInfo.status) }}
            </el-tag>
          </div>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Edit" @click="handleEdit">编辑合同</el-button>
      </div>
    </div>

    <!-- 顶部关键指标卡片 -->
    <div class="metrics-row">
      <div class="metric-card metric-blue">
        <div class="metric-icon">
          <el-icon :size="26"><Money /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">合同金额</div>
          <div class="metric-value">{{ formatMoney(contractInfo.contract_amount) }}</div>
        </div>
      </div>

      <div class="metric-card metric-cyan">
        <div class="metric-icon">
          <el-icon :size="26"><Files /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">审计金额</div>
          <div class="metric-value">{{ formatMoney(contractInfo.audit_amount) }}</div>
        </div>
      </div>

      <div class="metric-card metric-green">
        <div class="metric-icon">
          <el-icon :size="26"><CircleCheck /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">累计回款</div>
          <div class="metric-value">{{ formatMoney(contractInfo.total_paid) }}</div>
          <div class="metric-sub">占审计 {{ ratio(contractInfo.total_paid, contractInfo.audit_amount) }}%</div>
        </div>
      </div>

      <div class="metric-card metric-orange">
        <div class="metric-icon">
          <el-icon :size="26"><Warning /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">到期应付</div>
          <div class="metric-value">{{ formatMoney(contractInfo.current_due_amount) }}</div>
        </div>
      </div>

      <div class="metric-card metric-red">
        <div class="metric-icon">
          <el-icon :size="26"><AlarmClock /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">尚欠金额</div>
          <div class="metric-value">{{ formatMoney(contractInfo.outstanding_amount) }}</div>
          <div class="metric-sub">占审计 {{ ratio(contractInfo.outstanding_amount, contractInfo.audit_amount) }}%</div>
        </div>
      </div>

      <div class="metric-card metric-purple" v-if="overdueData.total_interest > 0">
        <div class="metric-icon">
          <el-icon :size="26"><Coin /></el-icon>
        </div>
        <div class="metric-content">
          <div class="metric-label">逾期利息</div>
          <div class="metric-value">{{ formatMoney(overdueData.total_interest) }}</div>
          <div class="metric-sub">{{ contractInfo.penalty_interest || '日万分之五' }}</div>
        </div>
      </div>
    </div>

    <!-- 标签页区域 -->
    <el-tabs v-model="activeTab" class="detail-tabs">
      <el-tab-pane label="基本信息" name="basic">
        <div class="pane-card">
          <div class="pane-title"><el-icon><Reading /></el-icon> 基础资料</div>
          <el-descriptions :column="2" border size="default">
            <el-descriptions-item label="合同编号">{{ contractInfo.contract_no }}</el-descriptions-item>
            <el-descriptions-item label="项目名称">{{ contractInfo.project_name }}</el-descriptions-item>
            <el-descriptions-item label="客户名称">{{ contractInfo.customer_name }}</el-descriptions-item>
            <el-descriptions-item label="签订日期">{{ contractInfo.sign_date }}</el-descriptions-item>
            <el-descriptions-item label="验收日期">{{ contractInfo.acceptance_date || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusType(contractInfo.status)" size="small" effect="light">{{ statusText(contractInfo.status) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="合同金额(万元)">{{ formatMoney(contractInfo.contract_amount) }}</el-descriptions-item>
            <el-descriptions-item label="审计金额(万元)">{{ formatMoney(contractInfo.audit_amount) }}</el-descriptions-item>
            <el-descriptions-item label="累计回款金额(万元)"><span style="color:#67c23a;font-weight:600">{{ formatMoney(contractInfo.total_paid) }}</span></el-descriptions-item>
            <el-descriptions-item label="累计开票金额(万元)">{{ formatMoney(contractInfo.total_invoiced) }}</el-descriptions-item>
            <el-descriptions-item label="尚欠金额(万元)"><span style="color:#f56c6c;font-weight:600">{{ formatMoney(contractInfo.outstanding_amount) }}</span></el-descriptions-item>
            <el-descriptions-item label="到期应付金额(万元)"><span style="color:#e6a23c;font-weight:600">{{ formatMoney(contractInfo.current_due_amount) }}</span></el-descriptions-item>
            <el-descriptions-item label="付款方式" :span="2">{{ contractInfo.payment_method || '-' }}</el-descriptions-item>
            <el-descriptions-item label="违约条款约定" :span="2">{{ contractInfo.breach_clause || '-' }}</el-descriptions-item>
            <el-descriptions-item label="违约金利息" :span="2">{{ contractInfo.penalty_interest || '日万分之五' }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ contractInfo.remark || '-' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>

      <el-tab-pane label="付款节点" name="paymentNodes">
        <div class="pane-card">
          <div class="pane-header">
            <div class="pane-title"><el-icon><Calendar /></el-icon> 付款节点计划</div>
            <el-button type="primary" :icon="Plus" size="default" @click="handleAddNode">新增节点</el-button>
          </div>
          <el-table :data="paymentNodes" stripe border :header-cell-style="{background:'#f7f9fc',color:'#333',fontWeight:600}">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="node_name" label="节点名称" min-width="130" />
            <el-table-column prop="pay_amount" label="应付金额(万元)" width="150" align="right">
              <template #default="{ row }">{{ formatMoney(row.pay_amount) }}</template>
            </el-table-column>
            <el-table-column prop="pay_ratio" label="比例(%)" width="90" align="center">
              <template #default="{ row }">{{ row.pay_ratio || '-' }}</template>
            </el-table-column>
            <el-table-column prop="due_date" label="计划日期" width="120" />
            <el-table-column prop="actual_pay_date" label="实际日期" width="120">
              <template #default="{ row }">{{ row.actual_pay_date || '-' }}</template>
            </el-table-column>
            <el-table-column prop="actual_pay_amount" label="实际金额(万元)" width="130" align="right">
              <template #default="{ row }">{{ row.actual_pay_amount ? formatMoney(row.actual_pay_amount) : '-' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="110" align="center">
              <template #default="{ row }">
                <el-tag :type="nodeStatusType(row.status)" size="small" effect="light">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="逾期天数" width="100" align="center">
              <template #default="{ $index }">
                <span v-if="overdueData.nodes[$index]?.overdue_days > 0" style="color: #f56c6c; font-weight: 600;">
                  {{ overdueData.nodes[$index]?.overdue_days }}天
                </span>
                <span v-else style="color: #c0c4cc;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="逾期利息" width="130" align="right">
              <template #default="{ $index }">
                <span v-if="overdueData.nodes[$index]?.interest > 0" style="color: #f56c6c; font-weight: 600;">
                  {{ formatMoney(overdueData.nodes[$index]?.interest) }}
                </span>
                <span v-else style="color: #c0c4cc;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleUpdateNodeStatus(row)">更新状态</el-button>
                <el-button type="danger" link @click="handleDeleteNode(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-dialog v-model="nodeDialogVisible" title="付款节点" width="520px">
            <el-form ref="nodeFormRef" :model="nodeForm" :rules="nodeRules" label-width="110px" class="dialog-form">
              <el-form-item label="节点名称" prop="node_name">
                <el-input v-model="nodeForm.node_name" placeholder="如：预付款、进度款、验收款、质保金" />
              </el-form-item>
              <el-form-item label="应付金额(元)" prop="pay_amount">
                <el-input-number v-model="nodeForm.pay_amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
              </el-form-item>
              <el-form-item label="付款比例(%)" prop="pay_ratio">
                <el-input-number v-model="nodeForm.pay_ratio" :min="0" :max="100" :precision="2" style="width: 100%" controls-position="right" />
              </el-form-item>
              <el-form-item label="计划日期" prop="due_date">
                <el-date-picker v-model="nodeForm.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
              <el-form-item label="付款条件" prop="due_condition">
                <el-input v-model="nodeForm.due_condition" placeholder="如：验收合格后30日内" />
              </el-form-item>
              <el-form-item label="实际日期">
                <el-date-picker v-model="nodeForm.actual_pay_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
              </el-form-item>
              <el-form-item label="实际金额(元)">
                <el-input-number v-model="nodeForm.actual_pay_amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
              </el-form-item>
              <el-form-item label="状态" prop="status">
                <el-select v-model="nodeForm.status" style="width: 100%">
                  <el-option label="未到期" value="未到期" />
                  <el-option label="已支付" value="已支付" />
                  <el-option label="逾期" value="逾期" />
                </el-select>
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="nodeDialogVisible = false">取消</el-button>
              <el-button type="primary" @click="handleSaveNode">确认</el-button>
            </template>
          </el-dialog>

          <el-dialog v-model="nodeStatusDialogVisible" title="更新节点状态" width="480px">
            <el-form ref="nodeStatusFormRef" :model="nodeStatusForm" label-width="120px" class="dialog-form">
              <el-form-item label="节点名称">
                <span>{{ nodeStatusForm.node_name }}</span>
              </el-form-item>
              <el-form-item label="状态" required>
                <el-select v-model="nodeStatusForm.status" style="width: 100%">
                  <el-option label="未到期" value="未到期" />
                  <el-option label="已支付" value="已支付" />
                  <el-option label="逾期" value="逾期" />
                </el-select>
              </el-form-item>
              <template v-if="nodeStatusForm.status === '已支付'">
                <el-form-item label="实际支付金额(元)">
                  <el-input-number v-model="nodeStatusForm.actual_pay_amount" :min="0" :precision="2" style="width: 100%" controls-position="right" />
                </el-form-item>
                <el-form-item label="实际支付日期">
                  <el-date-picker v-model="nodeStatusForm.actual_pay_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
                <el-form-item label="生成回款记录">
                  <el-switch v-model="nodeStatusForm.create_payment_record" />
                </el-form-item>
              </template>
            </el-form>
            <template #footer>
              <el-button @click="nodeStatusDialogVisible = false">取消</el-button>
              <el-button type="primary" @click="handleSubmitNodeStatus">确认更新</el-button>
            </template>
          </el-dialog>
        </div>
      </el-tab-pane>

      <el-tab-pane label="回款记录" name="payments">
        <div class="pane-card">
          <PaymentTab :contract-id="contractId" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="开票记录" name="invoices">
        <div class="pane-card">
          <InvoiceTab :contract-id="contractId" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="催款记录" name="collections">
        <div class="pane-card">
          <CollectionTab :contract-id="contractId" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="时效记录" name="limitations">
        <div class="pane-card">
          <LimitationTab :contract-id="contractId" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="附件管理" name="files">
        <AttachmentManagement :contract-id="contractId" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Plus, Edit, Money, Files, CircleCheck,
  Warning, AlarmClock, Document, User, Reading, Calendar, Coin
} from '@element-plus/icons-vue'
import { getContractDetail, getPaymentNodes, savePaymentNodes, updatePaymentNodeStatus, getOverdueInterest } from '@/api/contract'
import PaymentTab from './tabs/PaymentTab.vue'
import InvoiceTab from './tabs/InvoiceTab.vue'
import CollectionTab from './tabs/CollectionTab.vue'
import LimitationTab from './tabs/LimitationTab.vue'
import AttachmentManagement from '@/components/AttachmentManagement.vue'

const router = useRouter()

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const route = useRoute()
const contractId = ref(props.id || route.params.id)
const activeTab = ref('basic')
const contractInfo = ref({})
const paymentNodes = ref([])
const nodeDialogVisible = ref(false)
const nodeFormRef = ref(null)
const editingNode = ref(null)
const nodeStatusDialogVisible = ref(false)
const nodeStatusFormRef = ref(null)
const nodeStatusForm = ref({
  id: null,
  node_name: '',
  status: '未到期',
  actual_pay_amount: 0,
  actual_pay_date: '',
  create_payment_record: true,
})
const overdueData = ref({ nodes: [], total_interest: 0 })

const nodeForm = ref({
  node_name: '',
  pay_amount: 0,
  pay_ratio: 0,
  due_date: '',
  due_condition: '',
  actual_pay_date: '',
  actual_pay_amount: 0,
  status: '未到期'
})

const nodeRules = {
  node_name: [{ required: true, message: '请输入节点名称', trigger: 'blur' }],
  pay_amount: [{ required: true, message: '请输入金额', trigger: 'blur' }],
  due_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

function ratio(a, b) {
  const numA = Number(a) || 0
  const numB = Number(b) || 0
  if (!numB) return '0'
  return (numA / numB * 100).toFixed(1)
}

function handleEdit() {
  router.push({ path: `/contract/edit/${contractId.value}` })
}

function statusType(s) {
  const map = { '执行中': 'primary', '已完成': 'success', '已终止': 'info' }
  return map[s] || 'info'
}

function statusText(s) {
  const map = { '执行中': '执行中', '已完成': '已完成', '已终止': '已终止' }
  return map[s] || s
}

function nodeStatusType(s) {
  const map = { '未到期': 'info', '已支付': 'success', '部分付款': 'warning', '逾期': 'danger' }
  return map[s] || 'info'
}

function nodeStatusText(s) {
  const map = { 'pending': '待付款', 'paid': '已付款', 'overdue': '已逾期' }
  return map[s] || s
}

async function fetchContractDetail() {
  try {
    const res = await getContractDetail(contractId.value)
    contractInfo.value = res.data || {}
  } catch { /* handled */ }
}

async function fetchPaymentNodes() {
  try {
    const res = await getPaymentNodes(contractId.value)
    paymentNodes.value = res.data || []
  } catch { paymentNodes.value = [] }
}

async function fetchOverdueInterest() {
  try {
    const res = await getOverdueInterest(contractId.value)
    overdueData.value = res.data || { nodes: [], total_interest: 0 }
  } catch { overdueData.value = { nodes: [], total_interest: 0 } }
}

function handleAddNode() {
  editingNode.value = null
  nodeForm.value = { node_name: '', pay_amount: 0, pay_ratio: 0, due_date: '', due_condition: '', actual_pay_date: '', actual_pay_amount: 0, status: '未到期' }
  nodeDialogVisible.value = true
}

async function handleSaveNode() {
  try {
    await nodeFormRef.value.validate()
  } catch { return }

  if (editingNode.value != null) {
    paymentNodes.value[editingNode.value] = { ...nodeForm.value }
  } else {
    paymentNodes.value.push({ ...nodeForm.value })
  }
  nodeDialogVisible.value = false

  try {
    await savePaymentNodes(contractId.value, paymentNodes.value)
    ElMessage.success('保存成功')
  } catch { /* handled */ }
}

function handleUpdateNodeStatus(row) {
  nodeStatusForm.value = {
    id: row.id,
    node_name: row.node_name || '',
    status: row.status || '未到期',
    actual_pay_amount: Number(row.actual_pay_amount || row.pay_amount || 0),
    actual_pay_date: row.actual_pay_date || new Date().toISOString().slice(0, 10),
    create_payment_record: true,
  }
  nodeStatusDialogVisible.value = true
}

async function handleSubmitNodeStatus() {
  const f = nodeStatusForm.value
  if (!f.status) {
    ElMessage.warning('请选择状态')
    return
  }
  try {
    await updatePaymentNodeStatus(contractId.value, f.id, {
      status: f.status,
      actual_pay_amount: Number(f.actual_pay_amount || 0),
      actual_pay_date: f.actual_pay_date,
      create_payment_record: f.create_payment_record,
    })
    ElMessage.success('状态已更新')
    nodeStatusDialogVisible.value = false
    fetchContractDetail()
    fetchPaymentNodes()
    fetchOverdueInterest()
  } catch (e) { /* handled by interceptor */ }
}

async function handleDeleteNode(row) {
  try {
    await ElMessageBox.confirm('确定要删除该节点吗？', '删除确认', { type: 'warning' })
    const idx = paymentNodes.value.indexOf(row)
    paymentNodes.value.splice(idx, 1)
    await savePaymentNodes(contractId.value, paymentNodes.value)
    ElMessage.success('删除成功')
  } catch { /* canceled */ }
}

onMounted(() => {
  fetchContractDetail()
  fetchPaymentNodes()
  fetchOverdueInterest()
})
</script>

<style scoped>
.contract-detail-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
  box-sizing: border-box;
}

/* 顶部头部 */
.detail-header {
  background: #fff;
  padding: 20px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  color: #303133;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e6f1ff;
  color: #409eff;
  border-color: #c6e2ff;
}

.divider-line {
  width: 1px;
  height: 36px;
  background: #e4e7ed;
}

.title-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subtitle-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
}

.subtitle-info .el-icon {
  vertical-align: -2px;
  margin-right: 2px;
}

.dot-sep {
  color: #c0c4cc;
}

/* 指标卡片行 */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.metric-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.metric-blue::before { background: #409eff; }
.metric-cyan::before { background: #13c2c2; }
.metric-green::before { background: #67c23a; }
.metric-orange::before { background: #e6a23c; }
.metric-red::before { background: #f56c6c; }
.metric-purple::before { background: #8b5cf6; }

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-blue .metric-icon {
  background: #ecf5ff;
  color: #409eff;
}
.metric-cyan .metric-icon {
  background: #e0fffd;
  color: #13c2c2;
}
.metric-green .metric-icon {
  background: #f0f9eb;
  color: #67c23a;
}
.metric-orange .metric-icon {
  background: #fdf6ec;
  color: #e6a23c;
}
.metric-red .metric-icon {
  background: #fef0f0;
  color: #f56c6c;
}
.metric-purple .metric-icon {
  background: #f3f0ff;
  color: #8b5cf6;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.metric-label {
  font-size: 13px;
  color: #909399;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}

.metric-green .metric-value { color: #529b2e; }
.metric-red .metric-value { color: #d9363e; }
.metric-orange .metric-value { color: #cf8a15; }

.metric-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 标签页 */
.detail-tabs {
  background: transparent;
  margin-top: 0;
}

.detail-tabs :deep(.el-tabs__header) {
  background: #fff;
  border-radius: 8px 8px 0 0;
  padding: 0 20px;
  margin-bottom: 0;
}

.detail-tabs :deep(.el-tabs__nav) {
  border: none;
}

.detail-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  padding: 0 20px;
  height: 50px;
  line-height: 50px;
  color: #606266;
  font-weight: 500;
}

.detail-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
  font-weight: 600;
}

.detail-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  background: #409eff;
}

.detail-tabs :deep(.el-tabs__content) {
  padding: 0;
}

.detail-tabs :deep(.el-tab-pane) {
  padding-top: 16px;
}

.pane-card {
  background: #fff;
  border-radius: 0 0 8px 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.pane-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pane-title .el-icon {
  color: #409eff;
}

:deep(.el-descriptions__label) {
  background: #f7f9fc;
  font-weight: 500;
  color: #5a6270;
}

:deep(.el-descriptions__cell.is-bordered) {
  padding: 14px 16px;
}

:deep(.el-table) {
  font-size: 14px;
  border-radius: 6px;
  overflow: hidden;
}

.dialog-form :deep(.el-form-item__label) {
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 1400px) {
  .metrics-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .metrics-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>
