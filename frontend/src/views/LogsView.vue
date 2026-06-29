<template>
  <div>
    <h2>执行日志</h2>
    <table v-if="logs.length">
      <thead>
        <tr>
          <th>时间</th>
          <th>员工</th>
          <th>步骤</th>
          <th>状态</th>
          <th>Work ID</th>
          <th>消息</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="l in logs" :key="l.id">
          <td>{{ formatTime(l.created_at) }}</td>
          <td>{{ employeeName(l.employee_id) }}</td>
          <td>{{ l.step }}</td>
          <td>{{ l.status }}</td>
          <td>{{ l.tactile_work_id || '—' }}</td>
          <td class="msg">{{ l.message }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">暂无执行记录</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const logs = ref([])
const employees = ref([])

function employeeName(id) {
  return employees.value.find((e) => e.id === id)?.display_name || id
}
function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(async () => {
  employees.value = await api('/employees')
  logs.value = await api('/tasks/executions')
})
</script>

<style scoped>
.msg { max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty { color: var(--muted); padding: 2rem 0; }
</style>
