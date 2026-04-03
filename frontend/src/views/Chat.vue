<template>
  <div class="chat-container">
    <!-- 左侧：项目选择和历史 -->
    <div class="chat-sidebar">
      <div style="margin-bottom: 20px;">
        <h4>选择项目</h4>
        <el-select 
          v-model="selectedProjectId" 
          placeholder="选择项目或跨项目查询"
          clearable
          style="width: 100%;"
        >
          <el-option label="跨项目查询" :value="null" />
          <el-option 
            v-for="p in projects" 
            :key="p.id" 
            :label="p.name" 
            :value="p.id"
          />
        </el-select>
      </div>
      
      <div>
        <h4>历史记录</h4>
        <el-scrollbar height="400px">
          <div 
            v-for="h in history" 
            :key="h.id"
            class="history-item"
            @click="loadFromHistory(h)"
          >
            <div style="font-size: 12px; color: #999;">{{ formatTime(h.created_at) }}</div>
            <div style="margin-top: 5px; overflow: hidden; text-overflow: ellipsis;">
              {{ h.question }}
            </div>
          </div>
        </el-scrollbar>
      </div>
    </div>
    
    <!-- 右侧：聊天区域 -->
    <div class="chat-main">
      <!-- 消息区 -->
      <div class="chat-messages" ref="messagesRef">
        <div 
          v-for="(msg, i) in messages" 
          :key="i"
          :class="'message-item ' + msg.role"
        >
          <div class="message-content">
            <div v-if="msg.role === 'user'" style="font-weight: bold;">你</div>
            <div v-else style="font-weight: bold; color: #409EFF;">AI助手</div>
            <div style="margin-top: 10px;">{{ msg.content }}</div>
          </div>
        </div>
        
        <div v-if="loading" class="message-item assistant">
          <div class="message-content">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在思考...
          </div>
        </div>
      </div>
      
      <!-- 输入区 -->
      <div class="chat-input">
        <el-input
          v-model="question"
          placeholder="输入你的问题，例如: 不同办学规模的学生表现有什么差异？"
          @keyup.enter="sendQuestion"
        >
          <template #append>
            <el-button type="primary" @click="sendQuestion" :loading="loading">
              发送
            </el-button>
          </template>
        </el-input>
        
        <div style="margin-top: 10px; color: #999; font-size: 12px;">
          <span>示例问题：</span>
          <el-tag 
            v-for="q in sampleQuestions" 
            :key="q"
            size="small"
            style="margin-right: 5px; cursor: pointer;"
            @click="question = q"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { chatAPI, projectAPI } from '../api'

const projects = ref([])
const selectedProjectId = ref(null)
const history = ref([])
const messages = ref([])
const question = ref('')
const loading = ref(false)
const messagesRef = ref()

const sampleQuestions = [
  '各指标的平均分是多少？',
  '男生和女生的学业达标有什么差异？',
  '不同办学规模的学生表现对比',
  '哪些指标的风险暴露率最高？',
  '第四象限的学生有多少？'
]

onMounted(() => {
  loadProjects()
  loadHistory()
})

const loadProjects = async () => {
  try {
    const res = await projectAPI.list(0, 100)
    projects.value = res.projects
  } catch (error) {
    console.error(error)
  }
}

const loadHistory = async () => {
  try {
    const res = await chatAPI.history(selectedProjectId.value, 0, 20)
    history.value = res.history
  } catch (error) {
    console.error(error)
  }
}

const sendQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: question.value
  })
  
  loading.value = true
  
  // 滚动到底部
  await nextTick()
  messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  
  try {
    const res = await chatAPI.query(selectedProjectId.value, question.value)
    
    // 添加AI回复
    messages.value.push({
      role: 'assistant',
      content: res.message
    })
    
    // 刷新历史
    loadHistory()
    
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，查询过程中出现错误，请稍后重试。'
    })
  } finally {
    loading.value = false
    question.value = ''
    
    // 滚动到底部
    await nextTick()
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const loadFromHistory = (h) => {
  // 从历史加载对话
  messages.value = [
    { role: 'user', content: h.question },
    { role: 'assistant', content: h.answer }
  ]
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.history-item {
  padding: 10px;
  margin-bottom: 10px;
  background: #f5f5f5;
  border-radius: 5px;
  cursor: pointer;
}

.history-item:hover {
  background: #e8e8e8;
}
</style>