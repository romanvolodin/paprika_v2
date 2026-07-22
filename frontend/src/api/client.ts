import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

// --- Attach the access token to every request -----------------------------

apiClient.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// --- Refresh-once-and-queue on 401 -----------------------------------------
//
// If several requests fail with 401 at the same time (e.g. a view fires
// off three requests in parallel right as the access token expires), we
// don't want to hit /auth/refresh/ three times. The first 401 kicks off
// a single refresh; every other 401 that arrives while it's in flight
// waits on the same promise instead of starting its own.

type RetryableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const auth = useAuthStore()

  refreshPromise ??= auth
    .refresh()
    .then((token) => token)
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined
    const auth = useAuthStore()

    const isAuthEndpoint = config?.url?.includes('/auth/')

    if (error.response?.status !== 401 || !config || config._retried || isAuthEndpoint) {
      throw error
    }

    config._retried = true

    try {
      const newAccessToken = await refreshAccessToken()
      config.headers.Authorization = `Bearer ${newAccessToken}`
      return apiClient(config)
    } catch (refreshError) {
      auth.logout()
      throw refreshError
    }
  },
)
