import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useProjectDetailStore } from '@/stores/projectDetail'
import * as companiesApi from '@/api/companies'
import * as projectsApi from '@/api/projects'
import type { CompanyMemberOut, ProjectMemberOut, ProjectOut } from '@/types/api'

vi.mock('@/api/projects')
vi.mock('@/api/companies')

function buildProject(overrides: Partial<ProjectOut> = {}): ProjectOut {
  return {
    id: 1,
    company_id: 7,
    name: 'Feature Film',
    code: 'PRJ',
    description: '',
    cover: null,
    start_date: null,
    deadline: null,
    is_active: true,
    created_by: null,
    updated_by: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function buildMember(overrides: Partial<ProjectMemberOut> = {}): ProjectMemberOut {
  return {
    id: 1,
    user_id: 1,
    email: 'a@paprika.dev',
    first_name: 'A',
    last_name: 'One',
    role: 'admin',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function buildCompanyMember(overrides: Partial<CompanyMemberOut> = {}): CompanyMemberOut {
  return {
    id: 1,
    user_id: 1,
    email: 'a@paprika.dev',
    first_name: 'A',
    last_name: 'One',
    role: 'admin',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('useProjectDetailStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetch', () => {
    it('loads the project, its members, and its company members together', async () => {
      vi.mocked(projectsApi.getProject).mockResolvedValue(buildProject({ company_id: 7 }))
      vi.mocked(projectsApi.listProjectMembers).mockResolvedValue({
        items: [buildMember()],
      })
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({
        items: [buildCompanyMember(), buildCompanyMember({ user_id: 2 })],
      })

      const store = useProjectDetailStore()
      await store.fetch(1)

      expect(projectsApi.getProject).toHaveBeenCalledWith(1)
      expect(projectsApi.listProjectMembers).toHaveBeenCalledWith(1)
      // The company to fetch members for comes from the project itself,
      // not from the caller.
      expect(companiesApi.listCompanyMembers).toHaveBeenCalledWith(7)
      expect(store.project).toEqual(buildProject({ company_id: 7 }))
      expect(store.members).toHaveLength(1)
      expect(store.companyMembers).toHaveLength(2)
      expect(store.isLoading).toBe(false)
    })

    it('sets isLoading while the fetch is in flight', async () => {
      let resolveProject!: (value: ProjectOut) => void
      vi.mocked(projectsApi.getProject).mockReturnValue(
        new Promise((resolve) => {
          resolveProject = resolve
        }),
      )
      vi.mocked(projectsApi.listProjectMembers).mockResolvedValue({ items: [] })
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({ items: [] })

      const store = useProjectDetailStore()
      const pending = store.fetch(1)
      expect(store.isLoading).toBe(true)

      resolveProject(buildProject())
      await pending

      expect(store.isLoading).toBe(false)
    })
  })

  describe('updateProject', () => {
    it('replaces the local project with the server response', async () => {
      vi.mocked(projectsApi.updateProject).mockResolvedValue(buildProject({ name: 'Renamed' }))

      const store = useProjectDetailStore()
      await store.updateProject(1, { name: 'Renamed' })

      expect(projectsApi.updateProject).toHaveBeenCalledWith(1, { name: 'Renamed' })
      expect(store.project?.name).toBe('Renamed')
    })
  })

  describe('addMember', () => {
    it('adds the member then refetches the members list', async () => {
      vi.mocked(projectsApi.addProjectMember).mockResolvedValue(buildMember())
      vi.mocked(projectsApi.listProjectMembers).mockResolvedValue({
        items: [buildMember()],
      })

      const store = useProjectDetailStore()
      await store.addMember(1, { user_id: 1, role: 'executor' })

      expect(projectsApi.addProjectMember).toHaveBeenCalledWith(1, {
        user_id: 1,
        role: 'executor',
      })
      expect(projectsApi.listProjectMembers).toHaveBeenCalledWith(1)
      expect(store.members).toHaveLength(1)
    })
  })

  describe('updateMemberRole', () => {
    it('updates the role then refetches the members list', async () => {
      vi.mocked(projectsApi.updateProjectMember).mockResolvedValue(
        buildMember({ role: 'coordinator' }),
      )
      vi.mocked(projectsApi.listProjectMembers).mockResolvedValue({
        items: [buildMember({ role: 'coordinator' })],
      })

      const store = useProjectDetailStore()
      await store.updateMemberRole(1, 1, 'coordinator')

      expect(projectsApi.updateProjectMember).toHaveBeenCalledWith(1, 1, {
        role: 'coordinator',
      })
      expect(store.members[0]?.role).toBe('coordinator')
    })
  })

  describe('removeMember', () => {
    it('removes the member then refetches the members list', async () => {
      vi.mocked(projectsApi.removeProjectMember).mockResolvedValue(
        undefined as unknown as Awaited<ReturnType<typeof projectsApi.removeProjectMember>>,
      )
      vi.mocked(projectsApi.listProjectMembers).mockResolvedValue({ items: [] })

      const store = useProjectDetailStore()
      await store.removeMember(1, 1)

      expect(projectsApi.removeProjectMember).toHaveBeenCalledWith(1, 1)
      expect(store.members).toHaveLength(0)
    })
  })
})
