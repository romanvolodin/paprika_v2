import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { useRemoteSearchOptions } from '@/composables/useRemoteSearchOptions'

interface Item {
  id: number
  name: string
}

describe('useRemoteSearchOptions', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts with no options and not loading', () => {
    const fetcher = vi.fn()
    const { options, loading } = useRemoteSearchOptions(fetcher, (item: Item) => ({
      value: item.id,
      label: item.name,
    }))

    expect(options.value).toEqual([])
    expect(loading.value).toBe(false)
    expect(fetcher).not.toHaveBeenCalled()
  })

  it('clears options immediately for an empty query, without calling the fetcher', () => {
    const fetcher = vi.fn()
    const { options, search } = useRemoteSearchOptions(fetcher, (item: Item) => ({
      value: item.id,
      label: item.name,
    }))

    search('')

    expect(fetcher).not.toHaveBeenCalled()
    expect(options.value).toEqual([])
  })

  it('debounces the fetcher call', async () => {
    const fetcher = vi.fn().mockResolvedValue([])
    const { search } = useRemoteSearchOptions(fetcher, (item: Item) => ({
      value: item.id,
      label: item.name,
    }))

    search('ac')
    search('acm')
    search('acme')

    expect(fetcher).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(300)

    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher).toHaveBeenCalledWith('acme')
  })

  it('maps fetched items through mapToOption', async () => {
    const fetcher = vi.fn().mockResolvedValue([{ id: 1, name: 'Acme' }])
    const { options, search } = useRemoteSearchOptions(fetcher, (item: Item) => ({
      value: item.id,
      label: item.name,
    }))

    search('acme')
    await vi.advanceTimersByTimeAsync(300)

    expect(options.value).toEqual([{ value: 1, label: 'Acme' }])
  })

  it('clears options and stops loading on a failed request', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('boom'))
    const { options, loading, search } = useRemoteSearchOptions(fetcher, (item: Item) => ({
      value: item.id,
      label: item.name,
    }))

    search('acme')
    await vi.advanceTimersByTimeAsync(300)

    expect(loading.value).toBe(false)
    expect(options.value).toEqual([])
  })
})
