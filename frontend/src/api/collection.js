import request from './request'

export function getCollectionList(params) {
  return request({ url: '/collection/', method: 'get', params })
}

export function createCollection(data) {
  return request({ url: '/collection/', method: 'post', data })
}

export function updateCollection(id, data) {
  return request({ url: `/collection/${id}`, method: 'put', data })
}

export function deleteCollection(id) {
  return request({ url: `/collection/${id}`, method: 'delete' })
}

export function uploadCollectionFile(id, data) {
  return request({ url: `/collection/${id}/upload`, method: 'post', data })
}
