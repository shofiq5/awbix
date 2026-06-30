<template>
  <div class="space-y-5 max-w-7xl mx-auto">

    <!-- Page header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold" style="color:var(--color-text-base);">Air Waybills</h1>
        <p class="text-sm mt-0.5" style="color:var(--color-text-muted);">
          Create and manage AWBs for air cargo shipments.
        </p>
      </div>
      <RouterLink to="/awb/new">
        <button
          type="button"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors duration-150"
          style="background:var(--color-primary);"
          @mouseenter="e => e.currentTarget.style.background='var(--color-primary-hover)'"
          @mouseleave="e => e.currentTarget.style.background='var(--color-primary)'"
        >
          <Icon name="plus" :size="15" />
          New AWB
        </button>
      </RouterLink>
    </div>

    <!-- Filters card -->
    <div
      class="rounded-xl border p-4"
      style="background:var(--color-surface);border-color:var(--color-border);"
    >
      <div class="flex gap-3 flex-wrap items-end">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Search by AWB number</label>
          <div class="relative">
            <Icon name="search" :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style="color:var(--color-text-subtle);" />
            <input
              v-model="search"
              type="search"
              placeholder="e.g. 020-12345678"
              @keydown.enter="reload"
              class="w-full pl-9 pr-3 py-2 text-sm rounded-lg border outline-none transition"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex gap-2" style="align-self:flex-end">
          <button
            @click="reload"
            class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border font-medium transition-colors duration-150"
            style="border-color:var(--color-primary);color:var(--color-primary);"
          >
            <Icon name="filter" :size="13" />
            Filter
          </button>
          <button
            @click="clearFilters"
            class="px-3 py-2 text-sm rounded-lg border transition-colors duration-150"
            style="border-color:var(--color-border);color:var(--color-text-muted);"
          >
            Clear
          </button>
        </div>
      </div>
    </div>

    <!-- Results count -->
    <p v-if="!loading && total > 0" class="text-xs" style="color:var(--color-text-muted);">
      Showing {{ start }}–{{ end }} of {{ total }} {{ total === 1 ? 'record' : 'records' }}
    </p>

    <!-- Table card -->
    <div class="rounded-xl border overflow-hidden" style="background:var(--color-surface);border-color:var(--color-border);">

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-16 gap-3" style="color:var(--color-text-muted);">
        <Icon name="loader" :size="20" class="animate-spin" />
        <span class="text-sm">Loading waybills…</span>
      </div>

      <!-- Empty state -->
      <div v-else-if="!rows.length" class="flex flex-col items-center py-16 gap-3">
        <div class="w-14 h-14 rounded-2xl flex items-center justify-center" style="background:var(--color-primary-light);">
          <Icon name="file-text" :size="26" style="color:var(--color-primary);" />
        </div>
        <div class="text-center">
          <p class="text-sm font-semibold" style="color:var(--color-text-base);">No waybills found</p>
          <p class="text-xs mt-0.5" style="color:var(--color-text-muted);">
            {{ search ? 'Try a different AWB number.' : 'Create your first AWB to get started.' }}
          </p>
        </div>
        <RouterLink v-if="!search" to="/awb/new" class="text-sm font-medium" style="color:var(--color-primary);">
          + New AWB
        </RouterLink>
      </div>

      <!-- Data table -->
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b text-left" style="border-color:var(--color-border);background:var(--color-bg);">
            <th class="px-5 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">AWB Number</th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">Route</th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">Shipper</th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">Consignee</th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-right" style="color:var(--color-text-muted);">Wt (kg)</th>
            <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">Status</th>
            <th class="px-4 py-3 w-16"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in rows"
            :key="s.name"
            class="border-b last:border-0 transition-colors duration-100 cursor-pointer"
            style="border-color:var(--color-border);"
            @click="$router.push(`/awb/${s.name}`)"
            @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.02)'"
            @mouseleave="e => e.currentTarget.style.background=''"
          >
            <td class="px-5 py-3.5">
              <RouterLink
                :to="`/awb/${s.name}`"
                class="font-mono font-semibold hover:underline"
                style="color:var(--color-primary);"
                @click.stop
              >{{ s.awb_number || s.name }}</RouterLink>
              <div class="text-xs mt-0.5" style="color:var(--color-text-subtle);">{{ s.modified?.substring(0, 10) }}</div>
            </td>
            <td class="px-4 py-3.5">
              <span v-if="s.origin || s.destination" class="font-mono text-sm" style="color:var(--color-text-base);">
                {{ s.origin || '???' }} ✈ {{ s.destination || '???' }}
              </span>
              <span v-else class="text-xs" style="color:var(--color-text-subtle);">—</span>
            </td>
            <td class="px-4 py-3.5 text-sm" style="color:var(--color-text-base);">{{ s.shipper_name || '—' }}</td>
            <td class="px-4 py-3.5 text-sm" style="color:var(--color-text-muted);">{{ s.consignee_name || '—' }}</td>
            <td class="px-4 py-3.5 text-sm text-right font-mono" style="color:var(--color-text-base);">
              {{ s.chargeable_weight != null ? s.chargeable_weight : '—' }}
            </td>
            <td class="px-4 py-3.5">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                :style="s.docstatus === 1
                  ? 'background:#dcfce7;color:#15803d;'
                  : s.docstatus === 2
                    ? 'background:#fee2e2;color:#b91c1c;'
                    : 'background:var(--color-primary-light);color:var(--color-primary);'"
              >
                {{ s.docstatus === 1 ? 'Submitted' : s.docstatus === 2 ? 'Cancelled' : 'Draft' }}
              </span>
            </td>
            <td class="px-4 py-3.5 text-right">
              <RouterLink
                :to="`/awb/${s.name}`"
                class="text-xs font-medium px-2.5 py-1 rounded-md border transition-colors"
                style="border-color:var(--color-border);color:var(--color-text-muted);"
                @click.stop
              >Edit</RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-end items-center gap-2">
      <button
        @click="prevPage"
        :disabled="page === 0"
        class="px-3 py-1.5 text-sm rounded-lg border transition disabled:opacity-40 disabled:cursor-not-allowed"
        style="border-color:var(--color-border);color:var(--color-text-muted);"
      >← Prev</button>
      <span class="text-sm px-2" style="color:var(--color-text-muted);">Page {{ page + 1 }} of {{ totalPages }}</span>
      <button
        @click="nextPage"
        :disabled="page >= totalPages - 1"
        class="px-3 py-1.5 text-sm rounded-lg border transition disabled:opacity-40 disabled:cursor-not-allowed"
        style="border-color:var(--color-border);color:var(--color-text-muted);"
      >Next →</button>
    </div>

    <!-- Error toast -->
    <div
      v-if="error"
      class="fixed bottom-5 right-5 flex items-center gap-3 px-4 py-3 rounded-xl text-sm shadow-lg"
      style="background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;"
    >
      <Icon name="alert-triangle" :size="15" />
      {{ error }}
      <button @click="error = ''" class="ml-2 opacity-60 hover:opacity-100"><Icon name="x" :size="14" /></button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const PAGE_SIZE  = 20
const page       = ref(0)
const total      = ref(0)
const rows       = ref([])
const loading    = ref(false)
const error      = ref('')
const search     = ref('')

const start      = computed(() => page.value * PAGE_SIZE + 1)
const end        = computed(() => Math.min(page.value * PAGE_SIZE + rows.value.length, total.value))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

function csrf() { return window.frappe?.csrf_token || '' }

function parseErr(j) {
  if (j._server_messages) {
    try { return JSON.parse(JSON.parse(j._server_messages)[0]).message } catch {}
  }
  return j.exc_type || 'Request failed'
}

async function apiGet(url, params = {}) {
  const u = new URL(url, window.location.origin)
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') u.searchParams.set(k, String(v))
  }
  const r = await fetch(u.toString(), { headers: { 'X-Frappe-CSRF-Token': csrf() } })
  const j = await r.json()
  if (j.exc) throw new Error(parseErr(j))
  return j.message
}

async function load() {
  loading.value = true
  error.value   = ''
  try {
    const data = await apiGet('/api/method/awbix.frontend_api.get_shipments', {
      page:      page.value,
      page_size: PAGE_SIZE,
      search:    search.value || undefined,
    })
    rows.value  = data.rows || []
    total.value = data.total || 0
  } catch (e) {
    error.value = e.message || 'Failed to load waybills.'
    rows.value  = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function reload()       { page.value = 0; load() }
function clearFilters() { search.value = ''; reload() }
function prevPage()     { if (page.value > 0)                    { page.value--; load() } }
function nextPage()     { if (page.value < totalPages.value - 1) { page.value++; load() } }

onMounted(load)
</script>
