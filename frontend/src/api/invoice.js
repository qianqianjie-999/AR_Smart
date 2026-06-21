import request from './request'

export function getInvoiceList(params) {
  return request({ url: '/invoice/', method: 'get', params })
}

export function createInvoice(data) {
  return request({ url: '/invoice/', method: 'post', data })
}

export function updateInvoice(id, data) {
  return request({ url: `/invoice/${id}`, method: 'put', data })
}

export function deleteInvoice(id) {
  return request({ url: `/invoice/${id}`, method: 'delete' })
}

export function uploadInvoiceFile(id, data) {
  return request({ url: `/invoice/${id}/upload`, method: 'post', data })
}
