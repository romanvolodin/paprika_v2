import type { Ref } from 'vue'
import { useMembershipPermissions } from './useMembershipPermissions'
import type { CompanyMemberOut } from '@/types/api'

/**
 * Company-flavored view over `useMembershipPermissions` - see there for
 * the shared rules. Kept as its own named export (rather than having
 * call sites use the generic composable directly) so `canEditCompany`
 * reads clearly at each call site.
 */
export function useCompanyPermissions(members: Ref<CompanyMemberOut[]>) {
  const { canEdit, ...rest } = useMembershipPermissions(members)

  return { canEditCompany: canEdit, ...rest }
}
