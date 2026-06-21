import request from './request'

export function getSummaryStats() {
  return request({ url: '/report/summary', method: 'get' })
}

export function getRegionalStats() {
  return request({ url: '/report/regional', method: 'get' })
}

export function getCustomerRanking() {
  return request({ url: '/report/customer-ranking', method: 'get' })
}

export function getAgingAnalysis() {
  return request({ url: '/report/aging', method: 'get' })
}

export function getDueReceivable() {
  return request({ url: '/report/due-receivable', method: 'get' })
}

export function getPaymentTrend() {
  return request({ url: '/report/payment-trend', method: 'get' })
}

export function getLimitationStats() {
  return request({ url: '/report/limitation-stats', method: 'get' })
}

export function exportReport(reportType) {
  return request({ url: `/report/export/${reportType}`, method: 'get', responseType: 'blob' })
}
