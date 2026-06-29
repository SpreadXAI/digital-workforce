<template>
  <div class="recruit-page">
    <div class="page-header">
      <div>
        <h2>招募中心 · Twitter 员工</h2>
        <p class="desc">招募并绑定 Twitter Cookie（base64 存储），招募后自动上岗，可批量派活。</p>
      </div>
      <div class="platform-tags">
        <span class="tag active">Twitter / X</span>
        <span class="tag disabled" title="敬请期待">邮箱</span>
        <span class="tag disabled" title="敬请期待">其他账号</span>
      </div>
    </div>

    <div class="tabs">
      <button :class="{ active: tab === 'single' }" @click="tab = 'single'">单个招募</button>
      <button :class="{ active: tab === 'batch' }" @click="tab = 'batch'">批量招募</button>
      <button :class="{ active: tab === 'dispatch' }" @click="tab = 'dispatch'">批量派活</button>
    </div>

    <!-- 单个招募 -->
    <div v-if="tab === 'single'" class="card form-card">
      <form @submit.prevent="submitSingle">
        <div class="form-row">
          <label>员工姓名</label>
          <input v-model="single.display_name" placeholder="如：运营小号A" required />
        </div>
        <div class="form-row">
          <label>Twitter 账号（选填）</label>
          <input v-model="single.twitter_handle" placeholder="@handle" />
        </div>
        <div class="form-row">
          <label>员工类型</label>
          <select v-model="single.employee_type">
            <option v-for="t in employeeTypes" :key="t.id" :value="t.id">{{ t.label }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>Twitter Cookie <span class="hint">（原始或 base64，服务端统一转 base64）</span></label>
          <textarea v-model="single.twitter_cookie" rows="4" placeholder="auth_token=...; ct0=..." required />
        </div>
        <label class="checkbox">
          <input type="checkbox" v-model="single.auto_onboard" />
          招募后自动上岗（provision Tactile Agent）
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '招募中…' : '招募员工' }}</button>
      </form>
    </div>

    <!-- 批量招募 -->
    <div v-if="tab === 'batch'" class="card form-card wide">
      <p class="hint-block">每行一个员工，用 <code>|</code> 分隔（Cookie 可含逗号）：<code>姓名|Cookie</code> 或 <code>姓名|类型|Cookie</code></p>
      <div class="form-row">
        <textarea v-model="batchText" rows="10" placeholder="运营A|auth_token=...&#10;互动B|twitter_engagement|auth_token=..." />
      </div>
      <label class="checkbox">
        <input type="checkbox" v-model="batchAutoOnboard" />
        批量招募后自动上岗
      </label>
      <p v-if="batchResult" class="result">
        成功 {{ batchResult.created.length }} 个，失败 {{ batchResult.failed.length }} 个
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <button @click="submitBatch" :disabled="loading">{{ loading ? '批量招募中…' : '批量招募' }}</button>
    </div>

    <!-- 批量派活 -->
    <div v-if="tab === 'dispatch'" class="card form-card wide">
      <div class="form-row">
        <label>任务标题</label>
        <input v-model="dispatch.title" placeholder="如今日互动任务" />
      </div>
      <div class="form-row">
        <label>任务指令</label>
        <textarea v-model="dispatch.instruction" rows="3" placeholder="浏览时间线，点赞并回复…" />
      </div>
      <p class="hint-block">勾选要派活的 Twitter 员工（须已绑定 Cookie）</p>
      <p v-if="dispatchResult" class="result">
        已派发 {{ dispatchResult.dispatched.length }} 个，失败 {{ dispatchResult.failed.length }} 个
      </p>
      <p v-if="error" class="error">{{ error }}</p>
      <button @click="submitDispatch" :disabled="loading || !selectedIds.length">
        {{ loading ? '派发中…' : `批量派活（${selectedIds.length} 人）` }}
      </button>
    </div>

    <!-- 员工列表 -->
    <div class="card list-card">
      <div class="list-header">
        <h3>已招募员工（{{ employees.length }}）</h3>
        <button class="secondary" @click="load">刷新</button>
      </div>
      <table v-if="employees.length">
        <thead>
          <tr>
            <th v-if="tab === 'dispatch'"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
            <th>编号</th>
            <th>姓名</th>
            <th>类型</th>
            <th>账号</th>
            <th>Cookie</th>
            <th>状态</th>
            <th>Agent</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in employees" :key="e.id">
            <td v-if="tab === 'dispatch'">
              <input type="checkbox" :value="e.id" v-model="selectedIds" />
            </td>
            <td>{{ e.code }}</td>
            <td>{{ e.display_name }}</td>
            <td>{{ e.employee_type_label }}</td>
            <td>{{ e.twitter_handle || '—' }}</td>
            <td>
              <span :class="['dot', e.has_twitter_cookie ? 'ok' : 'miss']"></span>
              {{ e.has_twitter_cookie ? '已绑定' : '未绑定' }}
            </td>
            <td><span :class="['badge', e.stage]">{{ STAGE_LABELS[e.stage] }}</span></td>
            <td>{{ e.tactile_agent_id || '—' }}</td>
            <td class="actions">
              <button class="secondary sm" @click="openCookie(e)">Cookie</button>
              <button class="danger sm" @click="remove(e)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无员工，请先招募</p>
    </div>

    <!-- Cookie 弹层 -->
    <div v-if="cookieModal" class="modal" @click.self="cookieModal = null">
      <div class="card modal-body">
        <h3>更新 Cookie — {{ cookieModal.display_name }}</h3>
        <textarea v-model="cookieEdit" rows="5" />
        <div class="modal-actions">
          <button @click="saveCookie" :disabled="loading">保存</button>
          <button class="secondary" @click="cookieModal = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, STAGE_LABELS } from '../api'

const tab = ref('single')
const employees = ref([])
const employeeTypes = ref([
  { id: 'twitter_operator', label: '运营号' },
  { id: 'twitter_engagement', label: '互动号' },
])
const loading = ref(false)
const error = ref('')

const single = reactive({
  display_name: '',
  twitter_handle: '',
  employee_type: 'twitter_operator',
  twitter_cookie: '',
  auto_onboard: true,
})

const batchText = ref('')
const batchAutoOnboard = ref(true)
const batchResult = ref(null)

const dispatch = reactive({ title: '', instruction: '' })
const selectedIds = ref([])
const dispatchResult = ref(null)

const cookieModal = ref(null)
const cookieEdit = ref('')

const allSelected = computed(() =>
  employees.value.length > 0 && selectedIds.value.length === employees.value.length
)

function toggleAll(ev) {
  selectedIds.value = ev.target.checked ? employees.value.map((e) => e.id) : []
}

async function load() {
  employees.value = await api('/employees?platform=twitter')
  try {
    const res = await api('/employees/types')
    if (res.types?.length) employeeTypes.value = res.types
  } catch { /* use defaults */ }
}

function parseBatchLines(text) {
  const items = []
  for (const line of text.split('\n')) {
    const row = line.trim()
    if (!row || row.startsWith('#')) continue
    const parts = row.split('|').map((s) => s.trim())
    if (parts.length === 2) {
      items.push({ display_name: parts[0], employee_type: 'twitter_operator', twitter_cookie: parts[1] })
    } else if (parts.length >= 3) {
      items.push({
        display_name: parts[0],
        employee_type: parts[1],
        twitter_cookie: parts.slice(2).join('|'),
      })
    }
  }
  return items
}

async function submitSingle() {
  error.value = ''
  loading.value = true
  try {
    await api('/employees', { method: 'POST', body: JSON.stringify(single) })
    single.display_name = ''
    single.twitter_handle = ''
    single.twitter_cookie = ''
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitBatch() {
  error.value = ''
  batchResult.value = null
  const items = parseBatchLines(batchText.value)
  if (!items.length) {
    error.value = '请按格式填写至少一行'
    return
  }
  loading.value = true
  try {
    batchResult.value = await api('/employees/batch', {
      method: 'POST',
      body: JSON.stringify({ items, auto_onboard: batchAutoOnboard.value }),
    })
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitDispatch() {
  error.value = ''
  dispatchResult.value = null
  if (!dispatch.title || !dispatch.instruction) {
    error.value = '请填写任务标题和指令'
    return
  }
  loading.value = true
  try {
    dispatchResult.value = await api('/tasks/batch', {
      method: 'POST',
      body: JSON.stringify({
        employee_ids: selectedIds.value,
        title: dispatch.title,
        instruction: dispatch.instruction,
      }),
    })
    selectedIds.value = []
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function openCookie(e) {
  cookieModal.value = e
  cookieEdit.value = ''
}

async function saveCookie() {
  loading.value = true
  try {
    await api(`/employees/${cookieModal.value.id}/cookie`, {
      method: 'PUT',
      body: JSON.stringify({ twitter_cookie: cookieEdit.value }),
    })
    cookieModal.value = null
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function remove(e) {
  if (!confirm(`删除员工 ${e.display_name}？`)) return
  await api(`/employees/${e.id}`, { method: 'DELETE' })
  await load()
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.desc { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }
.platform-tags { display: flex; gap: 0.5rem; }
.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem; border: 1px solid var(--border); }
.tag.active { background: #14532d; color: #4ade80; border-color: #14532d; }
.tag.disabled { color: var(--muted); opacity: 0.6; cursor: not-allowed; }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.tabs button { background: var(--surface); border: 1px solid var(--border); color: var(--muted); }
.tabs button.active { background: var(--accent); color: white; border-color: var(--accent); }
.form-card { max-width: 520px; margin-bottom: 1rem; }
.form-card.wide { max-width: 100%; }
.hint { color: var(--muted); font-weight: 400; font-size: 0.8rem; }
.hint-block { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.75rem; }
.checkbox { display: flex; align-items: center; gap: 0.5rem; margin: 0.75rem 0; font-size: 0.9rem; color: var(--muted); }
.list-card { margin-top: 0.5rem; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.dot.ok { background: var(--success); }
.dot.miss { background: var(--danger); }
.actions { display: flex; gap: 0.35rem; }
button.sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
.empty { color: var(--muted); padding: 1rem 0; }
.result { color: var(--success); margin: 0.5rem 0; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-body { width: 480px; max-width: 90vw; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
</style>
