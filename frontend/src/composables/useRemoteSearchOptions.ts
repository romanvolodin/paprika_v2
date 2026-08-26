import { ref } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import type { SelectOption } from 'naive-ui'

/**
 * Powers a `<n-select filterable remote>` from any async search function:
 * debounces keystrokes, tracks `loading`, and keeps `options` in sync.
 *
 * Entity-agnostic on purpose - it doesn't know about users, shots, tasks,
 * or anything else. Per-entity wrappers (`useUserSearchOptions`, and
 * later `useShotSearchOptions`, ...) configure it with a fetcher and a
 * mapping function; this composable is written and tested once.
 *
 * Usage:
 *   const { options, loading, search } = useRemoteSearchOptions(
 *     (query) => listUsers({ search: query }).then((r) => r.items),
 *     (user) => ({ value: user.id, label: `${user.first_name} ${user.last_name}` }),
 *   )
 *   <n-select filterable remote :loading="loading" :options="options" @search="search" />
 */
export function useRemoteSearchOptions<T>(
  fetcher: (query: string) => Promise<T[]>,
  mapToOption: (item: T) => SelectOption,
  debounceMs = 300,
) {
  const options = ref<SelectOption[]>([])
  const loading = ref(false)

  const debouncedFetch = useDebounceFn(async (query: string) => {
    loading.value = true
    try {
      const items = await fetcher(query)
      options.value = items.map(mapToOption)
    } catch {
      // A failed search shouldn't crash the UI - just show no results.
      options.value = []
    } finally {
      loading.value = false
    }
  }, debounceMs)

  function search(query: string) {
    if (!query) {
      options.value = []
      return
    }
    debouncedFetch(query)
  }

  return { options, loading, search }
}
