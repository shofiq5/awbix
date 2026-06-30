<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background:rgba(0,0,0,0.5);"
      @click.self="$emit('close')"
      @keydown.escape="$emit('close')"
    >
      <div
        class="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl overflow-hidden shadow-2xl"
        style="background:var(--color-surface);"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b" style="border-color:var(--color-border);">
          <div>
            <h2 class="text-base font-semibold" style="color:var(--color-text-base);">Dimension Lines</h2>
            <p class="text-xs mt-0.5" style="color:var(--color-text-muted);">Enter per-piece dimensions; volume weight is computed server-side by compute_dimensions().</p>
          </div>
          <button type="button" @click="$emit('close')" style="color:var(--color-text-subtle);">
            <Icon name="x" :size="18" />
          </button>
        </div>

        <!-- Body: scrollable grid -->
        <div class="flex-1 overflow-y-auto px-6 py-4 space-y-3">

          <!-- Header row -->
          <div class="grid gap-2 text-xs font-semibold uppercase tracking-wider" :class="gridClass" style="color:var(--color-text-muted);">
            <div>Line #</div>
            <div>Pieces</div>
            <div>Length</div>
            <div>Width</div>
            <div>Height</div>
            <div>Unit</div>
            <div>Remarks</div>
            <div></div>
          </div>

          <!-- Rows -->
          <div
            v-for="(row, i) in rows"
            :key="i"
            class="grid gap-2 items-center"
            :class="gridClass"
          >
            <input
              :value="row.line_number || i + 1"
              readonly
              tabindex="-1"
              class="px-2 py-1.5 text-sm rounded-lg border text-center"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-subtle);cursor:not-allowed;"
            />
            <input
              v-model.number="row.pieces"
              type="number" min="1" step="1"
              @input="recalc"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none text-right"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
            <input
              v-model.number="row.length"
              type="number" min="0" step="0.1"
              @input="recalc"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none text-right"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
            <input
              v-model.number="row.width"
              type="number" min="0" step="0.1"
              @input="recalc"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none text-right"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
            <input
              v-model.number="row.height"
              type="number" min="0" step="0.1"
              @input="recalc"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none text-right"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
            <select
              v-model="row.dim_unit"
              @change="recalc"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            >
              <option value="CM">CM</option>
              <option value="IN">IN</option>
            </select>
            <input
              v-model="row.remarks"
              type="text" maxlength="35"
              class="px-2 py-1.5 text-sm rounded-lg border outline-none"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            />
            <button type="button" @click="removeRow(i)" style="color:#dc2626;">
              <Icon name="x" :size="14" />
            </button>
          </div>

          <!-- Add row + CSV upload -->
          <div class="flex items-center gap-3 mt-2 flex-wrap">
            <button
              type="button"
              @click="addRow"
              class="flex items-center gap-1.5 text-sm"
              style="color:var(--color-primary);"
            >
              <Icon name="plus" :size="13" /> Add Row
            </button>

            <label
              class="flex items-center gap-1.5 text-sm cursor-pointer"
              :class="uploading ? 'opacity-60 pointer-events-none' : ''"
              style="color:var(--color-text-muted);"
              title="Import rows from a CSV or XLSX file (columns: pieces, length, width, height, unit)"
            >
              <Icon :name="uploading ? 'loader' : 'upload'" :size="13" :class="uploading ? 'animate-spin' : ''" />
              {{ uploading ? 'Importing…' : 'Import CSV / XLSX' }}
              <input
                ref="fileInputEl"
                type="file"
                accept=".csv,.xlsx,.xls"
                class="hidden"
                @change="onFileChange"
              />
            </label>
          </div>

          <!-- Import errors -->
          <div v-if="importErrors.length" class="mt-3 p-3 rounded-lg border text-xs space-y-1" style="border-color:#fca5a5;background:#fee2e2;color:#b91c1c;">
            <p class="font-semibold">Import warnings (rows still added):</p>
            <p v-for="e in importErrors" :key="e.row">Row {{ e.row }}: {{ e.message }}</p>
          </div>
        </div>

        <!-- Preview footer — mirrors compute_dimensions() output -->
        <div class="border-t px-6 py-4" style="border-color:var(--color-border);background:var(--color-bg);">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-4">
            <div>
              <p class="text-xs mb-0.5" style="color:var(--color-text-muted);">Total Volume (m³)</p>
              <p class="font-mono font-semibold" style="color:var(--color-text-base);">{{ fmtNum(preview.volume, 4) }}</p>
            </div>
            <div>
              <p class="text-xs mb-0.5" style="color:var(--color-text-muted);">Volume Weight (kg)</p>
              <p class="font-mono font-semibold" style="color:var(--color-text-base);">{{ fmtNum(preview.volumeWeight, 2) }}</p>
            </div>
            <div>
              <p class="text-xs mb-0.5" style="color:var(--color-text-muted);">Gross Weight (kg)</p>
              <p class="font-mono" style="color:var(--color-text-muted);">{{ fmtNum(props.weight, 2) }} {{ props.weight != null ? props.volumeWeightFactor : '' }}</p>
            </div>
            <div>
              <p class="text-xs mb-0.5" style="color:var(--color-text-muted);">Chargeable (kg)</p>
              <p class="font-mono font-semibold" :style="'color:' + (preview.chargeableWeight > (props.weight||0) ? 'var(--color-primary)' : 'var(--color-text-base)') + ';'">
                {{ fmtNum(preview.chargeableWeight, 2) }}
              </p>
            </div>
          </div>

          <p class="text-xs mb-3" style="color:var(--color-text-subtle);">
            Preview only — server will recompute via compute_dimensions() on save. Unit conversion: 1 IN = 2.54 CM.
          </p>

          <div class="flex justify-end gap-3">
            <button type="button" @click="$emit('close')" class="px-4 py-2 text-sm rounded-lg border" style="border-color:var(--color-border);color:var(--color-text-muted);">
              Cancel
            </button>
            <button type="button" @click="apply" class="px-4 py-2 text-sm rounded-lg text-white font-medium" style="background:var(--color-primary);">
              Apply {{ rows.length ? rows.length + (rows.length === 1 ? ' row' : ' rows') : '' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'

const props = defineProps({
  initialRows:         { type: Array,  default: () => [] },
  weight:              { type: Number, default: null },
  volumeWeightFactor:  { type: Number, default: 6000 },
  volumeAmount:        { type: Number, default: null },
  volumeCode:          { type: String, default: '' },
})

const emit = defineEmits(['apply', 'close'])

const gridClass = 'grid-cols-[48px_64px_72px_72px_72px_64px_1fr_32px]'

const rows = ref([])
const fileInputEl = ref(null)
const uploading   = ref(false)
const importErrors = ref([])

function blankRow(i) {
  return { line_number: i + 1, pieces: null, length: null, width: null, height: null, dim_unit: 'CM', remarks: '' }
}

function addRow() {
  rows.value.push(blankRow(rows.value.length))
}

function removeRow(i) {
  rows.value.splice(i, 1)
  rows.value.forEach((r, idx) => { r.line_number = idx + 1 })
  recalc()
}

// Preview mirrors compute_dimensions() from shipment.py
const preview = reactive({ volume: 0, volumeWeight: 0, chargeableWeight: 0 })

function recalc() {
  let totalVolumeCm3 = 0
  for (const r of rows.value) {
    if (!r.pieces || !r.length || !r.width || !r.height) continue
    let l = r.length, w = r.width, h = r.height
    if ((r.dim_unit || 'CM') === 'IN') { l *= 2.54; w *= 2.54; h *= 2.54 }
    totalVolumeCm3 += r.pieces * l * w * h
  }
  const factor = props.volumeWeightFactor || 6000
  // volume in m³ = cm³ / 1_000_000; volume_weight = (cm³/factor) in kg
  const volM3 = totalVolumeCm3 / 1_000_000
  const volWt = totalVolumeCm3 / factor   // factor is cm³ per kg
  const grossWt = props.weight || 0
  preview.volume = volM3
  preview.volumeWeight = volWt
  preview.chargeableWeight = Math.max(grossWt, volWt)
}

function fmtNum(n, decimals = 2) {
  if (n == null || isNaN(n)) return '—'
  return Number(n).toFixed(decimals)
}

function csrf() { return window.frappe?.csrf_token || '' }

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!fileInputEl.value) return
  fileInputEl.value.value = ''   // reset so same file can be re-imported
  if (!file) return

  uploading.value = true
  importErrors.value = []
  try {
    // Step 1: upload file to Frappe's file manager
    const fd = new FormData()
    fd.append('file', file)
    fd.append('is_private', '1')
    fd.append('cmd', 'uploadfile')
    const upRes = await fetch('/api/method/uploadfile', {
      method: 'POST',
      headers: { 'X-Frappe-CSRF-Token': csrf() },
      body: fd,
    })
    const upJson = await upRes.json()
    const fileUrl = upJson.message?.file_url
    if (!fileUrl) throw new Error('Upload failed — no file_url returned.')

    // Step 2: call parse_dimension_file with the uploaded URL
    const u = new URL('/api/method/awbix.shipment.doctype.shipment.shipment.parse_dimension_file', window.location.origin)
    u.searchParams.set('file_url', fileUrl)
    const parseRes = await fetch(u.toString(), { headers: { 'X-Frappe-CSRF-Token': csrf() } })
    const parseJson = await parseRes.json()
    if (parseJson.exc) throw new Error('Parse error — check file format.')
    const { rows: newRows, errors } = parseJson.message || {}

    // Merge: append parsed rows (auto line_number from current length)
    const base = rows.value.length
    ;(newRows || []).forEach((r, i) => {
      rows.value.push({
        line_number: base + i + 1,
        pieces: r.pieces || 1,
        length: r.length || null,
        width:  r.width  || null,
        height: r.height || null,
        dim_unit: (r.dim_unit || 'cm').toUpperCase(),
        remarks: '',
      })
    })
    importErrors.value = errors || []
    recalc()
  } catch (err) {
    importErrors.value = [{ row: '—', message: err.message || 'Import failed.' }]
  } finally {
    uploading.value = false
  }
}

function apply() {
  recalc()
  emit('apply', {
    rows: rows.value.map(r => ({ ...r })),
    volumeWeight: preview.volumeWeight,
    chargeableWeight: preview.chargeableWeight,
    suggestedVolumeAmount: rows.value.length ? preview.volume : null,
  })
}

onMounted(() => {
  if (props.initialRows && props.initialRows.length) {
    rows.value = props.initialRows.map(r => ({ ...r }))
  } else {
    rows.value = [blankRow(0)]
  }
  recalc()
})

// Recompute if weight or factor changes while modal is open
watch(() => [props.weight, props.volumeWeightFactor], recalc)
</script>
