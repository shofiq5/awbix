<template>
  <div class="flex h-screen overflow-hidden" style="background:var(--color-bg);">
    <!-- Mobile sidebar backdrop -->
    <Transition name="fade">
      <div
        v-if="mobileOpen"
        class="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
        @click="mobileOpen = false"
      />
    </Transition>

    <!-- Sidebar: overlay on mobile, flex item on desktop -->
    <div
      class="fixed md:relative z-50 md:z-auto h-full flex-none transition-transform duration-300 ease-in-out"
      :class="[
        'md:translate-x-0',
        mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
      ]"
    >
      <Sidebar />
    </div>

    <!-- Content area -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <TopBar @menu-click="mobileOpen = !mobileOpen" />

      <main class="flex-1 overflow-y-auto p-5 md:p-6">
        <RouterView v-slot="{ Component, route }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '@/components/shell/Sidebar.vue'
import TopBar from '@/components/shell/TopBar.vue'

const mobileOpen = ref(false)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
