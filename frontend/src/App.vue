<script setup>
// =========================================================================
// Task Flow Vue 前端交互大脑主控核心栈 (SFC - Single File Component)
// [技术向]：搭建在纯血系统内并引入了多类扩展的第三方操作组建，实现超高频极速的无刷新沉浸变质式操作流。
// =========================================================================
import { ref, computed, onMounted, watch } from 'vue'
import * as XLSX from 'xlsx'         // 深度解析库挂载：主要用这套引擎把提取汇总组装出来的虚拟内存字典阵列瞬间反向打包成本页的跨平台多维表格
import { marked } from 'marked'      // 内联解析流核：负责截取物理地址下的那个静态大版面文本文件转化为我们页面可直接渲染的高阶网页语意包
import api from './api'              // 二次高阶组装后的动态网络雷达探测发起器

// ---- 【系统全局常态缓存响应域】（双端绑定缓存树）----
const tasks = ref([])
const isModalOpen = ref(false)
const isReportModalOpen = ref(false)
const isDocsModalOpen = ref(false)
const readmeHtml = ref('')
const editingTask = ref(null)
const zoomedImage = ref(null)

const selectedProjectsForReport = ref([])
const shortTermProjects = ref([])
const shortTermCustom = ref('')
const reportFilterType = ref('')
const reportFilterAssignee = ref('')
const generatedReport = ref('')

const isPreviewHtmlOpen = ref(false)

const emailSubject = ref('个人团队每日工作进展汇报')
const emailSendMode = ref('immediate')
const emailScheduledTime = ref('')
const isSendingEmail = ref(false)

const savedEmailProfiles = ref(JSON.parse(localStorage.getItem('taskflow_email_profiles') || '[]'))
const selectedProfileId = ref('')

watch(savedEmailProfiles, (val) => {
  localStorage.setItem('taskflow_email_profiles', JSON.stringify(val))
}, { deep: true })

const emailRecipient = ref('')
const emailCc = ref('')

const applyEmailProfile = () => {
  const profile = savedEmailProfiles.value.find(p => p.id === selectedProfileId.value)
  if (profile) {
    emailRecipient.value = profile.to || ''
    emailCc.value = profile.cc || ''
  } else {
    emailRecipient.value = ''
    emailCc.value = ''
  }
}

const saveCurrentAsProfile = () => {
  if (!emailRecipient.value) {
    alert("至少需要填写一份目标接收人 (To) 才能保存预设组合！")
    return
  }
  const desc = prompt("给这份收发名单取个好记的名字吧 (例如：研发组高层汇报配置)：")
  if (desc) {
    savedEmailProfiles.value.push({
      id: Date.now().toString(),
      desc: desc,
      to: emailRecipient.value,
      cc: emailCc.value
    })
    selectedProfileId.value = savedEmailProfiles.value[savedEmailProfiles.value.length - 1].id
    alert("保存快捷预设套餐成功！")
  }
}

const deleteProfile = (id) => {
  savedEmailProfiles.value = savedEmailProfiles.value.filter(p => p.id !== id)
  if (selectedProfileId.value === id) {
    selectedProfileId.value = ''
    emailRecipient.value = ''
    emailCc.value = ''
  }
}

const isScheduledTasksModalOpen = ref(false)
const scheduledTasks = ref([])

const taskForm = ref({
  title: '',
  description: '',
  progress: '',
  priority: 'Medium',
  deadline: '',
  project_name: 'Default Project',
  task_type: '新需求',
  assignee: '',
  attachments: []
})

// ---- 【交互视图条件筛选网阵池】（多维雷达过滤系统预设值表） ----
const filters = ref({
  project: '',      // 用于精准探测捕捉业务源头属组，锁定工作分支
  type: '',         // 用来锁定任务性质类别（例如锁定当前的所有‘新需求’或专门去找‘缺陷修复’卡带等）
  assignee: '',     // 指定负责人筛取过滤名流
  dateStart: '',    // 在时间截断面上定一个物理的初识截取限制闭流起始界限
  dateEnd: ''       // 日期时间限死截流结尾控制标
})

const uniqueProjects = computed(() => {
  const projects = new Set()
  const tasksList = Array.isArray(tasks.value) ? tasks.value : []
  tasksList.forEach(t => {
    if (t.project_name && t.project_name.trim() !== '') {
      projects.add(t.project_name.trim())
    }
  })
  return Array.from(projects).sort()
})

const uniqueAssignees = computed(() => {
  const assignees = new Set()
  const tasksList = Array.isArray(tasks.value) ? tasks.value : []
  tasksList.forEach(t => {
    if (t.assignee && t.assignee.trim() !== '') {
      assignees.add(t.assignee.trim())
    }
  })
  return Array.from(assignees).sort()
})

const columns = ['To Do', 'In Progress', 'Done']

// 【关键引擎钩子】通过提取过滤板上的组合条件与数据底层任务节点做映射实时运算返回无感替换视图流。无抖动无重定向极速拦截：
const filteredTasks = computed(() => {
  const tasksList = Array.isArray(tasks.value) ? tasks.value : []
  return tasksList.filter(t => {
    const matchProject = filters.value.project === '' || t.project_name === filters.value.project
    const matchType = filters.value.type === '' || t.task_type === filters.value.type
    const matchAssignee = filters.value.assignee === '' || t.assignee === filters.value.assignee
    
    let matchDate = true
    if (filters.value.dateStart && t.deadline) {
      matchDate = matchDate && (t.deadline >= filters.value.dateStart)
    }
    if (filters.value.dateEnd && t.deadline) {
      matchDate = matchDate && (t.deadline <= filters.value.dateEnd)
    }
    if ((filters.value.dateStart || filters.value.dateEnd) && !t.deadline) {
      matchDate = false
    }

    return matchProject && matchType && matchAssignee && matchDate
  })
})

const clearFilters = () => {
  filters.value = { project: '', type: '', assignee: '', dateStart: '', dateEnd: '' }
}

const hasFilters = computed(() => !!(filters.value.project || filters.value.type || filters.value.assignee || filters.value.dateStart || filters.value.dateEnd))

const fetchTasks = async () => {
  try {
    const { data } = await api.get('/tasks')
    tasks.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('Failed to fetch tasks', e)
    tasks.value = []
  }
}

onMounted(() => {
  fetchTasks()
})

// Modal Actions
const openModal = (task = null) => {
  if (task) {
    editingTask.value = task
    taskForm.value = { ...task }
  } else {
    editingTask.value = null
    taskForm.value = { 
      title: '', description: '', progress: '', priority: 'Medium', deadline: '',
      project_name: '', task_type: '新需求', assignee: '', attachments: []
    }
  }
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
}

// ==========================================
// 【黑科技项】通过静态抓取原生拉起读取大页面的反溯展示大模块器
// 让前端不依赖第三方后端就可以自己通过前端域寻获大件并组装成为弹开呈现使用指引的核心机制件！
// ==========================================
const openDocsModal = async () => {
  if (!readmeHtml.value) {
    try {
      const res = await fetch('/README.md')
      const text = await res.text()
      readmeHtml.value = marked(text)
    } catch (e) {
      readmeHtml.value = '<p>无法加载说明文档，请检查 README.md 是否存放在 public 目录下。</p>'
    }
  }
  isDocsModalOpen.value = true
}

// ==========================================
// 【智能日志大业务处理枢纽核心算法场】
// ==========================================
const openReportModal = () => {
  selectedProjectsForReport.value = [...uniqueProjects.value] // Select all by default
  shortTermProjects.value = []
  shortTermCustom.value = ''
  reportFilterType.value = ''
  reportFilterAssignee.value = ''
  generatedReport.value = ''
  isReportModalOpen.value = true
}

const closeReportModal = () => {
  isReportModalOpen.value = false
}

const openScheduledTasksModal = async () => {
  isScheduledTasksModalOpen.value = true
  await fetchScheduledTasks()
}

const closeScheduledTasksModal = () => {
  isScheduledTasksModalOpen.value = false
}

const fetchScheduledTasks = async () => {
  try {
    const res = await api.get('/emails/scheduled')
    scheduledTasks.value = res.data
  } catch (err) {
    console.error("无法提取定时任务列表", err)
  }
}

const cancelScheduledTask = async (id) => {
  if(!confirm('确定取消该条定时发送任务吗？')) return
  try {
    await api.delete(`/emails/scheduled/${id}`)
    await fetchScheduledTasks()
  } catch (e) {
    console.error(e)
    alert("取消操作失败")
  }
}

const scheduleEmail = async () => {
  if (!emailRecipient.value) {
    alert("请填写收件人邮箱！")
    return
  }
  isSendingEmail.value = true
  try {
    const payload = {
      recipient: emailRecipient.value,
      cc: emailCc.value,
      subject: emailSubject.value,
      content: generatedReport.value
    }
    if (emailSendMode.value === 'scheduled' && emailScheduledTime.value) {
      payload.send_time = new Date(emailScheduledTime.value).toISOString()
    }
    await api.post('/emails/schedule', payload)
    
    alert(emailSendMode.value === 'immediate' ? "邮件外发请求已成功发送并投入后台缓冲执行列队！" : "定时任务邮件已妥善挂载至主控安全时钟锁中！")
  } catch (err) {
    console.error(err)
    alert("邮件分发任务启动失败，请检查网络链路、后台引擎状态或核心 .env 表环境。")
  } finally {
    isSendingEmail.value = false
  }
}

const formatDate = (isoString) => {
  if(!isoString) return '-'
  return new Date(isoString).toLocaleString('zh-CN', { hour12: false })
}

const generateReport = () => {
  const targetProjects = selectedProjectsForReport.value
  const fType = reportFilterType.value
  const fAssignee = reportFilterAssignee.value
  
  const todayTasks = tasks.value.filter(t => targetProjects.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    (t.status === 'Done' || t.status === 'In Progress' || (t.progress && t.progress.trim() !== '')))
    
  const tomorrowTasks = tasks.value.filter(t => targetProjects.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    (t.status === 'To Do' || t.status === 'In Progress'))

  const dateStr = new Date().toLocaleDateString('zh-CN')
  let report = `# 📅 个人工作日报 (${dateStr})\n\n---\n\n`
  
  report += `## 🟢 今日进展情况\n\n`
  if (todayTasks.length === 0) {
    report += `> 暂无内容\n\n`
  } else {
    const todayByProj = {}
    todayTasks.forEach(t => {
      if(!todayByProj[t.project_name]) todayByProj[t.project_name] = []
      todayByProj[t.project_name].push(t)
    })
    
    Object.keys(todayByProj).forEach(proj => {
      report += `### 📁 项目：${proj}\n\n`
      todayByProj[proj].forEach((t, i) => {
        let statusTag = t.status === 'Done' ? '✅ **[已完成]**' : (t.status === 'In Progress' ? '🚀 **[进行中]**' : '📝 **[预研起步]**')
        let priority = t.priority === 'High' ? '🔴高' : (t.priority === 'Medium' ? '🟡中' : '🟢低')
        let assignee = t.assignee ? ` | 👤 ${t.assignee}` : ''
        
        report += `${i + 1}. **${t.title}** ${statusTag} (优先级: ${priority}${assignee})\n`
        
        if (t.progress && t.progress.trim() !== '') {
          report += `   > **进展细节：** ${t.progress.replace(/\n/g, '<br>')}\n`
        } else if (t.description && t.description.trim() !== '') {
          report += `   > **方案描述：** ${t.description.replace(/\n/g, '<br>')}\n`
        }
      })
      report += `\n`
    })
  }

  report += `---\n\n## 🎯 明日工作计划\n\n`
  if (tomorrowTasks.length === 0) {
    report += `> 暂无内容\n\n`
  } else {
    const tmrwByProj = {}
    tomorrowTasks.forEach(t => {
      if(!tmrwByProj[t.project_name]) tmrwByProj[t.project_name] = []
      tmrwByProj[t.project_name].push(t)
    })
    
    Object.keys(tmrwByProj).forEach(proj => {
      report += `### 📁 项目：${proj}\n\n`
      tmrwByProj[proj].forEach((t) => {
        let statusTag = t.status === 'In Progress' ? '🚀 **[继续推进]**' : '🕒 **[计划启动]**'
        let priority = t.priority === 'High' ? '🔴高' : (t.priority === 'Medium' ? '🟡中' : '🟢低')
        let assignee = t.assignee ? ` | 👤 ${t.assignee}` : ''
        
        report += `- **${t.title}** ${statusTag} (优先级: ${priority}${assignee})\n`
      })
      report += `\n`
    })
  }

  report += `---\n\n## 🗺️ 短期项目规划\n\n`
  const stProj = shortTermProjects.value
  if (stProj.length > 0) {
    report += `**涉及项目**：${stProj.join(', ')}\n\n`
  }
  if (shortTermCustom.value.trim() !== '') {
    report += `**补充目标与随写**：\n> ${shortTermCustom.value.replace(/\n/g, '<br>')}\n\n`
  }
  const stTasks = tasks.value.filter(t => stProj.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    t.status === 'To Do')
  if (stTasks.length > 0) {
    report += `**系统待办任务提取**：\n`
    stTasks.forEach(t => {
      report += `- [${t.project_name}] ${t.title} | 👤 ${t.assignee || '未分配'}\n`
    })
    report += `\n`
  }
  if (stProj.length === 0 && shortTermCustom.value.trim() === '') {
    report += `> 暂无内容\n\n`
  }
  
  generatedReport.value = report
}

// -----------------------------------------
// 【终极重炮挂载】：系统底层越级处理将当前分析汇总流强制化抓取到多段结构列组写入 `XLSX` 多层实体大件下发
// -----------------------------------------
const downloadReportExcel = () => {
  const wb = XLSX.utils.book_new()
  
  // Sheet 1: 今日进展
  const targetProjects = selectedProjectsForReport.value
  const fType = reportFilterType.value
  const fAssignee = reportFilterAssignee.value

  const todayTasks = tasks.value.filter(t => targetProjects.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    (t.status === 'Done' || t.status === 'In Progress' || (t.progress && t.progress.trim() !== '')))
  const todayData = todayTasks.map(t => ({
    '项目名称': t.project_name,
    '任务标题': t.title,
    '状态': t.status,
    '优先级': t.priority,
    '责任人': t.assignee || '',
    '最新进展': t.progress || t.description || ''
  }))
  const ws1 = XLSX.utils.json_to_sheet(todayData.length ? todayData : [{'数据': '暂无'}])
  XLSX.utils.book_append_sheet(wb, ws1, "今日进展")

  // Sheet 2: 明日计划
  const tomorrowTasks = tasks.value.filter(t => targetProjects.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    (t.status === 'To Do' || t.status === 'In Progress'))
  const tomorrowData = tomorrowTasks.map(t => ({
    '项目名称': t.project_name,
    '任务标题': t.title,
    '状态': t.status,
    '优先级': t.priority,
    '责任人': t.assignee || ''
  }))
  const ws2 = XLSX.utils.json_to_sheet(tomorrowData.length ? tomorrowData : [{'数据': '暂无'}])
  XLSX.utils.book_append_sheet(wb, ws2, "明日计划")

  // Sheet 3: 短期计划
  const stProj = shortTermProjects.value
  const stTasks = tasks.value.filter(t => stProj.includes(t.project_name) && 
    (fType === '' || t.task_type === fType) &&
    (fAssignee === '' || t.assignee === fAssignee) &&
    t.status === 'To Do')
  const stData = []
  if (stProj.length > 0) stData.push({'类型': '涉及项目', '内容': stProj.join(', ')})
  if (shortTermCustom.value.trim()) stData.push({'类型': '补充规划', '内容': shortTermCustom.value})
  stTasks.forEach(t => {
    stData.push({'类型': '相关待办任务', '内容': `[${t.project_name}] ${t.title} (责任人: ${t.assignee || '暂无'})`})
  })
  const ws3 = XLSX.utils.json_to_sheet(stData.length ? stData : [{'数据': '暂无'}])
  XLSX.utils.book_append_sheet(wb, ws3, "短期计划")

  XLSX.writeFile(wb, `Project_Daily_Report_${new Date().toISOString().slice(0,10)}.xlsx`)
}

const downloadReportText = () => {
  if (!generatedReport.value) return
  const blob = new Blob([generatedReport.value], { type: 'text/markdown;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Project_Daily_Report_${new Date().toISOString().slice(0,10)}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

const copyReport = async () => {
  if(!generatedReport.value) return
  try {
    await navigator.clipboard.writeText(generatedReport.value)
    alert('日报已成功复制到剪贴板！可以直接粘贴到群里啦 🚀')
  } catch(e) {
    alert('复制失败，请您手动全选框内文本后复制。')
  }
}

const saveTask = async () => {
  try {
    if (editingTask.value) {
      await api.put(`/tasks/${editingTask.value.id}`, taskForm.value)
    } else {
      await api.post('/tasks', taskForm.value)
    }
    closeModal()
    fetchTasks()
  } catch (e) {
    console.error('Failed to save task', e)
  }
}

const deleteTask = async (id) => {
  try {
    await api.delete(`/tasks/${id}`)
    fetchTasks()
  } catch (e) {
    console.error('Failed to delete', e)
  }
}

const onDragStart = (e, task) => {
  e.dataTransfer.dropEffect = 'move'
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('taskId', task.id)
}

const onDrop = async (e, newStatus) => {
  const taskId = e.dataTransfer.getData('taskId')
  const task = tasks.value.find(t => t.id == taskId)
  if (task && task.status !== newStatus) {
    task.status = newStatus
    try {
      await api.put(`/tasks/${taskId}`, { status: newStatus })
    } catch(err) {
      console.error(err)
      fetchTasks()
    }
  }
}

const getTasksByStatus = (status) => {
  return filteredTasks.value.filter(t => t.status === status)
}

const getBadgeClass = (type) => {
  if (type === '新需求') return 'feature';
  if (type === '缺陷修复') return 'bug';
  if (type === '优化项') return 'optimization';
  return '';
}

// Upload file handler
const uploadFiles = async (event) => {
  const fileList = event.target.files
  if (!fileList || fileList.length === 0) return
  
  const formData = new FormData()
  for (let i = 0; i < fileList.length; i++) {
    formData.append('files', fileList[i])
  }
  
  try {
    const res = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    if (!taskForm.value.attachments) taskForm.value.attachments = []
    taskForm.value.attachments.push(...res.data.urls)
  } catch (err) {
    console.error('Upload failed', err)
  }
}

const forceDownload = async (url) => {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    const urlCreator = window.URL || window.webkitURL
    const blobUrl = urlCreator.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = getFileName(url)
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    urlCreator.revokeObjectURL(blobUrl)
  } catch (err) {
    window.open(url, '_blank')
  }
}

// -----------------------------------------
// 【高级越权野垃圾捕快抹杀引擎】：如果只是点击叉叉就让本地废图淤塞是不被允许的。
// 发起底端网络强制斩杀来剔除前序不保存情况所致留存。
// -----------------------------------------
const removeAttachment = async (index) => {
  if (taskForm.value.attachments) {
    const urlToRemove = taskForm.value.attachments[index]
    
    // Physical server proxy deletion bypass if currently untracked inside a new task entity
    if (!editingTask.value && urlToRemove) {
      try {
        await api.delete('/upload', { data: { url: urlToRemove } })
      } catch (err) {
        console.error('Failed to remotely destroy unlinked file entity', err)
      }
    }
    
    taskForm.value.attachments.splice(index, 1)
  }
}

const isImage = (url) => {
  if (!url) return false
  return /\.(jpg|jpeg|png|gif|webp|svg|bmp)(\?.*)?$/i.test(url)
}

const getFileName = (url) => {
  if (!url) return ''
  const parts = url.split('/')
  let decoded = decodeURIComponent(parts[parts.length - 1])
  
  // 【新视觉魔法】：我们利用正则表达式捕获我们在大后方塞入的 “_时间戳_6位UUID”
  // 在呈现给用户的界面上将其隐形脱水，还给用户一个干净的视觉与下载命名！
  decoded = decoded.replace(/_\d+_[a-f0-9]{6}(?=\.[a-zA-Z0-9]+$|$)/i, '')
  
  return decoded
}

const enlargeImage = (url) => {
  zoomedImage.value = url
}

const closeZoom = () => {
  zoomedImage.value = null
}
</script>

<template>
  <div class="app-container">
    <header class="glass-header">
      <h1>Task Flow</h1>
      <div class="header-actions">
        <button class="btn text-btn glass-btn" @click="openScheduledTasksModal()" style="border: 1px solid #ffab40; color: #ffab40; font-weight: bold;">⏰ 调度阵列大盘</button>
        <button class="btn text-btn glass-btn" @click="openDocsModal()">📖 操作指南</button>
        <button class="btn secondary glass-btn" @click="openReportModal()">📊 生成日报</button>
        <button class="btn primary glass-btn" @click="openModal()">+ New Task</button>
      </div>
    </header>

    <div class="filter-bar glass-panel">
      <select v-model="filters.project" class="glass-input filter-input">
        <option value="">所有项目</option>
        <option v-for="proj in uniqueProjects" :key="proj" :value="proj">📁 {{ proj }}</option>
      </select>
      <select v-model="filters.type" class="glass-input filter-input">
        <option value="">所有任务类型</option>
        <option value="新需求">新需求</option>
        <option value="缺陷修复">缺陷修复</option>
        <option value="优化项">优化项</option>
      </select>
      <select v-model="filters.assignee" class="glass-input filter-input">
        <option value="">所有责任人</option>
        <option v-for="name in uniqueAssignees" :key="name" :value="name">👤 {{ name }}</option>
      </select>
      
      <div class="date-filters">
        <input type="date" v-model="filters.dateStart" class="glass-input date-input" title="截止日期(起)" />
        <span>至</span>
        <input type="date" v-model="filters.dateEnd" class="glass-input date-input" title="截止日期(止)" />
      </div>

      <button class="btn text-btn clear-btn" @click="clearFilters" v-if="hasFilters">清除</button>
    </div>

    <main class="kanban-board">
      <div 
        v-for="col in columns" 
        :key="col" 
        class="kanban-column glass-panel"
        @drop="onDrop($event, col)"
        @dragover.prevent
        @dragenter.prevent
      >
        <h2>{{ col }}</h2>
        <div class="task-list">
          <div 
            v-for="task in getTasksByStatus(col)" 
            :key="task.id"
            class="task-card glass-card"
            draggable="true"
            @dragstart="onDragStart($event, task)"
          >
            <div class="task-project">{{ task.project_name }}</div>
            
            <!-- Attachment Section -->
            <div v-if="task.attachments && task.attachments.length > 0" class="attachment-section kanban-attach-grid">
              <template v-for="(url, idx) in task.attachments" :key="idx">
                <img v-if="isImage(url)" :src="url" class="card-image" @dblclick="enlargeImage(url)" title="双击放大" />
                <a v-else href="javascript:void(0)" @click.prevent="forceDownload(url)" class="attachment-link inline-link">
                  📥 {{ getFileName(url) }}
                </a>
              </template>
            </div>

            <div class="task-header">
              <div class="badges">
                <span class="type-badge" :class="getBadgeClass(task.task_type)">{{ task.task_type }}</span>
                <span class="priority-badge" :class="task.priority.toLowerCase()">{{ task.priority }}</span>
              </div>
              <div class="actions">
                <button @click="openModal(task)" class="icon-btn">✎</button>
                <button @click="deleteTask(task.id)" class="icon-btn danger">×</button>
              </div>
            </div>
            <h3 class="task-title">{{ task.title }}</h3>
            <p v-if="task.description" class="task-desc">{{ task.description }}</p>
            
            <div class="task-progress" v-if="task.progress">
              <strong>进展：</strong>{{ task.progress }}
            </div>

            <div class="task-footer">
              <small v-if="task.deadline">⏳ {{ task.deadline }}</small>
              <div class="assignee-badge" v-if="task.assignee">👤 {{ task.assignee }}</div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Task Modal overlay -->
    <div v-if="isModalOpen" class="modal-overlay">
      <div class="modal-content glass-modal">
        <div class="modal-header">
          <h2>{{ editingTask ? 'Edit Task' : 'New Task' }}</h2>
          <button type="button" @click="closeModal" class="btn text-btn" style="padding: 0.5rem; font-size: 1.5rem; margin-top:-1rem;">×</button>
        </div>
        <form @submit.prevent="saveTask">
          <div class="form-row">
            <div class="form-group">
              <label>Project Name</label>
              <input v-model="taskForm.project_name" required class="glass-input" placeholder="e.g. Phoenix Project"/>
            </div>
            <div class="form-group">
              <label>Task Type</label>
              <select v-model="taskForm.task_type" class="glass-input">
                <option value="新需求">新需求</option>
                <option value="缺陷修复">缺陷修复</option>
                <option value="优化项">优化项</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Title</label>
            <input v-model="taskForm.title" required class="glass-input"/>
          </div>
          <div class="form-group">
            <label>Description 方案描述</label>
            <textarea v-model="taskForm.description" class="glass-input textarea"></textarea>
          </div>
          <div class="form-group">
            <label>Progress 今日进展情况</label>
            <textarea v-model="taskForm.progress" class="glass-input textarea" style="min-height: 60px;"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Assignee</label>
              <input v-model="taskForm.assignee" class="glass-input" placeholder="e.g. John Doe"/>
            </div>
            <div class="form-group">
              <label>Priority</label>
              <select v-model="taskForm.priority" class="glass-input">
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
            <div class="form-group">
              <label>Deadline</label>
              <input type="date" v-model="taskForm.deadline" class="glass-input"/>
            </div>
          </div>
          <div class="form-group upload-group">
            <label>Attachments 附件 (支持多个任意格式)</label>
            <input type="file" multiple @change="uploadFiles" class="glass-input file-input" title="可多选文件" />
            <div v-if="taskForm.attachments && taskForm.attachments.length > 0" class="preview-section files-grid">
              <div class="file-item-wrap" v-for="(url, idx) in taskForm.attachments" :key="idx">
                <button type="button" @click="removeAttachment(idx)" class="remove-btn" title="Remove">×</button>
                <img v-if="isImage(url)" :src="url" class="preview-image" @dblclick="enlargeImage(url)" title="双击放大" />
                <a v-else href="javascript:void(0)" @click.prevent="forceDownload(url)" class="attachment-link inline-link">
                  📥 {{ getFileName(url) }}
                </a>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn primary">Save</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Daily Report Modal overlay -->
    <div v-if="isReportModalOpen" class="modal-overlay">
      <div class="modal-content glass-modal report-modal" style="max-width: 1000px; width: 95vw;">
        <div class="modal-header">
          <h2>📊 生成团队日报</h2>
          <button type="button" @click="closeReportModal" class="btn text-btn" style="padding: 0.5rem; font-size: 1.5rem; margin-top:-1rem;">×</button>
        </div>
        
        <div class="form-row" style="margin-bottom: 1rem; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 1rem;">
          <div class="form-group" style="margin-bottom: 0;">
            <label>🎯 提取任务类型包含：</label>
            <select v-model="reportFilterType" class="glass-input">
              <option value="">所有任务类型 (全部提取)</option>
              <option value="新需求">新需求</option>
              <option value="缺陷修复">缺陷修复</option>
              <option value="优化项">优化项</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label>👤 提取责任人归属：</label>
            <select v-model="reportFilterAssignee" class="glass-input">
              <option value="">所有责任人 (全部提取)</option>
              <option v-for="name in uniqueAssignees" :key="name" :value="name">{{ name }}</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>📦 1. 选择要纳入【今日进展与明日计划】的项目：</label>
          <div class="checkbox-list">
            <label class="checkbox-item" v-for="proj in uniqueProjects" :key="proj">
              <input type="checkbox" :value="proj" v-model="selectedProjectsForReport" /> {{ proj }}
            </label>
            <div v-if="uniqueProjects.length === 0" style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">
              看板内暂无任何业务流数据
            </div>
          </div>
        </div>

        <div class="form-group" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed rgba(255,255,255,0.1);">
          <label>🗺️ 2. 【短期计划】专属板块定制：</label>
          <label style="font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-bottom: 0.5rem;">筛选需要被纳入规划的已有业务流及待办项目</label>
          <div class="checkbox-list">
            <label class="checkbox-item" v-for="proj in uniqueProjects" :key="'st-'+proj">
              <input type="checkbox" :value="proj" v-model="shortTermProjects" /> {{ proj }}
            </label>
          </div>
          <label style="font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: 0.5rem;">您也可以在此补充输入专属的短期规划目标：</label>
          <textarea v-model="shortTermCustom" class="glass-input textarea" placeholder="手动输入属于短期的特定安排或战略规划..."></textarea>
        </div>

        <div class="modal-actions" style="justify-content: flex-start; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem;">
          <button type="button" @click="generateReport" class="btn primary">🚀 确认读取并一键生成完整报告 🚀</button>
        </div>

        <div class="form-group" v-if="generatedReport !== ''">
          <label>✅ 日报生成结果预览（您可以手动修改、或者选择下方的原生下载）：</label>
          <textarea v-model="generatedReport" class="glass-input textarea report-area"></textarea>
          <div class="modal-actions" style="flex-wrap: wrap;">
            <button type="button" @click="copyReport" class="btn text-btn">📋 复制剪贴板</button>
            <button type="button" @click="downloadReportText" class="btn secondary">📥 归档为 .md 文本</button>
            <button type="button" @click="downloadReportExcel" class="btn primary" style="background: linear-gradient(135deg, #43a047 0%, #1de9b6 100%);">📊 生成真实 Excel 电子表格</button>
          </div>
          
          <div style="margin-top: 1.5rem; padding: 1.5rem; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px dashed rgba(64, 224, 208, 0.5);">
            
            <!-- Address Book Manager Line -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
              <h3 style="margin: 0; color: #40e0d0; font-size: 1.1rem; display: flex; align-items: center; gap: 0.5rem;">
                📧 Outlook 企业级邮箱高管分发流引擎
              </h3>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <select v-model="selectedProfileId" @change="applyEmailProfile" class="glass-input" style="padding: 0.3rem 0.5rem; font-size: 0.85rem; height: auto;">
                  <option value="">-- 手动任意输入 / 选择下方历史组合 --</option>
                  <option v-for="p in savedEmailProfiles" :key="p.id" :value="p.id">🔖 {{ p.desc }}</option>
                </select>
                <button type="button" @click="saveCurrentAsProfile" class="btn secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" title="将下方当前填入的信箱打包记忆保存">💾 保存套组</button>
                <button v-if="selectedProfileId" type="button" @click="deleteProfile(selectedProfileId)" class="btn danger-btn" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;">🗑️ 删除此套组</button>
              </div>
            </div>

            <p style="font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-top: -0.5rem; margin-bottom: 1rem;">
              该引擎会自动将您上方的原生 Markdown 语意转换为企业高感度 HTML 回执表格，并经由专属 TLS 信道点对点极速送达。（支持立刻发射与离线静默挂起两类作业模式）
            </p>
            <div class="form-row">
              <div class="form-group" style="flex:1; margin-bottom: 0.5rem;">
                <label>目标接收账户 To (多个请用逗号隔开)</label>
                <input type="text" v-model="emailRecipient" class="glass-input" placeholder="boss@outlook.com, team@outlook.com">
              </div>
              <div class="form-group" style="flex:1; margin-bottom: 0.5rem;">
                <label>邮件抄送方 Cc (可选)</label>
                <input type="text" v-model="emailCc" class="glass-input" placeholder="manager@outlook.com">
              </div>
            </div>
            <div class="form-group" style="margin-bottom: 0.5rem;">
              <label>专属发文投递核准主标题 (Subject)</label>
              <input type="text" v-model="emailSubject" class="glass-input">
            </div>
            <div class="form-row">
              <div class="form-group" style="flex:1; margin-bottom: 0;">
                <label>强行发文底层调度逻辑选择</label>
                <select v-model="emailSendMode" class="glass-input">
                  <option value="immediate">⚡ 强制即刻底层点火穿透 (Immediately)</option>
                  <option value="scheduled">⏱️ 锁定并静待系统的远期强唤醒指令投送</option>
                </select>
              </div>
              <div class="form-group" style="flex:1; margin-bottom: 0;" v-if="emailSendMode === 'scheduled'">
                <label>📅 请严格锁定系统定时阻断撤防日期轴</label>
                <input type="datetime-local" v-model="emailScheduledTime" class="glass-input" style="color: #ffab40; font-weight: bold;">
              </div>
            </div>

            <div style="margin-top: 1rem; border-top: 1px dashed rgba(255,255,255,0.2); padding-top: 1rem;">
              <button type="button" @click="isPreviewHtmlOpen = !isPreviewHtmlOpen" class="btn text-btn" style="width: 100%; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 1rem;">
                {{ isPreviewHtmlOpen ? '👀 收起 HTML 收件端真实排版预览' : '👀 预览接收方 Outlook 中的真实 HTML 效果' }}
              </button>
              
              <div v-if="isPreviewHtmlOpen" style="background: white; color: black; padding: 2rem; border-radius: 8px; max-height: 400px; overflow-y: auto; text-align: left; margin-bottom: 1rem; user-select: text;" v-html="marked(generatedReport || '暂无内容')"></div>
            </div>

            <button type="button" @click="scheduleEmail" class="btn primary" :disabled="isSendingEmail" style="width: 100%; height: 50px; background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%); font-weight: bold; font-size: 1.1rem; border-radius: 8px;">
              {{ isSendingEmail ? '⚙️ 高可用节点接入接管打包处理中，切勿中断关机...' : (emailSendMode === 'immediate' ? '🚀 核对无误，弹链上膛直接开火发送！' : '📥 提取密匙入库进锁！精准离线定时挂载！') }}
            </button>
          </div>

        </div>

      </div>
    </div>

    <!-- ⏰ 定时调度总控室大盘 Modal -->
    <div v-if="isScheduledTasksModalOpen" class="modal-overlay" @click.self="closeScheduledTasksModal">
      <div class="modal-content glass-modal docs-modal" style="max-width: 1200px; width: 95vw;">
        <div class="modal-header">
          <h2 style="margin: 0; font-size: 1.5rem; color: #ffab40;">⏰ Outlook 预载防线及调度指挥阵列中心</h2>
          <button type="button" @click="closeScheduledTasksModal" class="btn text-btn" style="padding: 0.5rem; font-size: 1.5rem; margin-top:-1rem;">×</button>
        </div>
        <div class="modal-body" style="padding-top: 1rem;">
          <p style="font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-bottom: 1rem;">
            全系尚未分发离轨或执行结束的历史作业与即期悬置列队在此处呈现零延迟全局快照监控大黑盒阵列网图。您可以随时监控发送端口状态，对于处于阻眠池状态下的寄挂型命令甚至支持极高权限的紧急硬斩断销毁防错！
          </p>
          <div style="overflow-x: auto;">
            <table class="glass-table schedule-table" style="width: 100%; text-align: left; border-collapse: collapse; margin-top: 1rem;">
              <thead>
                <tr style="border-bottom: 2px solid rgba(255,255,255,0.1);">
                  <th style="padding: 1rem; width: 10%;">系统机控状态</th>
                  <th style="padding: 1rem; width: 15%;">收件方(To)</th>
                  <th style="padding: 1rem; width: 15%;">抄送方(Cc)</th>
                  <th style="padding: 1rem; width: 25%;">内核标题(Subject)</th>
                  <th style="padding: 1rem; width: 15%;">预警解除时间点</th>
                  <th style="padding: 1rem; width: 10%;">异常栈(Errors)</th>
                  <th style="padding: 1rem; width: 10%;">一键切除预配(Actions)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="scheduledTasks.length === 0">
                  <td colspan="7" style="text-align: center; color: rgba(255,255,255,0.4); padding: 3rem;">底库时钟区现目前呈现极度清洁状态，没有获取及游离任何待发射与归档预配指令包裹。</td>
                </tr>
                <tr v-for="t in scheduledTasks" :key="t.id" style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                  <td style="padding: 1rem;">
                    <span :style="{ fontWeight: 'bold', color: t.status === 'Sent' ? '#00e676' : (t.status === 'Failed' ? '#ff1744' : (t.status === 'Cancelled' ? '#9e9e9e' : '#ffd700'))}">
                      {{ t.status === 'Pending' ? '⏱️ Pend' : t.status }}
                    </span>
                  </td>
                  <td style="padding: 1rem; font-size: 0.85rem; word-break: break-all;">{{ t.recipient }}</td>
                  <td style="padding: 1rem; font-size: 0.85rem; word-break: break-all;">{{ t.cc || '-' }}</td>
                  <td style="padding: 1rem; font-size: 0.9rem;">{{ t.subject }}</td>
                  <td style="padding: 1rem; font-size: 0.85rem; color: rgba(255,255,255,0.8);">{{ t.send_time ? formatDate(t.send_time) : '立即突破' }}</td>
                  <td style="padding: 1rem; font-size: 0.75rem; color: #ff8a80;">{{ t.error_msg || '-' }}</td>
                  <td style="padding: 1rem;">
                    <button v-if="t.status === 'Pending'" @click="cancelScheduledTask(t.id)" class="btn danger-btn" style="padding: 0.3rem 0.6rem; font-size: 0.8rem; border-radius:4px; border:1px solid #ff1744; color:white; background:transparent;">🚨 强杀！</button>
                    <span v-else style="color: rgba(255,255,255,0.3); font-size: 0.8rem;">锁定</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- System Documentation Modal -->
    <div v-if="isDocsModalOpen" class="modal-overlay">
      <div class="modal-content glass-modal docs-modal">
        <div class="modal-header">
          <h2 style="margin: 0; font-size: 1.5rem; border-bottom: none; padding-bottom: 0;">📖 Task Flow 使用手册</h2>
          <button type="button" @click="isDocsModalOpen = false" class="btn text-btn" style="padding: 0.5rem; font-size: 1.5rem; margin-top:-1rem;">×</button>
        </div>
        <div class="markdown-body" v-html="readmeHtml"></div>
      </div>
    </div>

    <!-- Image Zoom Lightbox -->
    <div v-if="zoomedImage" class="lightbox-overlay" @click="closeZoom">
      <div class="lightbox-content">
        <img :src="zoomedImage" class="zoomed-image" @click.stop />
        <button class="close-lightbox" @click="closeZoom">×</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 2rem;
  box-sizing: border-box;
}

.glass-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  margin-bottom: 2rem;
  color: white;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.filter-bar {
  display: flex;
  gap: 1rem;
  padding: 1rem 2rem;
  margin-bottom: 2rem;
  align-items: center;
  flex-wrap: wrap;
}

.filter-input {
  flex: 1;
  min-width: 160px;
}

.clear-btn {
  padding: 0.8rem 1rem;
}

.date-filters {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.date-input {
  max-width: 140px;
  padding: 0.7rem 0.5rem;
  font-size: 0.85rem;
}

.kanban-board {
  flex: 1;
  display: flex;
  gap: 2rem;
  overflow-x: auto;
  padding-bottom: 1rem;
}

.kanban-column {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
}

.glass-panel {
  background: rgba(25, 25, 35, 0.4);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  color: white;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
}

.kanban-column h2 {
  margin-top: 0;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 0.8rem;
}

.task-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  min-height: 150px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 1.2rem;
  cursor: grab;
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
  background: rgba(255, 255, 255, 0.12);
}

.glass-card:active {
  cursor: grabbing;
}

.task-project {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

/* Attachment Styles */
.attachment-section {
  margin-bottom: 0.8rem;
}

.card-image {
  width: 100%;
  max-height: 160px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  cursor: zoom-in;
}

.attachment-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255,255,255,0.05);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  color: #90caf9;
  text-decoration: none;
  font-size: 0.85rem;
  border: 1px solid rgba(255,255,255,0.1);
  word-break: break-all;
  transition: all 0.2s;
}

.attachment-link:hover {
  background: rgba(255,255,255,0.15);
  color: #bbdefb;
}

.preview-section {
  margin-top: 10px;
}

.preview-image {
  max-height: 120px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.2);
  cursor: zoom-in;
}

.kanban-attach-grid {
  display: flex; flex-direction: column; gap: 0.5rem;
}

.files-grid {
  display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 10px;
}
.file-item-wrap {
  position: relative; display: inline-flex; flex-direction: column;
}
.remove-btn {
  position: absolute; top: -5px; right: -5px; background: rgba(244, 67, 54, 0.9);
  color: white; border: none; border-radius: 50%; width: 22px; height: 22px;
  font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.inline-link { margin-bottom: 0; }

/* Lightbox Styles */
.lightbox-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lightbox-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
}

.zoomed-image {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  animation: zoomFade 0.2s ease-out;
}

@keyframes zoomFade {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.close-lightbox {
  position: absolute;
  top: -40px;
  right: -40px;
  background: none;
  border: none;
  color: white;
  font-size: 2.5rem;
  cursor: pointer;
  transition: color 0.2s;
}

.close-lightbox:hover {
  color: #ff5252;
}

@media (max-width: 768px) {
  .close-lightbox {
    top: -40px;
    right: 0;
  }
}

.badges {
  display: flex;
  gap: 0.5rem;
}

.type-badge {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255,255,255,0.2);
}
.type-badge.feature { background: rgba(33, 150, 243, 0.2); color: #90caf9; border-color: rgba(33, 150, 243, 0.3);}
.type-badge.bug { background: rgba(244, 67, 54, 0.2); color: #e57373; border-color: rgba(244, 67, 54, 0.3);}
.type-badge.optimization { background: rgba(156, 39, 176, 0.2); color: #ce93d8; border-color: rgba(156, 39, 176, 0.3);}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.8rem;
}

.priority-badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.priority-badge.low { background: rgba(76, 175, 80, 0.2); color: #81c784; border: 1px solid rgba(76, 175, 80, 0.3); }
.priority-badge.medium { background: rgba(255, 152, 0, 0.2); color: #ffb74d; border: 1px solid rgba(255, 152, 0, 0.3); }
.priority-badge.high { background: rgba(244, 67, 54, 0.2); color: #e57373; border: 1px solid rgba(244, 67, 54, 0.3); }

.task-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.task-desc {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 1rem 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.task-progress {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.85);
  background: rgba(255,255,255,0.05);
  padding: 0.6rem;
  border-radius: 6px;
  margin-bottom: 0.8rem;
  border-left: 3px solid #667eea;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 0.8rem;
  margin-top: 0.8rem;
}

.assignee-badge {
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.icon-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0.2rem;
  transition: color 0.2s;
}
.icon-btn:hover { color: white; }
.icon-btn.danger:hover { color: #ff5252; }

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.glass-modal {
  background: rgba(30, 30, 40, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 2.5rem;
  width: 90%;
  max-width: 600px;
  color: white;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.3s ease-out;
  max-height: 90vh;
  overflow-y: auto;
}

.report-modal {
  max-width: 500px;
}

.docs-modal {
  max-width: 850px;
  max-height: 85vh;
  padding: 2rem 3rem;
}
.markdown-body {
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 1rem;
  padding-right: 1.5rem;
  overflow-y: auto;
  max-height: 65vh;
}
.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 0.5rem;
  margin-top: 2rem;
  color: white;
}
.markdown-body h1 { font-size: 1.5rem; margin-top: 0; }
.markdown-body h2 { font-size: 1.25rem; }
.markdown-body h3 { font-size: 1.1rem; }
.markdown-body ul, .markdown-body ol {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}
.markdown-body p { margin-bottom: 1rem; }
.markdown-body code {
  background: rgba(0,0,0,0.3);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  color: #81c784;
}
.markdown-body a { color: #90caf9; }
.markdown-body blockquote {
  border-left: 4px solid #667eea;
  padding-left: 1rem;
  margin-left: 0;
  color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.05);
  padding: 0.5rem 1rem;
}

.checkbox-list { 
  display: flex; flex-direction: column; gap: 0.5rem; 
  max-height: 150px; overflow-y: auto; padding: 0.8rem; 
  background: rgba(0,0,0,0.2); border-radius: 8px;
}
.checkbox-item { 
  display: flex; align-items: center; gap: 0.5rem; 
  font-size: 0.95rem; cursor: pointer;
}

.report-area { 
  min-height: 200px; 
  font-family: 'Courier New', Courier, monospace; 
  white-space: pre-wrap; 
  font-size: 0.9rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-group {
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.upload-group {
  margin-bottom: 0.5rem;
}

.file-input {
  padding: 0.5rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}
.form-row .form-group { flex: 1; }

label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.glass-input {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.8rem 1rem;
  color: white;
  font-family: inherit;
  font-size: 1rem;
  transition: border-color 0.2s, background 0.2s;
}
.glass-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(0, 0, 0, 0.3);
}
.glass-input.textarea {
  min-height: 100px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}
.btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(118, 75, 162, 0.4);
}

.btn.secondary {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
}
.btn.secondary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 172, 254, 0.4);
}

.btn.text-btn {
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
}
.btn.text-btn:hover {
  color: white;
  background: rgba(255, 255, 255, 0.05);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
