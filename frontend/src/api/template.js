import request from './request'

export function getTemplateList(params) {
  return request({ url: '/template/', method: 'get', params })
}

export function getTemplateDetail(id) {
  return request({ url: `/template/${id}`, method: 'get' })
}

export function createTemplate(data) {
  return request({ url: '/template/', method: 'post', data })
}

export function updateTemplate(id, data) {
  return request({ url: `/template/${id}`, method: 'put', data })
}

export function deleteTemplate(id) {
  return request({ url: `/template/${id}`, method: 'delete' })
}

export function getTemplateTypes() {
  return request({ url: '/template/types', method: 'get' })
}

export function getDefaultTemplate(type) {
  return request({ url: `/template/default/${type}`, method: 'get' })
}