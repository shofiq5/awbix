<template>
  <div class="space-y-6">

    <!-- ── Rate strip (top-level fields) ──────────────────────────────── -->
    <section>
      <h3 class="section-title">Rating Header</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <label class="field-label">IATA Rate <span class="hint">DE600</span></label>
          <input v-model.number="form.iata_rate" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div>
          <label class="field-label">Rate Class</label>
          <input v-model="form.rate_class" type="text" maxlength="3" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Charge Code</label>
          <LinkField v-model="form.charge_code" doctype="Charge Code" placeholder="Code…" />
        </div>
        <div>
          <label class="field-label">Wt/Val (P/C)</label>
          <select v-model="form.wt_val_prepaid_collect" v-bind="sel">
            <option value="">—</option>
            <option value="P">Prepaid</option>
            <option value="C">Collect</option>
          </select>
        </div>
        <div>
          <label class="field-label">Other Chgs (P/C)</label>
          <select v-model="form.other_charges_prepaid_collect" v-bind="sel">
            <option value="">—</option>
            <option value="P">Prepaid</option>
            <option value="C">Collect</option>
          </select>
        </div>

        <!-- Declared Value Carriage -->
        <div>
          <label class="field-label">Decl. Value Carriage</label>
          <select v-model="form.declared_value_carriage_type" v-bind="sel">
            <option value="">—</option>
            <option value="NVD">NVD (no value)</option>
            <option value="Value">Declared Value</option>
          </select>
        </div>
        <div v-if="form.declared_value_carriage_type === 'Value'">
          <label class="field-label">Amount</label>
          <input v-model.number="form.declared_value_carriage_amount" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div v-else class="opacity-40">
          <label class="field-label">Amount</label>
          <input value="" readonly v-bind="inp" tabindex="-1" />
        </div>

        <!-- Declared Value Customs -->
        <div>
          <label class="field-label">Decl. Value Customs</label>
          <select v-model="form.declared_value_customs_type" v-bind="sel">
            <option value="">—</option>
            <option value="NCV">NCV (no customs value)</option>
            <option value="Value">Declared Value</option>
          </select>
        </div>
        <div v-if="form.declared_value_customs_type === 'Value'">
          <label class="field-label">Amount</label>
          <input v-model.number="form.declared_value_customs_amount" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div v-else class="opacity-40">
          <label class="field-label">Amount</label>
          <input value="" readonly v-bind="inp" tabindex="-1" />
        </div>

        <!-- Insurance -->
        <div>
          <label class="field-label">Insurance</label>
          <select v-model="form.insurance_type" v-bind="sel">
            <option value="">—</option>
            <option value="XXX">XXX (no insurance)</option>
            <option value="Value">Insured Value</option>
          </select>
        </div>
        <div v-if="form.insurance_type === 'Value'">
          <label class="field-label">Amount</label>
          <input v-model.number="form.insurance_amount" type="number" min="0" step="0.01" v-bind="inp" />
        </div>
        <div v-else class="opacity-40">
          <label class="field-label">Amount</label>
          <input value="" readonly v-bind="inp" tabindex="-1" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Rate Lines ─────────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="section-title mb-0">Rate Lines</h3>
          <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">At least one rate line is required to compute totals.</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="$emit('auto-rate-line')" type="button" class="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border font-medium" style="border-color:var(--color-primary);color:var(--color-primary);">
            <Icon name="sliders" :size="12" /> Auto Rate Line
          </button>
          <button @click="addRateLine" type="button" class="add-btn">
            <Icon name="plus" :size="13" /> Add Row
          </button>
        </div>
      </div>

      <div v-if="!rateLines.length" class="empty-state">No rate lines. Add one or click Auto Rate Line to generate from header data.</div>

      <div v-else class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-xs">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th">#</th>
              <th class="th">Pcs</th>
              <th class="th">Rate Class</th>
              <th class="th">G.Wt</th>
              <th class="th">WC</th>
              <th class="th">Chg.Wt</th>
              <th class="th">Rate</th>
              <th class="th">Total</th>
              <th class="th">G/C</th>
              <th class="th">Description</th>
              <th class="th">RCP</th>
              <th class="th">Commodity</th>
              <th class="th">ULD</th>
              <th class="th">%</th>
              <th class="th w-8"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in rateLines" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="p-1"><input :value="row.line_number || i+1" readonly tabindex="-1" v-bind="cell" class="w-8 text-center" style="cursor:not-allowed;color:var(--color-text-subtle);" /></td>
              <td class="p-1"><input v-model.number="row.number_of_pieces" type="number" min="0" v-bind="cell" class="w-14 text-right" /></td>
              <td class="p-1 w-28"><LinkField v-model="row.rate_class_code" doctype="Rate Class Code" placeholder="Q" /></td>
              <td class="p-1"><input v-model.number="row.gross_weight" type="number" min="0" step="0.001" v-bind="cell" class="w-20 text-right" /></td>
              <td class="p-1">
                <select v-model="row.gross_weight_code" class="w-10 px-1 py-1.5 text-xs rounded border outline-none" style="background:var(--color-bg);border-color:var(--color-border);">
                  <option value="K">K</option>
                  <option value="L">L</option>
                </select>
              </td>
              <td class="p-1"><input v-model.number="row.chargeable_weight" type="number" min="0" step="0.001" v-bind="cell" class="w-20 text-right" /></td>
              <td class="p-1"><input v-model.number="row.rate_charge" type="number" min="0" step="0.01" v-bind="cell" class="w-20 text-right" @input="recalcTotal(row)" /></td>
              <td class="p-1"><input v-model.number="row.total" type="number" min="0" step="0.01" v-bind="cell" class="w-24 text-right" /></td>
              <td class="p-1">
                <select v-model="row.goods_data_identifier" class="w-12 px-1 py-1.5 text-xs rounded border outline-none" style="background:var(--color-bg);border-color:var(--color-border);">
                  <option value="">—</option>
                  <option value="G">G</option>
                  <option value="C">C</option>
                </select>
              </td>
              <td class="p-1"><input v-model="row.description" type="text" maxlength="20" v-bind="cell" class="w-32" style="text-transform:uppercase;" /></td>
              <td class="p-1"><input v-model="row.rate_combination_point" type="text" maxlength="3" v-bind="cell" class="w-12 text-center uppercase" style="text-transform:uppercase;" /></td>
              <td class="p-1"><input v-model="row.commodity_item_number" type="text" maxlength="7" v-bind="cell" class="w-20" /></td>
              <td class="p-1"><input v-model="row.uld_rate_class_type" type="text" maxlength="4" v-bind="cell" class="w-14" style="text-transform:uppercase;" /></td>
              <td class="p-1"><input v-model.number="row.rate_class_percentage" type="number" min="0" step="0.1" v-bind="cell" class="w-14 text-right" /></td>
              <td class="p-1 text-center">
                <button @click="rateLines.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="13" /></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Goods Details (P5) ─────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="section-title mb-0">Goods Details <span class="hint normal-case font-normal">(RTD second-line)</span></h3>
          <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">Fields shown change based on the goods identifier (G/C/D/V/U/S/H/O).</p>
        </div>
        <button @click="addGoodsRow" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Row
        </button>
      </div>

      <div v-if="!goodsDetails.length" class="empty-state">No goods detail rows. Optional — add to provide structured goods description.</div>

      <div v-for="(row, i) in goodsDetails" :key="i" class="mb-3 p-3 rounded-xl border" style="border-color:var(--color-border);background:var(--color-bg);">
        <div class="flex items-center justify-between mb-3">
          <!-- Identifier selector drives visible fields below -->
          <div class="flex items-center gap-3">
            <div>
              <label class="field-label">Identifier <span class="hint">DE711</span></label>
              <select v-model="row.goods_data_identifier" v-bind="sel" class="w-24">
                <option value="">—</option>
                <option v-for="id in GDS_IDENTIFIERS" :key="id.code" :value="id.code" :title="id.desc">{{ id.code }} — {{ id.label }}</option>
              </select>
            </div>
            <div>
              <label class="field-label">Rate Line # <span class="hint">(link to rate line)</span></label>
              <select v-model.number="row.rate_line_number" v-bind="sel" class="w-20">
                <option :value="null">—</option>
                <option v-for="rl in rateLines" :key="rl.line_number" :value="rl.line_number || rateLines.indexOf(rl)+1">
                  {{ rl.line_number || rateLines.indexOf(rl)+1 }}
                </option>
              </select>
            </div>
          </div>
          <button @click="goodsDetails.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="14" /></button>
        </div>

        <!-- Context-sensitive fields based on identifier -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">

          <!-- G/C: basic goods description -->
          <template v-if="!row.goods_data_identifier || ['G','C'].includes(row.goods_data_identifier)">
            <div class="sm:col-span-2">
              <label class="field-label">Description</label>
              <input v-model="row.description" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
            </div>
            <div>
              <label class="field-label">HS Code</label>
              <input v-model="row.hs_code" type="text" maxlength="12" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Country of Origin</label>
              <LinkField v-model="row.country_of_origin" doctype="Country" />
            </div>
            <div>
              <label class="field-label">SLAC</label>
              <input v-model.number="row.slac" type="number" min="0" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Service Code</label>
              <LinkField v-model="row.service_code" doctype="Service Code" />
            </div>
          </template>

          <!-- D: dimensions sub-line -->
          <template v-else-if="row.goods_data_identifier === 'D'">
            <div>
              <label class="field-label">Dim Pieces</label>
              <input v-model.number="row.dim_pieces" type="number" min="1" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Length</label>
              <input v-model.number="row.dim_length" type="number" min="0" step="0.1" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Width</label>
              <input v-model.number="row.dim_width" type="number" min="0" step="0.1" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Height</label>
              <input v-model.number="row.dim_height" type="number" min="0" step="0.1" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Wt Code</label>
              <select v-model="row.dim_weight_code" v-bind="sel" class="w-20">
                <option value="K">K</option>
                <option value="L">L</option>
              </select>
            </div>
            <div>
              <label class="field-label">Dim Weight</label>
              <input v-model.number="row.dim_weight" type="number" min="0" step="0.001" v-bind="inp" />
            </div>
          </template>

          <!-- V: volume -->
          <template v-else-if="row.goods_data_identifier === 'V'">
            <div>
              <label class="field-label">Volume Code</label>
              <LinkField v-model="row.volume_code" doctype="Volume Code" />
            </div>
            <div>
              <label class="field-label">Volume Amount</label>
              <input v-model.number="row.volume_amount" type="number" min="0" step="0.0001" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Measurement Unit</label>
              <LinkField v-model="row.measurement_unit" doctype="Measurement Unit Code" />
            </div>
          </template>

          <!-- U: ULD number -->
          <template v-else-if="row.goods_data_identifier === 'U'">
            <div>
              <label class="field-label">ULD Type</label>
              <LinkField v-model="row.uld_type" doctype="ULD Type" />
            </div>
            <div>
              <label class="field-label">ULD Serial #</label>
              <input v-model="row.uld_serial" type="text" maxlength="8" v-bind="inp" style="text-transform:uppercase;" />
            </div>
            <div>
              <label class="field-label">ULD Owner</label>
              <input v-model="row.uld_owner" type="text" maxlength="3" v-bind="inp" style="text-transform:uppercase;" />
            </div>
          </template>

          <!-- S: service code -->
          <template v-else-if="row.goods_data_identifier === 'S'">
            <div>
              <label class="field-label">Service Code</label>
              <LinkField v-model="row.service_code" doctype="Service Code" />
            </div>
          </template>

          <!-- H: HS code / customs -->
          <template v-else-if="row.goods_data_identifier === 'H'">
            <div>
              <label class="field-label">HS Code</label>
              <input v-model="row.hs_code" type="text" maxlength="12" v-bind="inp" />
            </div>
            <div>
              <label class="field-label">Country of Origin</label>
              <LinkField v-model="row.country_of_origin" doctype="Country" />
            </div>
          </template>

          <!-- O: other (all visible) -->
          <template v-else-if="row.goods_data_identifier === 'O'">
            <div class="sm:col-span-4">
              <label class="field-label">Description</label>
              <input v-model="row.description" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
            </div>
          </template>

        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Other Charges ─────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">Other Charges</h3>
        <button @click="addCharge" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Charge
        </button>
      </div>

      <div v-if="!otherCharges.length" class="empty-state">No other charges.</div>

      <div v-else class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-sm">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th w-28">Prepaid / Collect</th>
              <th class="th">Charge Code <span class="text-red-400">*</span></th>
              <th class="th text-right">Amount</th>
              <th class="th w-8"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in otherCharges" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="p-1.5">
                <select v-model="row.prepaid_collect" v-bind="sel">
                  <option value="P">Prepaid</option>
                  <option value="C">Collect</option>
                </select>
              </td>
              <td class="p-1.5">
                <LinkField v-model="row.other_charge_code" doctype="Other Charge Code" placeholder="Code…" />
              </td>
              <td class="p-1.5">
                <input v-model.number="row.amount" type="number" min="0" step="0.01" v-bind="cell" class="w-28 text-right ml-auto block" />
              </td>
              <td class="p-1.5 text-center">
                <button @click="otherCharges.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="13" /></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Charge Summary (read-only server-computed display card) ─────── -->
    <section v-if="chargeSummary.length">
      <h3 class="section-title flex items-center gap-2">
        Charge Summary
        <span class="normal-case font-normal text-xs" style="color:var(--color-text-muted);">server-computed · read-only · never submitted</span>
      </h3>
      <div class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-sm">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th">Settlement</th>
              <th class="th">Charge Identifier</th>
              <th class="th text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in chargeSummary" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="px-3 py-2 text-sm" style="color:var(--color-text-muted);">{{ r.settlement }}</td>
              <td class="px-3 py-2 text-sm" style="color:var(--color-text-muted);">{{ r.charge_identifier }}</td>
              <td class="px-3 py-2 text-sm text-right font-mono" style="color:var(--color-text-base);">{{ r.amount }}</td>
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
  form:          { type: Object, required: true },
  rateLines:     { type: Array,  required: true },
  goodsDetails:  { type: Array,  required: true },
  otherCharges:  { type: Array,  required: true },
  chargeSummary: { type: Array,  required: true },
})

defineEmits(['auto-rate-line'])

const GDS_IDENTIFIERS = [
  { code: 'G', label: 'Goods',        desc: 'General goods description' },
  { code: 'C', label: 'Consol',       desc: 'Consolidation goods' },
  { code: 'D', label: 'Dimensions',   desc: 'Per-piece dimensions sub-line' },
  { code: 'V', label: 'Volume',       desc: 'Volumetric data' },
  { code: 'U', label: 'ULD',          desc: 'Unit Load Device number' },
  { code: 'S', label: 'Service Code', desc: 'Service code' },
  { code: 'H', label: 'HS Code',      desc: 'Harmonized System customs code' },
  { code: 'O', label: 'Other',        desc: 'Other information' },
]

const inp  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const sel  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const cell = { class: 'px-2 py-1.5 text-sm rounded border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }

function recalcTotal(row) {
  const isQ = !row.rate_class_code || row.rate_class_code === 'Q'
  row.total = isQ
    ? (row.rate_charge || 0) * (row.chargeable_weight || 0)
    : (row.rate_charge || 0)
}

function addRateLine() {
  props.rateLines.push({
    line_number: props.rateLines.length + 1,
    number_of_pieces: null, rate_class_code: '', gross_weight: null, gross_weight_code: 'K',
    chargeable_weight: null, rate_charge: null, total: null, goods_data_identifier: '',
    description: '', rate_combination_point: '', commodity_item_number: '',
    uld_rate_class_type: '', rate_class_percentage: null,
  })
}

function addGoodsRow() {
  props.goodsDetails.push({
    rate_line_number: null, goods_data_identifier: '', description: '', hs_code: '',
    country_of_origin: '', slac: null, volume_code: '', volume_amount: null,
    uld_type: '', uld_serial: '', uld_owner: '', measurement_unit: '',
    dim_weight_code: 'K', dim_weight: null, dim_length: null, dim_width: null,
    dim_height: null, dim_pieces: null, service_code: '',
  })
}

function addCharge() {
  props.otherCharges.push({ prepaid_collect: 'P', other_charge_code: '', amount: null })
}
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); display:flex; align-items:center; gap:.375rem; margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
.empty-state    { font-size:.8rem; padding:.75rem; text-align:center; border-radius:.5rem; border:1px dashed var(--color-border); color:var(--color-text-muted); }
.add-btn        { display:flex; align-items:center; gap:.375rem; font-size:.8rem; color:var(--color-primary); }
.th             { padding:.4rem .5rem; text-align:left; font-size:.65rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--color-text-muted); white-space:nowrap; }
</style>
