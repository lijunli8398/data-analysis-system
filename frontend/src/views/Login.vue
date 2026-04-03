<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-logo">
        <i class="bi bi-graph-up-arrow"></i>
      </div>
      <div class="login-title">
        <h1>数据分析系统</h1>
        <p>Data Analysis System</p>
      </div>
      
      <el-form :model="loginForm" :rules="rules" ref="loginFormRef">
        <el-form-item prop="username">
          <el-input 
            v-model="loginForm.username" 
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password" 
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large"
            style="width: 100%; border-radius: 12px; padding: 14px;"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录系统' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { authAPI } from '../api'
import { useUserStore } from '../stores/user'

const emit = defineEmits(['login-success'])
const userStore = useUserStore()
const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    const res = await authAPI.login(loginForm.username, loginForm.password)
    
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    
    ElMessage.success('登录成功')
    emit('login-success', res.user)
    
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-logo {
  text-align: center;
  margin-bottom: 20px;
}

.login-logo i {
  font-size: 70px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.login-title {
  text-align: center;
  margin-bottom: 40px;
}

.login-title h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 8px 0;
}

.login-title p {
  color: #718096;
  font-size: 14px;
  margin: 0;
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 4px 15px;
  box-shadow: 0 0 0 2px #e2e8f0 inset;
}

.login-card :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px #667eea inset;
}
</style>