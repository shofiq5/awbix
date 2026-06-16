import { ref, watch } from 'vue'

export function useStorage(key, defaultValue) {
  let initial = defaultValue
  try {
    const raw = localStorage.getItem(key)
    if (raw !== null) initial = JSON.parse(raw)
  } catch {}

  const value = ref(initial)

  watch(
    value,
    (v) => {
      try { localStorage.setItem(key, JSON.stringify(v)) } catch {}
    },
    { deep: true },
  )

  return value
}
