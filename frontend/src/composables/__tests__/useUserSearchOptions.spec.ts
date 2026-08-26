import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { useUserSearchOptions } from '@/composables/useUserSearchOptions'
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

describe('useUserSearchOptions', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('searches users via the API with a small page size', async () => {
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [buildUser()],
      total: 1,
      page: 1,
      page_size: 10,
    })

    const { search } = useUserSearchOptions()
    search('roman')
    await vi.advanceTimersByTimeAsync(300)

    expect(usersApi.listUsers).toHaveBeenCalledWith({ search: 'roman', page_size: 10 })
  })

  it('maps users to options with the raw user attached', async () => {
    const user = buildUser({ id: 5, first_name: 'Roman', last_name: 'Volodin' })
    vi.mocked(usersApi.listUsers).mockResolvedValue({
      items: [user],
      total: 1,
      page: 1,
      page_size: 10,
    })

    const { options, search } = useUserSearchOptions()
    search('roman')
    await vi.advanceTimersByTimeAsync(300)

    expect(options.value).toEqual([{ value: 5, label: 'Roman Volodin', user }])
  })
})
