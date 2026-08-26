import { useRemoteSearchOptions } from './useRemoteSearchOptions'
import { listUsers } from '@/api/users'
import type { UserOut } from '@/types/api'

/**
 * Configures `useRemoteSearchOptions` for picking an existing user - used
 * wherever a person needs to be attached to something (company members
 * today; assignees on shots/tasks later). Each option carries the raw
 * `UserOut` under `user` so callers can render a custom label (e.g. an
 * avatar) via `<n-select :render-label>`.
 */
export function useUserSearchOptions() {
  return useRemoteSearchOptions(
    (query: string) => listUsers({ search: query, page_size: 10 }).then((result) => result.items),
    (user: UserOut) => ({
      value: user.id,
      label: `${user.first_name} ${user.last_name}`,
      user,
    }),
  )
}
