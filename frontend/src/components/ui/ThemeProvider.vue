<template>
  <slot />
</template>

<script setup>
import { onMounted } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { applyTheme } = useTheme()
onMounted(() => applyTheme())
</script>
