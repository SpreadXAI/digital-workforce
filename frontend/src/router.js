import { createRouter, createWebHistory } from 'vue-router'
import { getToken, api } from './api'
import Layout from './views/Layout.vue'
import LoginView from './views/LoginView.vue'
import DashboardView from './views/DashboardView.vue'
import RecruitView from './views/RecruitView.vue'
import TasksView from './views/TasksView.vue'
import LogsView from './views/LogsView.vue'
import AdminView from './views/AdminView.vue'

const routes = [
  { path: '/login', component: LoginView, meta: { public: true } },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', component: DashboardView },
      { path: 'recruit', component: RecruitView },
      { path: 'train', redirect: '/recruit' },
      { path: 'roster', redirect: '/recruit' },
      { path: 'employees/:id', redirect: '/recruit' },
      { path: 'tasks', component: TasksView },
      { path: 'logs', component: LogsView },
      { path: 'admin', component: AdminView, meta: { admin: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.public && !getToken()) return '/login'
  if (to.path === '/login' && getToken()) return '/'
  if (to.meta.admin && getToken()) {
    try {
      const user = await api('/auth/me')
      if (!user.is_admin) return '/'
    } catch {
      return '/login'
    }
  }
})

export default router
