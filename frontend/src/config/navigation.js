export const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'home',
    route: '/',
  },

  // ── Operations ───────────────────────────────────────────────
  {
    id: 'shipments',
    label: 'Shipments',
    icon: 'package',
    group: 'Operations',
    children: [
      { id: 'awb',      label: 'Air Waybills',    icon: 'file-text',     route: '/awb' },
      { id: 'hawb',     label: 'House AWBs',       icon: 'layers',        route: '/hawb' },
      { id: 'manifest', label: 'Manifests',        icon: 'list',          route: '/manifest' },
      { id: 'dgd',      label: 'DG Declarations',  icon: 'alert-triangle',route: '/dgd' },
    ],
  },

  // ── Parties ──────────────────────────────────────────────────
  {
    id: 'parties',
    label: 'Parties',
    icon: 'users',
    group: 'Parties',
    children: [
      { id: 'party-list', label: 'All Parties', icon: 'list',      route: '/parties'     },
      { id: 'party-new',  label: 'New Party',   icon: 'user-plus', route: '/parties/new' },
    ],
  },

  // ── Finance ──────────────────────────────────────────────────
  {
    id: 'billing',
    label: 'Billing',
    icon: 'credit-card',
    group: 'Finance',
    route: '/billing',
  },

  // ── Analytics ────────────────────────────────────────────────
  {
    id: 'reports',
    label: 'Reports',
    icon: 'bar-chart-2',
    group: 'Analytics',
    route: '/reports',
    badge: 'New',
  },

  // ── Bottom-pinned ─────────────────────────────────────────────
  {
    id: 'settings',
    label: 'Settings',
    icon: 'settings',
    route: '/settings',
    bottom: true,
  },
]
