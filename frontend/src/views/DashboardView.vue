<template>
  <div>
    <h2>总览</h2>
    <p class="desc">数字员工生命周期：招募 → 培训 → 上岗 → 执行任务</p>
    <div v-if="stats" class="stats-grid">
      <div class="card stat"><div class="num">{{ stats.total_employees }}</div><div class="label">员工总数</div></div>
      <div class="card stat"><div class="num">{{ stats.active }}</div><div class="label">在岗</div></div>
      <div class="card stat"><div class="num">{{ stats.training }}</div><div class="label">培训中</div></div>
      <div class="card stat"><div class="num">{{ stats.tasks_today }}</div><div class="label">今日任务</div></div>
    </div>
    <div class="actions">
      <router-link to="/recruit" class="btn">招募新员工</router-link>
      <router-link to="/tasks" class="btn secondary">派发任务</router-link>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const stats = ref(null)
onMounted(async () => {
  stats.value = await api('/dashboard/stats')
})
</script>

<style scoped>
h2 { margin-bottom: 0.5rem; }
.desc { color: var(--muted); margin-bottom: 1.5rem; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.stat .num { font-size: 2rem; font-weight: 700; }
.stat .label { color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem; }
.actions { display: flex; gap: 0.75rem; }
.actions .btn { display: inline-block; text-decoration: none; }
</style>
