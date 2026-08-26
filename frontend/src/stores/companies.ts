import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as companiesApi from '@/api/companies'
import type { CompanyOut } from '@/types/api'

export const useCompaniesStore = defineStore('companies', () => {
  const items = ref<CompanyOut[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const search = ref('')
  const isLoading = ref(false)

  async function fetchCompanies() {
    isLoading.value = true
    try {
      const result = await companiesApi.listCompanies({
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

  async function setSearch(value: string) {
    search.value = value
    page.value = 1
    await fetchCompanies()
  }

  async function setPage(value: number) {
    page.value = value
    await fetchCompanies()
  }

  return {
    items,
    total,
    page,
    pageSize,
    search,
    isLoading,
    fetchCompanies,
    setSearch,
    setPage,
  }
})
