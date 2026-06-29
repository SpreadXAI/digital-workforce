<template>
  <div>
    <h2>员工名册</h2>
    <div class="filters">
      <button
        v-for="s in stages"
        :key="s.value"
        :class="['filter', { active: stage === s.value }]"
        @click="stage = s.value; load()"
      >{{ s.label }}</button>
    </div>
    <EmployeeTable :employees="employees" @refresh="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import EmployeeTable from '../components/EmployeeTable.vue'

const employees = ref([])
const stage = ref('')
const stages = [
  { value: '', label: '全部' },
  { value: 'recruiting', label: '招募中' },
  { value: 'training', label: '培训中' },
  { value: 'ready', label: '待上岗' },
  { value: 'active', label: '在岗' },
  { value: 'suspended', label: '已暂停' },
]

async function load() {
  const q = stage.value ? `?stage=${stage.value}` : ''
  employees.value = await api(`/employees${q}`)
}
onMounted(load)
</script>

<style scoped>
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.filter {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--muted);
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
}
.filter.active { background: var(--accent); color: white; border-color: var(--accent); }
</style>
