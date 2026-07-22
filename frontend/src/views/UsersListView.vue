<script setup lang="ts">
import { onMounted, ref, h } from 'vue'
import { useRouter } from 'vue-router'
import { useDebounceFn } from '@vueuse/core'
import {
  NButton,
  NInput,
  NIcon,
  NDataTable,
  NPagination,
  NAvatar,
  NTag,
  useDialog,
  useMessage,
  type DataTableColumns,
} from 'naive-ui'
import { AddOutline, SearchOutline, TrashOutline, PencilOutline } from '@vicons/ionicons5'
import { useUsersStore } from '@/stores/users'
import type { UserOut } from '@/types/api'

const router = useRouter()
const users = useUsersStore()
const dialog = useDialog()
const message = useMessage()

const searchInput = ref('')

const debouncedSearch = useDebounceFn((value: string) => {
  users.setSearch(value)
}, 300)

function handleSearchInput(value: string) {
  searchInput.value = value
  debouncedSearch(value)
}

function initials(user: UserOut): string {
  return `${user.first_name[0] ?? ''}${user.last_name[0] ?? ''}`.toUpperCase()
}

function confirmDelete(user: UserOut) {
  dialog.warning({
    title: 'Удалить пользователя',
    content: `Удалить ${user.first_name} ${user.last_name}? Это действие необратимо.`,
    positiveText: 'Удалить',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await users.removeUser(user.id)
        message.success('Пользователь удалён.')
      } catch {
        message.error('Не удалось удалить пользователя.')
      }
    },
  })
}

const columns: DataTableColumns<UserOut> = [
  {
    title: '',
    key: 'avatar',
    width: 56,
    render: (user) =>
      h(
        NAvatar,
        {
          round: true,
          size: 36,
          src: user.avatar ?? undefined,
          style: { fontFamily: 'var(--font-mono)', fontSize: '13px' },
        },
        user.avatar ? undefined : { default: () => [initials(user)] },
      ),
  },
  {
    title: 'Имя',
    key: 'name',
    render: (user) => `${user.first_name} ${user.last_name}`,
  },
  {
    title: 'Email',
    key: 'email',
    render: (user) => h('span', { class: 'mono' }, user.email),
  },
  {
    title: 'Статус',
    key: 'is_active',
    width: 120,
    render: (user) =>
      h(
        NTag,
        { size: 'small', type: user.is_active ? 'success' : 'default', round: true },
        { default: () => (user.is_active ? 'Активен' : 'Отключён') },
      ),
  },
  {
    title: '',
    key: 'actions',
    width: 96,
    render: (user) =>
      h('div', { style: 'display: flex; gap: 4px; justify-content: flex-end;' }, [
        h(
          NButton,
          {
            quaternary: true,
            circle: true,
            size: 'small',
            onClick: () => router.push({ name: 'user-detail', params: { id: user.id } }),
          },
          { icon: () => h(NIcon, { component: PencilOutline }) },
        ),
        h(
          NButton,
          {
            quaternary: true,
            circle: true,
            size: 'small',
            onClick: () => confirmDelete(user),
          },
          { icon: () => h(NIcon, { component: TrashOutline }) },
        ),
      ]),
  },
]

onMounted(() => {
  users.fetchUsers()
})
</script>

<template>
  <div class="users-page">
    <div class="users-page__toolbar">
      <n-input
        :value="searchInput"
        placeholder="Поиск по имени или email"
        clearable
        style="max-width: 320px"
        @update:value="handleSearchInput"
      >
        <template #prefix><n-icon :component="SearchOutline" /></template>
      </n-input>

      <n-button type="primary" @click="router.push({ name: 'user-create' })">
        <template #icon><n-icon :component="AddOutline" /></template>
        Новый пользователь
      </n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="users.items"
      :loading="users.isLoading"
      :bordered="false"
      :row-key="(row: UserOut) => row.id"
      class="users-page__table"
    />

    <div class="users-page__pagination">
      <n-pagination
        :page="users.page"
        :page-size="users.pageSize"
        :item-count="users.total"
        @update:page="users.setPage"
      />
    </div>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 960px;
}

.users-page__toolbar {
  display: flex;
  gap: var(--space-3);
  justify-content: space-between;
  flex-wrap: wrap;
}

.users-page__pagination {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .users-page__table {
    font-size: var(--text-sm, 13px);
  }
}
</style>
