<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found">
    <span class="not-found__code mono">404</span>
    <p class="not-found__text">Такой страницы нет.</p>
    <n-button @click="router.push({ name: 'users-list' })">К пользователям</n-button>
  </div>
</template>

<style scoped>
.not-found {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  background-color: var(--color-bg);
  color: var(--color-text);
}

.not-found__code {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-text-tertiary);
}

.not-found__text {
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
