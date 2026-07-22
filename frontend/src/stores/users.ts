import { ref } from 'vue'
import { defineStore } from 'pinia'
import * as usersApi from '@/api/users'
import type { UserOut } from '@/types/api'

export const useUsersStore = defineStore('users', () => {
  const items = ref<UserOut[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const search = ref('')
  const isLoading = ref(false)

  async function fetchUsers() {
    isLoading.value = true
    try {
      const result = await usersApi.listUsers({
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
    await fetchUsers()
  }

  async function setPage(value: number) {
    page.value = value
    await fetchUsers()
  }

  async function removeUser(userId: number) {
    await usersApi.deleteUser(userId)
    await fetchUsers()
  }

  return {
    items,
    total,
    page,
    pageSize,
    search,
    isLoading,
    fetchUsers,
    setSearch,
    setPage,
    removeUser,
  }
})
