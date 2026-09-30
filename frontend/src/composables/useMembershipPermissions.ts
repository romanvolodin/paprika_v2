import { computed, type Ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { MembershipRole } from '@/types/api'

interface MemberLike {
  user_id: number
  role: MembershipRole
}

/**
 * Frontend-side role gating shared by company and project members lists.
 * The API itself doesn't enforce role-based restrictions yet (any member
 * can manage any other member - see `apps/companies/api/views.py` and
 * `apps/projects/api/views.py`), so these checks are a UI-only
 * guardrail, not a security boundary.
 *
 * `ProjectMembership.role` is a straight alias of `CompanyMembership.role`
 * on the backend (same enum, same values), so both `useCompanyPermissions`
 * and `useProjectPermissions` are thin wrappers around this one
 * implementation rather than each carrying their own copy of the rules.
 */
export function useMembershipPermissions<T extends MemberLike>(members: Ref<T[]>) {
  const auth = useAuthStore()

  const currentMembership = computed(() =>
    members.value.find((member) => member.user_id === auth.currentUser?.id),
  )

  const currentRole = computed(() => currentMembership.value?.role ?? null)

  const canEdit = computed(() => currentRole.value === 'admin')

  const canManageMembers = computed(
    () => currentRole.value === 'admin' || currentRole.value === 'producer',
  )

  function isSelf(userId: number): boolean {
    return userId === auth.currentUser?.id
  }

  // An admin can't remove themselves or change their own role - doing so
  // could leave the company/project with no admin left to fix it.
  function canRemoveMember(userId: number): boolean {
    return canManageMembers.value && !isSelf(userId)
  }

  function canChangeMemberRole(userId: number): boolean {
    return canManageMembers.value && !isSelf(userId)
  }

  return {
    currentRole,
    canEdit,
    canManageMembers,
    isSelf,
    canRemoveMember,
    canChangeMemberRole,
  }
}
