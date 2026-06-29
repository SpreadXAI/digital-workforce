import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from './api'
import Layout from './views/Layout.vue'
import LoginView from './views/LoginView.vue'
import DashboardView from './views/DashboardView.vue'
import RecruitView from './views/RecruitView.vue'
import TrainView from './views/TrainView.vue'
import RosterView from './views/RosterView.vue'
import EmployeeDetailView from './views/EmployeeDetailView.vue'
import TasksView from './views/TasksView.vue'
import LogsView from './views/LogsView.vue'

const routes = [
  { path: '/login', component: LoginView, meta: { public: true } },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', component: DashboardView },
      { path: 'recruit', component: RecruitView },
      { path: 'train', component: TrainView },
      { path: 'roster', component: RosterView },
      { path: 'employees/:id', component: EmployeeDetailView },
      { path: 'tasks', component: TasksView },
      { path: 'logs', component: LogsView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (!to.meta.public && !getToken()) return '/login'
  if (to.path === '/login' && getToken()) return '/'
})

export default router
