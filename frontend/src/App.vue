<template>
  <div id="app-container">
    <!-- 未登录：显示登录页 -->
    <LoginView v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
    
    <!-- 已登录：显示主界面 -->
    <MainLayout v-else />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from './stores/user'
import LoginView from './views/Login.vue'
import MainLayout from './layouts/MainLayout.vue'

const userStore = useUserStore()
const isAuthenticated = computed(() => userStore.isAuthenticated)

const handleLoginSuccess = (user) => {
  userStore.setUser(user)
}
</script>

<style>
#app-container {
  height: 100vh;
  width: 100vw;
}
</style>