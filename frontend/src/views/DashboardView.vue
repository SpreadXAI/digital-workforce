<template>
  <div>
    <h2 class="page-title">总览</h2>
    <p class="page-desc">招募 Twitter 员工 → 绑定 Cookie → 批量派活 → 查看任务详情</p>
    <div v-if="stats" class="stats-grid">
      <div class="card stat">
        <div class="num">{{ stats.total_employees }}</div>
        <div class="label">员工总数</div>
      </div>
      <div class="card stat accent">
        <div class="num">{{ stats.twitter_active || stats.active }}</div>
        <div class="label">可干活</div>
      </div>
      <div class="card stat">
        <div class="num">{{ stats.tasks_today }}</div>
        <div class="label">今日任务</div>
      </div>
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
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
  max-width: 820px;
}
.stat .num {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
}
.stat .label {
  color: var(--muted);
  font-size: 0.85rem;
  margin-top: 0.35rem;
}
@media (max-width: 720px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
