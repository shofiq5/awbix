<template>
  <div ref="el" class="relative">
    <!-- Avatar button -->
    <button
      type="button"
      @click="open = !open"
      class="flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors duration-150"
      style="color:var(--color-text-muted);"
      @mouseenter="e => e.currentTarget.style.background='rgba(0,0,0,0.05)'"
      @mouseleave="e => e.currentTarget.style.background=''"
    >
      <div
        class="w-7 h-7 rounded-full flex items-center justify-center text-white text-[11px] font-bold shrink-0"
        style="background:var(--color-primary);"
      >{{ initials }}</div>
      <span class="text-sm font-medium hidden md:block truncate max-w-[100px]" style="color:var(--color-text-base);">
        {{ firstName }}
      </span>
      <Icon name="chevron-down" :size="13" />
    </button>

    <!-- Dropdown menu -->
    <Transition name="dropdown">
      <div
        v-if="open"
        class="absolute right-0 top-full mt-1.5 w-60 rounded-xl shadow-xl border z-50 overflow-hidden"
        style="background:var(--color-sidebar-bg);border-color:var(--color-border);"
      >
        <!-- User info header -->
        <div class="px-4 py-3 border-b" style="border-color:var(--color-border);">
          <p class="text-sm font-semibold truncate" style="color:var(--color-text-base);">{{ fullName }}</p>
          <p class="text-xs truncate mt-0.5" style="color:var(--color-text-muted);">{{ userEmail }}</p>
        </div>

        <!-- Menu items -->
        <div class="py-1">
          <button type="button" class="menu-item" @click="open = false">
            <Icon name="user" :size="15" />
            My Profile
          </button>
          <button type="button" class="menu-item" @click="open = false">
            <Icon name="settings" :size="15" />
            Preferences
          </button>
        </div>

        <!-- Theme selector -->
        <div class="px-4 py-3 border-t" style="border-color:var(--color-border);">
          <p class="text-[10px] font-semibold uppercase tracking-widest mb-2" style="color:var(--color-text-subtle);">
            Color Theme
          </p>
          <div class="flex items-center gap-2">
            <button
              v-for="t in THEMES"
              :key="t"
              type="button"
              @click="setTheme(t)"
              class="w-6 h-6 rounded-full transition-all duration-150 border-2"
              :style="`background:${themeColors[t]};border-color:${theme === t ? themeColors[t] : 'transparent'};`"
              :class="theme === t ? 'scale-110 ring-2 ring-offset-1' : 'hover:scale-105'"
              :style2="`--tw-ring-color:${themeColors[t]}`"
              :title="t"
            />
          </div>
        </div>

        <!-- Dark mode toggle -->
        <div class="border-t" style="border-color:var(--color-border);">
          <button type="button" class="menu-item" @click="toggleDark">
            <Icon :name="isDark ? 'sun' : 'moon'" :size="15" />
            {{ isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode' }}
          </button>
        </div>

        <!-- Logout -->
        <div class="border-t py-1" style="border-color:var(--color-border);">
          <button type="button" class="menu-item" style="color:#ef4444;" @click="logout">
            <Icon name="log-out" :size="15" />
            Log Out
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTheme, THEMES } from '@/composables/useTheme'
import Icon from '@/components/ui/Icon.vue'

const { theme, isDark, setTheme, toggleDark } = useTheme()

const el = ref(null)
const open = ref(false)

function onOutside(e) {
  if (el.value && !el.value.contains(e.target)) open.value = false
}
onMounted(() => document.addEventListener('mousedown', onOutside))
onUnmounted(() => document.removeEventListener('mousedown', onOutside))

const themeColors = {
  blue:    '#2563eb',
  green:   '#16a34a',
  emerald: '#059669',
  purple:  '#7c3aed',
  orange:  '#ea580c',
}

const frappe = window.frappe ?? {}
const fullName  = computed(() => frappe.session?.user_fullname ?? 'User')
const userEmail = computed(() => frappe.session?.user ?? '')
const firstName = computed(() => fullName.value.split(' ')[0])
const initials  = computed(() => {
  const parts = fullName.value.trim().split(' ').filter(Boolean)
  return parts.length >= 2
    ? parts[0][0].toUpperCase() + parts[parts.length - 1][0].toUpperCase()
    : (parts[0]?.[0] ?? 'U').toUpperCase()
})

function logout() {
  open.value = false
  window.location.href = '/logout'
}
</script>

<style scoped>
.menu-item {
  @apply flex items-center gap-2.5 w-full px-4 py-2 text-sm text-left transition-colors duration-100;
  color: var(--color-text-base);
}
.menu-item:hover {
  background: rgba(0, 0, 0, 0.05);
}
.dark .menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
</style>
