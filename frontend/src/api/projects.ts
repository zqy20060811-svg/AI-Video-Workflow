import { api } from './client'

export interface Project {
  id: number
  name: string
  story: string | null
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

export interface ProjectDetail extends Project {
  characters: Character[]
  shots: unknown[]
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
