import request from './request'

export function getCustomerList(params) {
  return request({ url: '/customer/', method: 'get', params })
}

export function getCustomerDetail(id) {
  return request({ url: `/customer/${id}`, method: 'get' })
}

export function createCustomer(data) {
  return request({ url: '/customer/', method: 'post', data })
}

export function updateCustomer(id, data) {
  return request({ url: `/customer/${id}`, method: 'put', data })
}

export function deleteCustomer(id) {
  return request({ url: `/customer/${id}`, method: 'delete' })
}

export function exportCustomers(params) {
  return request({ url: '/customer/export', method: 'get', params, responseType: 'blob' })
}

export function getCustomerRegions() {
  return request({ url: '/customer/regions', method: 'get' })
}

export function importCustomers(formData) {
  return request({ url: '/customer/import', method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
}
