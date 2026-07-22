import { apiClient } from './client'
import type { MessageResponse, TokenPairResponse } from '@/types/api'

export function login(email: string, password: string) {
  return apiClient
    .post<TokenPairResponse>('/auth/login/', { email, password })
    .then((res) => res.data)
}

export function refresh(refreshToken: string) {
  return apiClient
    .post<TokenPairResponse>('/auth/refresh/', { refresh_token: refreshToken })
    .then((res) => res.data)
}

export function logout(refreshToken?: string | null) {
  return apiClient
    .post<MessageResponse>('/auth/logout/', refreshToken ? { refresh_token: refreshToken } : {})
    .then((res) => res.data)
}
