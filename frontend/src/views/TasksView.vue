<template>
  <div class="tasks-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">批量派活</h2>
        <p class="page-desc">
          选择员工后，任务将派发到 Tactile 共用 Agent 执行；每位员工携带自己的 Twitter Cookie 环境变量。
        </p>
      </div>
    </div>

    <div class="grid">
      <div class="card form-card">
        <h3>新建派活</h3>
        <form @submit.prevent="submit">
          <div class="form-row">
            <label>任务标题</label>
            <input v-model="form.title" required placeholder="如今日互动" />
          </div>
          <div class="form-row">
            <label>任务指令</label>
            <textarea v-model="form.instruction" required rows="4" placeholder="浏览时间线，点赞并回复…" />
          </div>
          <div class="select-bar">
            <button type="button" class="secondary" @click="selectAll">全选可干活</button>
            <button type="button" class="secondary" @click="selectedIds = []">清空</button>
            <span class="count">已选 {{ selectedIds.length }} 人</span>
          </div>
          <div class="employee-pick">
            <label v-for="e in employees" :key="e.id" class="pick-row">
              <input type="checkbox" :value="e.id" v-model="selectedIds" :disabled="!e.has_twitter_cookie" />
              <span>{{ e.display_name }}</span>
              <span class="meta">{{ e.employee_type_label }} · {{ e.twitter_handle || e.code }}</span>
              <span v-if="!e.has_twitter_cookie" class="warn">无 Cookie</span>
            </label>
            <p v-if="!employees.length" class="empty">暂无员工，请先到「员工管理」招募</p>
          </div>
          <p v-if="result" class="success">
            已派发 {{ result.dispatched.length }}，失败 {{ result.failed.length }}
            <span v-if="result.dispatched.length">
              ·
              <router-link :to="`/tasks/${result.dispatched[0].id}`">查看最新任务</router-link>
            </span>
          </p>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading || !selectedIds.length">
            {{ loading ? '派发中…' : `派发给 ${selectedIds.length} 名员工` }}
          </button>
        </form>
      </div>

      <div class="card info-card">
        <h3>派发给谁？</h3>
        <p class="info-text">
          你勾选的是<strong>数字员工</strong>（各自 Twitter 账号/Cookie）。
          实际执行统一走管理台配置的 <strong>Tactile Agent</strong>，在 Tactile 侧创建 Work 任务。
        </p>
        <div class="info-list">
          <div><span>员工</span><strong>你选中的账号</strong></div>
          <div><span>Agent</span><strong>全员共用 #{{ dispatchInfo.agent_id || '未配置' }}</strong></div>
          <div><span>Workspace</span><strong>#{{ dispatchInfo.workspace_id || '—' }}</strong></div>
        </div>
        <router-link to="/admin" class="link-btn">去管理台查看配置 →</router-link>
      </div>
    </div>

    <div class="card list-card">
      <div class="list-header">
        <h3>最近派活</h3>
        <button class="secondary" @click="loadTasks">刷新</button>
      </div>
      <table v-if="tasks.length">
        <thead>
          <tr>
            <th>时间</th>
            <th>标题</th>
            <th>员工</th>
            <th>状态</th>
            <th>Work ID</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tasks" :key="t.id">
            <td>{{ formatTime(t.created_at) }}</td>
            <td>{{ t.title }}</td>
            <td>{{ t.employee_name }} <span class="meta">{{ t.employee_handle }}</span></td>
            <td><span :class="['badge', t.status]">{{ TASK_STATUS_LABELS[t.status] || t.status }}</span></td>
            <td>{{ t.tactile_work_id || '—' }}</td>
            <td><router-link :to="`/tasks/${t.id}`" class="link-btn">详情</router-link></td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无派活记录</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api, TASK_STATUS_LABELS } from '../api'

const form = reactive({ title: '', instruction: '' })
const employees = ref([])
const tasks = ref([])
const dispatchInfo = ref({ agent_id: null, workspace_id: 0 })
const selectedIds = ref([])
const loading = ref(false)
const error = ref('')
const result = ref(null)

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function load() {
  employees.value = await api('/employees?platform=twitter')
}

async function loadTasks() {
  const [taskRows, info] = await Promise.all([api('/tasks'), api('/tasks/dispatch-info')])
  tasks.value = taskRows
  dispatchInfo.value = info
}

function selectAll() {
  selectedIds.value = employees.value.filter((e) => e.has_twitter_cookie).map((e) => e.id)
}

async function submit() {
  error.value = ''
  result.value = null
  loading.value = true
  try {
    result.value = await api('/tasks/batch', {
      method: 'POST',
      body: JSON.stringify({
        employee_ids: selectedIds.value,
        title: form.title,
        instruction: form.instruction,
      }),
    })
    selectedIds.value = []
    await Promise.all([load(), loadTasks()])
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([load(), loadTasks()])
})
</script>

<style scoped>
.page-header { margin-bottom: 1.25rem; }
.grid {
  display: grid;
  grid-template-columns: 1.4fr 0.9fr;
  gap: 1rem;
  margin-bottom: 1rem;
}
.form-card h3, .info-card h3, .list-card h3 {
  margin-bottom: 1rem;
  color: var(--muted);
}
.select-bar { display: flex; align-items: center; gap: 0.5rem; margin: 0.75rem 0; }
.count { color: var(--muted); font-size: 0.85rem; margin-left: auto; }
.employee-pick {
  max-height: 280px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
  margin-bottom: 1rem;
  background: var(--bg);
}
.pick-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.25rem; cursor: pointer; }
.pick-row .meta { color: var(--muted); font-size: 0.8rem; }
.pick-row .warn { color: var(--warning); font-size: 0.75rem; margin-left: auto; }
.info-text { color: var(--text-soft); line-height: 1.7; margin-bottom: 1rem; }
.info-list {
  display: grid;
  gap: 0.65rem;
  margin-bottom: 1rem;
}
.info-list div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 0.85rem;
  background: var(--bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.info-list span { color: var(--muted); font-size: 0.85rem; }
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.meta { color: var(--muted); font-size: 0.8rem; margin-left: 0.35rem; }
.empty { color: var(--muted); padding: 1rem 0; }
@media (max-width: 960px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
