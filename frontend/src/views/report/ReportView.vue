<template>
  <div class="report-container">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title"><el-icon><DataAnalysis /></el-icon> 报表中心</h2>
        <div class="page-subtitle">全维度数据透视 · 应收账款全景分析</div>
      </div>
      <div class="header-right">
        <el-button type="primary" size="default" :icon="Download" @click="exportReport('summary')">
          导出Excel
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="report-tabs">
      <!-- 应收账款总览 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><Monitor /></el-icon> 总览</span>
        </template>

        <!-- 顶部关键指标卡 -->
        <div class="metric-row">
          <div v-for="(card, idx) in summaryCards" :key="card.label"
               class="metric-card"
               :class="['metric-card-' + card.theme, idx === 0 ? 'metric-primary' : '']">
            <div class="metric-icon">
              <el-icon :size="26"><component :is="card.icon" /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-label">{{ card.label }}</div>
              <div class="metric-value-row">
                <span class="metric-value">{{ card.value }}</span>
                <span class="metric-unit">{{ card.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 总览图表区 -->
        <div class="chart-row">
          <div class="chart-card chart-card-half">
            <div class="chart-card-header">
              <div class="chart-card-title">
                <el-icon><PieChart /></el-icon> 账龄分布
              </div>
              <span class="chart-card-badge">按金额占比</span>
            </div>
            <div ref="agingSummaryChart" class="chart-body"></div>
          </div>

          <div class="chart-card chart-card-half">
            <div class="chart-card-header">
              <div class="chart-card-title">
                <el-icon><TrendCharts /></el-icon> 回款率
              </div>
              <span class="chart-card-badge">{{ recoveryRate }}%</span>
            </div>
            <div ref="recoveryChart" class="chart-body"></div>
          </div>
        </div>

        <div class="chart-row">
          <div class="chart-card">
            <div class="chart-card-header">
              <div class="chart-card-title">
                <el-icon><Histogram /></el-icon> 区域合同金额分布
              </div>
              <span class="chart-card-badge">Top 区域</span>
            </div>
            <div ref="regionalSummaryChart" class="chart-body"></div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 区域分布 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><LocationFilled /></el-icon> 区域分布</span>
        </template>
        <div class="chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">各区域合同金额与尚欠金额对比</div>
            <span class="chart-card-badge">柱状图</span>
          </div>
          <div ref="regionalChart" class="chart-body"></div>
        </div>
        <div class="table-card">
          <el-table :data="regionalData" border stripe style="width:100%">
            <el-table-column prop="region" label="区域" width="180" />
            <el-table-column prop="contract_count" label="合同数" align="center" width="120" />
            <el-table-column label="合同金额">
              <template #default="{row}">{{ formatMoney(row.total_amount) }}</template>
            </el-table-column>
            <el-table-column label="尚欠金额">
              <template #default="{row}">{{ formatMoney(row.outstanding_amount) }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 客户欠款TOP10 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><Rank /></el-icon> 客户欠款TOP10</span>
        </template>
        <div class="chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">尚欠金额最多的前 10 个客户</div>
            <span class="chart-card-badge">横向条形</span>
          </div>
          <div ref="rankingChart" class="chart-body"></div>
        </div>
      </el-tab-pane>

      <!-- 账龄分析 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><PieChart /></el-icon> 账龄分析</span>
        </template>
        <div class="chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">应收账款账龄结构</div>
            <span class="chart-card-badge">环形图</span>
          </div>
          <div ref="agingChart" class="chart-body"></div>
        </div>
      </el-tab-pane>

      <!-- 到期应收款 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><Warning /></el-icon> 到期应收款</span>
        </template>
        <div class="table-card">
          <el-table :data="dueList" border stripe v-loading="dueLoading" style="width:100%">
            <el-table-column prop="project_name" label="项目名称" min-width="200" />
            <el-table-column prop="customer_name" label="客户" min-width="160" />
            <el-table-column prop="node_name" label="付款节点" min-width="140" />
            <el-table-column prop="due_date" label="到期日" width="140" />
            <el-table-column label="应付金额(万元)" width="160" align="right">
              <template #default="{row}">{{ formatMoney(row.pay_amount) }}</template>
            </el-table-column>
            <el-table-column label="逾期天数" width="140" align="center">
              <template #default="{row}">
                <el-tag :type="row.days_overdue > 90 ? 'danger' : row.days_overdue > 30 ? 'warning' : 'success'" effect="dark">
                  {{ row.days_overdue }}天
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="duePage"
              :page-size="20"
              :total="dueTotal"
              layout="total, prev, pager, next"
              @current-change="loadDueList"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 回款趋势 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><TrendCharts /></el-icon> 回款趋势</span>
        </template>
        <div class="chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">历史回款金额趋势</div>
            <span class="chart-card-badge">折线图</span>
          </div>
          <div ref="trendChart" class="chart-body"></div>
        </div>
      </el-tab-pane>

      <!-- 时效统计 -->
      <el-tab-pane>
        <template #label>
          <span class="tab-label"><el-icon><Clock /></el-icon> 时效统计</span>
        </template>
        <div class="chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">合同诉讼时效分布</div>
            <span class="chart-card-badge">饼图</span>
          </div>
          <div ref="limStatChart" class="chart-body"></div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Download, Monitor, PieChart, TrendCharts, Histogram,
  LocationFilled, Rank, Warning, Clock,
  User, Files, Money, Coin, Wallet, AlarmClock
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getSummaryStats, getRegionalStats, getCustomerRanking,
  getAgingAnalysis, getDueReceivable, getPaymentTrend, getLimitationStats
} from '@/api/report'

const activeTab = ref('summary')
const summaryStats = ref({})
const regionalData = ref([])
const dueList = ref([])
const dueTotal = ref(0)
const duePage = ref(1)
const dueLoading = ref(false)

const agingSummaryChart = ref(null)
const recoveryChart = ref(null)
const regionalSummaryChart = ref(null)
const regionalChart = ref(null)
const rankingChart = ref(null)
const agingChart = ref(null)
const trendChart = ref(null)
const limStatChart = ref(null)

const chartInstances = []

// 安全初始化 ECharts：通过 ResizeObserver + 多轮重试，确保容器获得真实尺寸后再 init
function safeInitChart(dom, option) {
  if (!dom) return

  const MAX_RETRIES = 8
  let attempts = 0

  function tryInit() {
    if (!dom) return
    const width = dom.clientWidth || dom.offsetWidth || 0
    const height = dom.clientHeight || dom.offsetHeight || 0
    if (width > 0 && height > 0) {
      const chart = echarts.init(dom)
      chart.setOption(option)
      chartInstances.push(chart)
      // 渲染完成后再执行一次 resize 兜底
      requestAnimationFrame(() => chart.resize())
      return true
    }
    attempts++
    if (attempts < MAX_RETRIES) {
      setTimeout(tryInit, 80)
    }
    return false
  }

  // 先尝试用 ResizeObserver 监听首次尺寸变化，失败则回退到多轮重试
  try {
    if (typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver((entries, observer) => {
        for (const entry of entries) {
          if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
            observer.disconnect()
            tryInit()
            return
          }
        }
      })
      ro.observe(dom)
      // 2 秒后兜底，避免 ResizeObserver 始终不触发
      setTimeout(() => { if (attempts === 0) tryInit() }, 1500)
      return
    }
  } catch (e) { /* ignore */ }

  tryInit()
}

// 窗口变化时同步调整图表
function handleWindowResize() {
  chartInstances.forEach(c => c && c.resize())
}

function formatMoney(v) {
  if (!v && v !== 0) return '-'
  return (Number(v) / 10000).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatCount(v) {
  if (!v && v !== 0) return '0'
  return Number(v).toLocaleString('zh-CN')
}

// 回款率
const recoveryRate = computed(() => {
  const total = Number(summaryStats.value.total_contract_amount) || 0
  const paid = Number(summaryStats.value.total_paid) || 0
  if (total <= 0) return '0.00'
  return ((paid / total) * 100).toFixed(1)
})

// 指标卡数据
const summaryCards = computed(() => {
  const s = summaryStats.value
  return [
    { label: '客户总数',    icon: markRaw(User),        value: formatCount(s.total_customers),         unit: '家', theme: 'blue' },
    { label: '合同总数',    icon: markRaw(Files),       value: formatCount(s.total_contracts),         unit: '份', theme: 'indigo' },
    { label: '合同总金额',  icon: markRaw(Money),       value: formatMoney(s.total_contract_amount),  unit: '万元', theme: 'amber' },
    { label: '累计回款',    icon: markRaw(Coin),        value: formatMoney(s.total_paid),             unit: '万元', theme: 'emerald' },
    { label: '尚欠金额',    icon: markRaw(Wallet),      value: formatMoney(s.total_outstanding),      unit: '万元', theme: 'rose' },
    { label: '到期应收款',  icon: markRaw(AlarmClock),  value: formatMoney(s.total_due),              unit: '万元', theme: 'red' },
  ]
})

/* ============ 总览加载 + 三个小图表 ============ */
async function loadSummary() {
  try {
    const res = await getSummaryStats()
    summaryStats.value = res.data || {}

    const [agingRes, regionalRes] = await Promise.all([
      getAgingAnalysis(),
      getRegionalStats(),
    ])
    const agingData = agingRes.data || {}
    const regional = regionalRes.data || []

    await nextTick()
    renderAgingSummary(agingData)
    renderRecoveryChart()
    renderRegionalSummary(regional)
  } catch (e) { /* ignore */ }
}

function renderAgingSummary(d) {
  const dom = agingSummaryChart.value
  if (!dom) return
  const items = [
    { name: '0-1年', value: Number(d.aging_0_1y?.amount) || 0, color: '#22c55e' },
    { name: '1-2年', value: Number(d.aging_1_2y?.amount) || 0, color: '#84cc16' },
    { name: '2-3年', value: Number(d.aging_2_3y?.amount) || 0, color: '#f59e0b' },
    { name: '>3年',  value: Number(d.aging_over_3y?.amount) || 0, color: '#ef4444' },
  ].filter(i => i.value > 0)

  safeInitChart(dom, {
    tooltip: { trigger: 'item', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
    legend: { bottom: 0, icon: 'circle' },
    color: items.map(i => i.color),
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { show: true, formatter: '{b}\n{d}%', color: '#374151', fontSize: 12 },
      data: items,
    }]
  })
}

function renderRecoveryChart() {
  const dom = recoveryChart.value
  if (!dom) return
  const rate = Number(recoveryRate.value) || 0

  safeInitChart(dom, {
    tooltip: { formatter: `回款率：{c}%` },
    series: [{
      type: 'gauge',
      startAngle: 210,
      endAngle: -30,
      min: 0,
      max: 100,
      radius: '85%',
      progress: { show: true, width: 22, itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#10b981' },
          { offset: 1, color: '#059669' }
        ])
      }},
      axisLine: { lineStyle: { width: 22, color: [[1, '#e5e7eb']] } },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      anchor: { show: false },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '0%'],
        fontSize: 36,
        fontWeight: 700,
        color: '#065f46',
        formatter: '{value}%'
      },
      title: { show: true, offsetCenter: [0, '55%'], fontSize: 14, color: '#6b7280' },
      data: [{ value: rate, name: '整体回款率' }]
    }]
  })
}

function renderRegionalSummary(data) {
  const dom = regionalSummaryChart.value
  if (!dom) return

  safeInitChart(dom, {
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
    legend: { top: 0, right: 10, icon: 'circle' },
    grid: { left: 50, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.region),
      axisLine: { lineStyle: { color: '#d1d5db' } },
      axisLabel: { color: '#4b5563', rotate: data.length > 6 ? 30 : 0 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万', color: '#6b7280' },
      splitLine: { lineStyle: { color: '#e5e7eb' } },
    },
    series: [
      {
        name: '合同金额',
        type: 'bar',
        barWidth: 22,
        data: data.map(d => Number(d.total_amount) || 0),
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#3b82f6' },
          { offset: 1, color: '#1d4ed8' }
        ]), borderRadius: [6, 6, 0, 0] }
      },
      {
        name: '尚欠金额',
        type: 'bar',
        barWidth: 22,
        data: data.map(d => Number(d.outstanding_amount) || 0),
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#f87171' },
          { offset: 1, color: '#dc2626' }
        ]), borderRadius: [6, 6, 0, 0] }
      },
    ]
  })
}

/* ============ 区域分布 ============ */
async function loadRegional() {
  try {
    const res = await getRegionalStats()
    regionalData.value = res.data || []
    await nextTick()
    renderRegionalChart()
  } catch (e) { /* ignore */ }
}

function renderRegionalChart() {
  const dom = regionalChart.value
  if (!dom) return
  const data = regionalData.value

  safeInitChart(dom, {
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
    legend: { data: ['合同金额', '尚欠金额'], top: 0, icon: 'circle' },
    grid: { left: 60, right: 30, top: 50, bottom: 60 },
    xAxis: { type: 'category', data: data.map(d => d.region), axisLabel: { rotate: 30, color: '#4b5563' }, axisLine: { lineStyle: { color: '#d1d5db' } } },
    yAxis: { type: 'value', axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万', color: '#6b7280' }, splitLine: { lineStyle: { color: '#e5e7eb' } } },
    series: [
      { name: '合同金额', type: 'bar', barWidth: 26, data: data.map(d => Number(d.total_amount) || 0),
        itemStyle: { color: '#3b82f6', borderRadius: [6, 6, 0, 0] } },
      { name: '尚欠金额', type: 'bar', barWidth: 26, data: data.map(d => Number(d.outstanding_amount) || 0),
        itemStyle: { color: '#ef4444', borderRadius: [6, 6, 0, 0] } },
    ]
  })
}

/* ============ TOP10 ============ */
async function loadRanking() {
  try {
    const res = await getCustomerRanking()
    rankingData.value = res.data || []
    await nextTick()
    const dom = rankingChart.value
    if (!dom) return

    safeInitChart(dom, {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
      grid: { left: 160, right: 40, top: 30, bottom: 30 },
      yAxis: { type: 'category', data: rankingData.value.map(d => d.customer_name).reverse(), axisLabel: { width: 140, overflow: 'truncate', color: '#374151' }, axisLine: { show: false }, axisTick: { show: false } },
      xAxis: { type: 'value', axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万', color: '#6b7280' }, splitLine: { lineStyle: { color: '#e5e7eb' } } },
      series: [{
        type: 'bar',
        data: rankingData.value.map(d => Number(d.outstanding_amount) || 0).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#f87171' },
            { offset: 1, color: '#dc2626' }
          ]),
          borderRadius: [0, 6, 6, 0]
        },
        barWidth: 22,
        label: { show: true, position: 'right', formatter: (p) => (p.value / 10000).toFixed(1) + '万', color: '#374151' }
      }],
    })
  } catch (e) { /* ignore */ }
}

/* ============ 账龄分析 ============ */
async function loadAging() {
  try {
    const res = await getAgingAnalysis()
    agingData.value = res.data || {}
    await nextTick()
    const dom = agingChart.value
    if (!dom) return
    const d = agingData.value

    safeInitChart(dom, {
      tooltip: { trigger: 'item', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
      legend: { bottom: 0, icon: 'circle' },
      color: ['#22c55e', '#84cc16', '#f59e0b', '#ef4444'],
      series: [{
        type: 'pie',
        radius: ['40%', '72%'],
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 4 },
        label: { show: true, formatter: '{b}\n{d}%', color: '#374151', fontSize: 13 },
        data: [
          { name: '0-1年', value: Number(d.aging_0_1y?.amount) || 0 },
          { name: '1-2年', value: Number(d.aging_1_2y?.amount) || 0 },
          { name: '2-3年', value: Number(d.aging_2_3y?.amount) || 0 },
          { name: '>3年',  value: Number(d.aging_over_3y?.amount) || 0 },
        ]
      }]
    })
  } catch (e) { /* ignore */ }
}

/* ============ 到期应收款 ============ */
async function loadDueList() {
  dueLoading.value = true
  try {
    const res = await getDueReceivable({ page: duePage.value, pageSize: 20 })
    dueList.value = res.data?.list || []
    dueTotal.value = res.data?.total || 0
  } catch (e) { /* ignore */ }
  dueLoading.value = false
}

/* ============ 回款趋势 ============ */
async function loadTrend() {
  try {
    const res = await getPaymentTrend({ period: 'monthly' })
    trendData.value = res.data?.trendList || res.data || []
    await nextTick()
    const dom = trendChart.value
    if (!dom) return
    const data = trendData.value

    safeInitChart(dom, {
      tooltip: { trigger: 'axis', valueFormatter: (v) => (v / 10000).toFixed(2) + ' 万元' },
      grid: { left: 60, right: 30, top: 40, bottom: 40 },
      xAxis: { type: 'category', data: data.map(d => d.period), boundaryGap: false, axisLine: { lineStyle: { color: '#d1d5db' } }, axisLabel: { color: '#4b5563' } },
      yAxis: { type: 'value', axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万', color: '#6b7280' }, splitLine: { lineStyle: { color: '#e5e7eb' } } },
      series: [{
        type: 'line',
        data: data.map(d => Number(d.amount) || 0),
        smooth: true,
        symbolSize: 8,
        lineStyle: { width: 3, color: '#3b82f6' },
        itemStyle: { color: '#3b82f6', borderColor: '#fff', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59,130,246,0.35)' },
            { offset: 1, color: 'rgba(59,130,246,0.02)' }
          ])
        }
      }]
    })
  } catch (e) { /* ignore */ }
}

/* ============ 时效统计 ============ */
async function loadLimitationStats() {
  try {
    const res = await getLimitationStats()
    limStatData.value = res.data?.object || res.data || {}
    await nextTick()
    const dom = limStatChart.value
    if (!dom) return
    const d = limStatData.value

    safeInitChart(dom, {
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, icon: 'circle' },
      color: ['#22c55e', '#f59e0b', '#ef4444'],
      series: [{
        type: 'pie',
        radius: '60%',
        center: ['50%', '45%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 4 },
        label: { show: true, formatter: '{b}: {c} 份 ({d}%)', color: '#374151', fontSize: 13 },
        data: [
          { name: '有效', value: Number(d.active) || 0 },
          { name: '即将到期', value: Number(d.expiring_soon) || 0 },
          { name: '已过期', value: Number(d.expired) || 0 },
        ]
      }]
    })
  } catch (e) { /* ignore */ }
}

/* ============ 导出 ============ */
async function exportReport(type) {
  try {
    const res = await fetch(`/api/report/export/${type}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type}_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

/* ============ 生命周期 ============ */
function disposeAllCharts() {
  chartInstances.forEach(c => {
    try { c && c.dispose() } catch (e) { /* ignore */ }
  })
  chartInstances.length = 0
}

watch(activeTab, (tab) => {
  disposeAllCharts()
  if (tab === 'summary') loadSummary()
  else if (tab === 'regional') loadRegional()
  else if (tab === 'ranking') loadRanking()
  else if (tab === 'aging') loadAging()
  else if (tab === 'due') loadDueList()
  else if (tab === 'trend') loadTrend()
  else if (tab === 'limitation') loadLimitationStats()
})

onMounted(() => {
  loadSummary()
  window.addEventListener('resize', handleWindowResize)
})

onBeforeUnmount(() => {
  disposeAllCharts()
  window.removeEventListener('resize', handleWindowResize)
})
</script>

<style scoped>
.report-container {
  padding: 0;
  background: #eef2f7;
  min-height: calc(100vh - 80px);
}

/* 顶部标题区 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 20px;
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #3b82f6 100%);
  border-radius: 0 0 0 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.25);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 400;
}

.header-right :deep(.el-button) {
  background: rgba(255, 255, 255, 0.95);
  border: none;
  color: #1e40af;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 8px;
  transition: all 0.2s;
}

.header-right :deep(.el-button:hover) {
  background: #fff;
  color: #1e40af;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Tab 栏 */
.report-tabs {
  margin: 0 24px 24px;
  background: #fff;
  border-radius: 12px;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.report-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding-top: 4px;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
}

.report-tabs :deep(.el-tabs__item.is-active .tab-label) {
  color: #2563eb;
}

.report-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: #e5e7eb;
}

.report-tabs :deep(.el-tabs__active-bar) {
  background-color: #2563eb;
  height: 3px;
  border-radius: 2px;
}

/* 顶部指标卡 */
.metric-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}

.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.metric-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.metric-card-blue::after    { background: linear-gradient(to bottom, #3b82f6, #1e40af); }
.metric-card-indigo::after  { background: linear-gradient(to bottom, #6366f1, #4338ca); }
.metric-card-amber::after   { background: linear-gradient(to bottom, #f59e0b, #b45309); }
.metric-card-emerald::after { background: linear-gradient(to bottom, #10b981, #047857); }
.metric-card-rose::after    { background: linear-gradient(to bottom, #f43f5e, #9f1239); }
.metric-card-red::after     { background: linear-gradient(to bottom, #ef4444, #7f1d1d); }

.metric-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-card-blue    .metric-icon { background: #dbeafe; color: #1e40af; }
.metric-card-indigo  .metric-icon { background: #e0e7ff; color: #4338ca; }
.metric-card-amber   .metric-icon { background: #fef3c7; color: #92400e; }
.metric-card-emerald .metric-icon { background: #d1fae5; color: #065f46; }
.metric-card-rose    .metric-icon { background: #ffe4e6; color: #9f1239; }
.metric-card-red     .metric-icon { background: #fee2e2; color: #7f1d1d; }

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.metric-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  line-height: 1.1;
}

.metric-card-blue    .metric-value { color: #1e3a8a; }
.metric-card-indigo  .metric-value { color: #3730a3; }
.metric-card-amber   .metric-value { color: #92400e; }
.metric-card-emerald .metric-value { color: #065f46; }
.metric-card-rose    .metric-value { color: #9f1239; }
.metric-card-red     .metric-value { color: #7f1d1d; }

.metric-unit {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

/* 图表卡片 */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.chart-row:has(.chart-card:not(.chart-card-half)) {
  grid-template-columns: 1fr;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.chart-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(to right, #fafbfc 0%, #fff 100%);
}

.chart-card-title {
  font-size: 15px;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-card-title .el-icon {
  color: #2563eb;
}

.chart-card-badge {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.chart-body {
  height: 340px;
  min-height: 340px;
  width: 100%;
  padding: 10px;
  box-sizing: border-box;
  display: block;
  overflow: hidden;
  position: relative;
}

.metric-row :deep(.el-tabs__item),
.metric-row :deep(.el-tabs__header) {
  /* 防止 tab 样式继承干扰 */
}

/* 表格卡片 */
.table-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 20px;
  margin-top: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 响应式 */
@media (max-width: 1400px) {
  .metric-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1100px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .metric-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
