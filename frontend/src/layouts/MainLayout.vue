<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <i class="bi bi-graph-up-arrow"></i>
          <span>数据分析</span>
        </div>
      </div>
      
      <nav class="sidebar-nav">
        <router-link to="/projects" class="nav-item" :class="{ active: currentRoute === '/projects' }">
          <i class="bi bi-folder"></i>
          <span>项目管理</span>
        </router-link>
        
        <router-link to="/reports" class="nav-item" :class="{ active: currentRoute === '/reports' }">
          <i class="bi bi-file-earmark-text"></i>
          <span>报告管理</span>
        </router-link>
        
        <router-link to="/dashboards" class="nav-item" :class="{ active: currentRoute === '/dashboards' }">
          <i class="bi bi-grid-1x2"></i>
          <span>看板管理</span>
        </router-link>
        
        <router-link to="/chat" class="nav-item" :class="{ active: currentRoute === '/chat' }">
          <i class="bi bi-chat-dots"></i>
          <span>智能问数</span>
        </router-link>
      </nav>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar">
            <i class="bi bi-person"></i>
          </div>
          <div class="user-details">
            <div class="user-name">{{ userStore.user?.username }}</div>
            <div class="user-role">{{ userStore.isAdmin ? '管理员' : '查看者' }}</div>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <i class="bi bi-box-arrow-right"></i>
          <span>退出</span>
        </button>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
    
    <!-- 智能问数悬浮按钮（非聊天页面显示） -->
    <button 
      v-if="currentRoute !== '/chat'"
      class="chat-float-btn" 
      @click="goToChat"
      title="智能问数"
    >
      <i class="bi bi-chat-dots"></i>
      <span>智能问数</span>
    </button>
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

const goToChat = () => {
  router.push('/chat')
}
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: #f0f2f5;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  font-size: 20px;
  font-weight: 700;
}

.logo i {
  font-size: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  color: #a0aec0;
  text-decoration: none;
  border-radius: 12px;
  margin-bottom: 6px;
  transition: all 0.3s;
  font-weight: 500;
}

.nav-item i {
  font-size: 20px;
  width: 24px;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.user-details {
  flex: 1;
}

.user-name {
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-role {
  color: #a0aec0;
  font-size: 12px;
  margin-top: 2px;
}

.logout-btn {
  height: 42px;
  padding: 0 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

.logout-btn i {
  font-size: 18px;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* 主内容 */
.main-content {
  flex: 1;
  margin-left: 260px;
  padding: 24px;
  min-height: 100vh;
}

/* 智能问数悬浮按钮 */
.chat-float-btn {
  position: fixed;
  right: 24px;
  bottom: 24px;
  height: 50px;
  padding: 0 20px;
  border-radius: 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
  z-index: 99;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-float-btn i {
  font-size: 22px;
}

.chat-float-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
}
</style>