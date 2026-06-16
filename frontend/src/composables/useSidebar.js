import { useStorage } from './useStorage'

const collapsed = useStorage('awbix-sidebar-collapsed', false)

export function useSidebar() {
  function toggle() {
    collapsed.value = !collapsed.value
  }
  return { collapsed, toggle }
}
