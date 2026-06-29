<template>
  <table v-if="employees.length">
    <thead>
      <tr>
        <th>编号</th>
        <th>姓名</th>
        <th>岗位</th>
        <th>阶段</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="e in employees" :key="e.id">
        <td>{{ e.code }}</td>
        <td>{{ e.display_name }}</td>
        <td>{{ e.role_title }}</td>
        <td><span :class="['badge', e.stage]">{{ STAGE_LABELS[e.stage] }}</span></td>
        <td><router-link :to="`/employees/${e.id}`">详情</router-link></td>
      </tr>
    </tbody>
  </table>
  <p v-else class="empty">暂无员工</p>
</template>

<script setup>
import { STAGE_LABELS } from '../api'
defineProps({ employees: { type: Array, default: () => [] } })
defineEmits(['refresh'])
</script>

<style scoped>
.empty { color: var(--muted); padding: 2rem 0; }
</style>
