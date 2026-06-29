<template>
  <div>
    <h2>培训中心</h2>
    <p class="desc">配置人设、凭证、Skill，试跑通过后标记待上岗。</p>
    <EmployeeTable :employees="employees" @refresh="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import EmployeeTable from '../components/EmployeeTable.vue'

const employees = ref([])
async function load() {
  employees.value = await api('/employees?stage=training')
}
onMounted(load)
</script>

<style scoped>
.desc { color: var(--muted); margin-bottom: 1rem; }
</style>
