<template>
  <div class="space-y-6 max-w-7xl mx-auto">

    <!-- Welcome header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold" style="color:var(--color-text-base);">
          Good {{ greeting }}, {{ firstName }} 👋
        </h1>
        <p class="text-sm mt-0.5" style="color:var(--color-text-muted);">
          {{ today }} · AWBIX Air Cargo Management
        </p>
      </div>
      <RouterLink to="/awb">
        <button
          type="button"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors duration-150"
          style="background:var(--color-primary);"
          @mouseenter="e => e.currentTarget.style.background='var(--color-primary-hover)'"
          @mouseleave="e => e.currentTarget.style.background='var(--color-primary)'"
        >
          <Icon name="plus" :size="15" />
          New Air Waybill
        </button>
      </RouterLink>
    </div>

    <!-- Stats cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="rounded-xl p-4 border transition-shadow hover:shadow-md"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >
        <div class="flex items-center justify-between mb-3">
          <div
            class="w-9 h-9 rounded-lg flex items-center justify-center"
            style="background:var(--color-primary-light);"
          >
            <Icon :name="stat.icon" :size="17" style="color:var(--color-primary);" />
          </div>
          <span
            class="text-xs font-semibold px-2 py-0.5 rounded-full"
            :class="stat.trend > 0 ? 'text-emerald-600 bg-emerald-50' : 'text-red-500 bg-red-50'"
          >
            {{ stat.trend > 0 ? '+' : '' }}{{ stat.trend }}%
          </span>
        </div>
        <p class="text-2xl font-bold" style="color:var(--color-text-base);">{{ stat.value }}</p>
        <p class="text-xs mt-0.5" style="color:var(--color-text-muted);">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Bottom grid: quick actions + recent activity -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">

      <!-- Quick actions -->
      <div
        class="rounded-xl border p-4"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >
        <h2 class="text-sm font-semibold mb-3" style="color:var(--color-text-base);">Quick Actions</h2>
        <div class="space-y-1.5">
          <RouterLink
            v-for="action in quickActions"
            :key="action.label"
            :to="action.route"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150"
            style="color:var(--color-text-base);"
            @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.04)'"
            @mouseleave="e => e.currentTarget.style.background=''"
          >
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
              style="background:var(--color-primary-light);"
            >
              <Icon :name="action.icon" :size="15" style="color:var(--color-primary);" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ action.label }}</p>
              <p class="text-xs truncate" style="color:var(--color-text-muted);">{{ action.desc }}</p>
            </div>
            <Icon name="chevron-right" :size="14" style="color:var(--color-text-subtle);" />
          </RouterLink>
        </div>
      </div>

      <!-- Recent shipments -->
      <div
        class="lg:col-span-2 rounded-xl border p-4"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold" style="color:var(--color-text-base);">Recent Shipments</h2>
          <RouterLink to="/awb" class="text-xs font-medium" style="color:var(--color-primary);">
            View all →
          </RouterLink>
        </div>

        <div class="space-y-1">
          <div
            v-for="s in recentShipments"
            :key="s.awb"
            class="flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-150 cursor-pointer"
            @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.04)'"
            @mouseleave="e => e.currentTarget.style.background=''"
          >
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-white text-[10px] font-bold"
              style="background:var(--color-primary);"
            >AWB</div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium" style="color:var(--color-text-base);">{{ s.awb }}</p>
              <p class="text-xs" style="color:var(--color-text-muted);">{{ s.route }} · {{ s.pieces }} pcs · {{ s.weight }}</p>
            </div>
            <div class="text-right shrink-0">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                :class="statusClass(s.status)"
              >{{ s.status }}</span>
              <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">{{ s.date }}</p>
            </div>
          </div>
        </div>

        <!-- Empty state placeholder -->
        <div v-if="recentShipments.length === 0" class="flex flex-col items-center py-10 gap-2">
          <Icon name="inbox" :size="32" style="color:var(--color-text-subtle);" />
          <p class="text-sm" style="color:var(--color-text-muted);">No shipments yet</p>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const frappe = window.frappe ?? {}
const fullName  = computed(() => frappe.session?.user_fullname ?? 'User')
const firstName = computed(() => fullName.value.split(' ')[0])

const hour = new Date().getHours()
const greeting = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening'

const today = new Date().toLocaleDateString('en-US', {
  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
})

const stats = [
  { label: 'Air Waybills',   value: '1,284', icon: 'file-text',  trend: 12 },
  { label: 'Active Flights', value: '42',    icon: 'send',       trend: 3  },
  { label: 'Customers',      value: '387',   icon: 'users',      trend: 7  },
  { label: 'Revenue (USD)',  value: '$48.2k',icon: 'trending-up',trend: 15 },
]

const quickActions = [
  { label: 'New Air Waybill',  icon: 'file-text',     route: '/awb',       desc: 'Create a new AWB document'     },
  { label: 'New House AWB',    icon: 'layers',        route: '/hawb',      desc: 'Create a HAWB for a shipment'  },
  { label: 'New Manifest',     icon: 'list',          route: '/manifest',  desc: 'Build a flight cargo manifest' },
  { label: 'Add Customer',     icon: 'user-plus',     route: '/customers', desc: 'Register a shipper or agent'   },
  { label: 'View Reports',     icon: 'bar-chart-2',   route: '/reports',   desc: 'Revenue and ops analytics'     },
]

const recentShipments = [
  { awb: 'AA-12345678', route: 'JFK → LAX', pieces: 12, weight: '340 kg', status: 'Active',   date: 'Today' },
  { awb: 'AA-12345679', route: 'LAX → ORD', pieces: 4,  weight: '85 kg',  status: 'Pending',  date: 'Today' },
  { awb: 'AA-12345680', route: 'ORD → DFW', pieces: 28, weight: '920 kg', status: 'In Transit',date: 'Yesterday' },
  { awb: 'AA-12345681', route: 'DFW → MIA', pieces: 6,  weight: '200 kg', status: 'Delivered',date: 'Yesterday' },
  { awb: 'AA-12345682', route: 'MIA → JFK', pieces: 18, weight: '540 kg', status: 'Active',   date: '14 Jun' },
]

function statusClass(s) {
  return {
    Active:      'bg-blue-50 text-blue-700',
    Pending:     'bg-amber-50 text-amber-700',
    'In Transit':'bg-purple-50 text-purple-700',
    Delivered:   'bg-emerald-50 text-emerald-700',
  }[s] ?? 'bg-gray-100 text-gray-600'
}
</script>
