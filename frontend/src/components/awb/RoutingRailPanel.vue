<template>
  <div class="space-y-6">

    <!-- ── Routing ───────────────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title mb-3">Routing <span class="hint normal-case font-normal">(RTG)</span></h3>
      <p class="text-xs mb-3" style="color:var(--color-text-subtle);">Up to 2 onward destinations from origin.</p>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="field-label">To Airport 1</label>
          <LinkField :model-value="toAirport1" @update:model-value="$emit('update:toAirport1', $event)" doctype="Airport" placeholder="Airport…" />
        </div>
        <div>
          <label class="field-label">By Carrier 1</label>
          <LinkField :model-value="byCarrier1" @update:model-value="$emit('update:byCarrier1', $event)" doctype="Airline" placeholder="Airline…" />
        </div>
        <div>
          <label class="field-label">To Airport 2</label>
          <LinkField :model-value="toAirport2" @update:model-value="$emit('update:toAirport2', $event)" doctype="Airport" placeholder="Airport…" />
        </div>
        <div>
          <label class="field-label">By Carrier 2</label>
          <LinkField :model-value="byCarrier2" @update:model-value="$emit('update:byCarrier2', $event)" doctype="Airline" placeholder="Airline…" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Flight Bookings ─────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">Flight Bookings</h3>
        <button @click="addFlight" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Flight
        </button>
      </div>

      <div v-if="!flightBookings.length" class="empty-state">No flight bookings. Add at least one carrier+flight for the first leg.</div>

      <div v-for="(row, i) in flightBookings" :key="i" class="mb-4 p-4 rounded-xl border relative" style="border-color:var(--color-border);background:var(--color-bg);">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold" style="color:var(--color-text-subtle);">Flight {{ i + 1 }}</span>
          <button @click="flightBookings.splice(i, 1)" type="button" style="color:var(--color-text-subtle);">
            <Icon name="x" :size="14" />
          </button>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">

          <!-- Carrier -->
          <div class="sm:col-span-1">
            <label class="field-label">Carrier <span class="text-red-400">*</span></label>
            <LinkField v-model="row.carrier" doctype="Airline" placeholder="Airline…" />
          </div>

          <!-- Flight number -->
          <div>
            <label class="field-label">Flight # <span class="hint">DE301</span></label>
            <input v-model="row.flight_number" type="text" maxlength="5" v-bind="inp" placeholder="e.g. 401" />
          </div>

          <!-- Date: day + month -->
          <div>
            <label class="field-label">Day <span class="hint">DD</span></label>
            <input v-model="row.flight_day" type="text" maxlength="2" v-bind="inp" placeholder="01" />
          </div>
          <div>
            <label class="field-label">Month</label>
            <select v-model="row.flight_month" v-bind="sel">
              <option value="">—</option>
              <option v-for="m in MONTHS" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>

          <!-- From / To airports -->
          <div>
            <label class="field-label">Departure Airport</label>
            <LinkField v-model="row.departure_airport" doctype="Airport" placeholder="From…" />
          </div>
          <div>
            <label class="field-label">Arrival Airport</label>
            <LinkField v-model="row.arrival_airport" doctype="Airport" placeholder="To…" />
          </div>

          <!-- Space allocation code with tooltip list -->
          <div>
            <label class="field-label">
              Space Code
              <span class="hint" :title="SPACE_CODE_LABELS.map(c => c.code + ': ' + c.label).join('\n')">(?)</span>
            </label>
            <select v-model="row.space_allocation_code" v-bind="sel">
              <option value="">—</option>
              <option v-for="c in SPACE_CODE_LABELS" :key="c.code" :value="c.code" :title="c.label">
                {{ c.code }} — {{ c.label }}
              </option>
            </select>
          </div>

          <!-- Allotment ID -->
          <div>
            <label class="field-label">Allotment ID <span class="hint">14-char</span></label>
            <input v-model="row.allotment_id" type="text" maxlength="14" v-bind="inp" />
          </div>

        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import LinkField from '@/components/ui/LinkField.vue'

const props = defineProps({
  flightBookings: { type: Array, required: true },
  toAirport1:     { type: String, default: '' },
  byCarrier1:     { type: String, default: '' },
  toAirport2:     { type: String, default: '' },
  byCarrier2:     { type: String, default: '' },
})

defineEmits(['update:toAirport1', 'update:byCarrier1', 'update:toAirport2', 'update:byCarrier2'])

const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

const SPACE_CODE_LABELS = [
  { code: 'NN', label: 'No action requested' },
  { code: 'NA', label: 'No action required (confirmed)' },
  { code: 'SS', label: 'Sold — space sold' },
  { code: 'CA', label: 'Cancelled' },
  { code: 'XX', label: 'Delete' },
  { code: 'HK', label: 'Holds confirmed' },
  { code: 'HL', label: 'Holds — awaiting list' },
  { code: 'HN', label: 'Holds — no action' },
  { code: 'KK', label: 'Confirming previous hold' },
  { code: 'UU', label: 'Unable to confirm' },
  { code: 'UN', label: 'Unable' },
  { code: 'LL', label: 'Wait-listed' },
]

const inp = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const sel = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }

function addFlight() {
  props.flightBookings.push({ carrier: '', carrier_code: '', flight_number: '', flight_day: '', flight_month: '', departure_airport: '', arrival_airport: '', space_allocation_code: '', allotment_id: '' })
}
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; cursor:default; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
.empty-state    { font-size:.8rem; padding:.75rem; text-align:center; border-radius:.5rem; border:1px dashed var(--color-border); color:var(--color-text-muted); }
.add-btn        { display:flex; align-items:center; gap:.375rem; font-size:.8rem; color:var(--color-primary); }
</style>
