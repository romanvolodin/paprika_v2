import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as companiesApi from '@/api/companies'
import * as projectsApi from '@/api/projects'
import type { UpdateProjectInput } from '@/api/projects'
import type {
  CompanyMemberOut,
  ProjectMemberCreateIn,
  ProjectMemberOut,
  ProjectMembershipRole,
  ProjectOut,
} from '@/types/api'

export const useProjectDetailStore = defineStore('projectDetail', () => {
  const project = ref<ProjectOut | null>(null)
  const members = ref<ProjectMemberOut[]>([])
  // The project's company members - only an existing company member can be
  // added to the project (see apps/projects/api/views.py), so this is
  // fetched alongside the project itself to build the "add member" picker
  // from, rather than offering a system-wide user search that would 404
  // for anyone outside the company.
  const companyMembers = ref<CompanyMemberOut[]>([])
  const isLoading = ref(false)

  async function fetch(projectId: number) {
    isLoading.value = true
    try {
      const projectResult = await projectsApi.getProject(projectId)
      const [membersResult, companyMembersResult] = await Promise.all([
        projectsApi.listProjectMembers(projectId),
        companiesApi.listCompanyMembers(projectResult.company_id),
      ])
      project.value = projectResult
      members.value = membersResult.items
      companyMembers.value = companyMembersResult.items
    } finally {
      isLoading.value = false
    }
  }

  async function updateProject(projectId: number, input: UpdateProjectInput) {
    project.value = await projectsApi.updateProject(projectId, input)
  }

  async function refetchMembers(projectId: number) {
    members.value = (await projectsApi.listProjectMembers(projectId)).items
  }

  async function addMember(projectId: number, input: ProjectMemberCreateIn) {
    await projectsApi.addProjectMember(projectId, input)
    await refetchMembers(projectId)
  }

  async function updateMemberRole(projectId: number, userId: number, role: ProjectMembershipRole) {
    await projectsApi.updateProjectMember(projectId, userId, { role })
    await refetchMembers(projectId)
  }

  async function removeMember(projectId: number, userId: number) {
    await projectsApi.removeProjectMember(projectId, userId)
    await refetchMembers(projectId)
  }

  return {
    project,
    members,
    companyMembers,
    isLoading,
    fetch,
    updateProject,
    addMember,
    updateMemberRole,
    removeMember,
  }
})
