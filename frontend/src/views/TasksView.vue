<template>
  <div class="tasks-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">批量派活</h2>
        <p class="page-desc">
          选择员工后，任务将派发到 Cloud Agent Lab 共用 Agent 执行；每位员工携带自己的 Twitter Cookie 环境变量。
        </p>
      </div>
    </div>

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
          <div v-if="employees.length" class="pick-head">
            <span class="pick-check" aria-hidden="true"></span>
            <span>姓名</span>
            <span>账号</span>
            <span>Cookie</span>
          </div>
          <label
            v-for="e in employees"
            :key="e.id"
            class="pick-row"
            :class="{ disabled: !e.has_twitter_cookie }"
          >
            <input
              class="pick-check"
              type="checkbox"
              :value="e.id"
              v-model="selectedIds"
              :disabled="!e.has_twitter_cookie"
            />
            <span class="pick-name" :title="e.display_name">{{ e.display_name }}</span>
            <span class="pick-handle" :title="e.twitter_handle || e.code">{{ e.twitter_handle || e.code }}</span>
            <span :class="['pick-cookie', e.has_twitter_cookie ? 'ok' : 'miss']">
              {{ e.has_twitter_cookie ? '已绑定' : '未绑定' }}
            </span>
          </label>
          <p v-if="!employees.length" class="empty">暂无员工，请先到「员工管理」招募</p>
        </div>
        <p v-if="result && !result.failed.length" class="success">
          已派发 {{ result.dispatched.length }} 人
          <span v-if="result.dispatched.length">
            ·
            <router-link :to="`/tasks/${result.dispatched[0].id}`">查看最新任务</router-link>
          </span>
        </p>
        <div v-if="result?.failed?.length" class="failed-box">
          <p class="error">派活失败 {{ result.failed.length }} 人</p>
          <ul>
            <li v-for="item in result.failed" :key="item.employee_id">
              {{ item.display_name || `员工 #${item.employee_id}` }}：{{ item.error }}
            </li>
          </ul>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading || !selectedIds.length">
          {{ loading ? '派发中…' : `派发给 ${selectedIds.length} 名员工` }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const form = reactive({ title: '', instruction: '' })
const employees = ref([])
const selectedIds = ref([])
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function load() {
  employees.value = await api('/employees?platform=twitter')
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
    if (!result.value.dispatched.length && result.value.failed.length) {
      error.value = result.value.failed.map((f) => f.error).join('；')
    }
    if (result.value.dispatched.length) selectedIds.value = []
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header { margin-bottom: 1.25rem; }
.form-card {
  max-width: 720px;
}
.form-card h3 {
  margin-bottom: 1rem;
  color: var(--muted);
}
.select-bar { display: flex; align-items: center; gap: 0.5rem; margin: 0.75rem 0; }
.count { color: var(--muted); font-size: 0.85rem; margin-left: auto; }
.employee-pick {
  max-height: 320px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  background: var(--surface);
}
.pick-head,
.pick-row {
  display: grid;
  grid-template-columns: 2rem 1fr minmax(9rem, 11rem) 4.5rem;
  gap: 0.75rem;
  align-items: center;
  padding: 0.6rem 0.85rem;
}
.pick-head {
  position: sticky;
  top: 0;
  z-index: 1;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--muted);
  background: #f8f8fa;
  border-bottom: 1px solid var(--border);
}
.pick-row {
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s ease;
}
.pick-row:last-child { border-bottom: none; }
.pick-row:hover:not(.disabled) { background: #f4f4f5; }
.pick-row.disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.pick-check {
  width: 1rem;
  height: 1rem;
  margin: 0;
}
.pick-name {
  font-weight: 500;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pick-handle {
  color: var(--muted);
  font-size: 0.85rem;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pick-cookie {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: right;
}
.pick-cookie.ok { color: var(--success); }
.pick-cookie.miss { color: var(--danger); }
.empty { color: var(--muted); padding: 1rem 0.85rem; }
.failed-box {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  border: 1px solid rgba(220, 38, 38, 0.25);
  border-radius: var(--radius-sm);
  background: rgba(220, 38, 38, 0.05);
}
.failed-box ul {
  margin: 0.35rem 0 0;
  padding-left: 1.1rem;
  color: var(--danger);
  font-size: 0.85rem;
  line-height: 1.6;
}
</style>
