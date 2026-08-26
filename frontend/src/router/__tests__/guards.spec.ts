import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { setupAuthGuard } from '@/router/guards'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/api/auth')
vi.mock('@/api/users')

function buildRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', name: 'login', component: { template: '<div />' }, meta: {} },
      {
        path: '/users',
        name: 'users-list',
        component: { template: '<div />' },
        meta: { requiresAuth: true },
      },
    ],
  })
  setupAuthGuard(router)
  return router
}

describe('setupAuthGuard', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('redirects an unauthenticated visitor away from a protected route, preserving the destination', async () => {
    const router = buildRouter()

    await router.push('/users')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/users')
  })

  it('lets an authenticated visitor through to a protected route', async () => {
    const router = buildRouter()
    const auth = useAuthStore()
    auth.accessToken = 'a-valid-token'

    await router.push('/users')

    expect(router.currentRoute.value.name).toBe('users-list')
  })

  it('redirects an already-authenticated visitor away from the login page', async () => {
    const router = buildRouter()
    const auth = useAuthStore()
    auth.accessToken = 'a-valid-token'

    await router.push('/login')

    expect(router.currentRoute.value.name).toBe('users-list')
  })

  it('lets an unauthenticated visitor reach the login page', async () => {
    const router = buildRouter()

    await router.push('/login')

    expect(router.currentRoute.value.name).toBe('login')
  })

  it('tries to restore a session from a persisted refresh token before deciding', async () => {
    localStorage.setItem('paprika:refresh-token', 'stale-refresh-token')
    const authApi = await import('@/api/auth')
    const usersApi = await import('@/api/users')
    vi.mocked(authApi.refresh).mockResolvedValue({
      access_token: 'restored-token',
      refresh_token: 'rotated-refresh-token',
    })
    vi.mocked(usersApi.getMe).mockResolvedValue({
      id: 1,
      email: 'roman@paprika.dev',
      first_name: 'Roman',
      last_name: 'Volodin',
      avatar: null,
      is_active: true,
      date_joined: '2026-01-01T00:00:00Z',
    })

    const router = buildRouter()
    await router.push('/users')

    expect(authApi.refresh).toHaveBeenCalledWith('stale-refresh-token')
    expect(router.currentRoute.value.name).toBe('users-list')
  })
})
