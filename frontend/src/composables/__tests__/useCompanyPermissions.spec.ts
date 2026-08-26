import { beforeEach, describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useCompanyPermissions } from '@/composables/useCompanyPermissions'
import { useAuthStore } from '@/stores/auth'
import type { CompanyMemberOut, UserOut } from '@/types/api'

function buildUser(overrides: Partial<UserOut> = {}): UserOut {
  return {
    id: 1,
    email: 'a@paprika.dev',
    first_name: 'A',
    last_name: 'One',
    avatar: null,
    is_active: true,
    date_joined: '2026-01-01T00:00:00Z',
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
    role: 'executor',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('useCompanyPermissions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('grants nothing when the current user has no membership in this company', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([buildMember({ user_id: 2, role: 'admin' })])

    const { currentRole, canEditCompany, canManageMembers } = useCompanyPermissions(members)

    expect(currentRole.value).toBeNull()
    expect(canEditCompany.value).toBe(false)
    expect(canManageMembers.value).toBe(false)
  })

  it('admin can edit the company and manage members', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([buildMember({ user_id: 1, role: 'admin' })])

    const { canEditCompany, canManageMembers } = useCompanyPermissions(members)

    expect(canEditCompany.value).toBe(true)
    expect(canManageMembers.value).toBe(true)
  })

  it('producer can manage members but not edit the company', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([buildMember({ user_id: 1, role: 'producer' })])

    const { canEditCompany, canManageMembers } = useCompanyPermissions(members)

    expect(canEditCompany.value).toBe(false)
    expect(canManageMembers.value).toBe(true)
  })

  it.each(['coordinator', 'executor', 'freelancer', 'client'] as const)(
    '%s can neither edit the company nor manage members',
    (role) => {
      const auth = useAuthStore()
      auth.currentUser = buildUser({ id: 1 })
      const members = ref<CompanyMemberOut[]>([buildMember({ user_id: 1, role })])

      const { canEditCompany, canManageMembers } = useCompanyPermissions(members)

      expect(canEditCompany.value).toBe(false)
      expect(canManageMembers.value).toBe(false)
    },
  )

  it('an admin cannot remove or change the role of their own membership', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([buildMember({ user_id: 1, role: 'admin' })])

    const { canRemoveMember, canChangeMemberRole, isSelf } = useCompanyPermissions(members)

    expect(isSelf(1)).toBe(true)
    expect(canRemoveMember(1)).toBe(false)
    expect(canChangeMemberRole(1)).toBe(false)
  })

  it('an admin can remove or change the role of someone else', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([
      buildMember({ user_id: 1, role: 'admin' }),
      buildMember({ id: 2, user_id: 2, role: 'executor' }),
    ])

    const { canRemoveMember, canChangeMemberRole, isSelf } = useCompanyPermissions(members)

    expect(isSelf(2)).toBe(false)
    expect(canRemoveMember(2)).toBe(true)
    expect(canChangeMemberRole(2)).toBe(true)
  })

  it('someone who cannot manage members cannot remove anyone, including themselves', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<CompanyMemberOut[]>([
      buildMember({ user_id: 1, role: 'executor' }),
      buildMember({ id: 2, user_id: 2, role: 'admin' }),
    ])

    const { canRemoveMember } = useCompanyPermissions(members)

    expect(canRemoveMember(1)).toBe(false)
    expect(canRemoveMember(2)).toBe(false)
  })
})
