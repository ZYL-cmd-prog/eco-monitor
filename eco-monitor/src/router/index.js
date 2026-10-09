import { createRouter, createWebHashHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '综合大屏' } },
      { path: 'indicators', name: 'Indicators', component: () => import('../views/Indicators.vue'), meta: { title: '指标管理' } },
      { path: 'uav', name: 'Uav', component: () => import('../views/Uav.vue'), meta: { title: '无人机巡查' } },
      { path: 'analysis', name: 'Analysis', component: () => import('../views/Analysis.vue'), meta: { title: '智能分析' } },
      { path: 'alerts', name: 'Alerts', component: () => import('../views/Alerts.vue'), meta: { title: '预警中心' } },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
