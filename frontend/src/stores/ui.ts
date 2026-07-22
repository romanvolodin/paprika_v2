import { computed } from 'vue'
import { defineStore } from 'pinia'
import { useStorage } from '@vueuse/core'

export type Theme = 'dark' | 'light'

export const useUiStore = defineStore('ui', () => {
  // Persisted, defaults to 'dark' when nothing is in localStorage yet.
  // Deliberately not using VueUse's usePreferredColorScheme here: the
  // product default is dark regardless of the OS setting.
  const theme = useStorage<Theme>('paprika:theme', 'dark')

  // Persisted so the sidebar's collapsed state survives a reload, but
  // not shared with anything else - purely a layout preference.
  const sidebarCollapsed = useStorage('paprika:sidebar-collapsed', false)

  const isDark = computed(() => theme.value === 'dark')

  function toggleTheme() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { theme, isDark, toggleTheme, sidebarCollapsed, toggleSidebar }
})
