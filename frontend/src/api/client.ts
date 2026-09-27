import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  // Auth now rides on httponly cookies instead of a header we attach by
  // hand - the browser sends/stores them on its own, but only if we ask
  // it to for cross-origin requests too (the Vite dev server and Django
  // run on different ports).
  withCredentials: true,
  // Django's CSRF cookie (`csrftoken`) is not httponly, specifically so
  // it can be echoed back as a header on state-changing requests. Axios
  // does this automatically once these are set - no code needed per call.
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withXSRFToken: true,
})

// --- Refresh-once-and-queue on 401 -----------------------------------------
//
// If several requests fail with 401 at the same time (e.g. a view fires
// off three requests in parallel right as the access token expires), we
// don't want to hit /auth/refresh/ three times. The first 401 kicks off
// a single refresh; every other 401 that arrives while it's in flight
// waits on the same promise instead of starting its own.

type RetryableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

let refreshPromise: Promise<void> | null = null

async function refreshSession(): Promise<void> {
  const auth = useAuthStore()

  refreshPromise ??= auth.refresh().finally(() => {
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
      await refreshSession()
      // The new access cookie is already attached by the browser - just
      // replay the original request.
      return apiClient(config)
    } catch (refreshError) {
      auth.logout()
      throw refreshError
    }
  },
)
