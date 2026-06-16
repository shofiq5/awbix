<template>
  <header
    class="flex items-center h-14 px-4 shrink-0 z-30 gap-3 border-b"
    style="background:var(--color-topbar-bg);border-color:var(--color-topbar-border);"
  >
    <!-- Sidebar toggle -->
    <button
      type="button"
      @click="toggle"
      class="p-1.5 rounded-lg transition-colors duration-150"
      style="color:var(--color-text-muted);"
      title="Toggle sidebar"
      @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.05)'"
      @mouseleave="e => e.currentTarget.style.background=''"
    >
      <Icon name="menu" :size="18" />
    </button>

    <!-- Divider -->
    <div class="w-px h-5 shrink-0" style="background:var(--color-border);" />

    <!-- Breadcrumb -->
    <Breadcrumb />

    <!-- Spacer -->
    <div class="flex-1" />

    <!-- Global search -->
    <button
      type="button"
      class="hidden sm:flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors duration-150 min-w-[200px]"
      style="background:var(--color-bg);color:var(--color-text-subtle);border:1px solid var(--color-border);"
      @click="searchOpen = true"
    >
      <Icon name="search" :size="14" />
      <span class="flex-1 text-left">Search…</span>
      <kbd class="text-[10px] font-mono px-1 py-0.5 rounded" style="background:var(--color-border);">Ctrl K</kbd>
    </button>

    <!-- Notification bell -->
    <button
      type="button"
      class="relative p-1.5 rounded-lg transition-colors duration-150"
      style="color:var(--color-text-muted);"
      title="Notifications"
      @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.05)'"
      @mouseleave="e => e.currentTarget.style.background=''"
    >
      <Icon name="bell" :size="18" />
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full text-white text-[9px] font-bold"
        style="background:var(--color-primary);"
      >{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
    </button>

    <!-- User dropdown -->
    <UserDropdown />
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useSidebar } from '@/composables/useSidebar'
import Breadcrumb from './Breadcrumb.vue'
import UserDropdown from './UserDropdown.vue'
import Icon from '@/components/ui/Icon.vue'

const { toggle } = useSidebar()
const searchOpen = ref(false)
const unreadCount = ref(0)
</script>
