import { watch } from 'vue'
import { useStorage } from './useStorage'

export const THEMES = ['blue', 'green', 'emerald', 'purple', 'orange']

const theme  = useStorage('awbix-theme', 'blue')
const isDark = useStorage('awbix-dark', false)

function applyTheme() {
  const html = document.documentElement
  THEMES.forEach((t) => html.classList.remove(`theme-${t}`))
  html.classList.add(`theme-${theme.value}`)
  isDark.value ? html.classList.add('dark') : html.classList.remove('dark')
}

export function useTheme() {
  function setTheme(name) {
    if (THEMES.includes(name)) {
      theme.value = name
      applyTheme()
    }
  }

  function toggleDark() {
    isDark.value = !isDark.value
    applyTheme()
  }

  watch([theme, isDark], applyTheme)

  return { theme, isDark, THEMES, setTheme, toggleDark, applyTheme }
}
