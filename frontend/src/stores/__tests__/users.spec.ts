import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUsersStore } from '@/stores/users'
import * as usersApi from '@/api/users'
import type { UserOut } from '@/types/api'

vi.mock('@/api/users')

function buildUser(overrides: Partial<UserOut> = {}): UserOut {
  return {
    id: 1,
    email: 'a@paprika.dev',
    first_name: 'A',
    last_name: 'One',
    avatar: null,
    is_active: true,
    date_joined: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('useUsersStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchUsers loads a page and mirrors the server-confirmed pagination back', async () => {
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [buildUser()],
      total: 1,
      page: 1,
      page_size: 20,
    })

    const store = useUsersStore()
    await store.fetchUsers()

    expect(usersApi.listUsers).toHaveBeenCalledWith({ page: 1, page_size: 20, search: undefined })
    expect(store.items).toHaveLength(1)
    expect(store.total).toBe(1)
    expect(store.isLoading).toBe(false)
  })

  it('sets isLoading while a fetch is in flight', async () => {
    let resolveFetch!: (value: Awaited<ReturnType<typeof usersApi.listUsers>>) => void
    vi.mocked(usersApi.listUsers).mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve
      }),
    )

    const store = useUsersStore()
    const pending = store.fetchUsers()
    expect(store.isLoading).toBe(true)

    resolveFetch({ items: [], total: 0, page: 1, page_size: 20 })
    await pending

    expect(store.isLoading).toBe(false)
  })

  it('setSearch resets to page 1 and refetches with the search term', async () => {
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    const store = useUsersStore()
    store.page = 3

    await store.setSearch('roman')

    expect(store.search).toBe('roman')
    expect(usersApi.listUsers).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      search: 'roman',
    })
  })

  it('setPage refetches with the requested page', async () => {
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [],
      total: 0,
      page: 2,
      page_size: 20,
    })

    const store = useUsersStore()
    await store.setPage(2)

    expect(usersApi.listUsers).toHaveBeenCalledWith({
      page: 2,
      page_size: 20,
      search: undefined,
    })
  })

  it('removeUser deletes then refetches the current page', async () => {
    vi.mocked(usersApi.deleteUser).mockResolvedValue({
      data: undefined,
      status: 204,
      statusText: 'No Content',
      headers: {},
      config: {},
    } as Awaited<ReturnType<typeof usersApi.deleteUser>>)
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    const store = useUsersStore()
    await store.removeUser(42)

    expect(usersApi.deleteUser).toHaveBeenCalledWith(42)
    expect(usersApi.listUsers).toHaveBeenCalledTimes(1)
  })
})
