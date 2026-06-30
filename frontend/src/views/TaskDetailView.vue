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

      <div v-if="task.tactile_links" class="card links-card">
        <h3>Cloud Agent Lab</h3>
        <div class="link-row">
          <a :href="task.tactile_links.work_url || task.tactile_links.workbench_url" target="_blank" rel="noopener">
            打开 Work 工作台
          </a>
          <a v-if="task.tactile_links.agent_url" :href="task.tactile_links.agent_url" target="_blank" rel="noopener">
            Agent 配置
          </a>
          <a :href="task.tactile_links.console_url" target="_blank" rel="noopener">
            控制台首页
          </a>
        </div>
        <p class="hint">在 Cloud Agent Lab 控制台可查看沙箱、对话与执行细节，便于排查派活问题。</p>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <div class="label">执行员工</div>
          <div class="value">{{ task.employee_name }} · {{ task.employee_handle || task.employee_id }}</div>
        </div>
        <div class="detail-item">
          <div class="label">Agent</div>
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
        <h3>Cloud Agent Lab 实时状态</h3>
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

      <div v-if="task.tactile_chat?.length" class="card chat-card">
        <h3>Agent 对话</h3>
        <div class="chat-list">
          <div
            v-for="(msg, idx) in task.tactile_chat"
            :key="`${msg.entry_index}-${idx}`"
            :class="['chat-bubble', msg.message_type]"
          >
            <div class="chat-meta">
              <span class="chat-role">{{ msg.message_type === 'user' ? '用户指令' : 'Agent' }}</span>
              <span v-if="msg.created_at" class="chat-time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <pre>{{ msg.content }}</pre>
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
        <p v-if="!task.tactile_chat?.length && task.tactile_session_id" class="hint">
          Agent 尚未产生对话，或对话同步失败。可点击「刷新状态」或前往 Cloud Agent Lab 查看。
        </p>
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
.chat-card h3,
.links-card h3,
.card h3 {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}
.instruction-box pre,
.chat-bubble pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
  margin: 0;
}
.tactile-card,
.links-card,
.chat-card { margin: 1rem 0; }
.link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
  margin-bottom: 0.5rem;
}
.link-row a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
}
.link-row a:hover { text-decoration: underline; }
.hint {
  font-size: 0.85rem;
  color: var(--muted);
  margin-top: 0.5rem;
}
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.chat-bubble {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  background: var(--bg);
}
.chat-bubble.user {
  border-left: 3px solid var(--accent);
}
.chat-bubble.agent {
  border-left: 3px solid var(--success);
}
.chat-meta {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
  color: var(--muted);
}
.chat-role { font-weight: 600; }
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
