import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from './guards'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    // Rendered full-screen, without the sidebar/header AppShell.
    standalone?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { standalone: true },
    },
    {
      path: '/',
      redirect: { name: 'users-list' },
    },
    {
      path: '/users',
      name: 'users-list',
      component: () => import('@/views/UsersListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/users/new',
      name: 'user-create',
      component: () => import('@/views/UserFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/users/:id(\\d+)',
      name: 'user-detail',
      component: () => import('@/views/UserFormView.vue'),
      props: (route) => ({ userId: Number(route.params.id) }),
      meta: { requiresAuth: true },
    },
    {
      path: '/companies',
      name: 'company-list',
      component: () => import('@/views/CompaniesListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/companies/new',
      name: 'company-create',
      component: () => import('@/views/CompanyFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/companies/:id(\\d+)',
      name: 'company-detail',
      component: () => import('@/views/CompanyDetailView.vue'),
      props: (route) => ({ companyId: Number(route.params.id) }),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { standalone: true },
    },
  ],
})

setupAuthGuard(router)

export default router
