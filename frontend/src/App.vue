<template>
  <RouterView />
</template>

<script lang="ts">
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'App',
  created() {
    // при инициализации приложения запрашиваем текущего пользователя
    const auth = useAuthStore()
    auth.fetchCurrentUser()
  }
})
</script>
