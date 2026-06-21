import request from './request'

export function getPaymentList(params) {
  return request({ url: '/payment/', method: 'get', params })
}

export function createPayment(data) {
  return request({ url: '/payment/', method: 'post', data })
}

export function updatePayment(id, data) {
  return request({ url: `/payment/${id}`, method: 'put', data })
}

export function deletePayment(id) {
  return request({ url: `/payment/${id}`, method: 'delete' })
}
