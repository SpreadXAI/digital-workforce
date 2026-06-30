<template>
  <div>
    <h2 class="page-title">执行日志</h2>
    <p class="page-desc">查看每次派活的执行记录，点击可进入任务详情（含 Tactile Work 状态）。</p>

    <div class="card">
      <table v-if="logs.length">
        <thead>
          <tr>
            <th>时间</th>
            <th>员工</th>
            <th>步骤</th>
            <th>状态</th>
            <th>Work ID</th>
            <th>消息</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="l in logs" :key="l.id">
            <td>{{ formatTime(l.created_at) }}</td>
            <td>{{ employeeName(l.employee_id) }}</td>
            <td>{{ l.step }}</td>
            <td><span :class="['badge', l.status]">{{ TASK_STATUS_LABELS[l.status] || l.status }}</span></td>
            <td>{{ l.tactile_work_id || '—' }}</td>
            <td class="msg" :title="l.message">{{ l.message }}</td>
            <td>
              <router-link v-if="l.task_id" :to="`/tasks/${l.task_id}`" class="link-btn">详情</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">暂无执行记录</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, TASK_STATUS_LABELS } from '../api'

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
.msg {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--muted);
  font-size: 0.85rem;
}
.empty { color: var(--muted); padding: 2rem 0; }
</style>
