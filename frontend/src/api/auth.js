import request from './request'

export function login(username, password) {
  return request({
    url: '/auth/login',
    method: 'post',
    data: { username, password }
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/userinfo',
    method: 'get'
  })
}

export function changePassword(data) {
  return request({
    url: '/auth/password',
    method: 'put',
    data
  })
}
