<template>
  <div class="relative" ref="wrapper">
    <div class="relative">
      <Icon
        name="search"
        :size="13"
        class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
        style="color:var(--color-text-subtle);"
      />
      <input
        ref="inputEl"
        v-model="query"
        type="text"
        :placeholder="placeholder || 'Search…'"
        :disabled="disabled"
        class="w-full pl-8 pr-3 py-2 text-sm rounded-lg border outline-none transition"
        :style="disabled
          ? 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-subtle);cursor:not-allowed;'
          : 'background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);'"
        @input="onInput"
        @focus="onFocus"
        @blur="onBlur"
        @keydown.down.prevent="moveDown"
        @keydown.up.prevent="moveUp"
        @keydown.enter.prevent="selectActive"
        @keydown.escape="close"
      />
      <button
        v-if="modelValue && !disabled"
        type="button"
        class="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded"
        style="color:var(--color-text-subtle);"
        @mousedown.prevent="clear"
      >
        <Icon name="x" :size="12" />
      </button>
    </div>

    <!-- Dropdown -->
    <div
      v-if="open && (options.length || searching)"
      class="absolute z-50 mt-1 w-full rounded-lg border shadow-lg overflow-hidden"
      style="background:var(--color-surface);border-color:var(--color-border);max-height:220px;overflow-y:auto;"
    >
      <div v-if="searching" class="flex items-center gap-2 px-3 py-2.5 text-xs" style="color:var(--color-text-muted);">
        <Icon name="loader" :size="12" class="animate-spin" />
        Searching…
      </div>
      <template v-else>
        <button
          v-for="(opt, i) in options"
          :key="opt.value"
          type="button"
          class="w-full text-left px-3 py-2 text-sm transition-colors"
          :style="i === activeIdx
            ? 'background:var(--color-primary-light);color:var(--color-primary);'
            : 'color:var(--color-text-base);'"
          @mousedown.prevent="select(opt)"
          @mouseover="activeIdx = i"
        >
          <span class="font-medium">{{ opt.value }}</span>
          <span v-if="opt.label && opt.label !== opt.value" class="ml-1.5 text-xs" style="color:var(--color-text-muted);">{{ opt.label }}</span>
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue:  { type: String, default: '' },
  doctype:     { type: String, required: true },
  placeholder: { type: String, default: '' },
  filters:     { type: Object, default: null },
  disabled:    { type: Boolean, default: false },
})
const emits = defineEmits(['update:modelValue'])

const inputEl  = ref(null)
const wrapper  = ref(null)
const query    = ref('')
const options  = ref([])
const open     = ref(false)
const searching = ref(false)
const activeIdx = ref(-1)
let debounceTimer = null
let currentValue = ''

function csrf() { return window.frappe?.csrf_token || '' }

function parseErr(j) {
  if (j._server_messages) {
    try { return JSON.parse(JSON.parse(j._server_messages)[0]).message } catch {}
  }
  return j.exc_type || 'Search failed'
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

async function search(txt) {
  searching.value = true
  try {
    const params = { doctype: props.doctype, txt: txt || '', page_length: 20 }
    if (props.filters) params.filters = JSON.stringify(props.filters)
    const results = await apiGet('/api/method/awbix.frontend_api.search_link', params)
    options.value = results || []
    activeIdx.value = -1
  } catch {
    options.value = []
  } finally {
    searching.value = false
  }
}

async function fetchLabel(value) {
  if (!value) return
  try {
    const results = await apiGet('/api/method/awbix.frontend_api.search_link', {
      doctype: props.doctype,
      txt: value,
      page_length: 5,
    })
    const match = (results || []).find(r => r.value === value)
    if (match) query.value = match.label && match.label !== match.value ? `${match.value} — ${match.label}` : match.value
    else query.value = value
  } catch {
    query.value = value
  }
}

function onInput() {
  clearTimeout(debounceTimer)
  open.value = true
  if (!query.value.trim()) {
    options.value = []
    emits('update:modelValue', '')
    currentValue = ''
    return
  }
  debounceTimer = setTimeout(() => search(query.value), 280)
}

function onFocus() {
  open.value = true
  if (!query.value) search('')
}

function onBlur() {
  setTimeout(() => {
    close()
    // If user typed something but didn't select, restore displayed label for current value
    if (currentValue && query.value !== currentValue) {
      fetchLabel(currentValue)
    } else if (!currentValue) {
      query.value = ''
    }
  }, 150)
}

function close() {
  open.value = false
  activeIdx.value = -1
}

function select(opt) {
  currentValue = opt.value
  query.value = opt.label && opt.label !== opt.value ? `${opt.value} — ${opt.label}` : opt.value
  emits('update:modelValue', opt.value)
  close()
}

function clear() {
  currentValue = ''
  query.value = ''
  options.value = []
  emits('update:modelValue', '')
  inputEl.value?.focus()
}

function moveDown() {
  if (!open.value) { open.value = true; search(query.value); return }
  activeIdx.value = Math.min(activeIdx.value + 1, options.value.length - 1)
}

function moveUp() {
  activeIdx.value = Math.max(activeIdx.value - 1, -1)
}

function selectActive() {
  if (activeIdx.value >= 0 && options.value[activeIdx.value]) {
    select(options.value[activeIdx.value])
  }
}

function onClickOutside(e) {
  if (wrapper.value && !wrapper.value.contains(e.target)) close()
}

// When modelValue changes externally (e.g. form reset or load), sync display
watch(() => props.modelValue, (val) => {
  if (val !== currentValue) {
    currentValue = val || ''
    if (val) fetchLabel(val)
    else query.value = ''
  }
}, { immediate: false })

onMounted(() => {
  document.addEventListener('mousedown', onClickOutside)
  if (props.modelValue) {
    currentValue = props.modelValue
    fetchLabel(props.modelValue)
  }
})

onUnmounted(() => {
  document.removeEventListener('mousedown', onClickOutside)
  clearTimeout(debounceTimer)
})
</script>
