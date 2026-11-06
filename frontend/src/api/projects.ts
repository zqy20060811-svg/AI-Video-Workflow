import { api } from './client'

export interface Project {
  id: number
  name: string
  story: string | null
  story_analysis?: Record<string, unknown> | null
  status: string
  aspect_ratio: string
  created_at: string
  updated_at: string
}

export interface Character {
  id: number
  project_id: number
  name: string
  description: string | null
  front_image: string | null
  side_image: string | null
  back_image: string | null
}

export interface Shot {
  id: number
  project_id: number
  shot_no: number
  scene: string | null
  location: string | null
  time: string | null
  characters: string[] | null
  action: string | null
  camera: string | null
  visual_description: string | null
  dialogue: string | null
  duration: number | null
  image_prompt: string | null
  video_prompt: string | null
  status: string
}

export interface ProjectDetail extends Project {
  characters: Character[]
  shots: Shot[]
  shot_count: number
}

export function listProjects() {
  return api.get<Project[]>('/projects')
}

export function getProject(id: number | string) {
  return api.get<ProjectDetail>(`/projects/${id}`)
}

export function createProject(data: { name: string; story?: string; aspect_ratio: string }) {
  return api.post<Project>('/projects', data)
}

export function updateProject(
  id: number | string,
  data: { name?: string; story?: string; aspect_ratio?: string }
) {
  return api.put<Project>(`/projects/${id}`, data)
}

export function createCharacter(
  projectId: number | string,
  data: { name: string; description?: string; front_image: File; side_image: File; back_image: File }
) {
  const form = new FormData()
  form.append('name', data.name)
  if (data.description) form.append('description', data.description)
  form.append('front_image', data.front_image)
  form.append('side_image', data.side_image)
  form.append('back_image', data.back_image)
  return api.post<Character>(`/projects/${projectId}/characters`, form)
}

// ---------- 分镜工作流 ----------

export function analyzeStory(projectId: number | string) {
  return api.post<{ story_analysis: Record<string, unknown> }>(
    `/projects/${projectId}/storyboard/story/analyze`,
    undefined,
    { timeout: 300000 }
  )
}

export function generateStoryboard(projectId: number | string) {
  return api.post<Shot[]>(`/projects/${projectId}/storyboard/generate`, undefined, {
    timeout: 600000
  })
}

export function confirmStoryboard(projectId: number | string) {
  return api.post<{ message: string; shot_count: number }>(
    `/projects/${projectId}/storyboard/confirm`
  )
}

export function createShot(projectId: number | string, data: Partial<Shot>) {
  return api.post<Shot>(`/projects/${projectId}/shots`, data)
}

export function updateShot(shotId: number, data: Partial<Shot>) {
  return api.put<Shot>(`/shots/${shotId}`, data)
}

export function deleteShot(shotId: number) {
  return api.delete<{ message: string }>(`/shots/${shotId}`)
}

export function reorderShots(projectId: number | string, shots: { id: number; shot_no: number }[]) {
  return api.post<{ message: string }>(`/projects/${projectId}/shots/reorder`, { shots })
}
