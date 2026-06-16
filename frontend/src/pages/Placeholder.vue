<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
    <div
      class="w-16 h-16 rounded-2xl flex items-center justify-center"
      style="background:var(--color-primary-light);"
    >
      <Icon :name="icon" :size="28" style="color:var(--color-primary);" />
    </div>
    <div>
      <h2 class="text-xl font-semibold" style="color:var(--color-text-base);">{{ title }}</h2>
      <p class="text-sm mt-1" style="color:var(--color-text-muted);">
        This page is coming soon. Check back after the next sprint.
      </p>
    </div>
    <RouterLink to="/" class="text-sm font-medium" style="color:var(--color-primary);">
      ← Back to Dashboard
    </RouterLink>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => route.meta?.title ?? 'Page')

const iconMap = {
  'Air Waybills': 'file-text', 'House AWBs': 'layers', Manifests: 'list',
  'DG Declarations': 'alert-triangle', Customers: 'users', Billing: 'credit-card',
  Reports: 'bar-chart-2', Settings: 'settings',
}
const icon = computed(() => iconMap[title.value] ?? 'box')
</script>
