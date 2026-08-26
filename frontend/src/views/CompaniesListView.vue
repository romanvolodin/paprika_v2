<script setup lang="ts">
import { onMounted, ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import { NButton, NInput, NIcon, NDataTable, NPagination, type DataTableColumns } from 'naive-ui'
import { AddOutline, PencilOutline, SearchOutline } from '@vicons/ionicons5'
import { useCompaniesStore } from '@/stores/companies'
import type { CompanyOut } from '@/types/api'

const router = useRouter()
const companies = useCompaniesStore()

const searchInput = ref('')

const debouncedSearch = useDebounceFn((value: string) => {
  companies.setSearch(value)
}, 300)

function handleSearchInput(value: string) {
  searchInput.value = value
  debouncedSearch(value)
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('ru-RU')
}

const columns: DataTableColumns<CompanyOut> = [
  {
    title: 'Название',
    key: 'name',
  },
  {
    title: 'Slug',
    key: 'slug',
    render: (company) => h('span', { class: 'mono' }, company.slug),
  },
  {
    title: 'Создана',
    key: 'created_at',
    width: 140,
    render: (company) => formatDate(company.created_at),
  },
  {
    title: '',
    key: 'actions',
    width: 48,
    render: (company) =>
      h(
        NButton,
        {
          quaternary: true,
          circle: true,
          size: 'small',
          onClick: () => router.push({ name: 'company-detail', params: { id: company.id } }),
        },
        { icon: () => h(NIcon, { component: PencilOutline }) },
      ),
  },
]

onMounted(() => {
  companies.fetchCompanies()
})
</script>

<template>
  <div class="companies-page">
    <div class="companies-page__toolbar">
      <n-input
        :value="searchInput"
        placeholder="Поиск по названию"
        clearable
        style="max-width: 320px"
        @update:value="handleSearchInput"
      >
        <template #prefix><n-icon :component="SearchOutline" /></template>
      </n-input>

      <n-button type="primary" @click="router.push({ name: 'company-create' })">
        <template #icon><n-icon :component="AddOutline" /></template>
        Новая компания
      </n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="companies.items"
      :loading="companies.isLoading"
      :bordered="false"
      :row-key="(row: CompanyOut) => row.id"
      class="companies-page__table"
    />

    <div class="companies-page__pagination">
      <n-pagination
        :page="companies.page"
        :page-size="companies.pageSize"
        :item-count="companies.total"
        @update:page="companies.setPage"
      />
    </div>
  </div>
</template>

<style scoped>
.companies-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 960px;
}

.companies-page__toolbar {
  display: flex;
  gap: var(--space-3);
  justify-content: space-between;
  flex-wrap: wrap;
}

.companies-page__pagination {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .companies-page__table {
    font-size: var(--text-sm, 13px);
  }
}
</style>
