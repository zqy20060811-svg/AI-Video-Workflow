import axios from 'axios'

const systemApi = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface ModelConfig {
  llm: { provider: string; base_url: string; model: string }
  image: { provider: string; model: string; configured: boolean }
  video: {
    provider: string
    model: string
    clip_model: string
    vae_model: string
    fps: number
    configured: boolean
  }
  comfyui_url: string
}

export interface EnvCheck {
  gpu: { available: boolean; name?: string; vram?: string; driver?: string; detail?: string }
  pytorch: { installed: boolean; version?: string; cuda_available?: boolean; detail?: string }
  comfyui: {
    reachable: boolean
    url: string
    detail?: string
    image_models?: string[]
    image_model_ready?: boolean | null
    video_models?: string[]
    video_model_ready?: boolean | null
  }
  image_provider: string
  video_provider: string
}

export function getModelConfig() {
  return systemApi.get<ModelConfig>('/system/config')
}

export function checkEnv() {
  return systemApi.get<EnvCheck>('/system/check-env')
}
