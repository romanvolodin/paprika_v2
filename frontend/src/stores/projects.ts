import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as projectsApi from '@/api/projects'
import type { ProjectOut } from '@/types/api'

/**
 * Unlike companies, projects only ever make sense within a company - so
 * every fetch here needs a `companyId`. The store remembers the last one
 * it was asked for so `setSearch`/`setPage` can refetch without the
 * caller re-passing it every time (mirrors `useCompaniesStore`'s shape
 * otherwise).
 */
export const useProjectsStore = defineStore('projects', () => {
  const items = ref<ProjectOut[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const search = ref('')
  const isLoading = ref(false)

  let currentCompanyId: number | null = null

  async function fetchProjects(companyId: number) {
    currentCompanyId = companyId
    isLoading.value = true
    try {
      const result = await projectsApi.listProjects(companyId, {
        page: page.value,
        page_size: pageSize.value,
        search: search.value || undefined,
      })
      items.value = result.items
      total.value = result.total
      page.value = result.page
      pageSize.value = result.page_size
    } finally {
      isLoading.value = false
    }
  }

  async function refetch() {
    if (currentCompanyId !== null) {
      await fetchProjects(currentCompanyId)
    }
  }

  async function setSearch(value: string) {
    search.value = value
    page.value = 1
    await refetch()
  }

  async function setPage(value: number) {
    page.value = value
    await refetch()
  }

  return {
    items,
    total,
    page,
    pageSize,
    search,
    isLoading,
    fetchProjects,
    setSearch,
    setPage,
  }
})
