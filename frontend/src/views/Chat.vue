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
          >
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <div style="flex: 1; cursor: pointer;" @click="loadFromHistory(h)">
                <div style="font-size: 12px; color: #999;">{{ formatTime(h.created_at) }}</div>
                <div style="margin-top: 5px; overflow: hidden; text-overflow: ellipsis;">
                  {{ h.question }}
                </div>
              </div>
              <el-button 
                size="small" 
                type="danger" 
                :icon="Delete" 
                circle
                @click="deleteHistory(h.id)"
                style="margin-left: 10px;"
              />
            </div>
          </div>
          
          <div v-if="history.length === 0" style="text-align: center; padding: 20px; color: #999;">
            暂无历史记录
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
            <div v-if="msg.role === 'user'" style="margin-top: 10px;">{{ msg.content }}</div>
            <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
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

// Markdown 渲染函数
const renderMarkdown = (text) => {
  if (!text) return ''
  
  // 转义 HTML
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  
  // 表格处理（多行匹配）
  html = html.replace(/\|(.+)\|\n(\|[-:\s|]+\|)\n((?:\|.+\|\n?)+)/g, (match, headerRow, separatorRow, bodyRows) => {
    const headerCells = headerRow.split('|').filter(c => c.trim())
    const bodyLines = bodyRows.trim().split('\n')
    
    let tableHtml = '<table class="data-table">\n<thead>\n<tr>\n'
    headerCells.forEach(cell => {
      tableHtml += `<th>${cell.trim()}</th>\n`
    })
    tableHtml += '</tr>\n</thead>\n<tbody>\n'
    
    bodyLines.forEach(line => {
      const cells = line.split('|').filter(c => c.trim())
      if (cells.length > 0) {
        tableHtml += '<tr>\n'
        cells.forEach(cell => {
          tableHtml += `<td>${cell.trim()}</td>\n`
        })
        tableHtml += '</tr>\n'
      }
    })
    
    tableHtml += '</tbody>\n</table>'
    return tableHtml
  })
  
  // 标题
  html = html
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    // 粗体
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 斜体
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // 列表
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    // 智能换行：连续多个换行变成段落分隔，单个换行变成空格（除非在列表中）
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, ' ')
  
  // 包装段落
  if (!html.startsWith('<table') && !html.startsWith('<h')) {
    html = '<p>' + html + '</p>'
  }
  
  return html
}

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

const deleteHistory = async (historyId) => {
  try {
    await ElMessageBox.confirm('确定删除这条历史记录？', '确认删除', {
      type: 'warning'
    })
    
    await chatAPI.deleteHistory(historyId)
    ElMessage.success('删除成功')
    
    // 刷新历史列表
    loadHistory()
    
    // 如果删除的是当前显示的对话，清空消息
    // 可选：保留当前显示
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
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

/* Markdown 样式 */
.markdown-body {
  margin-top: 10px;
  line-height: 1.5;
}

.markdown-body p {
  margin: 5px 0;
}

.markdown-body h2 {
  font-size: 16px;
  margin: 8px 0 4px;
  color: #333;
}

.markdown-body h3 {
  font-size: 15px;
  margin: 6px 0 3px;
  color: #444;
}

.markdown-body h4 {
  font-size: 14px;
  margin: 5px 0 2px;
  color: #555;
}

.markdown-body strong {
  color: #409EFF;
}

/* 数据表格样式 */
.markdown-body table.data-table {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
}

.markdown-body table.data-table th,
.markdown-body table.data-table td {
  border: 1px solid #ddd;
  padding: 6px 10px;
  text-align: left;
}

.markdown-body table.data-table th {
  background: #f5f7fa;
  font-weight: 600;
  color: #333;
}

.markdown-body table.data-table tr:nth-child(even) {
  background: #fafafa;
}

.markdown-body table.data-table tr:hover {
  background: #f0f7ff;
}

.markdown-body li {
  margin: 3px 0;
  padding-left: 5px;
}
</style>