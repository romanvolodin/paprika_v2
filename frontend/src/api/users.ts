import { apiClient } from './client'
import type { UserListOut, UserListQuery, UserOut, UserUpdateIn } from '@/types/api'

export function getMe() {
  return apiClient.get<UserOut>('/users/me/').then((res) => res.data)
}

export function listUsers(query: UserListQuery = {}) {
  return apiClient.get<UserListOut>('/users/', { params: query }).then((res) => res.data)
}

export function getUser(userId: number) {
  return apiClient.get<UserOut>(`/users/${userId}/`).then((res) => res.data)
}

interface CreateUserInput {
  email: string
  password?: string | null
  firstName: string
  lastName: string
  avatar?: File | null
}

export function createUser(input: CreateUserInput) {
  const form = new FormData()
  form.append('email', input.email)
  if (input.password) form.append('password', input.password)
  form.append('first_name', input.firstName)
  form.append('last_name', input.lastName)
  if (input.avatar) form.append('avatar', input.avatar)

  return apiClient
    .post<UserOut>('/users/', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then((res) => res.data)
}

interface UpdateUserInput extends UserUpdateIn {
  avatar?: File | null
}

export function updateUser(userId: number, input: UpdateUserInput) {
  const form = new FormData()
  if (input.first_name != null) form.append('first_name', input.first_name)
  if (input.last_name != null) form.append('last_name', input.last_name)
  if (input.is_active !== undefined) form.append('is_active', String(input.is_active))
  if (input.remove_avatar) form.append('remove_avatar', 'true')
  if (input.avatar) form.append('avatar', input.avatar)

  return apiClient
    .patch<UserOut>(`/users/${userId}/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((res) => res.data)
}

export function deleteUser(userId: number) {
  return apiClient.delete<void>(`/users/${userId}/`)
}
