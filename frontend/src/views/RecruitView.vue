<template>
  <div class="recruit-page">
    <div class="page-header">
      <div>
        <h2>员工管理</h2>
        <p class="desc">Twitter 数字员工名册，绑定 Cookie 即可派活。</p>
      </div>
      <div class="header-actions">
        <div class="platform-tags">
          <span class="tag active">Twitter / X</span>
          <span class="tag disabled" title="敬请期待">邮箱</span>
          <span class="tag disabled" title="敬请期待">其他账号</span>
        </div>
        <button @click="openRecruitModal('single')">+ 招募员工</button>
      </div>
    </div>

    <div class="card list-card">
      <div class="list-header">
        <div class="filters">
          <input v-model="search" placeholder="搜索姓名 / @账号" class="search" />
        </div>
        <div class="list-actions">
          <button class="secondary" @click="openRecruitModal('batch')">批量招募</button>
          <button class="secondary" @click="load">刷新</button>
        </div>
      </div>

      <table v-if="filteredEmployees.length">
        <thead>
          <tr>
            <th>编号</th>
            <th>姓名</th>
            <th>账号</th>
            <th>Cookie</th>
            <th>状态</th>
            <th>Agent</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in filteredEmployees" :key="e.id">
            <td>{{ e.code }}</td>
            <td>{{ e.display_name }}</td>
            <td>{{ e.twitter_handle || '—' }}</td>
            <td>
              <span :class="['dot', e.has_twitter_cookie ? 'ok' : 'miss']"></span>
              {{ e.has_twitter_cookie ? '已绑定' : '未绑定' }}
            </td>
            <td><span :class="['badge', e.stage]">{{ STAGE_LABELS[e.stage] }}</span></td>
            <td>{{ e.tactile_agent_id || '—' }}</td>
            <td class="actions-cell">
              <div class="row-menu">
                <button
                  type="button"
                  class="menu-trigger"
                  aria-label="操作"
                  @click.stop="toggleMenu(e.id)"
                >
                  ⋮
                </button>
                <div v-if="openMenuId === e.id" class="menu-dropdown" @click.stop>
                  <button
                    v-if="e.has_twitter_cookie"
                    type="button"
                    @click="viewCookie(e)"
                  >
                    查看 Cookie
                  </button>
                  <button
                    v-else
                    type="button"
                    @click="bindCookie(e)"
                  >
                    绑定 Cookie
                  </button>
                  <button type="button" class="danger-text" @click="remove(e)">删除</button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">{{ employees.length ? '无匹配员工' : '暂无员工，点击「招募员工」添加' }}</p>
      <p class="count">共 {{ filteredEmployees.length }} / {{ employees.length }} 人</p>
    </div>

    <!-- 招募弹窗 -->
    <div v-if="recruitModal" class="modal" @click.self="closeRecruitModal">
      <div class="card modal-body wide">
        <div class="modal-header">
          <h3>招募员工</h3>
          <button class="secondary sm" @click="closeRecruitModal">✕</button>
        </div>
        <div class="tabs">
          <button :class="{ active: recruitTab === 'single' }" @click="recruitTab = 'single'">单个招募</button>
          <button :class="{ active: recruitTab === 'batch' }" @click="recruitTab = 'batch'">批量招募</button>
        </div>

        <form v-if="recruitTab === 'single'" @submit.prevent="submitSingle">
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
            <label>Twitter Cookie <span class="hint">（原始或 base64）</span></label>
            <textarea v-model="single.twitter_cookie" rows="4" placeholder="auth_token=...; ct0=..." required />
          </div>
          <p v-if="modalError" class="error">{{ modalError }}</p>
          <div class="modal-actions">
            <button type="submit" :disabled="loading">{{ loading ? '招募中…' : '确认招募' }}</button>
            <button type="button" class="secondary" @click="closeRecruitModal">取消</button>
          </div>
        </form>

        <div v-else>
          <p class="hint-block">每行：<code>姓名|Cookie</code> 或 <code>姓名|类型|Cookie</code></p>
          <textarea v-model="batchText" rows="8" class="batch-area" placeholder="运营A|auth_token=...&#10;互动B|twitter_engagement|auth_token=..." />
          <p v-if="batchResult" class="result">
            成功 {{ batchResult.created.length }}，失败 {{ batchResult.failed.length }}
          </p>
          <p v-if="modalError" class="error">{{ modalError }}</p>
          <div class="modal-actions">
            <button @click="submitBatch" :disabled="loading">{{ loading ? '招募中…' : '确认批量招募' }}</button>
            <button type="button" class="secondary" @click="closeRecruitModal">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看 Cookie -->
    <div v-if="cookieViewModal" class="modal" @click.self="cookieViewModal = null">
      <div class="card modal-body wide">
        <h3>查看 Cookie — {{ cookieViewModal.display_name }}</h3>
        <textarea :value="cookieViewText" rows="8" readonly class="readonly" />
        <div class="modal-actions">
          <button class="secondary" @click="cookieViewModal = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- 绑定 Cookie -->
    <div v-if="cookieModal" class="modal" @click.self="cookieModal = null">
      <div class="card modal-body">
        <h3>绑定 Cookie — {{ cookieModal.display_name }}</h3>
        <textarea v-model="cookieEdit" rows="5" placeholder="auth_token=...; ct0=..." />
        <p v-if="modalError" class="error">{{ modalError }}</p>
        <div class="modal-actions">
          <button @click="saveCookie" :disabled="loading">保存</button>
          <button class="secondary" @click="cookieModal = null">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { api, STAGE_LABELS } from '../api'

const employees = ref([])
const employeeTypes = ref([
  { id: 'twitter_operator', label: '运营号' },
  { id: 'twitter_engagement', label: '互动号' },
])
const loading = ref(false)
const modalError = ref('')
const search = ref('')

const recruitModal = ref(false)
const recruitTab = ref('single')

const single = reactive({
  display_name: '',
  twitter_handle: '',
  employee_type: 'twitter_operator',
  twitter_cookie: '',
  auto_onboard: false,
})

const batchText = ref('')
const batchResult = ref(null)
const openMenuId = ref(null)
const cookieModal = ref(null)
const cookieEdit = ref('')
const cookieViewModal = ref(null)
const cookieViewText = ref('')

const filteredEmployees = computed(() => {
  const q = search.value.trim().toLowerCase()
  return employees.value.filter((e) => {
    if (!q) return true
    return (
      e.display_name.toLowerCase().includes(q) ||
      (e.twitter_handle || '').toLowerCase().includes(q) ||
      e.code.toLowerCase().includes(q)
    )
  })
})

function closeMenu() {
  openMenuId.value = null
}

function toggleMenu(id) {
  openMenuId.value = openMenuId.value === id ? null : id
}

function openRecruitModal(tab) {
  closeMenu()
  recruitTab.value = tab
  modalError.value = ''
  batchResult.value = null
  recruitModal.value = true
}

function closeRecruitModal() {
  recruitModal.value = false
  modalError.value = ''
}

async function load() {
  employees.value = await api('/employees?platform=twitter')
  try {
    const res = await api('/employees/types')
    if (res.types?.length) employeeTypes.value = res.types
  } catch { /* defaults */ }
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
  modalError.value = ''
  loading.value = true
  try {
    await api('/employees', { method: 'POST', body: JSON.stringify(single) })
    single.display_name = ''
    single.twitter_handle = ''
    single.twitter_cookie = ''
    await load()
    closeRecruitModal()
  } catch (e) {
    modalError.value = e.message
  } finally {
    loading.value = false
  }
}

async function submitBatch() {
  modalError.value = ''
  batchResult.value = null
  const items = parseBatchLines(batchText.value)
  if (!items.length) {
    modalError.value = '请按格式填写至少一行'
    return
  }
  loading.value = true
  try {
    batchResult.value = await api('/employees/batch', {
      method: 'POST',
      body: JSON.stringify({ items, auto_onboard: false }),
    })
    await load()
    if (!batchResult.value.failed.length) {
      batchText.value = ''
      closeRecruitModal()
    }
  } catch (e) {
    modalError.value = e.message
  } finally {
    loading.value = false
  }
}

function bindCookie(e) {
  closeMenu()
  modalError.value = ''
  cookieModal.value = e
  cookieEdit.value = ''
}

async function viewCookie(e) {
  closeMenu()
  modalError.value = ''
  loading.value = true
  try {
    const data = await api(`/employees/${e.id}/cookie`)
    cookieViewText.value = data.twitter_cookie
    cookieViewModal.value = e
  } catch (err) {
    alert(err.message)
  } finally {
    loading.value = false
  }
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
    modalError.value = e.message
  } finally {
    loading.value = false
  }
}

async function remove(e) {
  closeMenu()
  if (!confirm(`删除员工 ${e.display_name}？`)) return
  await api(`/employees/${e.id}`, { method: 'DELETE' })
  await load()
}

onMounted(() => {
  load()
  document.addEventListener('click', closeMenu)
})
onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.header-actions { display: flex; flex-direction: column; align-items: flex-end; gap: 0.75rem; }
.desc { color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem; }
.platform-tags { display: flex; gap: 0.5rem; }
.tag { padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem; border: 1px solid var(--border); }
.tag.active { background: #eef2ff; color: #4f46e5; border-color: #c7d2fe; }
.tag.disabled { color: var(--muted); opacity: 0.6; }
.list-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.filters { display: flex; gap: 0.5rem; flex: 1; }
.search { max-width: 220px; }
.list-actions { display: flex; gap: 0.5rem; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.dot.ok { background: var(--success); }
.dot.miss { background: var(--danger); }
.actions-cell { width: 48px; text-align: center; }
.row-menu { position: relative; display: inline-block; }
.menu-trigger {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 1.1rem;
  line-height: 1;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
}
.menu-trigger:hover {
  background: #f4f4f5;
  color: var(--text);
}
.menu-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 4px);
  min-width: 128px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow);
  z-index: 20;
  overflow: hidden;
}
.menu-dropdown button {
  display: block;
  width: 100%;
  text-align: left;
  background: transparent;
  color: var(--text);
  border: none;
  border-radius: 0;
  padding: 0.55rem 0.85rem;
  font-size: 0.85rem;
  font-weight: 500;
}
.menu-dropdown button:hover { background: #f4f4f5; }
.menu-dropdown .danger-text { color: var(--danger); }
.readonly { background: #f4f4f5; color: var(--text); }
button.sm { padding: 0.25rem 0.5rem; font-size: 0.75rem; }
.empty { color: var(--muted); padding: 2rem 0; text-align: center; }
.count { color: var(--muted); font-size: 0.8rem; margin-top: 0.75rem; }
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.65); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
.modal-body { width: 480px; max-width: 100%; max-height: 90vh; overflow: auto; }
.modal-body.wide { width: 560px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.modal-header h3 { margin: 0; }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.tabs button { background: var(--surface); border: 1px solid var(--border); color: var(--muted); padding: 0.4rem 0.75rem; }
.tabs button.active { background: var(--accent); color: white; border-color: var(--accent); }
.hint { color: var(--muted); font-weight: 400; font-size: 0.8rem; }
.hint-block { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.75rem; }
.batch-area { width: 100%; margin-bottom: 0.75rem; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.result { color: var(--success); margin: 0.5rem 0; }
</style>
