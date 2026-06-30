<template>
  <div class="space-y-6">

    <!-- ── Special Service Requests ───────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="section-title mb-0">Special Service Requests <span class="hint normal-case font-normal">(SSR)</span></h3>
          <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">65-char free text; IATA ABNF allows 1–3 rows.</p>
        </div>
      </div>

      <div v-for="(row, i) in specialServiceRequests" :key="i" class="flex gap-2 mb-2 items-center">
        <span class="text-xs font-mono w-4 shrink-0 text-right" style="color:var(--color-text-subtle);">{{ i+1 }}</span>
        <input v-model="row.special_service_request" type="text" maxlength="65" v-bind="inp" class="flex-1" placeholder="Free text, 65 chars max" />
        <button @click="specialServiceRequests.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="14" /></button>
      </div>

      <button v-if="specialServiceRequests.length < 3" @click="specialServiceRequests.push({special_service_request:''})" type="button" class="add-btn">
        <Icon name="plus" :size="13" /> Add SSR
      </button>
      <p v-else class="text-xs mt-1" style="color:var(--color-text-muted);">Maximum 3 SSRs (IATA limit).</p>
    </section>

    <hr class="section-divider" />

    <!-- ── Special Handling Codes ──────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">Special Handling Codes <span class="hint normal-case font-normal">(SHC)</span></h3>
        <button @click="specialHandling.push({special_handling_code:'',description:''})" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Code
        </button>
      </div>

      <div v-if="!specialHandling.length" class="empty-state">No special handling codes (e.g. PER, VAL, RCL).</div>

      <div v-else class="flex flex-wrap gap-2 mb-2">
        <!-- Existing rows rendered as tags (if just a code); editing below -->
      </div>

      <div v-for="(row, i) in specialHandling" :key="i" class="flex gap-2 items-center mb-2">
        <div class="w-48 shrink-0">
          <LinkField v-model="row.special_handling_code" doctype="Special Handling Code" placeholder="e.g. PER" />
        </div>
        <span class="flex-1 text-xs" style="color:var(--color-text-muted);">{{ row.description }}</span>
        <button @click="specialHandling.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="14" /></button>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Other Service Information ──────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="section-title mb-0">Other Service Information <span class="hint normal-case font-normal">(OSI)</span></h3>
          <p class="text-xs mt-0.5" style="color:var(--color-text-subtle);">65-char free text; max 3 rows (IATA).</p>
        </div>
      </div>

      <div v-for="(row, i) in otherServiceInfo" :key="i" class="flex gap-2 mb-2 items-center">
        <span class="text-xs font-mono w-4 shrink-0 text-right" style="color:var(--color-text-subtle);">{{ i+1 }}</span>
        <!-- field is other_service_information (not other_service_info — verified fieldname) -->
        <input v-model="row.other_service_information" type="text" maxlength="65" v-bind="inp" class="flex-1" />
        <button @click="otherServiceInfo.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="14" /></button>
      </div>

      <button v-if="otherServiceInfo.length < 3" @click="otherServiceInfo.push({other_service_information:''})" type="button" class="add-btn">
        <Icon name="plus" :size="13" /> Add OSI
      </button>
      <p v-else class="text-xs mt-1" style="color:var(--color-text-muted);">Maximum 3 OSI rows (IATA limit).</p>
    </section>

    <hr class="section-divider" />

    <!-- ── Customs / OCI ──────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Customs &amp; OCI</h3>
      <div class="mb-4">
        <label class="field-label">Customs Origin Code <span class="hint">3-char</span></label>
        <input v-model="form.customs_origin_code" type="text" maxlength="3" v-bind="inp" class="w-24" style="text-transform:uppercase;" />
      </div>

      <div class="flex items-center justify-between mb-3">
        <p class="text-xs" style="color:var(--color-text-muted);">OCI rows (Other Customs Information)</p>
        <button @click="ociCustoms.push({country:'',information_identifier:'',customs_info_identifier:'',supplementary:''})" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add OCI Row
        </button>
      </div>

      <div v-if="!ociCustoms.length" class="empty-state">No OCI rows.</div>

      <div v-for="(row, i) in ociCustoms" :key="i" class="mb-3 p-4 rounded-xl border relative" style="border-color:var(--color-border);background:var(--color-bg);">
        <button @click="ociCustoms.splice(i, 1)" type="button" class="absolute top-3 right-3" style="color:var(--color-text-subtle);">
          <Icon name="x" :size="14" />
        </button>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="field-label">Country</label>
            <LinkField v-model="row.country" doctype="Country" />
          </div>
          <div>
            <label class="field-label">OCI Identifier</label>
            <LinkField v-model="row.information_identifier" doctype="OCI Information Identifier" />
          </div>
          <div>
            <label class="field-label">Customs Info Identifier</label>
            <LinkField v-model="row.customs_info_identifier" doctype="Customs Information Identifier" />
          </div>
          <div>
            <label class="field-label">Supplementary <span class="hint">35-char</span></label>
            <input v-model="row.supplementary" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
          </div>
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Accounting Information ─────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">Accounting Information</h3>
        <button @click="accountingInformation.push({identifier:'',information:''})" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Row
        </button>
      </div>

      <div v-if="!accountingInformation.length" class="empty-state">No accounting information rows.</div>

      <div v-else class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-sm">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th w-48">Identifier <span class="text-red-400">*</span></th>
              <th class="th">Information <span class="hint">(34-char)</span></th>
              <th class="th w-8"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in accountingInformation" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="p-1.5">
                <LinkField v-model="row.identifier" doctype="Accounting Information Identifier" placeholder="Identifier…" />
              </td>
              <td class="p-1.5">
                <input v-model="row.information" type="text" maxlength="34" v-bind="cell" class="w-full" />
              </td>
              <td class="p-1.5 text-center">
                <button @click="accountingInformation.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="13" /></button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── References ─────────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">References</h3>
        <button @click="references.push({reference_number:'',supplementary_1:'',supplementary_2:''})" type="button" class="add-btn">
          <Icon name="plus" :size="13" /> Add Reference
        </button>
      </div>

      <div v-if="!references.length" class="empty-state">No references.</div>

      <div v-else class="overflow-x-auto rounded-xl border" style="border-color:var(--color-border);">
        <table class="w-full text-sm">
          <thead>
            <tr style="background:var(--color-bg);">
              <th class="th">Reference # <span class="hint">(14)</span></th>
              <th class="th">Supplementary 1 <span class="hint">(12)</span></th>
              <th class="th">Supplementary 2 <span class="hint">(12)</span></th>
              <th class="th w-8"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in references" :key="i" class="border-t" style="border-color:var(--color-border);">
              <td class="p-1.5"><input v-model="row.reference_number" type="text" maxlength="14" v-bind="cell" class="w-full" /></td>
              <td class="p-1.5"><input v-model="row.supplementary_1" type="text" maxlength="12" v-bind="cell" class="w-full" /></td>
              <td class="p-1.5"><input v-model="row.supplementary_2" type="text" maxlength="12" v-bind="cell" class="w-full" /></td>
              <td class="p-1.5 text-center">
                <button @click="references.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="13" /></button>
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

defineProps({
  form:                   { type: Object, required: true },
  specialServiceRequests: { type: Array,  required: true },
  specialHandling:        { type: Array,  required: true },
  otherServiceInfo:       { type: Array,  required: true },
  ociCustoms:             { type: Array,  required: true },
  accountingInformation:  { type: Array,  required: true },
  references:             { type: Array,  required: true },
})

const inp  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const cell = { class: 'px-2 py-1.5 text-sm rounded border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
.empty-state    { font-size:.8rem; padding:.75rem; text-align:center; border-radius:.5rem; border:1px dashed var(--color-border); color:var(--color-text-muted); }
.add-btn        { display:flex; align-items:center; gap:.375rem; font-size:.8rem; color:var(--color-primary); }
.th             { padding:.4rem .5rem; text-align:left; font-size:.65rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--color-text-muted); white-space:nowrap; }
</style>
