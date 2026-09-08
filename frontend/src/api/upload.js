import request from './request'

// 上传本地图片，返回 { url }（形如 /api/uploads/<uuid>.<ext>）
// 覆盖全局 10s 超时：本地上传大图需要更长时间
export const uploadImage = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return request.post('/upload', fd, { timeout: 60000 })
}
