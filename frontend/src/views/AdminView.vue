<template>
  <div class="admin-page">
    <h1>管理台</h1>
    <p class="subtitle">Tactile Gateway / Cloud Agent Lab 对接配置（全员共用一个 Agent）</p>

    <div class="card">
      <div class="status-row">
        <span>连接状态</span>
        <span :class="settings.configured ? 'ok' : 'warn'">
          {{ settings.configured ? '已配置' : '未配置' }}
        </span>
        <span :class="settings.ready ? 'ok' : 'warn'">
          {{ settings.ready ? '可派活' : '待填 Agent ID' }}
        </span>
      </div>

      <div v-if="settings.console_url" class="console-links">
        <h3>Cloud Agent Lab 快捷入口</h3>
        <div class="link-row">
          <a :href="settings.workbench_url" target="_blank" rel="noopener">工作台</a>
          <a :href="settings.agent_url" target="_blank" rel="noopener">Agent #{{ settings.agent_id || '—' }} 配置</a>
          <a :href="settings.console_url" target="_blank" rel="noopener">控制台首页</a>
        </div>
        <p class="hint">排查派活问题时，可在工作台按 Work ID 打开对应会话与沙箱。</p>
      </div>

      <form @submit.prevent="save">
        <div class="form-row">
          <label>API Base URL</label>
          <input v-model="form.api_base" type="url" placeholder="https://test.foxrouter.com/api" />
        </div>
        <div class="form-row">
          <label>API Key</label>
          <input v-model="form.api_key" type="password" :placeholder="settings.has_api_key ? settings.api_key_masked : 'tkt_...'" />
          <p class="hint">留空表示不修改已有 Key</p>
        </div>
        <div class="form-row">
          <label>工作空间 ID</label>
          <input v-model.number="form.workspace_id" type="number" min="0" />
        </div>
        <div class="form-row">
          <label>Agent ID（全员共用）</label>
          <input v-model.number="form.agent_id" type="number" min="0" placeholder="稍后填写" />
        </div>
        <div class="form-row">
          <label>机器类型</label>
          <select v-model="form.machine_type">
            <option value="ubuntu">ubuntu</option>
            <option value="windows">windows</option>
            <option value="sandbox">sandbox</option>
          </select>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>

        <div class="actions">
          <button type="submit" :disabled="saving">保存</button>
          <button type="button" class="secondary" :disabled="testing" @click="testConnection">
            {{ testing ? '测试中…' : '测试连接' }}
          </button>
        </div>
      </form>

      <p v-if="healthMsg" class="health">{{ healthMsg }}</p>
    </div>

    <div class="card note-card">
      <h3>账号说明</h3>
      <p><strong>admin@spreadx.ai</strong> 为管理员，可访问本页并配置 Tactile。</p>
      <p><strong>qa@spreadx.ai</strong> 为普通测试账号，<em>不是</em>管理员，无法进入管理台。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const settings = ref({
  api_base: '',
  api_key_masked: '',
  has_api_key: false,
  workspace_id: 0,
  agent_id: null,
  machine_type: 'ubuntu',
  configured: false,
  ready: false,
  console_url: '',
  workbench_url: '',
  agent_url: '',
})

const form = reactive({
  api_base: '',
  api_key: '',
  workspace_id: 0,
  agent_id: null,
  machine_type: 'ubuntu',
})

const saving = ref(false)
const testing = ref(false)
const error = ref('')
const success = ref('')
const healthMsg = ref('')

async function load() {
  const data = await api('/admin/tactile')
  settings.value = data
  form.api_base = data.api_base
  form.api_key = ''
  form.workspace_id = data.workspace_id
  form.agent_id = data.agent_id
  form.machine_type = data.machine_type
}

async function save() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    const body = {
      api_base: form.api_base,
      workspace_id: form.workspace_id,
      agent_id: form.agent_id || 0,
      machine_type: form.machine_type,
    }
    if (form.api_key.trim()) body.api_key = form.api_key.trim()
    settings.value = await api('/admin/tactile', { method: 'PUT', body: JSON.stringify(body) })
    form.api_key = ''
    success.value = '已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  healthMsg.value = ''
  testing.value = true
  try {
    const res = await api('/admin/tactile/test', { method: 'POST' })
    healthMsg.value = res.ok
      ? `连接成功：${res.service || res.status}`
      : `连接失败：${res.detail}`
  } catch (e) {
    healthMsg.value = `连接失败：${e.message}`
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.admin-page h1 { margin-bottom: 0.25rem; }
.subtitle { color: var(--muted); margin-bottom: 1.5rem; }
.status-row { display: flex; gap: 1rem; margin-bottom: 1rem; font-size: 0.9rem; }
.ok { color: var(--success); }
.warn { color: var(--danger); }
.hint { font-size: 0.75rem; color: var(--muted); margin-top: 0.25rem; }
.actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.error { color: var(--danger); }
.success { color: var(--success); }
.health { margin-top: 1rem; font-size: 0.9rem; color: var(--muted); }
.console-links {
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.console-links h3,
.note-card h3 {
  font-size: 0.9rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
}
.link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.25rem;
}
.link-row a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
}
.link-row a:hover { text-decoration: underline; }
.note-card {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: var(--muted);
  line-height: 1.6;
}
.note-card p { margin: 0.35rem 0; }
</style>
