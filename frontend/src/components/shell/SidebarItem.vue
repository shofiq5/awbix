<template>
  <!-- External link -->
  <a
    v-if="item.external"
    :href="item.external"
    target="_blank"
    rel="noopener noreferrer"
    class="nav-item"
    :title="collapsed ? item.label : undefined"
  >
    <Icon :name="item.icon" :size="16" class="shrink-0" />
    <span v-if="!collapsed" class="flex-1 truncate">{{ item.label }}</span>
    <Icon v-if="!collapsed" name="external-link" :size="12" class="text-[var(--color-text-subtle)]" />
  </a>

  <!-- Internal route -->
  <RouterLink
    v-else
    :to="item.route"
    custom
    v-slot="{ isActive, isExactActive, navigate }"
  >
    <button
      type="button"
      @click="navigate"
      class="nav-item"
      :class="isItemActive(item.route, isActive, isExactActive)
        ? 'nav-item--active'
        : 'nav-item--default'"
      :title="collapsed ? item.label : undefined"
    >
      <Icon :name="item.icon" :size="16" class="shrink-0" />
      <span v-if="!collapsed" class="flex-1 truncate text-left">{{ item.label }}</span>
      <span
        v-if="!collapsed && item.badge"
        class="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
        style="background:var(--color-primary);color:#fff;"
      >{{ item.badge }}</span>
    </button>
  </RouterLink>
</template>

<script setup>
import Icon from '@/components/ui/Icon.vue'

const props = defineProps({
  item: { type: Object, required: true },
  collapsed: { type: Boolean, default: false },
})

function isItemActive(route, isActive, isExactActive) {
  return route === '/' ? isExactActive : isActive
}
</script>

<style scoped>
.nav-item {
  @apply flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm w-full transition-colors duration-150 cursor-pointer border-0 bg-transparent;
}
.nav-item--default {
  color: var(--color-text-muted);
}
.nav-item--default:hover {
  background: rgba(0,0,0,0.05);
  color: var(--color-text-base);
}
.dark .nav-item--default:hover {
  background: rgba(255,255,255,0.06);
}
.nav-item--active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
  box-shadow: inset 2px 0 0 var(--color-primary);
}
</style>
