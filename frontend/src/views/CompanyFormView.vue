<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton,
  NInput,
  NFormItem,
  NIcon,
  useMessage,
  type FormInst,
  type FormRules,
} from 'naive-ui'
import { ArrowBackOutline } from '@vicons/ionicons5'
import * as companiesApi from '@/api/companies'
import { slugify } from '@/utils/slugify'

const router = useRouter()
const message = useMessage()

const formRef = ref<FormInst | null>(null)
const isSaving = ref(false)

const name = ref('')
const slug = ref('')

// The slug tracks the name automatically until the person edits it by
// hand - at that point we stop overwriting their choice.
const slugTouchedManually = ref(false)

watch(name, (newName) => {
  if (!slugTouchedManually.value) {
    slug.value = slugify(newName)
  }
})

function handleSlugInput(value: string) {
  slug.value = value
  slugTouchedManually.value = true
}

const rules: FormRules = {
  name: [{ required: true, message: 'Укажите название', trigger: ['input', 'blur'] }],
}

const formModel = computed(() => ({ name: name.value }))

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  isSaving.value = true
  try {
    await companiesApi.createCompany({
      name: name.value,
      slug: slug.value || null,
    })
    message.success('Компания создана.')
    router.push({ name: 'company-list' })
  } catch {
    message.error('Не удалось создать компанию. Проверьте введённые данные.')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="company-form">
    <button class="company-form__back" type="button" @click="router.back()">
      <n-icon :component="ArrowBackOutline" />
      Назад
    </button>

    <h1 class="company-form__title">Новая компания</h1>

    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="top"
      @submit.prevent="handleSubmit"
    >
      <n-form-item label="Название" path="name">
        <n-input v-model:value="name" placeholder="Крутая Студия" />
      </n-form-item>

      <n-form-item label="Slug">
        <n-input :value="slug" placeholder="krutaya-studiya" @update:value="handleSlugInput" />
      </n-form-item>

      <div class="company-form__actions">
        <n-button @click="router.back()">Отмена</n-button>
        <n-button type="primary" attr-type="submit" :loading="isSaving">Создать</n-button>
      </div>
    </n-form>
  </div>
</template>

<style scoped>
.company-form {
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.company-form__back {
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

.company-form__back:hover {
  color: var(--color-text);
}

.company-form__title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.company-form__actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}
</style>
