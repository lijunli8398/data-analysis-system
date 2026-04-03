<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">数据分析系统</h2>
      
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
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div style="text-align: center; color: #999; margin-top: 20px; font-size: 12px;">
        <p>管理员: admin / admin123</p>
        <p>查看者: viewer / viewer123</p>
      </div>
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