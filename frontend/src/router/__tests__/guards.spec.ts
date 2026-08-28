import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { setupAuthGuard } from '@/router/guards'
import { useAuthStore } from '@/stores/auth'
import { useCurrentCompanyStore } from '@/stores/currentCompany'
import * as companiesApi from '@/api/companies'

vi.mock('@/api/auth')
vi.mock('@/api/users')
vi.mock('@/api/companies')

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
    // Most guard tests aren't about the company switcher - give it an
    // empty, harmless default so authenticated navigations don't choke
    // on an unmocked response.
    vi.mocked(companiesApi.listCompanies).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
    })
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

  it('resolves the active company for an authenticated visitor without redirecting anywhere', async () => {
    vi.mocked(companiesApi.listCompanies).mockResolvedValue({
      items: [{ id: 1, name: 'Acme', slug: 'acme', created_at: '', updated_at: '' }],
      total: 1,
      page: 1,
      page_size: 100,
    })

    const router = buildRouter()
    const auth = useAuthStore()
    auth.accessToken = 'a-valid-token'

    await router.push('/users')

    const currentCompany = useCurrentCompanyStore()
    expect(router.currentRoute.value.name).toBe('users-list')
    expect(currentCompany.isInitialized).toBe(true)
    expect(currentCompany.currentCompanyId).toBe(1)
  })

  it('does not re-fetch companies on a second navigation once already initialized', async () => {
    const router = buildRouter()
    const auth = useAuthStore()
    auth.accessToken = 'a-valid-token'

    await router.push('/users')
    await router.push('/login')
    await router.push('/users')

    expect(companiesApi.listCompanies).toHaveBeenCalledTimes(1)
  })
})
