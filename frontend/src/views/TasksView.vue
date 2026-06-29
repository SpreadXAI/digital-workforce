<template>
  <div>
    <h2>批量派活</h2>
    <p class="desc">选择已绑定 Cookie 的员工，同一指令批量下发到 Tactile 执行。</p>
    <div class="card form-card">
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
          <label v-for="e in employees" :key="e.id" class="pick-row">
            <input type="checkbox" :value="e.id" v-model="selectedIds" :disabled="!e.has_twitter_cookie" />
            <span>{{ e.display_name }}</span>
            <span class="meta">{{ e.employee_type_label }} · {{ e.twitter_handle || e.code }}</span>
            <span v-if="!e.has_twitter_cookie" class="warn">无 Cookie</span>
          </label>
          <p v-if="!employees.length" class="empty">暂无员工，请先到「员工管理」招募</p>
        </div>
        <p v-if="result" class="result">已派发 {{ result.dispatched.length }}，失败 {{ result.failed.length }}</p>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading || !selectedIds.length">
          {{ loading ? '派发中…' : `派发给 ${selectedIds.length} 名员工` }}
        </button>
      </form>
    </div>
    <router-link to="/recruit" class="link">← 去员工管理招募 / 更新 Cookie</router-link>
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
    selectedIds.value = []
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
.form-card { max-width: 640px; }
.select-bar { display: flex; align-items: center; gap: 0.5rem; margin: 0.75rem 0; }
.count { color: var(--muted); font-size: 0.85rem; margin-left: auto; }
.employee-pick { max-height: 280px; overflow: auto; border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem; margin-bottom: 1rem; }
.pick-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.25rem; cursor: pointer; }
.pick-row .meta { color: var(--muted); font-size: 0.8rem; }
.pick-row .warn { color: var(--warning); font-size: 0.75rem; margin-left: auto; }
.empty { color: var(--muted); padding: 0.5rem; }
.result { color: var(--success); margin-bottom: 0.5rem; }
.link { display: inline-block; margin-top: 1rem; color: var(--muted); font-size: 0.9rem; }
</style>
