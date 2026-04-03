<template>
  <div class="content-card">
    <!-- 提示信息 -->
    <div style="background: #ecf5ff; padding: 12px 16px; border-radius: 4px; color: #409eff; margin-bottom: 15px;">
      需要先在【报告管理】中生成报告后，才能在此页面生成数据看板。
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
      <h3>看板管理</h3>
      <el-button 
        v-if="userStore.isAdmin"
        type="primary" 
        @click="showGenerateDialog"
      >
        生成看板
      </el-button>
    </div>
    
    <!-- 看板列表 -->
    <el-table :data="dashboards" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="project_name" label="项目名称" width="120">
        <template #default="{ row }">
          {{ row.project_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="title" label="看板标题" width="180" />
      <el-table-column prop="summary" label="摘要" min-width="200">
        <template #default="{ row }">
          <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            {{ row.summary || '暂无摘要' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="viewDashboard(row)">查看</el-button>
          <el-button size="small" type="success" @click="downloadDashboard(row)">下载</el-button>
          <el-button 
            v-if="userStore.isAdmin"
            size="small" 
            type="danger" 
            @click="deleteDashboard(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div style="margin-top: 20px; display: flex; justify-content: center;">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
  
  <!-- 生成看板对话框 -->
  <el-dialog v-model="generateDialogVisible" title="生成看板" width="500px">
    <el-form :model="dashboardForm" :rules="rules" ref="dashboardFormRef">
      <el-form-item prop="project_id" label="选择项目">
        <el-select v-model="dashboardForm.project_id" placeholder="请选择项目">
          <el-option 
            v-for="p in projects" 
            :key="p.id" 
            :label="p.name" 
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item prop="title" label="看板标题">
        <el-input v-model="dashboardForm.title" />
      </el-form-item>
    </el-form>
    
    <div style="color: #999; margin-top: 15px;">
      提示: 需要先生成报告，才能生成看板（看板依赖报告的CSV数据）
    </div>
    
    <template #footer>
      <el-button @click="generateDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="generateLoading" @click="generateDashboard">生成</el-button>
    </template>
  </el-dialog>
  
  <!-- 看板查看对话框 -->
  <el-dialog v-model="viewDialogVisible" title="查看看板" width="90%" top="5vh">
    <iframe 
      v-if="dashboardUrl"
      :src="dashboardUrl" 
      class="dashboard-iframe"
    />
  </el-dialog>
  
  <!-- 任务状态监控 -->
  <div v-if="currentTask" class="content-card" style="margin-top: 20px;">
    <el-alert title="正在生成看板..." type="info">
      <div style="margin-top: 10px;">
        任务状态: 
        <span :class="'task-status ' + currentTask.status">
          {{ currentTask.status }}
        </span>
        <el-button size="small" style="margin-left: 10px;" @click="checkTaskStatus">
          刷新状态
        </el-button>
      </div>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { dashboardAPI, projectAPI, taskAPI } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const dashboards = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const projects = ref([])
const generateDialogVisible = ref(false)
const generateLoading = ref(false)
const dashboardFormRef = ref()
const dashboardForm = reactive({
  project_id: null,
  title: ''
})
const rules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  title: [{ required: true, message: '请输入看板标题', trigger: 'blur' }]
}

const viewDialogVisible = ref(false)
const dashboardUrl = ref('')

const currentTask = ref(null)
let taskCheckInterval = null

onMounted(() => {
  loadDashboards()
  loadProjects()
})

onUnmounted(() => {
  if (taskCheckInterval) {
    clearInterval(taskCheckInterval)
  }
})

// 时间格式化函数
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadDashboards = async () => {
  try {
    loading.value = true
    const res = await dashboardAPI.list(null, (currentPage.value - 1) * pageSize.value, pageSize.value)
    dashboards.value = res.dashboards
    total.value = res.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const res = await projectAPI.list(0, 100)
    projects.value = res.projects
  } catch (error) {
    console.error(error)
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadDashboards()
}

const showGenerateDialog = () => {
  dashboardForm.project_id = null
  dashboardForm.title = ''
  generateDialogVisible.value = true
}

const generateDashboard = async () => {
  try {
    await dashboardFormRef.value.validate()
    generateLoading.value = true
    
    const res = await dashboardAPI.generate(dashboardForm.project_id, dashboardForm.title)
    ElMessage.success(res.message)
    
    // 获取任务ID并开始监控
    const taskId = parseInt(res.message.match(/任务ID: (\d+)/)?.[1])
    if (taskId) {
      startTaskMonitoring(taskId)
    }
    
    generateDialogVisible.value = false
  } catch (error) {
    console.error(error)
  } finally {
    generateLoading.value = false
  }
}

const startTaskMonitoring = (taskId) => {
  currentTask.value = { id: taskId, status: 'pending' }
  
  taskCheckInterval = setInterval(async () => {
    try {
      const task = await taskAPI.get(taskId)
      currentTask.value = task
      
      if (task.status === 'completed') {
        ElMessage.success('看板生成完成!')
        clearInterval(taskCheckInterval)
        loadDashboards()
        currentTask.value = null
      } else if (task.status === 'failed') {
        ElMessage.error('看板生成失败: ' + task.error_message)
        clearInterval(taskCheckInterval)
        currentTask.value = null
      }
    } catch (error) {
      console.error(error)
    }
  }, 5000)
}

const checkTaskStatus = async () => {
  if (currentTask.value) {
    try {
      const task = await taskAPI.get(currentTask.value.id)
      currentTask.value = task
    } catch (error) {
      console.error(error)
    }
  }
}

const viewDashboard = (row) => {
  dashboardUrl.value = `/api/dashboards/${row.id}/view`
  viewDialogVisible.value = true
}

const downloadDashboard = async (row) => {
  try {
    const blob = await dashboardAPI.download(row.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.title}.html`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(error)
  }
}

const deleteDashboard = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除看板 ${row.title}?`, '确认删除', {
      type: 'warning'
    })
    
    await dashboardAPI.delete(row.id)
    ElMessage.success('看板删除成功')
    loadDashboards()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}
</script>