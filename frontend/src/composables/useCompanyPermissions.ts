import { computed, type Ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { CompanyMemberOut } from '@/types/api'

/**
 * Frontend-side role gating for a single company's members list. The
 * API itself doesn't enforce role-based restrictions yet (any member can
 * manage any other member - see `apps/companies/api/views.py`), so these
 * checks are a UI-only guardrail, not a security boundary.
 *
 * Scoped to companies for now rather than written as a fully generic
 * "entity permissions" composable - Project will likely need its own
 * role model with its own rules, and we don't have a second data point
 * yet to know what's actually shared between them.
 */
export function useCompanyPermissions(members: Ref<CompanyMemberOut[]>) {
  const auth = useAuthStore()

  const currentMembership = computed(() =>
    members.value.find((member) => member.user_id === auth.currentUser?.id),
  )

  const currentRole = computed(() => currentMembership.value?.role ?? null)

  const canEditCompany = computed(() => currentRole.value === 'admin')

  const canManageMembers = computed(
    () => currentRole.value === 'admin' || currentRole.value === 'producer',
  )

  function isSelf(userId: number): boolean {
    return userId === auth.currentUser?.id
  }

  // An admin can't remove themselves or change their own role - doing so
  // could leave the company with no admin left to fix it.
  function canRemoveMember(userId: number): boolean {
    return canManageMembers.value && !isSelf(userId)
  }

  function canChangeMemberRole(userId: number): boolean {
    return canManageMembers.value && !isSelf(userId)
  }

  return {
    currentRole,
    canEditCompany,
    canManageMembers,
    isSelf,
    canRemoveMember,
    canChangeMemberRole,
  }
}
