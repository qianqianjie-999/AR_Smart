<template>
  <div class="dashboard-container">
    <h2 class="page-title">首页仪表盘</h2>

    <!-- 统计卡片 -->
    <div class="stat-card-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(64,158,255,0.1); color: #409eff;">
          <el-icon :size="28"><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.customerCount }}</div>
          <div class="stat-label">客户总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(103,194,58,0.1); color: #67c23a;">
          <el-icon :size="28"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.contractCount }}</div>
          <div class="stat-label">合同总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(230,162,60,0.1); color: #e6a23c;">
          <el-icon :size="28"><Money /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatMoney(stats.totalReceivable) }}</div>
          <div class="stat-label">应收账款总额(万元)</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(245,108,108,0.1); color: #f56c6c;">
          <el-icon :size="28"><WarningFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ formatMoney(stats.outstandingAmount) }}</div>
          <div class="stat-label">尚欠金额总额(万元)</div>
        </div>
      </div>
    </div>

    <div class="stat-card-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(230,162,60,0.1); color: #e6a23c;">
          <el-icon :size="28"><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.expiringLimitations }}</div>
          <div class="stat-label">即将到期时效数</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">应收账款月度趋势</span>
          </div>
          <div ref="trendChartRef" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">时效状态分布</span>
          </div>
          <div ref="pieChartRef" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 近期到期预警 -->
    <div class="table-container mt-20">
      <div class="table-header">
        <span class="table-title">近期到期预警（7天内）</span>
      </div>
      <el-table :data="warningList" stripe border style="width: 100%">
        <el-table-column prop="contract_no" label="合同编号" width="140" />
        <el-table-column prop="customer_name" label="客户名称" />
        <el-table-column prop="due_date" label="到期日期" width="120" />
        <el-table-column prop="remaining_days" label="剩余天数" width="100">
          <template #default="{ row }">
            <el-tag :type="row.remaining_days <= 3 ? 'danger' : 'warning'" size="small">
              {{ row.remaining_days }}天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额(万元)" width="140">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已过期' ? 'danger' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getSummaryStats, getPaymentTrend, getLimitationStats } from '@/api/report'

const stats = ref({
  customerCount: 0,
  contractCount: 0,
  totalReceivable: 0,
  outstandingAmount: 0,
  expiringLimitations: 0
})

const warningList = ref([])
const trendChartRef = ref(null)
const pieChartRef = ref(null)
let trendChart = null
let pieChart = null

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

async function initTrendChart(data) {
  if (!trendChartRef.value) return
  const months = data?.months || ['1月', '2月', '3月', '4月', '5月', '6月']
  const amounts = data?.amounts || [0, 0, 0, 0, 0, 0]
  const chart = await safeInitChart(trendChartRef.value, {
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
    grid: { left: 60, right: 20, top: 30, bottom: 30 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', axisLabel: { formatter: (v) => (v / 10000).toFixed(2) + ' 万元' } },
    series: [{
      name: '应收账款',
      type: 'line',
      data: amounts,
      smooth: true,
      lineStyle: { color: '#409eff', width: 3 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(64,158,255,0.3)' },
        { offset: 1, color: 'rgba(64,158,255,0.05)' }
      ])},
      itemStyle: { color: '#409eff' }
    }]
  })
  if (chart) trendChart = chart
}

async function initPieChart(data) {
  if (!pieChartRef.value) return
  const items = data?.map(item => ({ name: item.name, value: item.value })) || []
  const chart = await safeInitChart(pieChartRef.value, {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 10 },
    series: [{
      name: '时效状态',
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      data: items.length ? items : [
        { name: '有效', value: 0 },
        { name: '即将到期', value: 0 },
        { name: '已过期', value: 0 }
      ],
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false }
    }]
  })
  if (chart) pieChart = chart
}

function handleResize() {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(async () => {
  try {
    const summaryRes = await getSummaryStats()
    if (summaryRes?.data) {
      stats.value = summaryRes.data
      warningList.value = summaryRes.data.warnings || []
    }

    const trendRes = await getPaymentTrend()
    initTrendChart(trendRes?.data)

    const limitRes = await getLimitationStats()
    initPieChart(limitRes?.data?.array || limitRes?.data)
  } catch {
    initTrendChart(null)
    initPieChart(null)
  }

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  pieChart?.dispose()
})
</script>

<style scoped>
.charts-row {
  margin-bottom: 0 !important;
}

.chart-card {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
}

.chart-header {
  padding: 16px 20px 0;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.chart-body {
  width: 100%;
  height: 320px;
}
</style>
