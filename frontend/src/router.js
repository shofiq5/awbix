import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'

const routes = [
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
        component: () => import('@/pages/Placeholder.vue'),
        meta: { breadcrumb: ['Shipments', 'Air Waybills'], title: 'Air Waybills' },
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
  history: createWebHistory('/frontend'),
  routes,
})

export default router
