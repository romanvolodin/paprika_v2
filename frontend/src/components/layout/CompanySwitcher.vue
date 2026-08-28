<script setup lang="ts">
import { computed, h } from 'vue'
import { NIcon, type DropdownOption } from 'naive-ui'
import { BusinessOutline, ChevronDownOutline, CheckmarkOutline } from '@vicons/ionicons5'
import { useCurrentCompanyStore } from '@/stores/currentCompany'

defineProps<{ collapsed?: boolean }>()

const currentCompany = useCurrentCompanyStore()

const options = computed<DropdownOption[]>(() =>
  currentCompany.companies.map((company) => ({
    label: company.name,
    key: company.id,
    icon:
      company.id === currentCompany.currentCompanyId
        ? () => h(NIcon, null, { default: () => h(CheckmarkOutline) })
        : undefined,
  })),
)

function handleSelect(key: string | number) {
  currentCompany.selectCompany(Number(key))
}
</script>

<template>
  <div v-if="currentCompany.companies.length === 0" class="company-switcher" />

  <div
    v-else-if="currentCompany.companies.length === 1"
    class="company-switcher company-switcher--static"
    :class="{ 'company-switcher--collapsed': collapsed }"
    :title="currentCompany.companies[0].name"
  >
    <n-icon :component="BusinessOutline" />
    <span v-if="!collapsed" class="company-switcher__label">
      {{ currentCompany.companies[0].name }}
    </span>
  </div>

  <n-dropdown v-else trigger="click" :options="options" @select="handleSelect">
    <button
      type="button"
      class="company-switcher company-switcher__trigger"
      :class="{ 'company-switcher--collapsed': collapsed }"
      :title="currentCompany.currentCompany?.name ?? 'Выберите компанию'"
    >
      <n-icon :component="BusinessOutline" />
      <span
        v-if="!collapsed"
        class="company-switcher__label"
        :class="{ 'company-switcher__label--placeholder': !currentCompany.currentCompany }"
      >
        {{ currentCompany.currentCompany?.name ?? 'Выберите компанию' }}
      </span>
      <n-icon v-if="!collapsed" :component="ChevronDownOutline" class="company-switcher__chevron" />
    </button>
  </n-dropdown>
</template>

<style scoped>
.company-switcher {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: var(--text-sm, 13px);
}

.company-switcher--collapsed {
  justify-content: center;
  padding: var(--space-3) 0;
}

.company-switcher__trigger {
  width: 100%;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  color: inherit;
  font: inherit;
}

.company-switcher__trigger:hover {
  color: var(--color-text);
}

.company-switcher__label {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.company-switcher__label--placeholder {
  font-style: italic;
}

.company-switcher__chevron {
  flex-shrink: 0;
  opacity: 0.6;
}
</style>
