<template>
  <svg
    :width="size"
    :height="size"
    :stroke-width="strokeWidth"
    fill="none"
    stroke="currentColor"
    stroke-linecap="round"
    stroke-linejoin="round"
    viewBox="0 0 24 24"
    v-bind="$attrs"
    class="shrink-0"
  >
    <g v-html="pathSvg" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'
import { getSvgPath } from '@/utils/icons'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 },
  strokeWidth: { type: [Number, String], default: 1.75 },
})

const pathSvg = computed(() => getSvgPath(props.name) ?? '')
</script>
