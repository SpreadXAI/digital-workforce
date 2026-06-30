<template>
  <div class="task-detail">
    <div class="top-bar">
      <router-link to="/tasks" class="link-btn">← 返回派活列表</router-link>
      <button class="secondary" @click="load" :disabled="loading">刷新状态</button>
    </div>

    <div v-if="loading && !task" class="loading card">加载中…</div>
    <div v-else-if="error" class="error card">{{ error }}</div>

    <template v-else-if="task">
      <div class="hero card">
        <div class="hero-top">
          <div>
            <p class="eyebrow">任务 #{{ task.id }}</p>
            <h2 class="page-title">{{ task.title }}</h2>
            <p class="page-desc">派发给 <strong>{{ task.employee_name }}</strong>（{{ task.employee_handle || '无账号' }}）</p>
          </div>
          <span :class="['badge', task.status]">{{ TASK_STATUS_LABELS[task.status] || task.status }}</span>
        </div>
        <div class="instruction-box">
          <div class="label">任务指令</div>
          <pre>{{ task.instruction }}</pre>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <div class="label">执行员工</div>
          <div class="value">{{ task.employee_name }} · {{ task.employee_handle || task.employee_id }}</div>
        </div>
        <div class="detail-item">
          <div class="label">Tactile Agent</div>
          <div class="value">#{{ task.tactile_agent_id || '—' }}（全员共用）</div>
        </div>
        <div class="detail-item">
          <div class="label">Work ID</div>
          <div class="value">{{ task.tactile_work_id || '—' }}</div>
        </div>
        <div class="detail-item">
          <div class="label">Session ID</div>
          <div class="value">{{ task.tactile_session_id || '—' }}</div>
        </div>
        <div class="detail-item">
          <div class="label">Workspace</div>
          <div class="value">#{{ task.tactile_workspace_id || '—' }}</div>
        </div>
        <div class="detail-item">
          <div class="label">创建时间</div>
          <div class="value">{{ formatTime(task.created_at) }}</div>
        </div>
      </div>

      <div v-if="task.tactile_work" class="card tactile-card">
        <h3>Tactile 实时状态</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <div class="label">任务状态</div>
            <div class="value">{{ task.tactile_work.status || '—' }}</div>
          </div>
          <div class="detail-item">
            <div class="label">沙箱状态</div>
            <div class="value">{{ task.tactile_work.sandbox_status || '—' }}</div>
          </div>
          <div class="detail-item">
            <div class="label">机器类型</div>
            <div class="value">{{ task.tactile_work.machine_type || task.tactile_work.runtime_type || '—' }}</div>
          </div>
          <div class="detail-item">
            <div class="label">当前阶段</div>
            <div class="value">{{ task.tactile_work.current_phase || '—' }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3>执行记录</h3>
        <table v-if="task.executions?.length">
          <thead>
            <tr>
              <th>时间</th>
              <th>步骤</th>
              <th>状态</th>
              <th>Work ID</th>
              <th>消息</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ex in task.executions" :key="ex.id">
              <td>{{ formatTime(ex.created_at) }}</td>
              <td>{{ ex.step }}</td>
              <td><span :class="['badge', ex.status]">{{ TASK_STATUS_LABELS[ex.status] || ex.status }}</span></td>
              <td>{{ ex.tactile_work_id || '—' }}</td>
              <td class="msg">{{ ex.message }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无执行记录</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, TASK_STATUS_LABELS } from '../api'

const route = useRoute()
const task = ref(null)
const loading = ref(false)
const error = ref('')

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    task.value = await api(`/tasks/${route.params.id}`)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.hero { margin-bottom: 1rem; }
.hero-top {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}
.eyebrow {
  color: var(--accent);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}
.instruction-box {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1rem;
}
.instruction-box .label,
.tactile-card h3,
.card h3 {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}
.instruction-box pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
}
.tactile-card { margin: 1rem 0; }
.msg {
  max-width: 420px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.85rem;
  color: var(--muted);
}
.empty, .loading { color: var(--muted); }
.detail-grid { margin-bottom: 1rem; }
</style>
