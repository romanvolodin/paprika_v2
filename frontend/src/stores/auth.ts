import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'
import * as authApi from '@/api/auth'
import { getMe } from '@/api/users'
import type { UserOut } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  // In-memory only: cleared on reload. Deliberate for now (see project
  // notes on cookie-based refresh before the real prod launch) - an XSS
  // could still read this while it lives, so we don't extend its
  // lifetime beyond the current tab session.
  const accessToken = ref<string | null>(null)

  // Persisted so a page reload doesn't force a re-login.
  const refreshToken = useStorage<string | null>('paprika:refresh-token', null)

  const currentUser = ref<UserOut | null>(null)

  const isAuthenticated = computed(() => accessToken.value !== null)

  function setTokens(tokens: { access_token: string; refresh_token: string }) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
  }

  function clearSession() {
    accessToken.value = null
    refreshToken.value = null
    currentUser.value = null
  }

  async function login(email: string, password: string) {
    const tokens = await authApi.login(email, password)
    setTokens(tokens)
    currentUser.value = await getMe()
  }

  /** Exchange the stored refresh token for a new pair. Returns the new access token. */
  async function refresh(): Promise<string> {
    if (!refreshToken.value) {
      throw new Error('No refresh token available.')
    }
    const tokens = await authApi.refresh(refreshToken.value)
    setTokens(tokens)
    return tokens.access_token
  }

  /** Restore a session from the persisted refresh token, e.g. on app load. */
  async function restoreSession() {
    if (!refreshToken.value || accessToken.value) return
    try {
      await refresh()
      currentUser.value = await getMe()
    } catch {
      clearSession()
    }
  }

  async function logout() {
    const tokenToRevoke = refreshToken.value
    clearSession()
    try {
      await authApi.logout(tokenToRevoke)
    } catch {
      // Already logged out locally; a failed revoke call server-side
      // isn't worth surfacing to the user.
    }
  }

  return {
    accessToken,
    currentUser,
    isAuthenticated,
    login,
    logout,
    refresh,
    restoreSession,
  }
})
