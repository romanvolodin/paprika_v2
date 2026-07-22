import { computed, watchEffect } from 'vue'
import { darkTheme, lightTheme, type GlobalThemeOverrides } from 'naive-ui'
import { useUiStore } from '@/stores/ui'

/**
 * Keeps three things in sync with the ui store's `theme`:
 *  - the `data-theme` attribute on <html>, which our own CSS variables
 *    in assets/styles/variables.css key off of
 *  - the Naive UI theme object passed to <n-config-provider>
 *  - Naive UI's theme overrides, so its accent matches our --color-accent
 *
 * Call this once, from App.vue.
 */
export function useTheme() {
  const ui = useUiStore()

  watchEffect(() => {
    document.documentElement.setAttribute('data-theme', ui.theme)
  })

  const naiveTheme = computed(() => (ui.isDark ? darkTheme : lightTheme))

  // Mirrors the accent values in assets/styles/variables.css so Naive UI
  // components and our own CSS-variable-based elements never disagree.
  const themeOverrides = computed<GlobalThemeOverrides>(() => ({
    common: {
      primaryColor: ui.isDark ? '#e8a33d' : '#c17d1e',
      primaryColorHover: ui.isDark ? '#f0b25c' : '#d68d34',
      primaryColorPressed: ui.isDark ? '#c98a2c' : '#a86c19',
      fontFamily: 'var(--font-ui)',
      fontFamilyMono: 'var(--font-mono)',
    },
  }))

  return { naiveTheme, themeOverrides }
}
