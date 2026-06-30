import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'
import { session } from '@/composables/useSession'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { public: true, title: 'Sign In' },
  },
  {
    path: '/',
    component: AppShell,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/pages/Home.vue'),
        meta: { breadcrumb: ['Dashboard'], title: 'Dashboard' },
      },
      // ── Shipments ─────────────────────────────────────────────
      {
        path: 'awb',
        name: 'AWBList',
        component: () => import('@/pages/AWBList.vue'),
        meta: { breadcrumb: ['Shipments', 'Air Waybills'], title: 'Air Waybills' },
      },
      {
        path: 'awb/new',
        name: 'AWBNew',
        component: () => import('@/pages/AWBForm.vue'),
        meta: { breadcrumb: ['Shipments', 'New AWB'], title: 'New Air Waybill' },
      },
      {
        path: 'awb/:name',
        name: 'AWBEdit',
        component: () => import('@/pages/AWBForm.vue'),
        meta: { breadcrumb: ['Shipments', 'Edit AWB'], title: 'Edit Air Waybill' },
      },
      {
        path: 'hawb',
        name: 'HAWBList',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Shipments', 'House AWBs'], title: 'House AWBs' },
      },
      {
        path: 'manifest',
        name: 'ManifestList',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Shipments', 'Manifests'], title: 'Manifests' },
      },
      {
        path: 'dgd',
        name: 'DGDList',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Shipments', 'DG Declarations'], title: 'DG Declarations' },
      },
      // ── Parties ───────────────────────────────────────────────
      {
        path: 'parties',
        name: 'PartyList',
        component: () => import('@/pages/PartyList.vue'),
        meta: { breadcrumb: ['Parties', 'All Parties'], title: 'Parties' },
      },
      {
        path: 'parties/new',
        name: 'PartyNew',
        component: () => import('@/pages/PartyForm.vue'),
        meta: { breadcrumb: ['Parties', 'New Party'], title: 'New Party' },
      },
      {
        path: 'parties/:name',
        name: 'PartyEdit',
        component: () => import('@/pages/PartyForm.vue'),
        meta: { breadcrumb: ['Parties', 'Edit Party'], title: 'Edit Party' },
      },
      // ── Finance ───────────────────────────────────────────────
      {
        path: 'billing',
        name: 'Billing',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Finance', 'Billing'], title: 'Billing' },
      },
      // ── Analytics ─────────────────────────────────────────────
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Analytics', 'Reports'], title: 'Reports' },
      },
      // ── Settings ──────────────────────────────────────────────
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Settings'], title: 'Settings' },
      },
    ],
  },
]

let router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL || '/'),
  routes,
})

router.beforeEach((to) => {
  // Public routes (login) are always reachable. If an already-authenticated
  // user lands on the login page, send them to the dashboard instead.
  if (to.meta.public) {
    return session.isLoggedIn && to.name === 'Login' ? { path: '/' } : true
  }
  // Protected routes require a session; otherwise route to the in-app login
  // page, remembering where the user was headed.
  if (!session.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
