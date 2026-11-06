import axios from 'axios'

// 生成任务可能耗时数分钟，使用独立的超时配置
const mediaApi = axios.create({
  baseURL: '/api',
  timeout: 660000
})

export interface Asset {
  id: number
  project_id: number
  shot_id: number | null
  asset_type: string // scene_image | shot_video | character_reference
  file_path: string
  version: number
  status: string // ready | confirmed
  provider: string
  model: string
  prompt: string | null
  created_at: string
}

export function listShotAssets(shotId: number) {
  return mediaApi.get<Asset[]>(`/shots/${shotId}/assets`)
}

export function generateSceneImage(shotId: number) {
  return mediaApi.post<Asset>(`/shots/${shotId}/images/generate`)
}

export function confirmSceneImage(shotId: number) {
  return mediaApi.post<Asset>(`/shots/${shotId}/images/confirm`)
}

export function generateShotVideo(shotId: number) {
  return mediaApi.post<Asset>(`/shots/${shotId}/videos/generate`)
}

export function confirmShotVideo(shotId: number) {
  return mediaApi.post<Asset>(`/shots/${shotId}/videos/confirm`)
}

export function uploadShotImage(shotId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  return mediaApi.post<Asset>(`/shots/${shotId}/images/upload`, form)
}

export function uploadShotVideo(shotId: number, file: File) {
  const form = new FormData()
  form.append('file', file)
  return mediaApi.post<Asset>(`/shots/${shotId}/videos/upload`, form)
}

export function storageUrl(filePath: string) {
  return `/storage/${filePath.replace(/\\/g, '/')}`
}
