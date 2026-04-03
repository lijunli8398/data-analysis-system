<template>
  <div class="main-layout">
    <!-- 顶部导航 -->
    <div class="main-header">
      <div class="header-left">
        <h2>数据分析系统</h2>
      </div>
      <div class="header-right">
        <span style="margin-right: 10px;">{{ userStore.user?.username }} ({{ userStore.user?.role }})</span>
        <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
      </div>
    </div>
    
    <!-- 侧边栏 + 内容区 -->
    <div class="main-body">
      <!-- 侧边栏 -->
      <div class="main-sidebar">
        <el-menu
          :default-active="currentRoute"
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#409EFF"
          router
        >
          <el-menu-item index="/projects">
            <el-icon><Folder /></el-icon>
            <span>项目管理</span>
          </el-menu-item>
          
          <el-menu-item index="/reports">
            <el-icon><Document /></el-icon>
            <span>报告管理</span>
          </el-menu-item>
          
          <el-menu-item index="/dashboards">
            <el-icon><DataBoard /></el-icon>
            <span>看板管理</span>
          </el-menu-item>
          
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问数</span>
          </el-menu-item>
        </el-menu>
      </div>
      
      <!-- 内容区 -->
      <div class="main-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { authAPI } from '../api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const currentRoute = computed(() => route.path)

const handleLogout = async () => {
  try {
    await authAPI.logout()
    userStore.clear()
    ElMessage.success('已退出登录')
  } catch (error) {
    userStore.clear()
  }
}
</script>