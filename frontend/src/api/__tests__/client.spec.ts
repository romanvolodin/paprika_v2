import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { InternalAxiosRequestConfig } from 'axios'

// The interceptor in client.ts calls `useAuthStore()` directly rather than
// receiving it as an argument, so we mock the store module itself with a
// single shared, mutable fake instead of spinning up a real Pinia store.
// This keeps these tests focused on the interceptor plumbing (refresh-once,
// queueing, give-up-and-logout) rather than on auth store behaviour, which
// already has its own tests.
const authState = {
  refresh: vi.fn<() => Promise<void>>(),
  logout: vi.fn(),
}

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => authState,
}))

// Imported *after* the mock so client.ts picks up the mocked store.
const { apiClient } = await import('@/api/client')

type RetryableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

function unauthorized(config: RetryableConfig) {
  return Object.assign(new Error('Unauthorized'), {
    isAxiosError: true,
    config,
    response: { status: 401, data: {}, statusText: 'Unauthorized', headers: {}, config },
  })
}

function ok(config: RetryableConfig, data: unknown = { ok: true }) {
  return { data, status: 200, statusText: 'OK', headers: {}, config }
}

describe('apiClient', () => {
  beforeEach(() => {
    authState.refresh.mockReset()
    authState.logout.mockReset()
  })

  it('sends cookies and the CSRF header on cross-origin requests too', () => {
    // Auth is cookie-based now, and the CSRF cookie/header pair is how
    // Django checks state-changing requests - both need to survive the
    // Vite dev server (5173) talking to Django (8000) on a different port.
    expect(apiClient.defaults.withCredentials).toBe(true)
    expect(apiClient.defaults.withXSRFToken).toBe(true)
    expect(apiClient.defaults.xsrfCookieName).toBe('csrftoken')
    expect(apiClient.defaults.xsrfHeaderName).toBe('X-CSRFToken')
  })

  it('refreshes once and retries the original request on a 401', async () => {
    authState.refresh.mockResolvedValue(undefined)
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      if (!config._retried) throw unauthorized(config)
      return ok(config)
    })

    const response = await apiClient.get('/users/me/')

    expect(response.data).toEqual({ ok: true })
    expect(authState.refresh).toHaveBeenCalledTimes(1)
  })

  it('deduplicates concurrent 401s into a single refresh call', async () => {
    authState.refresh.mockResolvedValue(undefined)
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      if (!config._retried) throw unauthorized(config)
      return ok(config)
    })

    const [a, b] = await Promise.all([
      apiClient.get('/protected-a/'),
      apiClient.get('/protected-b/'),
    ])

    expect(a.data).toEqual({ ok: true })
    expect(b.data).toEqual({ ok: true })
    // The whole point of the shared in-flight promise: two independent
    // 401s arriving together must not trigger two refresh calls.
    expect(authState.refresh).toHaveBeenCalledTimes(1)
  })

  it('logs out and gives up if the refresh call itself fails', async () => {
    authState.refresh.mockRejectedValue(new Error('refresh token revoked'))
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      throw unauthorized(config)
    })

    await expect(apiClient.get('/users/me/')).rejects.toThrow('refresh token revoked')
    expect(authState.logout).toHaveBeenCalledTimes(1)
  })

  it('does not attempt a refresh for auth endpoints themselves', async () => {
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      throw unauthorized(config)
    })

    await expect(apiClient.post('/auth/refresh/', {})).rejects.toBeTruthy()
    expect(authState.refresh).not.toHaveBeenCalled()
    expect(authState.logout).not.toHaveBeenCalled()
  })

  it('does not retry a request a second time if it 401s again after refresh', async () => {
    authState.refresh.mockResolvedValue(undefined)
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      // Always 401s, even after the retry - e.g. the user was deactivated
      // server-side. Should surface the error instead of looping forever.
      throw unauthorized(config)
    })

    await expect(apiClient.get('/users/me/')).rejects.toBeTruthy()
    expect(authState.refresh).toHaveBeenCalledTimes(1)
    expect(apiClient.defaults.adapter).toHaveBeenCalledTimes(2)
  })
})
