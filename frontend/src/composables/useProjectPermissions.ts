import type { Ref } from 'vue'
import { useMembershipPermissions } from './useMembershipPermissions'
import type { ProjectMemberOut } from '@/types/api'

/**
 * Project-flavored view over `useMembershipPermissions` - see there for
 * the shared rules, and `useCompanyPermissions` for the company-side
 * equivalent.
 */
export function useProjectPermissions(members: Ref<ProjectMemberOut[]>) {
  const { canEdit, ...rest } = useMembershipPermissions(members)

  return { canEditProject: canEdit, ...rest }
}
