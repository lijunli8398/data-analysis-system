<template>
  <div class="content-card">
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
      <h3>报告管理</h3>
      <el-button 
        v-if="userStore.isAdmin"
        type="primary" 
        @click="showGenerateDialog"
      >
        生成报告
      </el-button>
    </div>
    
    <!-- 报告列表 -->
    <el-table :data="reports" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="project_name" label="项目名称" width="150">
        <template #default="{ row }">
          {{ row.project_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="title" label="报告标题" />
      <el-table-column prop="summary" label="摘要">
        <template #default="{ row }">
          <div style="max-height: 60px; overflow: hidden;">
            {{ row.summary || '暂无摘要' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="downloadReport(row)">下载</el-button>
          <el-button 
            v-if="userStore.isAdmin"
            size="small" 
            type="danger" 
            @click="deleteReport(row)"
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
  
  <!-- 生成报告对话框 -->
  <el-dialog v-model="generateDialogVisible" title="生成报告" width="500px">
    <el-form :model="reportForm" :rules="rules" ref="reportFormRef">
      <el-form-item prop="project_id" label="选择项目">
        <el-select v-model="reportForm.project_id" placeholder="请选择项目" style="width: 100%">
          <el-option 
            v-for="p in projects" 
            :key="p.id" 
            :label="p.name" 
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item prop="title" label="报告标题">
        <el-input v-model="reportForm.title" placeholder="请输入报告标题" />
      </el-form-item>
    </el-form>
    
    <div style="color: #999; margin-top: 15px;">
      提示: 报告将异步生成，生成完成后可在列表查看并下载
    </div>
    
    <template #footer>
      <el-button @click="generateDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="generateLoading" @click="generateReport">生成</el-button>
    </template>
  </el-dialog>
  
  <!-- 任务状态监控 -->
  <div v-if="currentTask" class="content-card" style="margin-top: 20px;">
    <el-alert title="正在生成报告..." type="info">
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
import { reportAPI, projectAPI, taskAPI } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const reports = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const projects = ref([])
const generateDialogVisible = ref(false)
const generateLoading = ref(false)
const reportFormRef = ref()
const reportForm = reactive({
  project_id: null,
  title: ''
})
const rules = {
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  title: [{ required: true, message: '请输入报告标题', trigger: 'blur' }]
}

const currentTask = ref(null)
let taskCheckInterval = null

onMounted(() => {
  loadReports()
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

const loadReports = async () => {
  try {
    loading.value = true
    const res = await reportAPI.list(null, (currentPage.value - 1) * pageSize.value, pageSize.value)
    reports.value = res.reports
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
  loadReports()
}

const showGenerateDialog = () => {
  reportForm.project_id = null
  reportForm.title = ''
  generateDialogVisible.value = true
}

const generateReport = async () => {
  try {
    await reportFormRef.value.validate()
    generateLoading.value = true
    
    const res = await reportAPI.generate(reportForm.project_id, reportForm.title)
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
  
  // 定期检查任务状态
  taskCheckInterval = setInterval(async () => {
    try {
      const task = await taskAPI.get(taskId)
      currentTask.value = task
      
      if (task.status === 'completed') {
        ElMessage.success('报告生成完成!')
        clearInterval(taskCheckInterval)
        loadReports()
        currentTask.value = null
      } else if (task.status === 'failed') {
        ElMessage.error('报告生成失败: ' + task.error_message)
        clearInterval(taskCheckInterval)
        currentTask.value = null
      }
    } catch (error) {
      console.error(error)
    }
  }, 5000) // 每5秒检查一次
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

const downloadReport = async (row) => {
  try {
    const blob = await reportAPI.download(row.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.title}.docx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(error)
  }
}

const deleteReport = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除报告 "${row.title}"?`, '确认删除', {
      type: 'warning'
    })
    
    await reportAPI.delete(row.id)
    ElMessage.success('报告删除成功')
    loadReports()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}
</script>