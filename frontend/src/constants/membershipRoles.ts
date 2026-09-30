import type { MembershipRole } from '@/types/api'

// Shared between company and project members - `ProjectMembership.role`
// is a straight alias of `CompanyMembership.role` on the backend, so
// there is only ever one set of role labels to maintain.
export const MEMBERSHIP_ROLE_LABELS: Record<MembershipRole, string> = {
  admin: 'Админ',
  producer: 'Продюсер',
  coordinator: 'Координатор',
  executor: 'Исполнитель',
  freelancer: 'Фрилансер',
  client: 'Клиент',
}

export const MEMBERSHIP_ROLE_OPTIONS = (
  Object.entries(MEMBERSHIP_ROLE_LABELS) as [MembershipRole, string][]
).map(([value, label]) => ({ value, label }))
