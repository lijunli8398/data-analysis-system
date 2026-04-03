import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/',
    redirect: '/projects'
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/Projects.vue'),
    meta: { title: '项目管理' }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Reports.vue'),
    meta: { title: '报告管理' }
  },
  {
    path: '/dashboards',
    name: 'Dashboards',
    component: () => import('../views/Dashboards.vue'),
    meta: { title: '看板管理' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue'),
    meta: { title: '智能问数' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router