<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NAvatar,
  NButton,
  NDataTable,
  NDatePicker,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NSelect,
  NSwitch,
  NTag,
  useDialog,
  useMessage,
  type DataTableColumns,
  type FormInst,
  type FormRules,
  type SelectOption,
} from 'naive-ui'
import { AddOutline, ArrowBackOutline, TrashOutline } from '@vicons/ionicons5'
import { useProjectDetailStore } from '@/stores/projectDetail'
import { useProjectPermissions } from '@/composables/useProjectPermissions'
import { MEMBERSHIP_ROLE_LABELS, MEMBERSHIP_ROLE_OPTIONS } from '@/constants/membershipRoles'
import type { CompanyMemberOut, ProjectMemberOut, ProjectMembershipRole } from '@/types/api'

const props = defineProps<{ projectId: number }>()

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const store = useProjectDetailStore()
const { canEditProject, canManageMembers, canRemoveMember, canChangeMemberRole } =
  useProjectPermissions(computed(() => store.members))

onMounted(() => {
  store.fetch(props.projectId)
})

// --- Project settings ---------------------------------------------------

const formRef = ref<FormInst | null>(null)
const isSaving = ref(false)
const name = ref('')
const description = ref('')
const startDate = ref<string | null>(null)
const deadline = ref<string | null>(null)
const isActive = ref(true)

watch(
  () => store.project,
  (project) => {
    if (!project) return
    name.value = project.name
    description.value = project.description
    startDate.value = project.start_date
    deadline.value = project.deadline
    isActive.value = project.is_active
  },
  { immediate: true },
)

const rules: FormRules = {
  name: [{ required: true, message: 'Укажите название', trigger: ['input', 'blur'] }],
}

const formModel = computed(() => ({ name: name.value }))

async function handleSaveProject() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  isSaving.value = true
  try {
    await store.updateProject(props.projectId, {
      name: name.value,
      description: description.value,
      start_date: startDate.value,
      deadline: deadline.value,
      is_active: isActive.value,
    })
    message.success('Проект обновлён.')
  } catch {
    message.error('Не удалось сохранить изменения.')
  } finally {
    isSaving.value = false
  }
}

// --- Members -------------------------------------------------------------

function initials(member: { first_name: string; last_name: string }): string {
  return `${member.first_name[0] ?? ''}${member.last_name[0] ?? ''}`.toUpperCase()
}

async function handleRoleChange(member: ProjectMemberOut, role: ProjectMembershipRole) {
  try {
    await store.updateMemberRole(props.projectId, member.user_id, role)
    message.success('Роль обновлена.')
  } catch {
    message.error('Не удалось изменить роль.')
  }
}

function confirmRemoveMember(member: ProjectMemberOut) {
  dialog.warning({
    title: 'Удалить участника',
    content: `Удалить ${member.first_name} ${member.last_name} из проекта?`,
    positiveText: 'Удалить',
    negativeText: 'Отмена',
    onPositiveClick: async () => {
      try {
        await store.removeMember(props.projectId, member.user_id)
        message.success('Участник удалён.')
      } catch {
        message.error('Не удалось удалить участника.')
      }
    },
  })
}

const columns = computed<DataTableColumns<ProjectMemberOut>>(() => [
  {
    title: '',
    key: 'avatar',
    width: 48,
    render: (member) =>
      h(
        NAvatar,
        {
          round: true,
          size: 32,
          src: member.avatar ?? undefined,
          style: { fontFamily: 'var(--font-mono)', fontSize: '12px' },
        },
        member.avatar ? undefined : { default: () => initials(member) },
      ),
  },
  {
    title: 'Имя',
    key: 'name',
    render: (member) => `${member.first_name} ${member.last_name}`,
  },
  {
    title: 'Email',
    key: 'email',
    render: (member) => h('span', { class: 'mono' }, member.email),
  },
  {
    title: 'Роль',
    key: 'role',
    width: 200,
    render: (member) =>
      canChangeMemberRole(member.user_id)
        ? h(NSelect, {
            value: member.role,
            options: MEMBERSHIP_ROLE_OPTIONS,
            size: 'small',
            onUpdateValue: (role: ProjectMembershipRole) => handleRoleChange(member, role),
          })
        : h(
            NTag,
            { size: 'small', round: true },
            { default: () => MEMBERSHIP_ROLE_LABELS[member.role] },
          ),
  },
  {
    title: '',
    key: 'actions',
    width: 48,
    render: (member) =>
      canRemoveMember(member.user_id)
        ? h(
            NButton,
            {
              quaternary: true,
              circle: true,
              size: 'small',
              onClick: () => confirmRemoveMember(member),
            },
            { icon: () => h(NIcon, { component: TrashOutline }) },
          )
        : null,
  },
])

// --- Add member ------------------------------------------------------------

// Only an existing member of the project's company can be added (the API
// rejects anyone else), so the picker is built from the company's member
// list rather than a system-wide user search - and only offers people who
// aren't already on the project.
const availableCompanyMembers = computed<CompanyMemberOut[]>(() =>
  store.companyMembers.filter(
    (companyMember) => !store.members.some((member) => member.user_id === companyMember.user_id),
  ),
)

const memberOptions = computed(() =>
  availableCompanyMembers.value.map((companyMember) => ({
    value: companyMember.user_id,
    label: `${companyMember.first_name} ${companyMember.last_name}`,
    member: companyMember,
  })),
)

const newMemberUserId = ref<number | null>(null)
const newMemberRole = ref<ProjectMembershipRole>('executor')
const isAddingMember = ref(false)

function renderMemberOption(option: SelectOption) {
  const member = (option as { member?: CompanyMemberOut }).member
  return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
    h(
      NAvatar,
      {
        round: true,
        size: 24,
        src: member?.avatar ?? undefined,
        style: { fontFamily: 'var(--font-mono)', fontSize: '10px' },
      },
      member?.avatar ? undefined : { default: () => (member ? initials(member) : '') },
    ),
    h('span', null, option.label as string),
  ])
}

async function handleAddMember() {
  if (!newMemberUserId.value) return

  isAddingMember.value = true
  try {
    await store.addMember(props.projectId, {
      user_id: newMemberUserId.value,
      role: newMemberRole.value,
    })
    message.success('Участник добавлен.')
    newMemberUserId.value = null
    newMemberRole.value = 'executor'
  } catch {
    message.error('Не удалось добавить участника.')
  } finally {
    isAddingMember.value = false
  }
}
</script>

<template>
  <div v-if="store.project" class="project-detail">
    <button
      class="project-detail__back"
      type="button"
      @click="router.push({ name: 'project-list' })"
    >
      <n-icon :component="ArrowBackOutline" />
      К списку проектов
    </button>

    <div class="project-detail__heading-row">
      <h1 class="project-detail__title">{{ store.project.name }}</h1>
      <span class="mono project-detail__code">{{ store.project.code }}</span>
    </div>

    <section class="project-detail__section">
      <h2 class="project-detail__heading">Настройки</h2>
      <n-form
        ref="formRef"
        :model="formModel"
        :rules="rules"
        label-placement="top"
        :disabled="!canEditProject"
        @submit.prevent="handleSaveProject"
      >
        <n-form-item label="Название" path="name">
          <n-input v-model:value="name" />
        </n-form-item>

        <n-form-item label="Код">
          <n-input :value="store.project.code" disabled />
        </n-form-item>
        <p class="project-detail__hint">Код нельзя изменить после создания проекта.</p>

        <n-form-item label="Описание">
          <n-input v-model:value="description" type="textarea" />
        </n-form-item>

        <n-form-item label="Начало">
          <n-date-picker
            v-model:formatted-value="startDate"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="Дедлайн">
          <n-date-picker
            v-model:formatted-value="deadline"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="Активен">
          <n-switch v-model:value="isActive" />
        </n-form-item>

        <n-button v-if="canEditProject" type="primary" attr-type="submit" :loading="isSaving">
          Сохранить
        </n-button>
      </n-form>
    </section>

    <section class="project-detail__section">
      <h2 class="project-detail__heading">Участники</h2>

      <n-data-table
        :columns="columns"
        :data="store.members"
        :loading="store.isLoading"
        :bordered="false"
        :row-key="(row: ProjectMemberOut) => row.id"
      />

      <div v-if="canManageMembers" class="project-detail__add-member">
        <n-select
          v-model:value="newMemberUserId"
          filterable
          clearable
          placeholder="Выбрать участника компании"
          style="max-width: 320px"
          :options="memberOptions"
          :render-label="renderMemberOption"
        />
        <n-select
          v-model:value="newMemberRole"
          :options="MEMBERSHIP_ROLE_OPTIONS"
          style="max-width: 180px"
        />
        <n-button
          type="primary"
          :disabled="!newMemberUserId"
          :loading="isAddingMember"
          @click="handleAddMember"
        >
          <template #icon><n-icon :component="AddOutline" /></template>
          Добавить
        </n-button>
      </div>
    </section>
  </div>
  <p v-else-if="store.isLoading" class="project-detail__loading">Загрузка…</p>
</template>

<style scoped>
.project-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-width: 720px;
}

.project-detail__back {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm, 13px);
  cursor: pointer;
  padding: 0;
  align-self: flex-start;
}

.project-detail__back:hover {
  color: var(--color-text);
}

.project-detail__heading-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
}

.project-detail__title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.project-detail__code {
  color: var(--color-text-secondary);
  font-size: var(--text-sm, 13px);
}

.project-detail__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.project-detail__heading {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.project-detail__hint {
  margin: calc(var(--space-2) * -1) 0 var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--text-sm, 13px);
}

.project-detail__loading {
  color: var(--color-text-secondary);
}

.project-detail__add-member {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  align-items: center;
}
</style>
