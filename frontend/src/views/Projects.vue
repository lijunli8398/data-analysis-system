<template>
  <div class="content-card">
    <!-- 提示信息 -->
    <div style="background: #fdf6ec; padding: 12px 16px; border-radius: 4px; color: #e6a23c; margin-bottom: 15px;">
      当前系统是体验版，只能上传学情调研学生指标得分数据。其他数据分析功能，正在开发中。
    </div>
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
      <h3>项目管理</h3>
      <el-button 
        v-if="userStore.isAdmin"
        type="primary" 
        @click="showCreateDialog"
      >
        新建项目
      </el-button>
    </div>
    
    <!-- 项目列表 -->
    <el-table :data="projects" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="数据文件" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.data_count > 0" type="success">{{ row.data_count }} 个</el-tag>
          <el-tag v-else type="info">无</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="showDataDialog(row)">查看数据</el-button>
          <el-button 
            v-if="userStore.isAdmin"
            size="small" 
            type="success" 
            @click="showUploadDialog(row)"
          >
            上传数据
          </el-button>
          <el-button 
            v-if="userStore.isAdmin"
            size="small" 
            type="danger" 
            @click="deleteProject(row)"
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
  
  <!-- 新建项目对话框 -->
  <el-dialog v-model="createDialogVisible" title="新建项目" width="400px">
    <el-form :model="projectForm" :rules="rules" ref="projectFormRef">
      <el-form-item prop="name" label="项目名称">
        <el-input v-model="projectForm.name" />
      </el-form-item>
      <el-form-item label="项目描述">
        <el-input v-model="projectForm.description" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="createLoading" @click="createProject">创建</el-button>
    </template>
  </el-dialog>
  
  <!-- 上传数据对话框 -->
  <el-dialog v-model="uploadDialogVisible" title="上传数据" width="500px">
    <div style="margin-bottom: 20px;">
      当前项目: {{ selectedProject?.name }}
    </div>
    
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :limit="1"
      accept=".xlsx,.xls,.csv,.json"
      :on-change="handleFileChange"
    >
      <template #trigger>
        <el-button type="primary">选择文件</el-button>
      </template>
      <template #tip>
        <div style="color: #999; margin-top: 10px;">
          支持 .xlsx, .xls, .csv, .json 格式
        </div>
      </template>
    </el-upload>
    
    <template #footer>
      <el-button @click="uploadDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="uploadLoading" @click="uploadFile">上传</el-button>
    </template>
  </el-dialog>
  
  <!-- 查看数据对话框 -->
  <el-dialog v-model="dataDialogVisible" title="项目数据文件" width="700px">
    <div style="margin-bottom: 15px; color: #666;">
      项目: {{ selectedProject?.name }}
    </div>
    
    <el-table :data="dataFiles" style="width: 100%" v-loading="dataLoading" max-height="400">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="filename" label="文件名" />
      <el-table-column label="文件大小" width="100">
        <template #default="{ row }">
          {{ formatFileSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column label="上传时间" width="150">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="downloadDataFile(row)">下载</el-button>
          <el-button 
            v-if="userStore.isAdmin"
            size="small" 
            type="danger" 
            @click="deleteDataFile(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div v-if="dataFiles.length === 0 && !dataLoading" style="text-align: center; padding: 40px; color: #999;">
      暂无数据文件
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectAPI, uploadAPI } from '../api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const projects = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const currentProject = ref(null)

const createDialogVisible = ref(false)
const createLoading = ref(false)
const projectFormRef = ref()
const projectForm = reactive({
  name: '',
  description: ''
})
const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const uploadDialogVisible = ref(false)
const uploadLoading = ref(false)
const selectedProject = ref(null)
const uploadRef = ref()
const selectedFile = ref(null)

// 数据文件相关
const dataDialogVisible = ref(false)
const dataLoading = ref(false)
const dataFiles = ref([])

onMounted(() => {
  loadProjects()
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

// 文件大小格式化
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const loadProjects = async () => {
  try {
    loading.value = true
    const res = await projectAPI.list((currentPage.value - 1) * pageSize.value, pageSize.value)
    projects.value = res.projects
    total.value = res.total
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadProjects()
}

const showCreateDialog = () => {
  projectForm.name = ''
  projectForm.description = ''
  createDialogVisible.value = true
}

const createProject = async () => {
  try {
    await projectFormRef.value.validate()
    createLoading.value = true
    
    await projectAPI.create(projectForm)
    ElMessage.success('项目创建成功')
    createDialogVisible.value = false
    loadProjects()
  } catch (error) {
    console.error(error)
  } finally {
    createLoading.value = false
  }
}

const showDataDialog = async (row) => {
  selectedProject.value = row
  dataDialogVisible.value = true
  await loadDataFiles(row.id)
}

const loadDataFiles = async (projectId) => {
  try {
    dataLoading.value = true
    const res = await projectAPI.getDataFiles(projectId)
    dataFiles.value = res.files || []
  } catch (error) {
    console.error(error)
    dataFiles.value = []
  } finally {
    dataLoading.value = false
  }
}

const downloadDataFile = async (row) => {
  try {
    const blob = await projectAPI.downloadDataFile(row.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.filename
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error(error)
  }
}

const deleteDataFile = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除文件 ${row.filename}?`, '确认删除', {
      type: 'warning'
    })
    
    await projectAPI.deleteDataFile(row.id)
    ElMessage.success('文件删除成功')
    await loadDataFiles(selectedProject.value.id)
    loadProjects() // 刷新列表中的数据文件数量
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const showUploadDialog = (row) => {
  selectedProject.value = row
  selectedFile.value = null
  uploadDialogVisible.value = true
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const uploadFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  try {
    uploadLoading.value = true
    await uploadAPI.upload(selectedProject.value.id, selectedFile.value)
    ElMessage.success('数据上传成功')
    uploadDialogVisible.value = false
    loadProjects() // 刷新列表中的数据文件数量
  } catch (error) {
    console.error(error)
  } finally {
    uploadLoading.value = false
  }
}

const deleteProject = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除项目 "${row.name}"？此操作将同时删除项目下的所有数据文件、报告和看板。`, '确认删除', {
      type: 'warning'
    })
    
    await projectAPI.delete(row.id)
    ElMessage.success('项目删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}
</script>