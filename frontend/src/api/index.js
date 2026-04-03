import axios from 'axios'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        const userStore = useUserStore()
        userStore.clear()
        ElMessage.error('登录已过期，请重新登录')
      } else if (error.response.status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else {
        ElMessage.error(error.response.data?.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

// ========== 认证API ==========

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me')
}

// ========== 项目API ==========

export const projectAPI = {
  list: (skip = 0, limit = 20) => api.get('/projects', { params: { skip, limit } }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`)
}

// ========== 数据上传API ==========

export const uploadAPI = {
  upload: (projectId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/upload?project_id=${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  list: (projectId) => api.get(`/upload?project_id=${projectId}`),
  delete: (id) => api.delete(`/upload/${id}`)
}

// ========== 报告API ==========

export const reportAPI = {
  list: (projectId, skip = 0, limit = 20) => 
    api.get('/reports', { params: { project_id: projectId, skip, limit } }),
  get: (id) => api.get(`/reports/${id}`),
  download: (id) => api.get(`/reports/${id}/download`, { responseType: 'blob' }),
  generate: (projectId, title) => api.post('/reports/generate', { project_id: projectId, title }),
  delete: (id) => api.delete(`/reports/${id}`)
}

// ========== 看板API ==========

export const dashboardAPI = {
  list: (projectId, skip = 0, limit = 20) => 
    api.get('/dashboards', { params: { project_id: projectId, skip, limit } }),
  get: (id) => api.get(`/dashboards/${id}`),
  view: (id) => api.get(`/dashboards/${id}/view`),
  download: (id) => api.get(`/dashboards/${id}/download`, { responseType: 'blob' }),
  generate: (projectId, title) => api.post('/dashboards/generate', { project_id: projectId, title }),
  delete: (id) => api.delete(`/dashboards/${id}`)
}

// ========== 智能问数API ==========

export const chatAPI = {
  query: (projectId, question) => api.post('/chat/query', { project_id: projectId, question }),
  history: (projectId, skip = 0, limit = 50) => 
    api.get('/chat/history', { params: { project_id: projectId, skip, limit } }),
  deleteHistory: (id) => api.delete(`/chat/history/${id}`)
}

// ========== 任务API ==========

export const taskAPI = {
  get: (id) => api.get(`/tasks/${id}`),
  list: (projectId, status) => api.get('/tasks', { params: { project_id: projectId, status } })
}

export default api