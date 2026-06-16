<template>
  <aside
    class="flex flex-col h-full border-r transition-all duration-300 ease-in-out overflow-hidden"
    :class="collapsed ? 'w-[64px]' : 'w-[224px]'"
    style="background:var(--color-sidebar-bg);border-color:var(--color-sidebar-border);"
  >
    <!-- Logo -->
    <div
      class="flex items-center gap-3 px-4 h-14 shrink-0 border-b"
      style="border-color:var(--color-sidebar-border);"
    >
      <div
        class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-white"
        style="background:var(--color-primary);"
      >
        <Icon name="package" :size="15" />
      </div>
      <Transition name="fade-slide">
        <span
          v-if="!collapsed"
          class="text-[15px] font-bold tracking-tight whitespace-nowrap overflow-hidden"
          style="color:var(--color-text-base);"
        >AWBIX</span>
      </Transition>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3 space-y-0.5">
      <!-- Ungrouped items -->
      <SidebarItem
        v-for="item in ungroupedItems"
        :key="item.id"
        :item="item"
        :collapsed="collapsed"
      />

      <!-- Grouped items -->
      <div v-for="group in groupedItems" :key="group.name" class="mt-4 first:mt-1">
        <!-- Group heading -->
        <template v-if="!collapsed">
          <p
            class="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest select-none"
            style="color:var(--color-text-subtle);"
          >{{ group.name }}</p>
        </template>
        <template v-else>
          <div class="mx-3 border-t mb-2" style="border-color:var(--color-border);" />
        </template>

        <!-- Items in group -->
        <template v-for="item in group.items" :key="item.id">
          <!-- Parent item with children -->
          <div v-if="item.children">
            <button
              type="button"
              @click="toggleParent(item.id)"
              class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm w-full transition-colors duration-150"
              :class="collapsed ? 'justify-center' : ''"
              :title="collapsed ? item.label : undefined"
              style="color:var(--color-text-muted);"
              @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.05)'"
              @mouseleave="e => e.currentTarget.style.background=''"
            >
              <Icon :name="item.icon" :size="16" class="shrink-0" />
              <span v-if="!collapsed" class="flex-1 truncate text-left">{{ item.label }}</span>
              <Icon
                v-if="!collapsed"
                :name="openParents.has(item.id) ? 'chevron-down' : 'chevron-right'"
                :size="13"
                style="color:var(--color-text-subtle);"
              />
            </button>
            <!-- Children -->
            <div
              v-if="!collapsed && openParents.has(item.id)"
              class="ml-3.5 mt-0.5 pl-3 space-y-0.5 border-l"
              style="border-color:var(--color-border);"
            >
              <SidebarItem
                v-for="child in item.children"
                :key="child.id"
                :item="child"
                :collapsed="false"
              />
            </div>
          </div>

          <!-- Leaf item -->
          <SidebarItem v-else :item="item" :collapsed="collapsed" />
        </template>
      </div>
    </nav>

    <!-- Bottom pinned items -->
    <div class="px-2 pt-1 pb-1 border-t" style="border-color:var(--color-sidebar-border);">
      <SidebarItem
        v-for="item in bottomItems"
        :key="item.id"
        :item="item"
        :collapsed="collapsed"
      />
    </div>

    <!-- Collapse toggle -->
    <div class="px-2 pb-3 pt-1">
      <button
        type="button"
        @click="toggle"
        class="w-full flex items-center justify-center py-1.5 rounded-lg transition-colors duration-150"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        style="color:var(--color-text-subtle);"
        @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.05)'"
        @mouseleave="e => e.currentTarget.style.background=''"
      >
        <Icon :name="collapsed ? 'chevron-right' : 'chevron-left'" :size="15" />
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { NAV_ITEMS } from '@/config/navigation.js'
import { useSidebar } from '@/composables/useSidebar.js'
import SidebarItem from './SidebarItem.vue'
import Icon from '@/components/ui/Icon.vue'

const { collapsed, toggle } = useSidebar()

const openParents = reactive(new Set(['shipments', 'parties']))

function toggleParent(id) {
  openParents.has(id) ? openParents.delete(id) : openParents.add(id)
}

const mainItems = computed(() => NAV_ITEMS.filter((i) => !i.bottom))
const bottomItems = computed(() => NAV_ITEMS.filter((i) => i.bottom))

const ungroupedItems = computed(() => mainItems.value.filter((i) => !i.group))

const groupedItems = computed(() => {
  const map = new Map()
  for (const item of mainItems.value) {
    if (!item.group) continue
    if (!map.has(item.group)) map.set(item.group, { name: item.group, items: [] })
    map.get(item.group).items.push(item)
  }
  return [...map.values()]
})
</script>

<style scoped>
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
</style>
