<template>
  <div class="max-w-7xl mx-auto space-y-4">

    <!-- ── Page header ──────────────────────────────────────────────── -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold font-mono" style="color:var(--color-text-base);">
          {{ isNew ? 'New Air Waybill' : (form.awb_number || (form.airline_prefix && form.awb_serial_number ? form.airline_prefix + '-' + form.awb_serial_number : 'Air Waybill')) }}
        </h1>
        <p class="text-sm mt-0.5" style="color:var(--color-text-muted);">
          <template v-if="isNew">Fill in the mandatory fields and save.</template>
          <template v-else>{{ docName }} · Last saved: {{ lastModified || '—' }}</template>
        </p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <RouterLink to="/awb">
          <button type="button" class="btn-secondary">
            <Icon name="arrow-left" :size="14" /> Back
          </button>
        </RouterLink>
        <button
          v-if="!isNew && form.docstatus === 0"
          @click="confirmDelete"
          type="button"
          class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border transition-colors"
          style="border-color:#fca5a5;color:#dc2626;"
        >
          <Icon name="trash-2" :size="14" /> Delete
        </button>
        <button @click="save" :disabled="saving" type="button" class="btn-primary">
          <Icon :name="saving ? 'loader' : 'save'" :size="14" :class="saving ? 'animate-spin' : ''" />
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>
    </div>

    <!-- Doc loading -->
    <div v-if="loadingDoc" class="flex items-center justify-center py-20 gap-3" style="color:var(--color-text-muted);">
      <Icon name="loader" :size="22" class="animate-spin" />
      <span class="text-sm">Loading waybill…</span>
    </div>

    <template v-else>

      <!-- ── Toast ────────────────────────────────────────────────────── -->
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

      <!-- ── AWB Identity Header Band ─────────────────────────────────── -->
      <div class="card">
        <div class="flex flex-wrap gap-6 items-start">

          <!-- AWB number box -->
          <div class="flex-1 min-w-[280px]">
            <label class="band-label">Air Waybill Number</label>
            <div class="flex items-center gap-2">
              <div>
                <label class="field-label">Prefix <span class="text-red-500">*</span></label>
                <input
                  v-model="form.airline_prefix"
                  type="text" maxlength="3" placeholder="020"
                  class="w-20 px-3 py-2 text-sm font-mono rounded-lg border outline-none transition uppercase"
                  :style="fieldErrors.airline_prefix
                    ? 'background:var(--color-bg);border-color:#f87171;color:var(--color-text-base);'
                    : 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);'"
                  style="text-transform:uppercase;"
                  @input="delete fieldErrors.airline_prefix"
                />
              </div>
              <span class="text-xl font-mono mt-4" style="color:var(--color-text-muted);">-</span>
              <div>
                <label class="field-label">Serial # <span class="text-red-500">*</span></label>
                <input
                  v-model="form.awb_serial_number"
                  type="text" maxlength="8" placeholder="12345678"
                  class="w-36 px-3 py-2 text-sm font-mono rounded-lg border outline-none transition"
                  :style="fieldErrors.awb_serial_number
                    ? 'background:var(--color-bg);border-color:#f87171;color:var(--color-text-base);'
                    : 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);'"
                  @input="delete fieldErrors.awb_serial_number"
                />
                <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">8 digits — 8th = mod-7 check</p>
              </div>
            </div>
            <div v-if="!isNew && form.awb_number" class="mt-2 font-mono text-lg font-bold" style="color:var(--color-primary);">
              {{ form.awb_number }}
            </div>
          </div>

          <!-- Route chip -->
          <div class="flex-1 min-w-[220px]">
            <label class="band-label">Route</label>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="field-label">Origin <span class="text-red-500">*</span></label>
                <LinkField v-model="form.origin" doctype="Airport" placeholder="e.g. DXB" />
              </div>
              <div>
                <label class="field-label">Destination <span class="text-red-500">*</span></label>
                <LinkField
                  v-model="form.destination" doctype="Airport" placeholder="e.g. JFK"
                  :style="fieldErrors.destination ? 'outline:2px solid #f87171;border-radius:8px;' : ''"
                />
              </div>
            </div>
            <div v-if="form.origin && form.destination" class="mt-2 text-base font-mono font-semibold" style="color:var(--color-text-base);">
              {{ form.origin }} ✈ {{ form.destination }}
            </div>
          </div>

          <!-- Flags -->
          <div>
            <label class="band-label">Flags</label>
            <div class="flex flex-col gap-2">
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" v-model="form.e_awb" class="rounded" />
                <span class="text-sm" style="color:var(--color-text-base);">e-AWB</span>
                <span class="text-xs px-1.5 py-0.5 rounded" style="background:var(--color-primary-light);color:var(--color-primary);">Electronic</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" v-model="form.console" class="rounded" />
                <span class="text-sm" style="color:var(--color-text-base);">Consolidation</span>
              </label>
            </div>
          </div>

        </div>
      </div>

      <!-- ── Two-column shell: main + right rail ───────────────────────── -->
      <div class="flex gap-4 items-start">

        <!-- ── Main content area ─────────────────────────────────────── -->
        <div class="flex-1 min-w-0 space-y-4">

          <!-- ── Mandatory Minimum (always visible) ───────────────────── -->
          <div class="card space-y-5">
            <h2 class="section-label">Mandatory Minimum</h2>

            <!-- Weight / Pieces / Currency -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label class="field-label">Pieces <span class="hint">DE701</span></label>
                <input v-model.number="form.number_of_pieces" type="number" min="1" v-bind="inp" />
              </div>
              <div>
                <label class="field-label">Weight <span class="text-red-500">*</span> <span class="hint">DE600</span></label>
                <div class="flex gap-1">
                  <input v-model.number="form.weight" type="number" min="0" step="0.001" v-bind="inp" class="flex-1 min-w-0" />
                  <select v-model="form.weight_code" class="w-14 px-2 py-2 text-sm rounded-lg border outline-none" style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);">
                    <option value="K">K</option>
                    <option value="L">L</option>
                  </select>
                </div>
              </div>
              <div>
                <label class="field-label">Currency <span class="text-red-500">*</span> <span class="hint">DE121</span></label>
                <LinkField v-model="form.currency" doctype="Currency" placeholder="USD" />
              </div>
              <div>
                <label class="field-label">IATA Rate</label>
                <input v-model.number="form.iata_rate" type="number" min="0" step="0.01" v-bind="inp" />
              </div>
            </div>

            <!-- Volume / computed weights -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <label class="field-label">Volume (m³) <span class="hint">DE500</span></label>
                <input v-model.number="form.volume_amount" type="number" min="0" step="0.0001" v-bind="inp" />
              </div>
              <div>
                <label class="field-label">Volume Wt (kg)</label>
                <input :value="form.volume_weight" readonly tabindex="-1" v-bind="ro" />
                <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">server-computed</p>
              </div>
              <div>
                <label class="field-label">Chargeable Wt (kg)</label>
                <input :value="form.chargeable_weight" readonly tabindex="-1" v-bind="ro" />
                <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">max(weight, vol_wt)</p>
              </div>
              <div>
                <label class="field-label">Vol Factor <span class="hint">cm³/kg</span></label>
                <input v-model.number="form.volume_weight_factor" type="number" min="1" v-bind="inp" placeholder="6000" />
              </div>
            </div>

            <!-- Dimensions button -->
            <div>
              <button type="button" @click="showDimModal = true" class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors" style="border-color:var(--color-primary);color:var(--color-primary);">
                <Icon name="grid" :size="14" />
                Dimensions
                <span v-if="dimensions.length" class="ml-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold text-white" style="background:var(--color-primary);">{{ dimensions.length }}</span>
              </button>
              <p class="text-xs mt-1" style="color:var(--color-text-subtle);">Per-piece dimensions → auto-calculates volume weight via compute_dimensions().</p>
            </div>

            <!-- Goods summary -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="field-label">Nature of Goods <span class="hint">DE170 / 20-char</span></label>
                <input v-model="form.nature_of_goods" type="text" maxlength="20" v-bind="inp" style="text-transform:uppercase;" />
              </div>
              <div>
                <label class="field-label">Commodity Item No. <span class="hint">DE707 / 7-char</span></label>
                <input v-model="form.commodity_item_no" type="text" maxlength="7" v-bind="inp" />
              </div>
            </div>
          </div>

          <!-- ── Active Rail Panel ──────────────────────────────────── -->
          <div class="card">
            <PartyRailPanel
              v-show="activeRail === 'parties'"
              :form="form"
              :also-notify="alsoNotify"
              :other-participants="otherParticipants"
            />
            <RoutingRailPanel
              v-show="activeRail === 'routing'"
              :flight-bookings="flightBookings"
              v-model:to-airport1="form.to_airport1"
              v-model:by-carrier1="form.by_carrier1"
              v-model:to-airport2="form.to_airport2"
              v-model:by-carrier2="form.by_carrier2"
            />
            <RateLinesRailPanel
              v-show="activeRail === 'rating'"
              :form="form"
              :rate-lines="rateLines"
              :goods-details="goodsDetails"
              :other-charges="otherCharges"
              :charge-summary="chargeSummary"
              @auto-rate-line="autoRateLine"
            />
            <ServicesRailPanel
              v-show="activeRail === 'services'"
              :form="form"
              :special-service-requests="specialServiceRequests"
              :special-handling="specialHandling"
              :other-service-info="otherServiceInfo"
              :oci-customs="ociCustoms"
              :accounting-information="accountingInformation"
              :references="references"
            />
            <FinePrintRailPanel
              v-show="activeRail === 'fineprint'"
              :form="form"
              :other-charges="otherCharges"
            />
          </div>

        </div>

        <!-- ── Right vertical rail ─────────────────────────────────── -->
        <nav class="hidden lg:flex flex-col gap-1 w-28 shrink-0 sticky" style="top:1rem;">
          <button
            v-for="item in railItems"
            :key="item.id"
            type="button"
            @click="activeRail = item.id"
            class="flex flex-col items-center gap-1 px-2 py-3 rounded-xl text-center transition-all duration-150 cursor-pointer"
            :style="activeRail === item.id
              ? 'background:var(--color-primary-light);color:var(--color-primary);'
              : 'color:var(--color-text-muted);'"
            @mouseenter="e => activeRail !== item.id && (e.currentTarget.style.background = 'var(--color-bg)')"
            @mouseleave="e => activeRail !== item.id && (e.currentTarget.style.background = '')"
          >
            <Icon :name="item.icon" :size="18" />
            <span class="text-xs font-medium leading-tight">{{ item.label }}</span>
          </button>
        </nav>

      </div>

      <!-- Mobile rail (horizontal scrolling) -->
      <div class="lg:hidden flex gap-2 overflow-x-auto py-1">
        <button
          v-for="item in railItems"
          :key="item.id"
          type="button"
          @click="activeRail = item.id"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors shrink-0"
          :style="activeRail === item.id
            ? 'background:var(--color-primary-light);color:var(--color-primary);'
            : 'background:var(--color-surface);border:1px solid var(--color-border);color:var(--color-text-muted);'"
        >
          <Icon :name="item.icon" :size="14" /> {{ item.label }}
        </button>
      </div>

      <!-- Bottom action bar -->
      <div class="flex justify-end gap-3 pb-4">
        <RouterLink to="/awb">
          <button type="button" class="btn-secondary">Cancel</button>
        </RouterLink>
        <button @click="save" :disabled="saving" type="button" class="btn-primary">
          <Icon :name="saving ? 'loader' : 'save'" :size="14" :class="saving ? 'animate-spin' : ''" />
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
      </div>

    </template>

    <!-- ── Dimensions Modal ─────────────────────────────────────────── -->
    <DimensionModal
      v-if="showDimModal"
      :initial-rows="dimensions"
      :weight="form.weight"
      :volume-weight-factor="form.volume_weight_factor"
      :volume-amount="form.volume_amount"
      :volume-code="form.volume_code"
      @apply="onDimApply"
      @close="showDimModal = false"
    />

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LinkField from '@/components/ui/LinkField.vue'
import DimensionModal from '@/components/awb/DimensionModal.vue'
import PartyRailPanel from '@/components/awb/PartyRailPanel.vue'
import RoutingRailPanel from '@/components/awb/RoutingRailPanel.vue'
import RateLinesRailPanel from '@/components/awb/RateLinesRailPanel.vue'
import ServicesRailPanel from '@/components/awb/ServicesRailPanel.vue'
import FinePrintRailPanel from '@/components/awb/FinePrintRailPanel.vue'

const route  = useRoute()
const router = useRouter()

const isNew      = computed(() => route.name === 'AWBNew')
const docName    = computed(() => route.params.name)
const activeRail = ref('parties')
const saving     = ref(false)
const loadingDoc = ref(false)
const lastModified = ref('')
const showDimModal = ref(false)
const toast        = reactive({ show: false, message: '', type: 'success' })
let   toastTimer   = null
const fieldErrors  = reactive({})

// ── Child tables ─────────────────────────────────────────────────────────
const dimensions             = ref([])
const alsoNotify             = ref([])
const otherParticipants      = ref([])
const flightBookings         = ref([])
const rateLines              = ref([])
const goodsDetails           = ref([])
const otherCharges           = ref([])
const specialServiceRequests = ref([])
const specialHandling        = ref([])
const otherServiceInfo       = ref([])
const ociCustoms             = ref([])
const accountingInformation  = ref([])
const references             = ref([])
const chargeSummary          = ref([])   // display-only — never submitted

// ── Flat form state ───────────────────────────────────────────────────────
const form = reactive({
  // Identity
  airline_prefix: '', awb_serial_number: '', awb_number: '',
  origin: '', destination: '', e_awb: false, console: false, docstatus: 0,
  // Weights
  number_of_pieces: null, weight: null, weight_code: 'K',
  volume_amount: null, volume_weight: null, chargeable_weight: null,
  volume_weight_factor: 6000, volume_code: '', currency: '',
  // Rating
  iata_rate: null, rate_class: '', charge_code: '',
  nature_of_goods: '', commodity_item_no: '',
  wt_val_prepaid_collect: '', other_charges_prepaid_collect: '',
  declared_value_carriage_type: '', declared_value_carriage_amount: null,
  declared_value_customs_type: '', declared_value_customs_amount: null,
  insurance_type: '', insurance_amount: null,
  // Shipper
  shipper_name: '', shipper_account: '', shipper_address: '',
  shipper_place: '', shipper_state: '', shipper_country: '', shipper_post_code: '',
  // Consignee
  consignee_name: '', consignee_account: '', consignee_address: '',
  consignee_place: '', consignee_state: '', consignee_country: '', consignee_post_code: '',
  // Agent (link + read-only fetched)
  agent: '', agent_name: '', agent_place: '', agent_account: '',
  agent_iata_code: '', agent_cass_address: '', agent_participant_id: '',
  // Nominated handling
  nominated_handling_name: '', nominated_handling_place: '',
  // Certification
  shippers_certification_signature: '', issue_date: '', issue_place: '',
  carrier_execution_signature: '',
  no_commission_indicator: false, commission_amount: null, commission_percentage: null,
  sales_incentive_amount: null, sales_incentive_indicator: '', agent_reference: '',
  // Sender
  sender_file_reference: '', sender_office_address: '',
  sender_participant_id: '', sender_participant_code: '',
  // EDX (read-only)
  edx_ack_status: '', edx_ack_detail: '', edx_ack_at: '',
  // CDC
  cc_dest_currency: '', rate_of_exchange: null, cc_charges_dest: null,
  charges_at_dest: null, total_collect_charges: null,
  // Routing
  to_airport1: '', by_carrier1: '', to_airport2: '', by_carrier2: '',
  // Customs
  customs_origin_code: '',
  // Internal
  customer: '', supplier: '',
})

// ── Rail items ────────────────────────────────────────────────────────────
const railItems = [
  { id: 'parties',   label: 'Parties',    icon: 'users'       },
  { id: 'routing',   label: 'Routing',    icon: 'map-pin'     },
  { id: 'rating',    label: 'Rating',     icon: 'dollar-sign' },
  { id: 'services',  label: 'Services',   icon: 'shield'      },
  { id: 'fineprint', label: 'Fine Print', icon: 'edit-3'      },
]

// ── Shared input style attrs ──────────────────────────────────────────────
const inp = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const ro  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-subtle);cursor:not-allowed;' }

// ── Utilities ─────────────────────────────────────────────────────────────
function csrf()  { return window.frappe?.csrf_token || '' }
function parseErr(j) {
  if (j._server_messages) {
    try { return JSON.parse(JSON.parse(j._server_messages)[0]).message } catch {}
  }
  return j.exc_type || 'Request failed'
}

function showToast(message, type = 'success') {
  clearTimeout(toastTimer)
  toast.message = message; toast.type = type; toast.show = true
  toastTimer = setTimeout(() => { toast.show = false }, 3500)
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

// ── Load & apply doc ──────────────────────────────────────────────────────
function applyDoc(doc) {
  const bools = ['e_awb', 'console', 'no_commission_indicator']
  Object.keys(form).forEach(k => {
    if (bools.includes(k)) form[k] = !!doc[k]
    else form[k] = doc[k] ?? (form[k] === null ? null : '')
  })
  dimensions.value             = doc.dimensions             || []
  alsoNotify.value             = doc.also_notify            || []
  otherParticipants.value      = doc.other_participants     || []
  flightBookings.value         = doc.flight_bookings        || []
  rateLines.value              = doc.rate_lines             || []
  goodsDetails.value           = doc.goods_details          || []
  otherCharges.value           = doc.other_charges          || []
  specialServiceRequests.value = doc.special_service_requests || []
  specialHandling.value        = doc.special_handling       || []
  otherServiceInfo.value       = doc.other_service_info     || []
  ociCustoms.value             = doc.oci_customs            || []
  accountingInformation.value  = doc.accounting_information || []
  references.value             = doc.references             || []
  chargeSummary.value          = doc.charge_summary         || []
  if (doc.modified) lastModified.value = doc.modified.substring(0, 16).replace('T', ' ')
}

async function loadDoc() {
  if (isNew.value) return
  loadingDoc.value = true
  try {
    const doc = await apiGet('/api/method/awbix.frontend_api.get_shipment', { name: docName.value })
    if (doc) applyDoc(doc)
  } catch (e) {
    showToast(e.message || 'Failed to load waybill.', 'error')
  } finally {
    loadingDoc.value = false
  }
}

// ── Dimensions modal ──────────────────────────────────────────────────────
function onDimApply({ rows, volumeWeight, chargeableWeight, suggestedVolumeAmount }) {
  dimensions.value = rows
  form.volume_weight = volumeWeight
  form.chargeable_weight = chargeableWeight
  if (suggestedVolumeAmount != null) form.volume_amount = suggestedVolumeAmount
  showDimModal.value = false
}

// ── Auto rate line — MIRRORS shipment.js auto_rate_line — keep in sync ────
function autoRateLine() {
  const chargeable_weight = form.chargeable_weight || 0
  const iata_rate = form.iata_rate || 0
  const rate_class_code = 'Q'
  rateLines.value = [{
    line_number: 1,
    number_of_pieces: form.number_of_pieces || null,
    rate_class_code,
    gross_weight: form.weight || null,
    gross_weight_code: form.weight_code || 'K',
    chargeable_weight: chargeable_weight || null,
    rate_charge: iata_rate,
    total: rate_class_code === 'Q' ? iata_rate * chargeable_weight : iata_rate,
    goods_data_identifier: form.console ? 'C' : 'G',
    description: form.nature_of_goods || '',
    commodity_item_number: form.commodity_item_no || '',
    rate_combination_point: '', uld_rate_class_type: '', rate_class_percentage: null,
  }]
  activeRail.value = 'rating'
}

// ── Build save payload ────────────────────────────────────────────────────
function buildPayload() {
  const data = {}
  Object.keys(form).forEach(k => { data[k] = form[k] })
  // Coerce booleans
  ;['e_awb', 'console', 'no_commission_indicator'].forEach(k => { data[k] = data[k] ? 1 : 0 })
  // Exclude server-set / read-only fields
  delete data.awb_number
  delete data.volume_weight
  delete data.chargeable_weight
  delete data.agent_name
  delete data.agent_place
  delete data.agent_account
  delete data.agent_iata_code
  delete data.agent_cass_address
  delete data.agent_participant_id
  delete data.edx_ack_status
  delete data.edx_ack_detail
  delete data.edx_ack_at
  delete data.docstatus

  // Child tables — raw rows only; charge_summary intentionally absent
  data.dimensions              = dimensions.value
  data.also_notify             = alsoNotify.value
  data.other_participants      = otherParticipants.value
  data.flight_bookings         = flightBookings.value
  data.rate_lines              = rateLines.value
  data.goods_details           = goodsDetails.value
  data.other_charges           = otherCharges.value
  data.special_service_requests = specialServiceRequests.value
  data.special_handling        = specialHandling.value
  data.other_service_info      = otherServiceInfo.value
  data.oci_customs             = ociCustoms.value
  data.accounting_information  = accountingInformation.value
  data.references              = references.value

  if (!isNew.value) data.name = docName.value
  return data
}

// ── Save ──────────────────────────────────────────────────────────────────
async function save() {
  saving.value = true
  Object.keys(fieldErrors).forEach(k => delete fieldErrors[k])
  try {
    const saved = await apiPost('/api/method/awbix.frontend_api.save_shipment', { data: buildPayload() })
    showToast('AWB saved.', 'success')
    if (isNew.value && saved?.name) {
      router.replace(`/awb/${saved.name}`)
    } else {
      if (saved?.awb_number) form.awb_number = saved.awb_number
      if (saved?.modified)   lastModified.value = saved.modified.substring(0, 16).replace('T', ' ')
      await loadDoc()   // reload to pick up server-computed fields
    }
  } catch (e) {
    const msg = e.message || 'Failed to save.'
    showToast(msg, 'error')
    if (/serial|check.?digit|mod.?7/i.test(msg))               fieldErrors.awb_serial_number = true
    if (/same.*(airport|origin|dest)|origin.*dest/i.test(msg)) fieldErrors.destination = true
  } finally {
    saving.value = false
  }
}

// ── Delete ────────────────────────────────────────────────────────────────
async function confirmDelete() {
  if (!confirm(`Delete AWB "${form.awb_number || docName.value}"? This cannot be undone.`)) return
  try {
    await apiPost('/api/method/awbix.frontend_api.delete_shipment', { name: docName.value })
    router.push('/awb')
  } catch (e) {
    showToast(e.message || 'Failed to delete.', 'error')
  }
}

// ── Lifecycle ─────────────────────────────────────────────────────────────
function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); save() }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  loadDoc()
})
onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(toastTimer)
})
</script>

<style scoped>
.card          { background:var(--color-surface); border:1px solid var(--color-border); border-radius:0.75rem; padding:1.25rem; }
.section-label { font-size:0.65rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--color-text-subtle); }
.band-label    { display:block; font-size:0.65rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--color-text-subtle); margin-bottom:0.5rem; }
.field-label   { display:block; font-size:0.7rem; font-weight:500; margin-bottom:0.35rem; color:var(--color-text-muted); }
.hint          { font-size:0.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:0.25rem; }
.btn-primary   { display:flex; align-items:center; gap:0.5rem; padding:0.5rem 1rem; border-radius:0.5rem; font-size:0.875rem; font-weight:500; color:white; background:var(--color-primary); transition:opacity 150ms; }
.btn-primary:disabled { opacity:0.6; cursor:not-allowed; }
.btn-secondary { display:flex; align-items:center; gap:0.375rem; padding:0.5rem 0.75rem; font-size:0.875rem; border-radius:0.5rem; border:1px solid var(--color-border); color:var(--color-text-muted); }
.toast-enter-active, .toast-leave-active { transition:opacity 200ms ease, transform 200ms ease; }
.toast-enter-from, .toast-leave-to { opacity:0; transform:translateY(8px); }
</style>
