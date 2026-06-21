<template>
  <div class="progress-container">
    <h2 class="page-title">付款进度</h2>

    <div class="search-form">
      <el-form inline>
        <el-form-item label="选择合同">
          <el-select v-model="selectedContract" placeholder="请选择合同" filterable style="width: 400px" @change="fetchProgress">
            <el-option
              v-for="c in contractOptions"
              :key="c.id"
              :label="`${c.contract_no} - ${c.project_name} (${c.customer_name || ''})`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="progressData" class="progress-content">
      <!-- 总进度 + 汇总卡片 -->
      <el-row :gutter="20" class="mb-20">
        <el-col :xs="24" :md="12">
          <div class="table-container">
            <div class="table-header"><span class="table-title">总体付款进度</span></div>
            <div class="progress-card">
              <div class="progress-info">
                <div class="progress-text">
                  已付款 <span class="amount-paid">{{ formatMoney(progressData.total_paid) }}</span> /
                  审计金额 <span class="amount-total">{{ formatMoney(progressData.audit_amount) }}</span>
                </div>
                <div class="progress-percent">{{ progressData.payment_percent || 0 }}%</div>
              </div>
              <el-progress
                :percentage="progressData.payment_percent || 0"
                :color="progressColor"
                :stroke-width="20"
              />
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :md="12">
          <div class="table-container">
            <div class="table-header"><span class="table-title">到期应收款汇总</span></div>
            <div class="stat-cards">
              <div class="stat-item">
                <div class="stat-value red">{{ formatMoney(progressData.current_due_amount) }}</div>
                <div class="stat-label">当前到期应收款(万元)</div>
              </div>
              <div class="stat-item">
                <div class="stat-value orange">{{ formatMoney(progressData.outstanding_amount) }}</div>
                <div class="stat-label">尚欠金额(万元)</div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 付款节点时间线 -->
      <div class="table-container">
        <div class="table-header"><span class="table-title">付款节点时间线</span></div>
        <div v-if="nodes.length" class="progress-timeline">
          <div v-for="(node, idx) in nodes" :key="idx" class="timeline-node">
            <div class="node-line">
              <div class="node-dot" :class="nodeStatusClass(calcNodeStatus(node))"></div>
              <div v-if="idx < nodes.length - 1" class="node-connector" :class="nodeStatusClass(calcNodeStatus(node))"></div>
            </div>
            <div class="node-card" :class="nodeStatusClass(calcNodeStatus(node))">
              <div class="node-header">
                <span class="node-name">{{ node.node_name }}</span>
                <el-tag :type="nodeTagType(calcNodeStatus(node))" size="small">{{ calcNodeStatus(node) }}</el-tag>
              </div>
              <div class="node-body">
                <span class="node-amount">{{ formatMoney(node.pay_amount) }}</span>
                <span v-if="node.pay_ratio" class="node-ratio">({{ node.pay_ratio }}%)</span>
                <span class="node-date">计划: {{ node.due_date || '未设置' }}</span>
              </div>
              <div v-if="node.due_condition" class="node-condition">{{ node.due_condition }}</div>
              <div v-if="node.actual_pay_date" class="node-footer">
                实际日期: {{ node.actual_pay_date }} | 实际金额: {{ formatMoney(node.actual_pay_amount) }}
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无付款节点" :image-size="100" />
      </div>
    </div>
    <el-empty v-else description="请选择合同查看付款进度" :image-size="120" class="mt-20" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getContractList, getPaymentNodes } from '@/api/contract'
import { getPaymentList } from '@/api/payment'

const contractOptions = ref([])
const selectedContract = ref('')
const progressData = ref(null)
const nodes = ref([])

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

const progressColor = [
  { color: '#f56c6c', percentage: 30 },
  { color: '#e6a23c', percentage: 60 },
  { color: '#67c23a', percentage: 80 },
  { color: '#409eff', percentage: 100 }
]

function nodeStatusClass(s) {
  const map = { '已付款': 'status-paid', '逾期': 'status-overdue', '已到期': 'status-due', '未到期': 'status-pending' }
  return map[s] || 'status-pending'
}

function nodeTagType(s) {
  const map = { '未到期': 'info', '已到期': 'warning', '已付款': 'success', '逾期': 'danger' }
  return map[s] || 'info'
}

// 自动计算节点状态
function calcNodeStatus(node) {
  if (node.actual_pay_date) return '已付款'
  if (!node.due_date) return '未到期'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const dueDate = new Date(node.due_date)
  dueDate.setHours(0, 0, 0, 0)
  if (dueDate < today) return '逾期'
  return '未到期'
}

async function fetchContracts() {
  try {
    const res = await getContractList({ page: 1, page_size: 999 })
    contractOptions.value = res.data?.list || res.data?.items || []
  } catch { contractOptions.value = [] }
}

async function fetchProgress(contractId) {
  if (!contractId) { progressData.value = null; nodes.value = []; return }
  try {
    const [nodesRes, paymentsRes] = await Promise.all([
      getPaymentNodes(contractId),
      getPaymentList({ contract_id: contractId, page: 1, page_size: 999 })
    ])

    nodes.value = (nodesRes.data || []).map(n => ({
      ...n,
      _status: calcNodeStatus(n)  // 预计算状态
    }))

    const payments = paymentsRes.data?.list || paymentsRes.data?.items || paymentsRes.data || []
    const totalPaid = payments.reduce((sum, p) => sum + Number(p.amount || 0), 0)

    const contract = contractOptions.value.find(c => c.id == contractId) || {}
    const auditAmount = Number(contract.audit_amount || contract.contract_amount || 0)

    // 计算到期应收款：所有已到期且未付款的节点金额之和
    const now = new Date(); now.setHours(0, 0, 0, 0)
    const dueAmount = nodes.value.reduce((sum, n) => {
      if (n.actual_pay_date) return sum  // 已付款的不算
      if (!n.due_date) return sum
      const dueDate = new Date(n.due_date); dueDate.setHours(0, 0, 0, 0)
      if (dueDate <= now) return sum + Number(n.pay_amount || 0)
      return sum
    }, 0)

    progressData.value = {
      contract_amount: contract.contract_amount || 0,
      audit_amount: auditAmount,
      total_paid: totalPaid,
      outstanding_amount: Math.max(0, auditAmount - totalPaid),
      current_due_amount: dueAmount,
      payment_percent: auditAmount ? Math.round((totalPaid / auditAmount) * 100) : 0
    }
  } catch {
    progressData.value = { contract_amount: 0, audit_amount: 0, total_paid: 0, outstanding_amount: 0, current_due_amount: 0, payment_percent: 0 }
    nodes.value = []
  }
}

onMounted(() => { fetchContracts() })
</script>

<style scoped>
.progress-wrapper { padding: 20px; }
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.progress-text { font-size: 15px; color: #666; }
.amount-paid { color: #67c23a; font-weight: 600; }
.amount-total { color: #333; font-weight: 600; }
.progress-percent { font-size: 32px; font-weight: 700; color: #409eff; }

.stat-cards { display: flex; gap: 20px; padding: 20px; }
.stat-item { flex: 1; text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-value.red { color: #f56c6c; }
.stat-value.orange { color: #e6a23c; }
.stat-label { font-size: 13px; color: #999; margin-top: 4px; }

.progress-timeline { padding: 20px; }
.timeline-node { display: flex; gap: 0; }
.node-line { display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0; }
.node-dot { width: 16px; height: 16px; border-radius: 50%; border: 3px solid #dcdfe6; background: #fff; }
.node-dot.status-paid { border-color: #67c23a; background: #67c23a; }
.node-dot.status-overdue { border-color: #f56c6c; background: #f56c6c; }
.node-dot.status-due { border-color: #e6a23c; background: #e6a23c; }
.node-dot.status-pending { border-color: #e6a23c; }
.node-connector { width: 2px; flex: 1; min-height: 20px; background: #dcdfe6; }
.node-connector.status-paid { background: #67c23a; }
.node-card { flex: 1; margin-left: 12px; margin-bottom: 20px; padding: 12px 16px; background: #f5f7fa; border-radius: 6px; border-left: 3px solid #dcdfe6; }
.node-card.status-paid { border-left-color: #67c23a; }
.node-card.status-overdue { border-left-color: #f56c6c; background: #fef0f0; }
.node-card.status-due { border-left-color: #e6a23c; background: #fef6e6; }
.node-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.node-name { font-weight: 600; color: #333; }
.node-body { display: flex; gap: 16px; font-size: 13px; color: #666; align-items: center; }
.node-amount { font-weight: 600; color: #333; }
.node-ratio { font-size: 12px; color: #999; }
.node-condition { margin-top: 6px; font-size: 12px; color: #909399; }
.node-footer { margin-top: 8px; font-size: 12px; color: #999; }
</style>
