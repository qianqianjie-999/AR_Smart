import request from './request'

export function getContractList(params) {
  return request({ url: '/contract/', method: 'get', params })
}

export function getContractDetail(id) {
  return request({ url: `/contract/${id}`, method: 'get' })
}

export function createContract(data) {
  return request({ url: '/contract/', method: 'post', data })
}

export function updateContract(id, data) {
  return request({ url: `/contract/${id}`, method: 'put', data })
}

export function deleteContract(id) {
  return request({ url: `/contract/${id}`, method: 'delete' })
}

export function getPaymentNodes(contractId) {
  return request({ url: `/contract/${contractId}/payment-nodes`, method: 'get' })
}

export function savePaymentNodes(contractId, nodes) {
  return request({ url: `/contract/${contractId}/payment-nodes`, method: 'put', data: { nodes } })
}

export function updatePaymentNodeStatus(contractId, nodeId, data) {
  return request({ url: `/contract/${contractId}/payment-node/${nodeId}/status`, method: 'put', data })
}

export function uploadContractFiles(id, data) {
  return request({ url: `/contract/${id}/upload`, method: 'post', data })
}

export function getOverdueInterest(contractId) {
  return request({ url: `/contract/${contractId}/overdue-interest`, method: 'get' })
}
