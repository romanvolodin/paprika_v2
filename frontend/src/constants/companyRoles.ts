import type { CompanyMembershipRole } from '@/types/api'

export const COMPANY_ROLE_LABELS: Record<CompanyMembershipRole, string> = {
  admin: 'Админ',
  producer: 'Продюсер',
  coordinator: 'Координатор',
  executor: 'Исполнитель',
  freelancer: 'Фрилансер',
  client: 'Клиент',
}

export const COMPANY_ROLE_OPTIONS = (
  Object.entries(COMPANY_ROLE_LABELS) as [CompanyMembershipRole, string][]
).map(([value, label]) => ({ value, label }))
