<template>
  <div class="space-y-6">

    <!-- ── Certification ─────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Certification &amp; Execution</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="sm:col-span-2">
          <label class="field-label">Shipper's Certification Signature <span class="hint">20-char</span></label>
          <input v-model="form.shippers_certification_signature" type="text" maxlength="20" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Issue Date</label>
          <input v-model="form.issue_date" type="date" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Issue Place <span class="hint">17-char</span></label>
          <input v-model="form.issue_place" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div class="sm:col-span-2">
          <label class="field-label">Carrier Execution Signature <span class="hint">20-char</span></label>
          <input v-model="form.carrier_execution_signature" type="text" maxlength="20" v-bind="inp" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Commission & Sales Incentive ──────────────────────────────── -->
    <section>
      <h3 class="section-title">Commission &amp; Sales Incentive</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="sm:col-span-3">
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="form.no_commission_indicator" class="rounded" />
            <span class="text-sm" style="color:var(--color-text-base);">No Commission Indicator</span>
          </label>
        </div>
        <div :class="form.no_commission_indicator ? 'opacity-40 pointer-events-none' : ''">
          <label class="field-label">Commission Amount</label>
          <input v-model.number="form.commission_amount" type="number" min="0" step="0.01" v-bind="inp" :disabled="form.no_commission_indicator" />
        </div>
        <div :class="form.no_commission_indicator ? 'opacity-40 pointer-events-none' : ''">
          <label class="field-label">Commission %</label>
          <input v-model.number="form.commission_percentage" type="number" min="0" max="100" step="0.01" v-bind="inp" :disabled="form.no_commission_indicator" />
        </div>
        <div>
          <label class="field-label">Agent Reference</label>
          <input v-model="form.agent_reference" type="text" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Sales Incentive Amount</label>
          <input v-model.number="form.sales_incentive_amount" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Sales Incentive Indicator</label>
          <input v-model="form.sales_incentive_indicator" type="text" maxlength="3" v-bind="inp" style="text-transform:uppercase;" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Sender / Office Info ───────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Sender &amp; Office Information</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="field-label">Sender File Reference <span class="hint">15-char</span></label>
          <input v-model="form.sender_file_reference" type="text" maxlength="15" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Sender Office Address <span class="hint">from Shipment Settings</span></label>
          <input v-model="form.sender_office_address" type="text" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Sender Participant ID <span class="hint">3-char</span></label>
          <input v-model="form.sender_participant_id" type="text" maxlength="3" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Sender Participant Code <span class="hint">17-char</span></label>
          <input v-model="form.sender_participant_code" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── CDC block (Collect Charges in Dest Currency) ────────────────── -->
    <!-- Shown only when wt_val is Collect OR any other-charge row is Collect -->
    <section v-if="showCdc">
      <h3 class="section-title">Collect Charges in Destination Currency <span class="hint normal-case font-normal">(CDC)</span></h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="field-label">Dest. Currency</label>
          <LinkField v-model="form.cc_dest_currency" doctype="Currency" placeholder="Currency…" />
        </div>
        <div>
          <label class="field-label">Rate of Exchange</label>
          <input v-model.number="form.rate_of_exchange" type="number" min="0" step="0.000001" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">CC Charges (Dest)</label>
          <input v-model.number="form.cc_charges_dest" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Charges at Dest.</label>
          <input v-model.number="form.charges_at_dest" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Total Collect Charges</label>
          <input v-model.number="form.total_collect_charges" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
      </div>
    </section>
    <div v-else class="rounded-lg border border-dashed px-4 py-3 text-sm" style="border-color:var(--color-border);color:var(--color-text-subtle);">
      CDC block hidden — only shown when Wt/Val or Other Charges are set to Collect.
    </div>

    <hr class="section-divider" />

    <!-- ── Internal (customer / supplier) ─────────────────────────────── -->
    <section>
      <h3 class="section-title flex items-center gap-2">
        Internal
        <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider" style="background:var(--color-primary-light);color:var(--color-primary);">Not IATA</span>
      </h3>
      <p class="text-xs mb-3" style="color:var(--color-text-subtle);">Internal cross-references — not part of the IATA AWB data model.</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="field-label">Customer (internal link)</label>
          <input v-model="form.customer" type="text" v-bind="inp" placeholder="Customer name…" />
        </div>
        <div>
          <label class="field-label">Supplier (internal link)</label>
          <input v-model="form.supplier" type="text" v-bind="inp" placeholder="Supplier name…" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── EDX Acknowledgement (read-only system fields) ──────────────── -->
    <section v-if="form.edx_ack_status">
      <h3 class="section-title flex items-center gap-2">
        EDX Acknowledgement
        <span class="normal-case font-normal text-xs" style="color:var(--color-text-subtle);">system · read-only</span>
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="field-label">Status</label>
          <input :value="form.edx_ack_status" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">Acknowledged At</label>
          <input :value="form.edx_ack_at" v-bind="ro" />
        </div>
        <div class="sm:col-span-3">
          <label class="field-label">Detail</label>
          <input :value="form.edx_ack_detail" v-bind="ro" />
        </div>
      </div>
    </section>
    <div v-else class="rounded-lg border border-dashed px-4 py-3 text-sm" style="border-color:var(--color-border);color:var(--color-text-subtle);">
      EDX acknowledgement — not yet sent or no response received.
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import LinkField from '@/components/ui/LinkField.vue'

const props = defineProps({
  form:        { type: Object, required: true },
  otherCharges:{ type: Array,  required: true },
})

// Show CDC block when wt_val is Collect OR any charge row is Collect
const showCdc = computed(() =>
  props.form.wt_val_prepaid_collect === 'C' ||
  props.otherCharges.some(r => r.prepaid_collect === 'C')
)

const inp = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const ro  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-subtle);cursor:not-allowed;', readonly: true, tabindex: '-1' }
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); display:flex; align-items:center; gap:.375rem; margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
</style>
