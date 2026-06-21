import request from './request'

export function getLimitationList(params) {
  return request({ url: '/limitation/', method: 'get', params })
}

export function getLimitationDashboard() {
  return request({ url: '/limitation/dashboard', method: 'get' })
}

export function interruptLimitation(id, data) {
  return request({ url: `/limitation/${id}/interrupt`, method: 'post', data })
}

export function getLimitationHistory(id) {
  return request({ url: `/limitation/${id}/history`, method: 'get' })
}
