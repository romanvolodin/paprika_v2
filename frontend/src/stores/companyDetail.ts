import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as companiesApi from '@/api/companies'
import type {
  CompanyMemberCreateIn,
  CompanyMemberOut,
  CompanyMembershipRole,
  CompanyOut,
  CompanyUpdateIn,
} from '@/types/api'

export const useCompanyDetailStore = defineStore('companyDetail', () => {
  const company = ref<CompanyOut | null>(null)
  const members = ref<CompanyMemberOut[]>([])
  const isLoading = ref(false)

  async function fetch(companyId: number) {
    isLoading.value = true
    try {
      const [companyResult, membersResult] = await Promise.all([
        companiesApi.getCompany(companyId),
        companiesApi.listCompanyMembers(companyId),
      ])
      company.value = companyResult
      members.value = membersResult.items
    } finally {
      isLoading.value = false
    }
  }

  async function updateCompany(companyId: number, input: CompanyUpdateIn) {
    company.value = await companiesApi.updateCompany(companyId, input)
  }

  async function refetchMembers(companyId: number) {
    members.value = (await companiesApi.listCompanyMembers(companyId)).items
  }

  async function addMember(companyId: number, input: CompanyMemberCreateIn) {
    await companiesApi.addCompanyMember(companyId, input)
    await refetchMembers(companyId)
  }

  async function updateMemberRole(companyId: number, userId: number, role: CompanyMembershipRole) {
    await companiesApi.updateCompanyMember(companyId, userId, { role })
    await refetchMembers(companyId)
  }

  async function removeMember(companyId: number, userId: number) {
    await companiesApi.removeCompanyMember(companyId, userId)
    await refetchMembers(companyId)
  }

  return {
    company,
    members,
    isLoading,
    fetch,
    updateCompany,
    addMember,
    updateMemberRole,
    removeMember,
  }
})
