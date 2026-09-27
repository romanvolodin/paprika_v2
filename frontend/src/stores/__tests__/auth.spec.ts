import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import * as authApi from '@/api/auth'
import type { UserOut } from '@/types/api'

vi.mock('@/api/auth')

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
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts unauthenticated with no user', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.currentUser).toBeNull()
  })

  it('login stores the returned user - there are no tokens to hold, they are cookies', async () => {
    vi.mocked(authApi.login).mockResolvedValue(user)

    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')

    expect(authApi.login).toHaveBeenCalledWith('roman@paprika.dev', 'hunter2')
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.currentUser).toEqual(user)
  })

  it('refresh calls the refresh endpoint with no arguments and updates currentUser', async () => {
    const rotated = { ...user, first_name: 'Romka' }
    vi.mocked(authApi.refresh).mockResolvedValue(rotated)

    const auth = useAuthStore()
    await auth.refresh()

    expect(authApi.refresh).toHaveBeenCalledWith()
    expect(auth.currentUser).toEqual(rotated)
  })

  it('restoreSession does nothing when already authenticated', async () => {
    vi.mocked(authApi.login).mockResolvedValue(user)
    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')
    vi.mocked(authApi.refresh).mockClear()

    await auth.restoreSession()

    expect(authApi.refresh).not.toHaveBeenCalled()
  })

  it('restoreSession exchanges the refresh cookie for a session', async () => {
    vi.mocked(authApi.refresh).mockResolvedValue(user)

    const auth = useAuthStore()
    await auth.restoreSession()

    expect(auth.isAuthenticated).toBe(true)
    expect(auth.currentUser).toEqual(user)
  })

  it('restoreSession clears the session if there is no valid refresh cookie', async () => {
    vi.mocked(authApi.refresh).mockRejectedValue(new Error('401'))

    const auth = useAuthStore()
    await auth.restoreSession()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.currentUser).toBeNull()
  })

  it('logout clears local state immediately, even if the server call fails', async () => {
    vi.mocked(authApi.login).mockResolvedValue(user)
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))

    const auth = useAuthStore()
    await auth.login('roman@paprika.dev', 'hunter2')
    await auth.logout()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.currentUser).toBeNull()
    expect(authApi.logout).toHaveBeenCalledWith()
  })
})
