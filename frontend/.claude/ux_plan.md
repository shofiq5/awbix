# AWBIX Frontend — App Shell UX Plan

## Overview

Build the foundational App Shell for AWBIX as a **Vue 3 SPA** using **frappe-ui + Tailwind CSS**.
This shell is the permanent scaffold — every future page (Shipment, AWB, HAWB, Manifest, DGD,
Customers, Billing, Reports, Settings) mounts inside it without touching the shell itself.

Stack: `frappe-ui ^0.0.105` · `vue-router 4` · `Tailwind CSS 3` · `Vite 2`

---

## 1. File Structure

```
frontend/src/
├── main.js                        # App bootstrap, plugins
├── App.vue                        # Root: ThemeProvider → RouterView
├── router.js                      # All routes (lazy-loaded)
├── index.css                      # Tailwind base + custom CSS vars
│
├── composables/
│   ├── useTheme.js                # Active theme + dark/light toggle
│   ├── useSidebar.js              # Collapsed/expanded state (localStorage)
│   ├── useSearch.js               # Global search state + API call
│   └── useNotifications.js        # Notification feed (polling or SSE)
│
├── config/
│   └── navigation.js              # Single source of truth for nav items
│
├── layouts/
│   └── AppShell.vue               # Sidebar + TopBar + <slot/>
│
├── components/
│   ├── shell/
│   │   ├── Sidebar.vue            # Collapsible left nav
│   │   ├── SidebarItem.vue        # Nav item (icon + label + badge)
│   │   ├── SidebarGroup.vue       # Collapsible group heading
│   │   ├── TopBar.vue             # Top navigation bar
│   │   ├── Breadcrumb.vue         # Auto-generated from route meta
│   │   ├── SearchModal.vue        # Global search overlay (Ctrl+K)
│   │   ├── NotificationPanel.vue  # Slide-in notifications drawer
│   │   └── UserDropdown.vue       # Avatar + profile/logout menu
│   │
│   └── ui/
│       ├── ThemeProvider.vue      # Injects CSS vars based on theme
│       ├── ColorSwatch.vue        # Theme picker tiles
│       └── PageHeader.vue         # Reusable page title + actions row
│
└── pages/
    ├── Home.vue                   # Dashboard / landing
    └── Settings/
        └── AppearanceSettings.vue # Theme + dark mode controls
```

---

## 2. Navigation Config (`config/navigation.js`)

The entire sidebar is driven by a **single config array**. Adding a new page, report, DocType, or
external link means adding one object here — no component changes required.

```js
// config/navigation.js
export const NAV_ITEMS = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'home',          // feather icon name
    route: '/',
  },
  {
    id: 'shipments',
    label: 'Shipments',
    icon: 'package',
    group: 'Operations',   // groups items under a collapsible heading
    children: [
      { id: 'awb',      label: 'Air Waybills',  icon: 'file-text', route: '/awb' },
      { id: 'hawb',     label: 'House AWBs',    icon: 'layers',    route: '/hawb' },
      { id: 'manifest', label: 'Manifests',     icon: 'list',      route: '/manifest' },
      { id: 'dgd',      label: 'DG Declarations', icon: 'alert-triangle', route: '/dgd' },
    ],
  },
  {
    id: 'customers',
    label: 'Customers',
    icon: 'users',
    group: 'Parties',
    route: '/customers',
  },
  {
    id: 'billing',
    label: 'Billing',
    icon: 'credit-card',
    group: 'Finance',
    route: '/billing',
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: 'bar-chart-2',
    group: 'Analytics',
    route: '/reports',
    badge: 'New',          // optional badge text
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: 'settings',
    route: '/settings',
    bottom: true,          // pinned to sidebar bottom
  },
]

// To add any new entry later, append to this array:
// { id, label, icon, route?, group?, children?, badge?, bottom?, external? }
```

---

## 3. App Shell Layout (`layouts/AppShell.vue`)

```
┌─────────────────────────────────────────────────────────────┐
│  TopBar (h-14, sticky, blur backdrop)                       │
│  [≡ Logo]  [Breadcrumb ···]  [Search]  [🔔]  [Avatar ▾]    │
├──────────┬──────────────────────────────────────────────────┤
│ Sidebar  │  Page Content Area                               │
│ (w-56,   │  <RouterView />                                  │
│  or w-16 │  (scrollable, padding)                           │
│ collapsed│                                                  │
│ sticky)  │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

- Sidebar width: `w-56` expanded / `w-16` collapsed (icons only, tooltip on hover)
- Collapse toggle: chevron button at sidebar bottom, state in `localStorage`
- Main content: `ml-56` or `ml-16` with CSS transition `transition-[margin] duration-300`
- TopBar: `position: sticky; top: 0; z-index: 40; backdrop-blur-md`

---

## 4. Sidebar (`components/shell/Sidebar.vue`)

```
┌────────────────┐   ┌────┐
│ ◀ AWBIX        │   │ AW │  ← collapsed (icons only)
│─────────────── │   │────│
│ 📦 Operations  │   │ 📦 │
│   ✈ Air Waybills│  │ ✈  │
│   📄 House AWBs │  │ 📄 │
│   📋 Manifests  │  │ 📋 │
│─────────────── │   │────│
│ 👥 Parties     │   │ 👥 │
│   👤 Customers │   │ 👤 │
│─────────────── │   │────│
│ 📊 Analytics   │   │ 📊 │
│─────────────── │   │────│
│ ⚙  Settings   │   │ ⚙  │  ← bottom-pinned
└────────────────┘   └────┘
```

Behavior:
- Group headings collapse/expand independently (state in localStorage)
- Active route item: accent-colored left border + background tint
- Hover: subtle background highlight
- Icons: feather-icons (consistent 16px stroke)
- Collapsed mode: tooltip shows full label on hover

---

## 5. TopBar (`components/shell/TopBar.vue`)

```
[≡]  [AWBIX Logo]  |  Home / Shipments / Air Waybills    [🔍 Search...]  [🔔 3]  [SH ▾]
```

Sections (left → right):
1. **Sidebar toggle** — hamburger icon, `useSidebar().toggle()`
2. **Logo** — text `AWBIX` in brand color, links to `/`
3. **Breadcrumb** — auto-built from `route.meta.breadcrumb`; separator `›`
4. **Spacer** (`flex-1`)
5. **Global Search button** — placeholder text `Search… (Ctrl+K)`, opens `SearchModal`
6. **Notification bell** — badge with unread count, opens `NotificationPanel`
7. **User avatar** — initials circle, opens `UserDropdown`

---

## 6. Global Search (`components/shell/SearchModal.vue`)

- Triggered by Ctrl+K or clicking search button
- Full-viewport overlay with centered input (max-w-2xl)
- Debounced frappe-ui `useResource` call to search API
- Result categories: DocTypes, Reports, Pages, Quick Links
- Keyboard navigation: ↑↓ to move, Enter to go, Esc to close
- Recent searches stored in localStorage (cleared on logout)

---

## 7. Notification Panel (`components/shell/NotificationPanel.vue`)

- Slides in from the right as a drawer (w-80)
- Fetches from `frappe.client.get_list('Notification Log', ...)`
- Groups by: Today / Earlier
- Mark-all-read button
- Individual dismiss
- Empty state illustration

---

## 8. User Dropdown (`components/shell/UserDropdown.vue`)

```
┌──────────────────┐
│ [Avatar]         │
│ Shofiq Ahmed     │
│ shofiq5@gmail.com│
├──────────────────┤
│ 👤 My Profile    │
│ 🎨 Appearance    │
│ ⌨  Shortcuts     │
├──────────────────┤
│ 🚪 Log Out       │
└──────────────────┘
```

---

## 9. Theme System

### Color Themes

Five themes, each defined as a set of CSS custom properties injected by `ThemeProvider.vue`:

| Theme    | Primary   | Accent    | CSS class      |
|----------|-----------|-----------|----------------|
| Green    | `#16a34a` | `#4ade80` | `theme-green`  |
| Emerald  | `#059669` | `#34d399` | `theme-emerald`|
| Blue     | `#2563eb` | `#60a5fa` | `theme-blue`   |
| Purple   | `#7c3aed` | `#a78bfa` | `theme-purple` |
| Orange   | `#ea580c` | `#fb923c` | `theme-orange` |

CSS variables used throughout (no hardcoded colors in components):
```css
--color-primary        /* button fill, active nav */
--color-primary-hover
--color-accent         /* badges, highlights */
--color-surface        /* card backgrounds */
--color-surface-hover
--color-border
--color-text-base
--color-text-muted
```

### Dark / Light Mode

- Toggle in UserDropdown and AppearanceSettings
- Stored in `localStorage` as `awbix-color-scheme`
- Applied via `.dark` class on `<html>` (Tailwind dark mode: `class`)
- All CSS vars have dark overrides in `index.css`

---

## 10. Animations & Transitions

| Element               | Animation                          | Duration  |
|-----------------------|------------------------------------|-----------|
| Sidebar expand/collapse | `transition-[width] ease-in-out` | 300ms     |
| Main content margin   | `transition-[margin] ease-in-out`  | 300ms     |
| Search modal open     | fade + scale from 95% → 100%       | 150ms     |
| Notification panel    | slide from right (`translateX`)    | 250ms     |
| User dropdown         | fade + slide down 4px              | 150ms     |
| Route change          | fade out/in via `<Transition>`     | 100ms     |
| Page header           | fade + slide up 8px on mount       | 200ms     |
| Active nav item       | background color transition        | 150ms     |

All transitions use `ease-in-out` or `ease-out`. No bounce/spring on business UI.

---

## 11. Typography & Spacing

- Font: `Inter` (loaded via frappe-ui's Tailwind preset)
- Base size: `14px` (Tailwind `text-sm`)
- Page titles: `text-xl font-semibold`
- Section headings: `text-xs font-medium uppercase tracking-wider text-gray-400`
- Body: `text-sm text-gray-700 dark:text-gray-300`
- Spacing unit: 4px (Tailwind default) — use multiples of 4

---

## 12. Responsive Breakpoints

| Viewport  | Sidebar behavior                            |
|-----------|---------------------------------------------|
| `< md`    | Sidebar hidden, opens as overlay drawer     |
| `md–lg`   | Sidebar collapsed (icons only) by default   |
| `> lg`    | Sidebar expanded by default                 |

TopBar always visible. SearchModal full-screen on mobile.

---

## 13. Route Meta Convention

Every route carries `meta` for breadcrumb and access:

```js
{
  path: '/awb',
  name: 'AWBList',
  component: () => import('@/pages/AWB/AWBList.vue'),
  meta: {
    breadcrumb: ['Shipments', 'Air Waybills'],
    icon: 'file-text',
    title: 'Air Waybills',
  }
}
```

`Breadcrumb.vue` reads `route.meta.breadcrumb` — no manual breadcrumb management per page.

---

## 14. Adding New Pages (Admin Checklist)

To add any new page/report/DocType link, touch **only these two files**:

1. **`config/navigation.js`** — add a nav item object
2. **`router.js`** — add a route with `meta`

No shell component modifications needed. Example — adding a "Tracking" page:

```js
// navigation.js
{ id: 'tracking', label: 'Tracking', icon: 'map-pin', group: 'Operations', route: '/tracking' }

// router.js
{ path: '/tracking', name: 'Tracking',
  component: () => import('@/pages/Tracking.vue'),
  meta: { breadcrumb: ['Operations', 'Tracking'], title: 'Tracking' } }
```

For an **external link**:
```js
{ id: 'erp', label: 'ERPNext', icon: 'external-link', external: 'https://erp.example.com' }
```

For a **frappe Report** embed:
```js
{ id: 'revenue', label: 'Revenue Report', icon: 'trending-up',
  group: 'Analytics', route: '/reports/revenue' }
```

---

## 15. Component Implementation Priority

| Phase | Components                                              | Status  |
|-------|---------------------------------------------------------|---------|
| 1     | `ThemeProvider`, `AppShell`, `Sidebar`, `TopBar`        | Pending |
| 2     | `Breadcrumb`, `UserDropdown`, `NotificationPanel`       | Pending |
| 3     | `SearchModal`, `PageHeader`                             | Pending |
| 4     | `AppearanceSettings` (theme + dark mode UI)             | Pending |
| 5     | Route guards, frappe session check, login redirect      | Pending |

---

## 16. Key Dependencies Already in package.json

- `frappe-ui` — Button, Dialog, Tooltip, Badge, Avatar, Input, Dropdown, ListView
- `feather-icons` — all sidebar/topbar icons
- `vue-router 4` — SPA routing
- `tailwindcss 3` — utility styles (frappe-ui preset extends it)

Additional installs needed:
```bash
# inside frontend/
yarn add @vueuse/core   # useStorage, useEventListener, useMediaQuery
```

---

## 17. Frappe Integration Points

- **Auth:** `frappe.call('frappe.auth.get_logged_user')` on app mount; redirect to `/login` if null
- **Search:** `frappe.call('frappe.desk.search.search_link', { txt, doctype })` or global search API
- **Notifications:** `frappe.client.get_list('Notification Log', { filters: [...], limit: 20 })`
- **User info:** `frappe.session.user`, `frappe.session.user_fullname`, `frappe.session.user_image`
- **Theme persistence:** localStorage (client-only, no server round-trip needed)
