import request from './request'

export function getUserList(params) {
  return request({ url: '/system/users', method: 'get', params })
}

export function createUser(data) {
  return request({ url: '/system/users', method: 'post', data })
}

export function updateUser(id, data) {
  return request({ url: `/system/users/${id}`, method: 'put', data })
}

export function deleteUser(id) {
  return request({ url: `/system/users/${id}`, method: 'delete' })
}

export function getRoleList() {
  return request({ url: '/system/roles', method: 'get' })
}

export function createRole(data) {
  return request({ url: '/system/roles', method: 'post', data })
}

export function updateRole(id, data) {
  return request({ url: `/system/roles/${id}`, method: 'put', data })
}

export function deleteRole(id) {
  return request({ url: `/system/roles/${id}`, method: 'delete' })
}

export function updateRolePermissions(id, permIds) {
  return request({ url: `/system/roles/${id}/permissions`, method: 'put', data: { perm_ids: permIds } })
}

export function getPermissionList() {
  return request({ url: '/system/permissions', method: 'get' })
}

export function getOperationLogs(params) {
  return request({ url: '/system/logs', method: 'get', params })
}

export function getConfig() {
  return request({ url: '/system/config', method: 'get' })
}

export function updateConfig(data) {
  return request({ url: '/system/config', method: 'put', data })
}

export function backupDatabase() {
  return request({ url: '/system/backup', method: 'get', responseType: 'blob' })
}
