<template>
  <div class="space-y-5">

    <!-- ── Shipper ─────────────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Shipper</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="field-label">Account No. <span class="hint">DE112</span></label>
          <input v-model="form.shipper_account" type="text" maxlength="14" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div class="sm:col-span-2">
          <label class="field-label">Name <span class="hint">DE116</span></label>
          <input v-model="form.shipper_name" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div class="sm:col-span-2">
          <label class="field-label">Street Address</label>
          <input v-model="form.shipper_address" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Place / City</label>
          <input v-model="form.shipper_place" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">State / Province</label>
          <input v-model="form.shipper_state" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Country</label>
          <LinkField v-model="form.shipper_country" doctype="Country" placeholder="Country" />
        </div>
        <div>
          <label class="field-label">Post Code</label>
          <input v-model="form.shipper_post_code" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Consignee ───────────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Consignee</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="field-label">Account No.</label>
          <input v-model="form.consignee_account" type="text" maxlength="14" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div class="sm:col-span-2">
          <label class="field-label">Name</label>
          <input v-model="form.consignee_name" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div class="sm:col-span-2">
          <label class="field-label">Street Address</label>
          <input v-model="form.consignee_address" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Place / City</label>
          <input v-model="form.consignee_place" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">State / Province</label>
          <input v-model="form.consignee_state" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Country</label>
          <LinkField v-model="form.consignee_country" doctype="Country" placeholder="Country" />
        </div>
        <div>
          <label class="field-label">Post Code</label>
          <input v-model="form.consignee_post_code" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Agent ──────────────────────────────────────────────────────── -->
    <section>
      <h3 class="section-title">Issuing Carrier's Agent</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="sm:col-span-2">
          <label class="field-label">Agent</label>
          <LinkField v-model="form.agent" doctype="Party" placeholder="Search agent…" />
        </div>
        <div>
          <label class="field-label">Agent Name <span class="hint">fetched</span></label>
          <input :value="form.agent_name" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">Place <span class="hint">fetched</span></label>
          <input :value="form.agent_place" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">Account No. <span class="hint">fetched</span></label>
          <input :value="form.agent_account" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">IATA Code <span class="hint">DE118</span></label>
          <input :value="form.agent_iata_code" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">CASS Address <span class="hint">4-char</span></label>
          <input :value="form.agent_cass_address" v-bind="ro" />
        </div>
        <div>
          <label class="field-label">Participant ID <span class="hint">3-char</span></label>
          <input :value="form.agent_participant_id" v-bind="ro" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Nominated Handling Agent ───────────────────────────────────── -->
    <section>
      <h3 class="section-title">Nominated Handling Agent</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="field-label">Name</label>
          <input v-model="form.nominated_handling_name" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
        </div>
        <div>
          <label class="field-label">Place</label>
          <input v-model="form.nominated_handling_place" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- ── Also Notify ─────────────────────────────────────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-3">
        <h3 class="section-title mb-0">Also Notify</h3>
        <span class="text-xs" style="color:var(--color-text-subtle);">typical max 2 rows (IATA)</span>
      </div>

      <div v-if="!alsoNotify.length" class="empty-state">No notify parties added.</div>

      <div v-for="(row, i) in alsoNotify" :key="i" class="mb-3 p-4 rounded-xl border relative" style="border-color:var(--color-border);background:var(--color-bg);">
        <button @click="alsoNotify.splice(i, 1)" type="button" class="absolute top-3 right-3" style="color:var(--color-text-subtle);">
          <Icon name="x" :size="14" />
        </button>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="field-label">Party (link)</label>
            <LinkField v-model="row.party" doctype="Party" placeholder="Search…" />
          </div>
          <div>
            <label class="field-label">Name <span class="text-red-400">*</span> <span class="hint">notify_name</span></label>
            <input v-model="row.notify_name" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" placeholder="Required" />
          </div>
          <div class="sm:col-span-2">
            <label class="field-label">Street Address</label>
            <input v-model="row.street_address" type="text" maxlength="35" v-bind="inp" style="text-transform:uppercase;" />
          </div>
          <div>
            <label class="field-label">Place</label>
            <input v-model="row.place" type="text" maxlength="17" v-bind="inp" style="text-transform:uppercase;" />
          </div>
          <div>
            <label class="field-label">State</label>
            <input v-model="row.state_province" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
          </div>
          <div>
            <label class="field-label">Country</label>
            <LinkField v-model="row.country" doctype="Country" />
          </div>
          <div>
            <label class="field-label">Post Code</label>
            <input v-model="row.post_code" type="text" maxlength="9" v-bind="inp" style="text-transform:uppercase;" />
          </div>
          <div>
            <label class="field-label">Telephone</label>
            <input v-model="row.telephone" type="text" maxlength="25" v-bind="inp" />
          </div>
          <div>
            <label class="field-label">Fax</label>
            <input v-model="row.fax" type="text" maxlength="25" v-bind="inp" />
          </div>
        </div>
      </div>

      <button @click="addNotify" type="button" class="add-btn">
        <Icon name="plus" :size="13" /> Add Notify Party
      </button>
    </section>

    <hr class="section-divider" />

    <!-- ── Other Participants (collapsed — rare field) ─────────────────── -->
    <section>
      <div class="flex items-center justify-between mb-2">
        <h3 class="section-title mb-0">Other Participants <span class="hint normal-case font-normal">(rare / advanced)</span></h3>
        <button @click="showParticipants = !showParticipants" type="button" class="text-xs flex items-center gap-1" style="color:var(--color-text-muted);">
          <Icon :name="showParticipants ? 'chevron-up' : 'chevron-down'" :size="13" />
          {{ showParticipants ? 'Collapse' : 'Expand' }}
          <span v-if="otherParticipants.length" class="badge">{{ otherParticipants.length }}</span>
        </button>
      </div>

      <template v-if="showParticipants">
        <div v-if="!otherParticipants.length" class="empty-state">No other participants.</div>
        <div v-else class="overflow-x-auto rounded-lg border" style="border-color:var(--color-border);">
          <table class="w-full text-sm">
            <thead>
              <tr style="background:var(--color-bg);">
                <th class="th">Name <span class="hint">(participant_name)</span></th>
                <th class="th">Office File Ref</th>
                <th class="th">Part. ID</th>
                <th class="th">Part. Code</th>
                <th class="th">Airport</th>
                <th class="th w-8"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in otherParticipants" :key="i" class="border-t" style="border-color:var(--color-border);">
                <td class="p-1"><input v-model="row.participant_name" type="text" maxlength="35" v-bind="cell" style="text-transform:uppercase;" /></td>
                <td class="p-1"><input v-model="row.office_file_reference" type="text" maxlength="15" v-bind="cell" style="text-transform:uppercase;" /></td>
                <td class="p-1 w-20"><input v-model="row.participant_id" type="text" maxlength="3" v-bind="cell" style="text-transform:uppercase;" /></td>
                <td class="p-1"><input v-model="row.participant_code" type="text" maxlength="17" v-bind="cell" style="text-transform:uppercase;" /></td>
                <td class="p-1 w-40"><LinkField v-model="row.airport" doctype="Airport" /></td>
                <td class="p-1 text-center">
                  <button @click="otherParticipants.splice(i, 1)" type="button" style="color:#dc2626;"><Icon name="x" :size="13" /></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <button @click="addParticipant" type="button" class="add-btn mt-2">
          <Icon name="plus" :size="13" /> Add Participant
        </button>
      </template>
    </section>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import LinkField from '@/components/ui/LinkField.vue'

const props = defineProps({
  form:              { type: Object, required: true },
  alsoNotify:        { type: Array,  required: true },
  otherParticipants: { type: Array,  required: true },
})

const showParticipants = ref(false)

const inp = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none transition', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }
const ro  = { class: 'w-full px-3 py-2 text-sm rounded-lg border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-subtle);cursor:not-allowed;', readonly: true, tabindex: '-1' }
const cell = { class: 'w-full px-2 py-1.5 text-sm rounded border outline-none', style: 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);' }

function addNotify() {
  props.alsoNotify.push({ party: '', notify_name: '', street_address: '', place: '', state_province: '', country: '', post_code: '', telephone: '', fax: '' })
}
function addParticipant() {
  props.otherParticipants.push({ participant_name: '', office_file_reference: '', participant_id: '', participant_code: '', airport: '' })
}
</script>

<style scoped>
.section-title  { font-size:.65rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--color-text-subtle); margin-bottom:.75rem; }
.field-label    { display:block; font-size:.7rem; font-weight:500; margin-bottom:.35rem; color:var(--color-text-muted); }
.hint           { font-size:.65rem; font-weight:400; color:var(--color-text-subtle); margin-left:.25rem; }
.section-divider{ border:0; border-top:1px solid var(--color-border); }
.empty-state    { font-size:.8rem; padding:.75rem; text-align:center; border-radius:.5rem; border:1px dashed var(--color-border); color:var(--color-text-muted); }
.add-btn        { display:flex; align-items:center; gap:.375rem; font-size:.8rem; color:var(--color-primary); margin-top:.5rem; }
.th             { padding:.4rem .5rem; text-align:left; font-size:.65rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--color-text-muted); white-space:nowrap; }
.badge          { margin-left:.25rem; padding:.1rem .375rem; border-radius:9999px; font-size:.6rem; font-weight:700; color:white; background:var(--color-text-muted); }
</style>
