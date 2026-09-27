import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { useCurrentCompanyStore } from '@/stores/currentCompany'
import type { UserOut } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  // Both tokens live in httponly cookies now - the browser sends and
  // stores them on its own, and JavaScript can't read them even to
  // check whether they exist. `currentUser` is the only signal we have
  // left for "am I logged in".
  const currentUser = ref<UserOut | null>(null)

  const isAuthenticated = computed(() => currentUser.value !== null)

  function clearSession() {
    currentUser.value = null
    useCurrentCompanyStore().reset()
  }

  async function login(email: string, password: string) {
    currentUser.value = await authApi.login(email, password)
  }

  /** Exchange the refresh cookie for a new pair and refresh `currentUser`. */
  async function refresh(): Promise<void> {
    currentUser.value = await authApi.refresh()
  }

  /** Restore a session from the refresh cookie, e.g. on app load. */
  async function restoreSession() {
    if (currentUser.value) return
    try {
      await refresh()
    } catch {
      clearSession()
    }
  }

  async function logout() {
    clearSession()
    try {
      await authApi.logout()
    } catch {
      // Already logged out locally; a failed revoke call server-side
      // isn't worth surfacing to the user.
    }
  }

  return {
    currentUser,
    isAuthenticated,
    login,
    logout,
    refresh,
    restoreSession,
  }
})
