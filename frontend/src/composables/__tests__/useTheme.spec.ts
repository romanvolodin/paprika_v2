import { beforeEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { darkTheme, lightTheme } from 'naive-ui'
import { useTheme } from '@/composables/useTheme'
import { useUiStore } from '@/stores/ui'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    document.documentElement.removeAttribute('data-theme')
  })

  it('resolves to Naive UI darkTheme by default', () => {
    const { naiveTheme } = useTheme()
    expect(naiveTheme.value).toBe(darkTheme)
  })

  it('resolves to Naive UI lightTheme once the ui store switches', async () => {
    const ui = useUiStore()
    const { naiveTheme } = useTheme()

    ui.toggleTheme()
    await nextTick()

    expect(naiveTheme.value).toBe(lightTheme)
  })

  it('keeps <html data-theme> in sync with the store', async () => {
    const ui = useUiStore()
    useTheme()
    await nextTick()

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    ui.toggleTheme()
    await nextTick()

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('exposes theme overrides with a primary color, distinct per theme', () => {
    const ui = useUiStore()
    const { themeOverrides } = useTheme()

    const darkPrimary = themeOverrides.value.common?.primaryColor
    ui.toggleTheme()
    const lightPrimary = themeOverrides.value.common?.primaryColor

    expect(darkPrimary).toBeTruthy()
    expect(lightPrimary).toBeTruthy()
    expect(darkPrimary).not.toBe(lightPrimary)
  })
})
