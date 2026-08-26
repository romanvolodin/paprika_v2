import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCompanyDetailStore } from '@/stores/companyDetail'
import * as companiesApi from '@/api/companies'
import type { CompanyMemberOut, CompanyOut } from '@/types/api'

vi.mock('@/api/companies')

function buildCompany(overrides: Partial<CompanyOut> = {}): CompanyOut {
  return {
    id: 1,
    name: 'Acme Studio',
    slug: 'acme-studio',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function buildMember(overrides: Partial<CompanyMemberOut> = {}): CompanyMemberOut {
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

describe('useCompanyDetailStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetch', () => {
    it('loads the company and its members together', async () => {
      vi.mocked(companiesApi.getCompany).mockResolvedValue(buildCompany())
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({
        items: [buildMember()],
      })

      const store = useCompanyDetailStore()
      await store.fetch(1)

      expect(companiesApi.getCompany).toHaveBeenCalledWith(1)
      expect(companiesApi.listCompanyMembers).toHaveBeenCalledWith(1)
      expect(store.company).toEqual(buildCompany())
      expect(store.members).toHaveLength(1)
      expect(store.isLoading).toBe(false)
    })

    it('sets isLoading while the fetch is in flight', async () => {
      let resolveCompany!: (value: CompanyOut) => void
      vi.mocked(companiesApi.getCompany).mockReturnValue(
        new Promise((resolve) => {
          resolveCompany = resolve
        }),
      )
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({ items: [] })

      const store = useCompanyDetailStore()
      const pending = store.fetch(1)
      expect(store.isLoading).toBe(true)

      resolveCompany(buildCompany())
      await pending

      expect(store.isLoading).toBe(false)
    })
  })

  describe('updateCompany', () => {
    it('replaces the local company with the server response', async () => {
      vi.mocked(companiesApi.updateCompany).mockResolvedValue(buildCompany({ name: 'Renamed' }))

      const store = useCompanyDetailStore()
      await store.updateCompany(1, { name: 'Renamed' })

      expect(companiesApi.updateCompany).toHaveBeenCalledWith(1, { name: 'Renamed' })
      expect(store.company?.name).toBe('Renamed')
    })
  })

  describe('addMember', () => {
    it('adds the member then refetches the members list', async () => {
      vi.mocked(companiesApi.addCompanyMember).mockResolvedValue(buildMember())
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({
        items: [buildMember()],
      })

      const store = useCompanyDetailStore()
      await store.addMember(1, { user_id: 1, role: 'executor' })

      expect(companiesApi.addCompanyMember).toHaveBeenCalledWith(1, {
        user_id: 1,
        role: 'executor',
      })
      expect(companiesApi.listCompanyMembers).toHaveBeenCalledWith(1)
      expect(store.members).toHaveLength(1)
    })
  })

  describe('updateMemberRole', () => {
    it('updates the role then refetches the members list', async () => {
      vi.mocked(companiesApi.updateCompanyMember).mockResolvedValue(
        buildMember({ role: 'coordinator' }),
      )
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({
        items: [buildMember({ role: 'coordinator' })],
      })

      const store = useCompanyDetailStore()
      await store.updateMemberRole(1, 1, 'coordinator')

      expect(companiesApi.updateCompanyMember).toHaveBeenCalledWith(1, 1, {
        role: 'coordinator',
      })
      expect(store.members[0]?.role).toBe('coordinator')
    })
  })

  describe('removeMember', () => {
    it('removes the member then refetches the members list', async () => {
      vi.mocked(companiesApi.removeCompanyMember).mockResolvedValue(
        undefined as unknown as Awaited<ReturnType<typeof companiesApi.removeCompanyMember>>,
      )
      vi.mocked(companiesApi.listCompanyMembers).mockResolvedValue({ items: [] })

      const store = useCompanyDetailStore()
      await store.removeMember(1, 1)

      expect(companiesApi.removeCompanyMember).toHaveBeenCalledWith(1, 1)
      expect(store.members).toHaveLength(0)
    })
  })
})
