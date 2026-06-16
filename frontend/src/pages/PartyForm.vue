<template>
  <div class="space-y-5 max-w-4xl mx-auto">

    <!-- Page header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold" style="color:var(--color-text-base);">
          {{ isNew ? 'New Party' : (form.party_name || 'Edit Party') }}
        </h1>
        <p class="text-sm mt-0.5" style="color:var(--color-text-muted);">
          <template v-if="isNew">Fill in party details and save.</template>
          <template v-else>{{ docName }} · Last saved: {{ lastModified || '—' }}</template>
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <RouterLink to="/parties">
          <button
            type="button"
            class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors"
            style="border-color:var(--color-border);color:var(--color-text-muted);"
          >
            <Icon name="arrow-left" :size="14" />
            Back
          </button>
        </RouterLink>
        <button
          v-if="!isNew"
          @click="confirmDelete"
          type="button"
          class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors hover:bg-red-50"
          style="border-color:#fca5a5;color:#dc2626;"
        >
          <Icon name="trash-2" :size="14" />
          Delete
        </button>
        <button
          @click="save"
          :disabled="saving"
          type="button"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
          style="background:var(--color-primary);"
          @mouseenter="e => !saving && (e.currentTarget.style.background='var(--color-primary-hover)')"
          @mouseleave="e => e.currentTarget.style.background='var(--color-primary)'"
        >
          <Icon :name="saving ? 'loader' : 'save'" :size="14" :class="saving ? 'animate-spin' : ''" />
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>

    <!-- Doc loading spinner -->
    <div v-if="loadingDoc" class="flex items-center justify-center py-20 gap-3" style="color:var(--color-text-muted);">
      <Icon name="loader" :size="22" class="animate-spin" />
      <span class="text-sm">Loading party…</span>
    </div>

    <template v-else>

      <!-- Toast notification -->
      <Transition name="toast">
        <div
          v-if="toast.show"
          class="fixed bottom-5 right-5 flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium shadow-lg z-50"
          :style="toast.type === 'success'
            ? 'background:#dcfce7;color:#15803d;border:1px solid #86efac;'
            : 'background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;'"
        >
          <Icon :name="toast.type === 'success' ? 'check' : 'alert-triangle'" :size="15" />
          {{ toast.message }}
        </div>
      </Transition>

      <!-- Tab bar -->
      <div class="flex gap-1 p-1 rounded-xl" style="background:var(--color-bg);">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          type="button"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150"
          :style="activeTab === tab.id
            ? 'background:var(--color-surface);color:var(--color-text-base);box-shadow:0 1px 3px rgba(0,0,0,0.08);'
            : 'color:var(--color-text-muted);'"
        >
          <Icon :name="tab.icon" :size="15" />
          {{ tab.label }}
          <span
            v-if="tab.id === 'contacts' && contacts.length"
            class="ml-0.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold text-white"
            style="background:var(--color-primary);"
          >{{ contacts.length }}</span>
        </button>
      </div>

      <!-- ── TAB: Details ──────────────────────────────────────────────────── -->
      <div
        v-show="activeTab === 'details'"
        class="rounded-xl border p-6 space-y-7"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >

        <!-- Identity -->
        <section>
          <h3 class="text-xs font-semibold uppercase tracking-wider mb-4" style="color:var(--color-text-subtle);">Identity</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">
                Party Name <span class="text-red-500 ml-0.5">*</span>
              </label>
              <input
                v-model="form.party_name"
                type="text"
                maxlength="35"
                placeholder="Full legal name"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                :style="nameError
                  ? 'background:var(--color-bg);border-color:#f87171;color:var(--color-text-base);'
                  : 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);'"
                @input="nameError = false"
              >
              <p v-if="nameError" class="text-xs mt-1 text-red-500">Party name is required.</p>
              <p v-else class="text-xs mt-1" style="color:var(--color-text-subtle);">DE300 · max 35 characters</p>
            </div>
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Account Number</label>
              <input
                v-model="form.account_number"
                type="text"
                maxlength="14"
                placeholder="e.g. 12345678"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              >
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE108 · max 14 characters</p>
            </div>
          </div>
        </section>

        <div class="border-t" style="border-color:var(--color-border);"></div>

        <!-- Address -->
        <section>
          <h3 class="text-xs font-semibold uppercase tracking-wider mb-4" style="color:var(--color-text-subtle);">Address</h3>
          <div class="space-y-4">
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Street Address</label>
              <textarea
                v-model="form.street_address"
                maxlength="35"
                rows="2"
                placeholder="Street and building number"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition resize-none"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              ></textarea>
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE301 · max 35 characters</p>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">City / Place</label>
                <input
                  v-model="form.place"
                  type="text"
                  maxlength="17"
                  placeholder="City"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
              </div>
              <div>
                <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">State / Province</label>
                <input
                  v-model="form.state_province"
                  type="text"
                  maxlength="9"
                  placeholder="State"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
              </div>
              <div>
                <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Post Code</label>
                <input
                  v-model="form.post_code"
                  type="text"
                  maxlength="9"
                  placeholder="Postal code"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
              </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Country</label>
                <select
                  v-model="form.country"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
                  <option value="">— select country —</option>
                  <option v-for="c in countries" :key="c.name" :value="c.name">{{ c.name }}</option>
                </select>
              </div>
            </div>
          </div>
        </section>

        <div class="border-t" style="border-color:var(--color-border);"></div>

        <!-- Roles -->
        <section>
          <h3 class="text-xs font-semibold uppercase tracking-wider mb-1" style="color:var(--color-text-subtle);">Roles</h3>
          <p class="text-xs mb-4" style="color:var(--color-text-muted);">
            Select all roles this party can serve in a shipment.
          </p>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <label
              v-for="role in ROLES"
              :key="role.field"
              class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all duration-150 select-none"
              :style="form[role.field]
                ? 'background:var(--color-primary-light);border-color:var(--color-primary);'
                : 'background:var(--color-bg);border-color:var(--color-border);'"
            >
              <input type="checkbox" v-model="form[role.field]" class="sr-only">
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors duration-150"
                :style="form[role.field]
                  ? 'background:var(--color-primary);'
                  : 'background:var(--color-border);'"
              >
                <Icon
                  :name="role.icon"
                  :size="15"
                  :style="form[role.field] ? 'color:white' : 'color:var(--color-text-muted)'"
                />
              </div>
              <span
                class="text-sm font-medium leading-tight"
                :style="form[role.field] ? 'color:var(--color-primary)' : 'color:var(--color-text-muted)'"
              >{{ role.label }}</span>
            </label>
          </div>
        </section>

      </div>

      <!-- ── TAB: Contacts ─────────────────────────────────────────────────── -->
      <div
        v-show="activeTab === 'contacts'"
        class="rounded-xl border overflow-hidden"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >
        <!-- Header -->
        <div
          class="px-6 py-4 border-b flex items-center justify-between"
          style="border-color:var(--color-border);background:var(--color-bg);"
        >
          <div>
            <h3 class="text-sm font-semibold" style="color:var(--color-text-base);">Contact Numbers</h3>
            <p class="text-xs mt-0.5" style="color:var(--color-text-muted);">
              Telephone (TE), fax (FX), or telex (TL) numbers for this party.
            </p>
          </div>
          <button
            @click="addContact"
            type="button"
            class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg font-medium transition"
            style="background:var(--color-primary-light);color:var(--color-primary);"
          >
            <Icon name="plus" :size="14" />
            Add Contact
          </button>
        </div>

        <!-- Empty state -->
        <div v-if="!contacts.length" class="flex flex-col items-center py-14 gap-3">
          <Icon name="phone" :size="32" style="color:var(--color-text-subtle);" />
          <p class="text-sm" style="color:var(--color-text-muted);">No contacts yet. Add a phone, fax or telex number.</p>
          <button
            @click="addContact"
            class="text-sm font-medium"
            style="color:var(--color-primary);"
          >+ Add first contact</button>
        </div>

        <!-- Contacts rows -->
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b text-left" style="border-color:var(--color-border);">
              <th class="px-6 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);width:230px;">Type</th>
              <th class="px-4 py-3 text-xs font-semibold uppercase tracking-wider" style="color:var(--color-text-muted);">Number</th>
              <th class="px-4 py-3 w-12"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(c, i) in contacts"
              :key="i"
              class="border-b last:border-0"
              style="border-color:var(--color-border);"
            >
              <td class="px-6 py-3">
                <select
                  v-model="c.contact_identifier"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
                  <option value="TE">TE — Telephone</option>
                  <option value="FX">FX — Fax</option>
                  <option value="TL">TL — Telex</option>
                </select>
              </td>
              <td class="px-4 py-3">
                <input
                  v-model="c.contact_number"
                  type="text"
                  maxlength="25"
                  placeholder="Contact number"
                  class="w-full px-3 py-2 text-sm rounded-lg border outline-none"
                  style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
                >
              </td>
              <td class="px-4 py-3 text-center">
                <button
                  @click="removeContact(i)"
                  type="button"
                  class="p-1.5 rounded-lg transition-colors"
                  style="color:var(--color-text-subtle);"
                  @mouseenter="e => e.currentTarget.style.color='#dc2626'"
                  @mouseleave="e => e.currentTarget.style.color='var(--color-text-subtle)'"
                >
                  <Icon name="x" :size="15" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── TAB: Agent Details ────────────────────────────────────────────── -->
      <div
        v-show="activeTab === 'agent'"
        class="rounded-xl border p-6 space-y-7"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >

        <!-- Info banner -->
        <div
          class="flex gap-3 p-4 rounded-lg text-sm"
          style="background:var(--color-primary-light);"
        >
          <Icon name="info" :size="16" style="color:var(--color-primary);flex-shrink:0;margin-top:1px;" />
          <p style="color:var(--color-primary);">
            IATA cargo agent identification fields — used when this party acts as a handling agent on a shipment.
          </p>
        </div>

        <!-- IATA section -->
        <section>
          <h3 class="text-xs font-semibold uppercase tracking-wider mb-4" style="color:var(--color-text-subtle);">IATA Identification</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">IATA Cargo Agent Code</label>
              <input
                v-model="form.iata_cargo_agent_code"
                type="text"
                maxlength="7"
                placeholder="7 characters"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              >
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE311</p>
            </div>
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">CASS Address</label>
              <input
                v-model="form.cass_address"
                type="text"
                maxlength="4"
                placeholder="4 characters"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              >
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE309</p>
            </div>
          </div>
        </section>

        <div class="border-t" style="border-color:var(--color-border);"></div>

        <!-- Participant section -->
        <section>
          <h3 class="text-xs font-semibold uppercase tracking-wider mb-4" style="color:var(--color-text-subtle);">Participant Identification</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Participant Identifier</label>
              <input
                v-model="form.participant_id"
                type="text"
                maxlength="3"
                placeholder="3 characters"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              >
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE319</p>
            </div>
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">Participant Code</label>
              <input
                v-model="form.participant_code"
                type="text"
                maxlength="17"
                placeholder="max 17 characters"
                class="w-full px-3 py-2 text-sm rounded-lg border outline-none transition"
                style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              >
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">DE320</p>
            </div>
          </div>
        </section>

      </div>

      <!-- Bottom action bar -->
      <div class="flex justify-end gap-3 pt-1 pb-2">
        <RouterLink to="/parties">
          <button
            type="button"
            class="px-4 py-2 text-sm rounded-lg border transition-colors"
            style="border-color:var(--color-border);color:var(--color-text-muted);"
          >Cancel</button>
        </RouterLink>
        <button
          @click="save"
          :disabled="saving"
          type="button"
          class="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          style="background:var(--color-primary);"
        >
          <Icon :name="saving ? 'loader' : 'save'" :size="14" :class="saving ? 'animate-spin' : ''" />
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route  = useRoute()
const router = useRouter()

const isNew      = computed(() => route.name === 'PartyNew')
const docName    = computed(() => route.params.name)
const activeTab  = ref('details')
const saving     = ref(false)
const loadingDoc = ref(false)
const nameError  = ref(false)
const lastModified = ref('')
const countries  = ref([])
const contacts   = ref([])
const toast      = reactive({ show: false, message: '', type: 'success' })
let   toastTimer = null

const ROLES = [
  { field: 'is_shipper',   label: 'Shipper',      icon: 'package'    },
  { field: 'is_consignee', label: 'Consignee',    icon: 'user-check' },
  { field: 'is_notify',    label: 'Notify Party', icon: 'bell'       },
  { field: 'is_agent',     label: 'Agent',        icon: 'briefcase'  },
]

const tabs = [
  { id: 'details',  label: 'Details',      icon: 'user'       },
  { id: 'contacts', label: 'Contacts',     icon: 'phone'      },
  { id: 'agent',    label: 'Agent Details', icon: 'briefcase' },
]

const form = reactive({
  party_name:           '',
  account_number:       '',
  street_address:       '',
  place:                '',
  state_province:       '',
  country:              '',
  post_code:            '',
  is_shipper:           false,
  is_consignee:         false,
  is_notify:            false,
  is_agent:             false,
  iata_cargo_agent_code: '',
  cass_address:         '',
  participant_id:       '',
  participant_code:     '',
})

function showToast(message, type = 'success') {
  clearTimeout(toastTimer)
  toast.message = message
  toast.type    = type
  toast.show    = true
  toastTimer = setTimeout(() => { toast.show = false }, 3000)
}

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

async function apiPost(url, body = {}) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf() },
    body: JSON.stringify(body),
  })
  const j = await r.json()
  if (j.exc) throw new Error(parseErr(j))
  return j.message
}

function addContact() {
  contacts.value.push({ contact_identifier: 'TE', contact_number: '' })
}

function removeContact(i) {
  contacts.value.splice(i, 1)
}

async function loadCountries() {
  try {
    const data = await fetch('/api/resource/Country?fields=["name"]&limit_page_length=500&order_by=name', {
      headers: { 'Accept': 'application/json', 'X-Frappe-CSRF-Token': csrf() }
    }).then(r => r.json())
    countries.value = (data.data || []).map(c => ({ name: c.name }))
  } catch {
    countries.value = []
  }
}

async function loadDoc() {
  if (isNew.value) return
  loadingDoc.value = true
  try {
    const doc = await apiGet('/api/method/awbix.frontend_api.get_party', { name: docName.value })
    if (!doc) return

    const boolFields = ['is_shipper', 'is_consignee', 'is_notify', 'is_agent']
    Object.keys(form).forEach(k => {
      if (boolFields.includes(k)) {
        form[k] = !!(doc[k])
      } else {
        form[k] = doc[k] ?? ''
      }
    })

    contacts.value = (doc.contacts || []).map(c => ({
      contact_identifier: c.contact_identifier || 'TE',
      contact_number:     c.contact_number     || '',
    }))

    if (doc.modified) lastModified.value = doc.modified.substring(0, 16).replace('T', ' ')
  } catch (e) {
    showToast(e.message || 'Failed to load party.', 'error')
  } finally {
    loadingDoc.value = false
  }
}

async function save() {
  if (!form.party_name.trim()) {
    nameError.value = true
    activeTab.value = 'details'
    return
  }

  saving.value = true
  try {
    const data = {
      party_name:            form.party_name,
      account_number:        form.account_number        || '',
      street_address:        form.street_address        || '',
      place:                 form.place                 || '',
      state_province:        form.state_province        || '',
      country:               form.country               || '',
      post_code:             form.post_code             || '',
      is_shipper:            form.is_shipper,
      is_consignee:          form.is_consignee,
      is_notify:             form.is_notify,
      is_agent:              form.is_agent,
      iata_cargo_agent_code: form.iata_cargo_agent_code || '',
      cass_address:          form.cass_address          || '',
      participant_id:        form.participant_id        || '',
      participant_code:      form.participant_code      || '',
      contacts: contacts.value
        .filter(c => c.contact_number?.trim())
        .map(c => ({
          contact_identifier: c.contact_identifier,
          contact_number:     c.contact_number,
        })),
    }

    if (!isNew.value) data.name = docName.value

    const saved = await apiPost('/api/method/awbix.frontend_api.save_party', { data })

    showToast('Party saved successfully.', 'success')

    if (isNew.value && saved?.name) {
      router.replace(`/parties/${saved.name}`)
    } else if (saved?.modified) {
      lastModified.value = saved.modified.substring(0, 16).replace('T', ' ')
    }
  } catch (e) {
    showToast(e.message || 'Failed to save party.', 'error')
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (!confirm(`Delete "${form.party_name}"? This cannot be undone.`)) return
  try {
    await apiPost('/api/method/awbix.frontend_api.delete_party', { name: docName.value })
    router.push('/parties')
  } catch (e) {
    showToast(e.message || 'Failed to delete party.', 'error')
  }
}

function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    save()
  }
}

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)
  await Promise.all([loadCountries(), loadDoc()])
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(toastTimer)
})
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
