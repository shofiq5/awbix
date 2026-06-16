<template>
  <nav v-if="crumbs.length" class="flex items-center gap-1.5 text-sm min-w-0">
    <template v-for="(crumb, i) in crumbs" :key="i">
      <span
        class="truncate"
        :class="i === crumbs.length - 1
          ? 'font-medium'
          : 'hidden sm:inline'"
        :style="i === crumbs.length - 1
          ? 'color:var(--color-text-base);'
          : 'color:var(--color-text-subtle);'"
      >{{ crumb }}</span>
      <Icon
        v-if="i < crumbs.length - 1"
        name="chevron-right"
        :size="13"
        class="shrink-0 hidden sm:inline-flex"
        style="color:var(--color-text-subtle);"
      />
    </template>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Icon from '@/components/ui/Icon.vue'

const route = useRoute()
const crumbs = computed(() => route.meta?.breadcrumb ?? [])
</script>
