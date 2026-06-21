<template>
  <div class="limitation-dashboard">
    <h2 class="page-title">时效看板</h2>

    <!-- 统计卡片 -->
    <div class="stat-card-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(103,194,58,0.1); color: #67c23a;">
          <el-icon :size="28"><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard.effectiveCount }}</div>
          <div class="stat-label">有效数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(230,162,60,0.1); color: #e6a23c;">
          <el-icon :size="28"><WarningFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard.expiringCount }}</div>
          <div class="stat-label">即将到期（≤90天）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(245,108,108,0.1); color: #f56c6c;">
          <el-icon :size="28"><CloseFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard.expiredCount }}</div>
          <div class="stat-label">已过期数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(64,158,255,0.1); color: #409eff;">
          <el-icon :size="28"><List /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard.totalCount }}</div>
          <div class="stat-label">总跟踪数</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header"><span class="chart-title">时效状态分布</span></div>
          <div ref="pieChartRef" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header"><span class="chart-title">各区域时效状态</span></div>
          <div ref="barChartRef" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 预警列表 -->
    <div class="table-container mt-20">
      <div class="table-header">
        <span class="table-title">⚠️ 近期到期预警（7天内）</span>
      </div>
      <el-table :data="warningList" stripe border style="width: 100%">
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="customer_name" label="客户" min-width="150" />
        <el-table-column prop="due_date" label="时效到期日" width="120" />
        <el-table-column prop="remaining_days" label="剩余天数" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.remaining_days <= 3 ? 'danger' : 'warning'" size="small">
              {{ row.remaining_days }}天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="base_date" label="基准日期" width="120" />
        <el-table-column prop="amount" label="涉及金额(万元)" width="150" align="right">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="warning" link @click="handleInterrupt(row)">中断</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 中断弹窗 -->
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
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getLimitationDashboard, interruptLimitation } from '@/api/limitation'

const dashboard = ref({ effectiveCount: 0, expiringCount: 0, expiredCount: 0, totalCount: 0 })
const warningList = ref([])
const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieChart = null
let barChart = null

const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const currentRow = ref(null)

const form = reactive({ reason: '部分回款', interrupt_date: '', new_due_date: '', remark: '' })
const rules = {
  reason: [{ required: true, message: '请选择原因', trigger: 'change' }],
  interrupt_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  new_due_date: [{ required: true, message: '请选择新到期日', trigger: 'change' }]
}

function formatMoney(val) {
  if (val == null) return '0.00 万元'
  return (Number(val) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' 万元'
}

function safeInitChart(dom, option) {
  return new Promise((resolve) => {
    if (!dom) return resolve(null)
    setTimeout(() => {
      requestAnimationFrame(() => {
        if (!dom || !dom.clientWidth || !dom.clientHeight) return resolve(null)
        const chart = echarts.init(dom)
        chart.setOption(option)
        setTimeout(() => chart.resize(), 100)
        resolve(chart)
      })
    }, 50)
  })
}

async function initPieChart(data) {
  if (!pieChartRef.value) return
  const chart = await safeInitChart(pieChartRef.value, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 10 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      data: data || [], itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false }
    }]
  })
  if (chart) pieChart = chart
}

async function initBarChart(data) {
  if (!barChartRef.value) return
  const regions = data?.regions || []
  const chart = await safeInitChart(barChartRef.value, {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['有效', '即将到期', '已过期'] },
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: regions.map(r => r.name) },
    yAxis: { type: 'value' },
    series: [
      { name: '有效', type: 'bar', data: regions.map(r => r.effective || 0), color: '#67c23a' },
      { name: '即将到期', type: 'bar', data: regions.map(r => r.expiring || 0), color: '#e6a23c' },
      { name: '已过期', type: 'bar', data: regions.map(r => r.expired || 0), color: '#f56c6c' }
    ]
  })
  if (chart) barChart = chart
}

function handleResize() { pieChart?.resize(); barChart?.resize() }

function handleInterrupt(row) {
  currentRow.value = row
  form.reason = '部分回款'; form.interrupt_date = ''; form.new_due_date = ''; form.remark = ''
  dialogVisible.value = true
}

async function handleSubmit() {
  try { await formRef.value.validate() } catch { return }
  submitLoading.value = true
  try {
    await interruptLimitation({ ...form, limitation_id: currentRow.value?.id })
    ElMessage.success('时效中断成功')
    dialogVisible.value = false
    fetchData()
  } catch { /* handled */ } finally { submitLoading.value = false }
}

async function fetchData() {
  try {
    const res = await getLimitationDashboard()
    if (res?.data) {
      dashboard.value = res.data
      warningList.value = res.data.warnings || []
      await nextTick()
      initPieChart(res.data.pieData)
      initBarChart({ regions: (res.data.barData || []) })
    }
  } catch {
    await nextTick()
    initPieChart([
      { name: '有效', value: 0 }, { name: '即将到期', value: 0 }, { name: '已过期', value: 0 }
    ])
    initBarChart({ regions: [] })
  }
}

onMounted(() => { fetchData(); window.addEventListener('resize', handleResize) })
onUnmounted(() => { window.removeEventListener('resize', handleResize); pieChart?.dispose(); barChart?.dispose() })
</script>

<style scoped>
.dashboard-container { background: #fff; border-radius: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 20px; }
.chart-header { padding: 16px 20px 0; }
.chart-title { font-size: 16px; font-weight: 600; color: #333; }
.chart-body { width: 100%; height: 320px; }
</style>
