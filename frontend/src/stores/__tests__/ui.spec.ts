import { beforeEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import { useUiStore } from '@/stores/ui'

describe('useUiStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('defaults to dark theme when nothing is persisted', () => {
    const ui = useUiStore()
    expect(ui.theme).toBe('dark')
    expect(ui.isDark).toBe(true)
  })

  it('toggleTheme flips between dark and light', () => {
    const ui = useUiStore()

    ui.toggleTheme()
    expect(ui.theme).toBe('light')
    expect(ui.isDark).toBe(false)

    ui.toggleTheme()
    expect(ui.theme).toBe('dark')
  })

  it('persists the theme choice to localStorage', async () => {
    const ui = useUiStore()
    ui.toggleTheme()
    await nextTick()
    // VueUse's useStorage stores string-typed values as plain strings,
    // not JSON-encoded ones - no surrounding quotes.
    expect(localStorage.getItem('paprika:theme')).toBe('light')
  })

  it('picks up a theme already persisted from a previous session', () => {
    localStorage.setItem('paprika:theme', 'light')
    const ui = useUiStore()
    expect(ui.theme).toBe('light')
    expect(ui.isDark).toBe(false)
  })

  it('toggleSidebar flips the collapsed state and persists it independently of theme', async () => {
    const ui = useUiStore()
    expect(ui.sidebarCollapsed).toBe(false)

    ui.toggleSidebar()
    await nextTick()

    expect(ui.sidebarCollapsed).toBe(true)
    expect(localStorage.getItem('paprika:sidebar-collapsed')).toBe('true')
    // Untouched - the two preferences don't leak into each other.
    expect(ui.theme).toBe('dark')
  })
})
