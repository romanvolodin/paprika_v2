<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NDatePicker,
  NIcon,
  NInput,
  NFormItem,
  useMessage,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { ArrowBackOutline, CameraOutline, TrashOutline } from '@vicons/ionicons5'
import * as projectsApi from '@/api/projects'
import { useCurrentCompanyStore } from '@/stores/currentCompany'

const router = useRouter()
const message = useMessage()
const currentCompany = useCurrentCompanyStore()

const formRef = ref<FormInst | null>(null)
const isSaving = ref(false)

const name = ref('')
const code = ref('')
const description = ref('')
const startDate = ref<string | null>(null)
const deadline = ref<string | null>(null)

const coverFile = ref<File | null>(null)
const coverPreviewUrl = ref<string | null>(null)
const coverInput = ref<HTMLInputElement | null>(null)

function pickCover() {
  coverInput.value?.click()
}

function handleCoverChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  coverFile.value = file
  coverPreviewUrl.value = URL.createObjectURL(file)
}

function clearCover() {
  coverFile.value = null
  coverPreviewUrl.value = null
}

// Mirrors the backend's `code_validator` - letters, numbers, hyphens and
// underscores only. Checked client-side too since `code` can't be
// changed after creation, so catching a typo here beats finding out
// after the project already exists.
const CODE_PATTERN = /^[A-Za-z0-9_-]+$/

const rules: FormRules = {
  name: [{ required: true, message: 'Укажите название', trigger: ['input', 'blur'] }],
  code: [
    { required: true, message: 'Укажите код', trigger: ['input', 'blur'] },
    {
      pattern: CODE_PATTERN,
      message: 'Только латинские буквы, цифры, дефис и подчёркивание',
      trigger: ['input', 'blur'],
    },
  ],
}

const formModel = computed(() => ({ name: name.value, code: code.value }))

async function handleSubmit() {
  if (currentCompany.currentCompanyId === null) {
    return
  }

  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  isSaving.value = true
  try {
    await projectsApi.createProject(currentCompany.currentCompanyId, {
      name: name.value,
      code: code.value,
      description: description.value,
      startDate: startDate.value,
      deadline: deadline.value,
      cover: coverFile.value,
    })
    message.success('Проект создан.')
    router.push({ name: 'project-list' })
  } catch {
    message.error('Не удалось создать проект. Проверьте введённые данные.')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="project-form">
    <button class="project-form__back" type="button" @click="router.back()">
      <n-icon :component="ArrowBackOutline" />
      Назад
    </button>

    <h1 class="project-form__title">Новый проект</h1>

    <p v-if="currentCompany.currentCompanyId === null" class="project-form__no-company">
      Выберите компанию в переключателе слева - проект создаётся внутри неё.
    </p>

    <n-form
      v-else
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="top"
      @submit.prevent="handleSubmit"
    >
      <div class="project-form__cover">
        <div class="project-form__cover-preview">
          <img v-if="coverPreviewUrl" :src="coverPreviewUrl" alt="" />
          <n-icon v-else :component="CameraOutline" size="28" />
        </div>
        <div class="project-form__cover-actions">
          <input
            ref="coverInput"
            type="file"
            accept="image/png,image/jpeg,image/gif"
            class="project-form__cover-input"
            @change="handleCoverChange"
          />
          <n-button size="small" @click="pickCover">
            {{ coverPreviewUrl ? 'Заменить обложку' : 'Загрузить обложку' }}
          </n-button>
          <n-button v-if="coverPreviewUrl" size="small" quaternary @click="clearCover">
            <template #icon><n-icon :component="TrashOutline" /></template>
          </n-button>
        </div>
      </div>

      <n-form-item label="Название" path="name">
        <n-input v-model:value="name" placeholder="Летающий кот" />
      </n-form-item>

      <n-form-item label="Код" path="code">
        <n-input v-model:value="code" placeholder="CAT" />
      </n-form-item>
      <p class="project-form__hint">
        Код используется в адресах и его нельзя изменить после создания.
      </p>

      <n-form-item label="Описание">
        <n-input v-model:value="description" type="textarea" placeholder="Необязательно" />
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

      <div class="project-form__actions">
        <n-button @click="router.back()">Отмена</n-button>
        <n-button type="primary" attr-type="submit" :loading="isSaving">Создать</n-button>
      </div>
    </n-form>
  </div>
</template>

<style scoped>
.project-form {
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.project-form__back {
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

.project-form__back:hover {
  color: var(--color-text);
}

.project-form__title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.project-form__no-company {
  color: var(--color-text-secondary);
}

.project-form__cover {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-2);
}

.project-form__cover-preview {
  width: 120px;
  height: 68px;
  border-radius: var(--radius-md);
  background: var(--color-bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.project-form__cover-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.project-form__cover-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.project-form__cover-input {
  display: none;
}

.project-form__hint {
  margin: calc(var(--space-2) * -1) 0 var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--text-sm, 13px);
}

.project-form__actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}
</style>
