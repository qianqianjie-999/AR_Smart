import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    sidebarCollapsed: false,
    breadcrumbs: [],
    loading: false
  }),
  getters: {
    isSidebarCollapsed: (state) => state.sidebarCollapsed,
    currentBreadcrumbs: (state) => state.breadcrumbs
  },
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    setSidebarCollapsed(collapsed) {
      this.sidebarCollapsed = collapsed
    },
    setBreadcrumbs(items) {
      this.breadcrumbs = items
    },
    setLoading(val) {
      this.loading = val
    }
  }
})
