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
 *   const { options, loading, search, loadInitial } = useRemoteSearchOptions(
 *     (query) => listUsers({ search: query }).then((r) => r.items),
 *     (user) => ({ value: user.id, label: `${user.first_name} ${user.last_name}` }),
 *   )
 *   <n-select filterable remote :loading="loading" :options="options"
 *     @search="search" @focus="loadInitial" />
 */
export function useRemoteSearchOptions<T>(
  fetcher: (query: string) => Promise<T[]>,
  mapToOption: (item: T) => SelectOption,
  debounceMs = 300,
) {
  const options = ref<SelectOption[]>([])
  const loading = ref(false)

  async function runFetch(query: string) {
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
  }

  const debouncedFetch = useDebounceFn(runFetch, debounceMs)

  function search(query: string) {
    if (!query) {
      options.value = []
      return
    }
    debouncedFetch(query)
  }

  /**
   * Load an unfiltered first page as soon as the select is opened, before
   * anything is typed. Without this, a freshly opened remote select shows
   * a bare empty dropdown with no hint that typing would help - it reads
   * as broken rather than as "type to search". Not debounced (it's a
   * one-off on open, not a keystroke), and skipped if there's already
   * something to show (e.g. from a previous search).
   */
  function loadInitial() {
    if (options.value.length === 0) {
      runFetch('')
    }
  }

  return { options, loading, search, loadInitial }
}
