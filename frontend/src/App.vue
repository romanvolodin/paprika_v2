<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider, NLoadingBarProvider } from 'naive-ui'
import { useRoute } from 'vue-router'
import { useTheme } from '@/composables/useTheme'
import AppLayout from '@/components/layout/AppLayout.vue'

const route = useRoute()
const { naiveTheme, themeOverrides } = useTheme()
</script>

<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <n-loading-bar-provider>
      <n-message-provider>
        <n-dialog-provider>
          <!-- Standalone routes (login, 404) render full-screen with no
               sidebar/header -->
          <router-view v-if="route.meta.standalone" />
          <app-layout v-else />
        </n-dialog-provider>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>
