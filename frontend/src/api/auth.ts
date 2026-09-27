import { apiClient } from './client'
import type { UserOut } from '@/types/api'

export function login(email: string, password: string) {
  return apiClient.post<UserOut>('/auth/login/', { email, password }).then((res) => res.data)
}

// No request/response body: the browser sends the refresh cookie on its
// own, and the new one comes back as a `Set-Cookie` header.
export function refresh() {
  return apiClient.post<UserOut>('/auth/refresh/').then((res) => res.data)
}

export function logout() {
  return apiClient.post<null>('/auth/logout/')
}
