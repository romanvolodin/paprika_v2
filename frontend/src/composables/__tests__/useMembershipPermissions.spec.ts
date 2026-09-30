import { beforeEach, describe, expect, it } from 'vitest'
import { ref } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useMembershipPermissions } from '@/composables/useMembershipPermissions'
import { useAuthStore } from '@/stores/auth'
import type { MembershipRole, UserOut } from '@/types/api'

interface Member {
  user_id: number
  role: MembershipRole
}

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

function buildMember(overrides: Partial<Member> = {}): Member {
  return { user_id: 1, role: 'executor', ...overrides }
}

describe('useMembershipPermissions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('grants nothing when the current user has no membership in the list', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([buildMember({ user_id: 2, role: 'admin' })])

    const { currentRole, canEdit, canManageMembers } = useMembershipPermissions(members)

    expect(currentRole.value).toBeNull()
    expect(canEdit.value).toBe(false)
    expect(canManageMembers.value).toBe(false)
  })

  it('admin can edit and manage members', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([buildMember({ user_id: 1, role: 'admin' })])

    const { canEdit, canManageMembers } = useMembershipPermissions(members)

    expect(canEdit.value).toBe(true)
    expect(canManageMembers.value).toBe(true)
  })

  it('producer can manage members but not edit', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([buildMember({ user_id: 1, role: 'producer' })])

    const { canEdit, canManageMembers } = useMembershipPermissions(members)

    expect(canEdit.value).toBe(false)
    expect(canManageMembers.value).toBe(true)
  })

  it.each(['coordinator', 'executor', 'freelancer', 'client'] as const)(
    '%s can neither edit nor manage members',
    (role) => {
      const auth = useAuthStore()
      auth.currentUser = buildUser({ id: 1 })
      const members = ref<Member[]>([buildMember({ user_id: 1, role })])

      const { canEdit, canManageMembers } = useMembershipPermissions(members)

      expect(canEdit.value).toBe(false)
      expect(canManageMembers.value).toBe(false)
    },
  )

  it('an admin cannot remove or change the role of their own membership', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([buildMember({ user_id: 1, role: 'admin' })])

    const { canRemoveMember, canChangeMemberRole, isSelf } = useMembershipPermissions(members)

    expect(isSelf(1)).toBe(true)
    expect(canRemoveMember(1)).toBe(false)
    expect(canChangeMemberRole(1)).toBe(false)
  })

  it('an admin can remove or change the role of someone else', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([
      buildMember({ user_id: 1, role: 'admin' }),
      buildMember({ user_id: 2, role: 'executor' }),
    ])

    const { canRemoveMember, canChangeMemberRole, isSelf } = useMembershipPermissions(members)

    expect(isSelf(2)).toBe(false)
    expect(canRemoveMember(2)).toBe(true)
    expect(canChangeMemberRole(2)).toBe(true)
  })

  it('someone who cannot manage members cannot remove anyone, including themselves', () => {
    const auth = useAuthStore()
    auth.currentUser = buildUser({ id: 1 })
    const members = ref<Member[]>([
      buildMember({ user_id: 1, role: 'executor' }),
      buildMember({ user_id: 2, role: 'admin' }),
    ])

    const { canRemoveMember } = useMembershipPermissions(members)

    expect(canRemoveMember(1)).toBe(false)
    expect(canRemoveMember(2)).toBe(false)
  })
})
