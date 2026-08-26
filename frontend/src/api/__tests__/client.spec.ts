import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { InternalAxiosRequestConfig } from 'axios'

// The interceptors in client.ts call `useAuthStore()` directly rather than
// receiving it as an argument, so we mock the store module itself with a
// single shared, mutable fake instead of spinning up a real Pinia store.
// This keeps these tests focused on the interceptor plumbing (header
// attachment, refresh-once, queueing, give-up-and-logout) rather than on
// auth store behaviour, which already has its own tests.
const authState = {
  accessToken: null as string | null,
  refresh: vi.fn<() => Promise<string>>(),
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
    authState.accessToken = null
    authState.refresh.mockReset()
    authState.logout.mockReset()
  })

  it('attaches the access token from the auth store as a Bearer header', async () => {
    authState.accessToken = 'abc123'
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      expect(config.headers.Authorization).toBe('Bearer abc123')
      return ok(config)
    })

    await apiClient.get('/users/me/')
  })

  it('sends no Authorization header when logged out', async () => {
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      expect(config.headers.Authorization).toBeUndefined()
      return ok(config)
    })

    await apiClient.get('/users/me/')
  })

  it('refreshes once and retries the original request on a 401', async () => {
    authState.refresh.mockResolvedValue('new-access-token')
    apiClient.defaults.adapter = vi.fn(async (config: RetryableConfig) => {
      if (!config._retried) throw unauthorized(config)
      expect(config.headers.Authorization).toBe('Bearer new-access-token')
      return ok(config)
    })

    const response = await apiClient.get('/users/me/')

    expect(response.data).toEqual({ ok: true })
    expect(authState.refresh).toHaveBeenCalledTimes(1)
  })

  it('deduplicates concurrent 401s into a single refresh call', async () => {
    authState.refresh.mockResolvedValue('new-access-token')
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
    authState.refresh.mockResolvedValue('new-access-token')
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
