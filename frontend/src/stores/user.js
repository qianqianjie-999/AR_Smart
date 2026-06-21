import { defineStore } from 'pinia'
import { login, getUserInfo, logout } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
    permissions: [],
    menus: []
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    hasPermission: (state) => (permCode) => {
      if (state.userInfo?.role_code === 'admin') return true
      return state.permissions.some(p => p === permCode || p.startsWith(`${permCode}:`))
    }
  },
  actions: {
    async loginAction(username, password) {
      const res = await login(username, password)
      this.token = res.data.token
      this.userInfo = res.data.user
      this.permissions = (res.data.permissions || []).map(p => p.perm_code)
      this.menus = res.data.menus || []
      localStorage.setItem('token', res.data.token)
      console.log('loginAction - permissions:', this.permissions)
      return res
    },
    async getUserInfoAction() {
      const res = await getUserInfo()
      this.userInfo = res.data.user
      this.permissions = (res.data.permissions || []).map(p => p.perm_code)
      this.menus = res.data.menus || []
      return res
    },
    async logoutAction() {
      await logout()
      this.token = ''
      this.userInfo = null
      this.permissions = []
      this.menus = []
      localStorage.removeItem('token')
    }
  }
})
