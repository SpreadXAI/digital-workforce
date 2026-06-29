<template>
  <div>
    <h2>任务中心</h2>
    <p class="desc">向在岗员工派发任务，员工作为执行器对接 Tactile。</p>
    <div class="card form-card">
      <form @submit.prevent="submit">
        <div class="form-row">
          <label>执行员工（须在岗）</label>
          <select v-model="form.employee_id" required>
            <option value="">选择员工</option>
            <option v-for="e in activeEmployees" :key="e.id" :value="e.id">
              {{ e.display_name }} ({{ e.code }})
            </option>
          </select>
        </div>
        <div class="form-row">
          <label>任务标题</label>
          <input v-model="form.title" required />
        </div>
        <div class="form-row">
          <label>任务指令</label>
          <textarea v-model="form.instruction" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '派发中…' : '派发任务' }}</button>
      </form>
    </div>
    <h3 class="sub">近期任务</h3>
    <table v-if="tasks.length">
      <thead>
        <tr><th>ID</th><th>标题</th><th>员工</th><th>状态</th><th>时间</th></tr>
      </thead>
      <tbody>
        <tr v-for="t in tasks" :key="t.id">
          <td>{{ t.id }}</td>
          <td>{{ t.title }}</td>
          <td>{{ employeeName(t.employee_id) }}</td>
          <td>{{ t.status }}</td>
          <td>{{ formatTime(t.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const form = reactive({ employee_id: '', title: '', instruction: '' })
const activeEmployees = ref([])
const allEmployees = ref([])
const tasks = ref([])
const loading = ref(false)
const error = ref('')

function employeeName(id) {
  return allEmployees.value.find((e) => e.id === id)?.display_name || id
}
function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function load() {
  allEmployees.value = await api('/employees')
  activeEmployees.value = allEmployees.value.filter((e) => e.stage === 'active')
  tasks.value = await api('/tasks')
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await api('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        employee_id: Number(form.employee_id),
        title: form.title,
        instruction: form.instruction,
      }),
    })
    form.title = ''
    form.instruction = ''
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
.desc { color: var(--muted); margin-bottom: 1rem; }
.form-card { max-width: 560px; margin-bottom: 2rem; }
.sub { margin-bottom: 0.75rem; }
</style>
