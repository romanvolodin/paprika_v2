import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import * as authApi from '@/api/auth'
import * as usersApi from '@/api/users'
import type { UserOut } from '@/types/api'

vi.mock('@/api/auth')
vi.mock('@/api/users')

const tokens = { access_token: 'access-1', refresh_token: 'refresh-1' }
const user: UserOut = {
  id: 1,
  email: 'roman@paprika.dev',
  first_name: 'Roman',
  last_name: 'Volodin',
  avatar: null,
  is_active: true,
  date_joined: '2026-01-01T00:00:00Z',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts unauthenticated with no user', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.currentUser).toBeNull()
  })

  it('login stores tokens and fetches the current user', async () => {
    vi.mocked(authApi.login).mockResolvedValue(tokens)
    vi.mocked(usersApi.getMe).mockResolvedValue(user)

    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')
    await nextTick()

    expect(authApi.login).toHaveBeenCalledWith('roman@paprika.dev', 'hunter2')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.accessToken).toBe('access-1')
    expect(auth.currentUser).toEqual(user)
    // Refresh token is the only thing persisted across reloads, stored
    // as a plain string (VueUse doesn't JSON-wrap string-typed values).
    expect(localStorage.getItem('paprika:refresh-token')).toBe('refresh-1')
  })

  it('refresh throws when there is no refresh token to exchange', async () => {
    const auth = useAuthStore()
    await expect(auth.refresh()).rejects.toThrow('No refresh token available.')
    expect(authApi.refresh).not.toHaveBeenCalled()
  })

  it('refresh exchanges the stored refresh token for a new pair', async () => {
    vi.mocked(authApi.login).mockResolvedValue(tokens)
    vi.mocked(usersApi.getMe).mockResolvedValue(user)
    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')

    const rotated = { access_token: 'access-2', refresh_token: 'refresh-2' }
    vi.mocked(authApi.refresh).mockResolvedValue(rotated)

    const newAccessToken = await auth.refresh()

    expect(authApi.refresh).toHaveBeenCalledWith('refresh-1')
    expect(newAccessToken).toBe('access-2')
    expect(auth.accessToken).toBe('access-2')
  })

  it('restoreSession does nothing when there is no persisted refresh token', async () => {
    const auth = useAuthStore()
    await auth.restoreSession()
    expect(authApi.refresh).not.toHaveBeenCalled()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('restoreSession does nothing when already authenticated', async () => {
    localStorage.setItem('paprika:refresh-token', 'refresh-1')
    const auth = useAuthStore()
    auth.accessToken = 'already-set'

    await auth.restoreSession()

    expect(authApi.refresh).not.toHaveBeenCalled()
  })

  it('restoreSession exchanges a persisted refresh token for a session', async () => {
    localStorage.setItem('paprika:refresh-token', 'refresh-1')
    vi.mocked(authApi.refresh).mockResolvedValue(tokens)
    vi.mocked(usersApi.getMe).mockResolvedValue(user)

    const auth = useAuthStore()
    await auth.restoreSession()

    expect(auth.isAuthenticated).toBe(true)
    expect(auth.currentUser).toEqual(user)
  })

  it('restoreSession clears the session if the refresh token is rejected', async () => {
    localStorage.setItem('paprika:refresh-token', 'stale-token')
    vi.mocked(authApi.refresh).mockRejectedValue(new Error('token revoked'))

    const auth = useAuthStore()
    await auth.restoreSession()
    await nextTick()

    expect(auth.isAuthenticated).toBe(false)
    // Clearing the ref removes the key entirely rather than writing "null".
    expect(localStorage.getItem('paprika:refresh-token')).toBeNull()
  })

  it('logout clears local state immediately, even if the server call fails', async () => {
    vi.mocked(authApi.login).mockResolvedValue(tokens)
    vi.mocked(usersApi.getMe).mockResolvedValue(user)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))

    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')
    await auth.logout()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.currentUser).toBeNull()
    // Revokes the token that was active *before* clearing, not `null`.
    expect(authApi.logout).toHaveBeenCalledWith('refresh-1')
  })
})
