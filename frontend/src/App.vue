<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    const userStore = useUserStore()
    const router = useRouter()
    if (!userStore.userInfo) {
      try {
        await userStore.getUserInfoAction()
        console.log('App init - permissions:', userStore.permissions)
      } catch (e) {
        console.error('Failed to init user info:', e)
      }
    }
  }
})
</script>
