import { apiClient } from './client'
import type {
  ProjectListOut,
  ProjectListQuery,
  ProjectMemberCreateIn,
  ProjectMemberListOut,
  ProjectMemberOut,
  ProjectMemberUpdateIn,
  ProjectOut,
} from '@/types/api'

export function listProjects(companyId: number, query: ProjectListQuery = {}) {
  return apiClient
    .get<ProjectListOut>(`/companies/${companyId}/projects/`, { params: query })
    .then((res) => res.data)
}

export function getProject(projectId: number) {
  return apiClient.get<ProjectOut>(`/projects/${projectId}/`).then((res) => res.data)
}

export interface CreateProjectInput {
  name: string
  code: string
  description?: string
  startDate?: string | null
  deadline?: string | null
  cover?: File | null
}

// The endpoint only accepts `multipart/form-data` now that it can take a
// `cover` file (mirrors `apps/users/api/views.py`'s avatar handling) -
// note that a `null` start_date/deadline is simply omitted rather than
// sent, since FormData has no way to represent "null" the way a JSON
// body did; omitted is fine here since there's nothing to clear yet.
export function createProject(companyId: number, input: CreateProjectInput) {
  const form = new FormData()
  form.append('name', input.name)
  form.append('code', input.code)
  if (input.description) form.append('description', input.description)
  if (input.startDate) form.append('start_date', input.startDate)
  if (input.deadline) form.append('deadline', input.deadline)
  if (input.cover) form.append('cover', input.cover)

  return apiClient
    .post<ProjectOut>(`/companies/${companyId}/projects/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}

export interface UpdateProjectInput {
  name?: string
  description?: string
  startDate?: string | null
  deadline?: string | null
  isActive?: boolean
  removeCover?: boolean
  cover?: File | null
}

// Same multipart requirement as `createProject` - see the note there
// about `null` start_date/deadline. Clearing an already-set date back
// to empty isn't supported yet (unlike `cover`, there's no
// `remove_start_date`/`remove_deadline` flag); changing it to a
// different date works fine.
export function updateProject(projectId: number, input: UpdateProjectInput) {
  const form = new FormData()
  if (input.name != null) form.append('name', input.name)
  if (input.description != null) form.append('description', input.description)
  if (input.startDate) form.append('start_date', input.startDate)
  if (input.deadline) form.append('deadline', input.deadline)
  if (input.isActive !== undefined) form.append('is_active', String(input.isActive))
  if (input.removeCover) form.append('remove_cover', 'true')
  if (input.cover) form.append('cover', input.cover)

  return apiClient
    .patch<ProjectOut>(`/projects/${projectId}/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}

export function deleteProject(projectId: number) {
  return apiClient.delete<void>(`/projects/${projectId}/`)
}

export function listProjectMembers(projectId: number) {
  return apiClient
    .get<ProjectMemberListOut>(`/projects/${projectId}/members/`)
    .then((res) => res.data)
}

export function addProjectMember(projectId: number, input: ProjectMemberCreateIn) {
  return apiClient
    .post<ProjectMemberOut>(`/projects/${projectId}/members/`, input)
    .then((res) => res.data)
}

export function updateProjectMember(
  projectId: number,
  userId: number,
  input: ProjectMemberUpdateIn,
) {
  return apiClient
    .patch<ProjectMemberOut>(`/projects/${projectId}/members/${userId}/`, input)
    .then((res) => res.data)
}

export function removeProjectMember(projectId: number, userId: number) {
  return apiClient.delete<void>(`/projects/${projectId}/members/${userId}/`)
}
