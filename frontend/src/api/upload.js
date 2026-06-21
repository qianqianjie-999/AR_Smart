import request from './request'

export function uploadFiles(files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  return request({
    url: '/upload/',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function downloadFile(filename) {
  return request({
    url: `/upload/${filename}`,
    method: 'get',
    responseType: 'blob'
  })
}

export function deleteFile(filename) {
  return request({
    url: `/upload/${filename}`,
    method: 'delete'
  })
}