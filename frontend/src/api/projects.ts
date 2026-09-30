import { apiClient } from './client'
import type {
  ProjectCreateIn,
  ProjectListOut,
  ProjectListQuery,
  ProjectMemberCreateIn,
  ProjectMemberListOut,
  ProjectMemberOut,
  ProjectMemberUpdateIn,
  ProjectOut,
  ProjectUpdateIn,
} from '@/types/api'

export function listProjects(companyId: number, query: ProjectListQuery = {}) {
  return apiClient
    .get<ProjectListOut>(`/companies/${companyId}/projects/`, { params: query })
    .then((res) => res.data)
}

export function getProject(projectId: number) {
  return apiClient.get<ProjectOut>(`/projects/${projectId}/`).then((res) => res.data)
}

export function createProject(companyId: number, input: ProjectCreateIn) {
  return apiClient
    .post<ProjectOut>(`/companies/${companyId}/projects/`, input)
    .then((res) => res.data)
}

export function updateProject(projectId: number, input: ProjectUpdateIn) {
  return apiClient.patch<ProjectOut>(`/projects/${projectId}/`, input).then((res) => res.data)
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
