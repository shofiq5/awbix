<template>
  <div class="space-y-6">

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

    <hr class="section-divider" />

    <!-- ── Routing Segments ────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="section-title mb-0">Routing Segments <span class="hint normal-case font-normal">(RTG)</span></h3>
          <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">Origin → up to 2 onward destinations. First row = first destination.</p>
        </div>
        <button @click="addRoutingRow" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Segment
        </button>
      </div>

      <div v-if="!routing.length" class="empty-state">No routing segments defined.</div>

      <div v-else class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-sm">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th w-16">Seq #</th>
              <th class="th">Airport</th>
              <th class="th">Carrier</th>
              <th class="th w-8"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in routing" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="p-1.5">
                <input v-model.number="row.sequence" type="number" min="1" v-bind="cell" class="text-center" />
              </td>
              <td class="p-1.5">
                <LinkField v-model="row.airport" doctype="Airport" placeholder="Airport…" />
              </td>
              <td class="p-1.5">
                <LinkField v-model="row.carrier" doctype="Airline" placeholder="Carrier…" />
              </td>
              <td class="p-1.5 text-center">
                <button @click="routing.splice(i, 1); renumber()" type="button" style="color:#dc2626;">
                  <Icon name="x" :size="13" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

  </div>
</template>

<script setup>
import LinkField from '@/components/ui/LinkField.vue'

const props = defineProps({
  flightBookings: { type: Array, required: true },
  routing:        { type: Array, required: true },
})

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

const inp  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const sel  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const cell = { class: 'w-full px-2 py-1.5 text-sm rounded border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }

function addFlight() {
  props.flightBookings.push({ carrier: '', carrier_code: '', flight_number: '', flight_day: '', flight_month: '', departure_airport: '', arrival_airport: '', space_allocation_code: '', allotment_id: '' })
}

function addRoutingRow() {
  props.routing.push({ sequence: props.routing.length + 1, airport: '', carrier: '', carrier_code: '' })
}

function renumber() {
  props.routing.forEach((r, i) => { r.sequence = i + 1 })
}
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; cursor:default; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
.empty-state    { font-size:.8rem; padding:.75rem; text-align:center; border-radius:.5rem; border:1px dashed var(--color-border); color:var(--color-text-muted); }
.add-btn        { display:flex; align-items:center; gap:.375rem; font-size:.8rem; color:var(--color-primary); }
.th             { padding:.4rem .5rem; text-align:left; font-size:.65rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--color-text-muted); white-space:nowrap; }
</style>
