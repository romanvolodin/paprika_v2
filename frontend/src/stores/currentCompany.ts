import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'
import * as companiesApi from '@/api/companies'
import type { CompanyOut } from '@/types/api'

export const useCurrentCompanyStore = defineStore('currentCompany', () => {
  const storedId = useStorage<string | null>('paprika:current-company-id', null, undefined, {
    listenToStorageChanges: false,
  })

  const companies = ref<CompanyOut[]>([])
  const isLoading = ref(false)
  const isInitialized = ref(false)

  const currentCompanyId = computed<number | null>(() =>
    storedId.value ? Number(storedId.value) : null,
  )

  const currentCompany = computed<CompanyOut | null>(
    () => companies.value.find((company) => company.id === currentCompanyId.value) ?? null,
  )

  const needsSelection = computed(
    () => isInitialized.value && companies.value.length > 1 && currentCompany.value === null,
  )

  async function loadCompanies() {
    isLoading.value = true
    try {
      const result = await companiesApi.listCompanies({ page_size: 100 })
      companies.value = result.items
    } finally {
      isLoading.value = false
    }
  }

  function resolveSelection() {
    const storedIsValid = companies.value.some((company) => company.id === currentCompanyId.value)
    if (!storedIsValid) {
      storedId.value = companies.value.length === 1 ? String(companies.value[0].id) : null
    }
  }

  /**
   * Load the user's companies and resolve which one is active.
   *
   * Called once per session (on login and on reload, from the router
   * guard) - never forces navigation. If the stored id is missing or
   * no longer valid (e.g. removed from the company), it's cleared and,
   * when there's exactly one company to fall back on, silently
   * reselected. Otherwise the switcher itself prompts for a pick.
   */
  async function initialize() {
    await loadCompanies()
    resolveSelection()
    isInitialized.value = true
  }

  async function refreshCompanies() {
    await loadCompanies()
    resolveSelection()
  }

  function selectCompany(companyId: number) {
    storedId.value = String(companyId)
  }

  function reset() {
    storedId.value = null
    companies.value = []
    isInitialized.value = false
  }

  return {
    companies,
    currentCompanyId,
    currentCompany,
    isLoading,
    isInitialized,
    needsSelection,
    initialize,
    loadCompanies,
    refreshCompanies,
    selectCompany,
    reset,
  }
})
