<template>
  <div
    class="h-screen w-screen flex items-center justify-center p-4 overflow-y-auto"
    style="background:var(--color-bg);"
  >
    <div class="w-full max-w-sm">
      <!-- Brand -->
      <div class="flex flex-col items-center mb-8">
        <div
          class="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold mb-3"
          style="background:var(--color-primary);"
        >
          A
        </div>
        <h1 class="text-xl font-bold" style="color:var(--color-text-base);">AWBix</h1>
        <p class="text-sm mt-0.5" style="color:var(--color-text-muted);">Sign in to your account</p>
      </div>

      <!-- Card -->
      <form
        @submit.prevent="submit"
        class="rounded-2xl border p-6 space-y-5"
        style="background:var(--color-surface);border-color:var(--color-border);"
      >
        <!-- Error banner -->
        <Transition name="toast">
          <div
            v-if="error"
            class="flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-sm"
            style="background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;"
          >
            <Icon name="alert-triangle" :size="15" />
            <span>{{ error }}</span>
          </div>
        </Transition>

        <!-- Email -->
        <div>
          <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">
            Email
          </label>
          <input
            v-model="email"
            type="text"
            autocomplete="username"
            autofocus
            placeholder="you@example.com"
            class="w-full px-3 py-2.5 text-sm rounded-lg border outline-none transition focus:ring-2"
            style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
            @input="error = ''"
          >
        </div>

        <!-- Password -->
        <div>
          <label class="block text-xs font-medium mb-1.5" style="color:var(--color-text-muted);">
            Password
          </label>
          <div class="relative">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="••••••••"
              class="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border outline-none transition"
              style="background:var(--color-bg);border-color:var(--color-border);color:var(--color-text-base);"
              @input="error = ''"
            >
            <button
              type="button"
              tabindex="-1"
              @click="showPassword = !showPassword"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md transition-colors"
              style="color:var(--color-text-subtle);"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
            >
              <Icon :name="showPassword ? 'eye-off' : 'eye'" :size="15" />
            </button>
          </div>
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="loading || !email || !password"
          class="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium text-white transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
          style="background:var(--color-primary);"
          @mouseenter="e => !loading && (e.currentTarget.style.background='var(--color-primary-hover)')"
          @mouseleave="e => e.currentTarget.style.background='var(--color-primary)'"
        >
          <Icon v-if="loading" name="loader" :size="15" class="animate-spin" />
          {{ loading ? 'Signing in…' : 'Sign In' }}
        </button>
      </form>

      <p class="text-center text-xs mt-6" style="color:var(--color-text-subtle);">
        AWBix · Air Waybill Management
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '@/composables/useSession'
import Icon from '@/components/ui/Icon.vue'

const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function submit() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    await login(email.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    // Guard against open redirects — only allow in-app paths.
    router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } catch (e) {
    error.value = e.message || 'Sign in failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
