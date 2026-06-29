<template>
  <div>
    <h2>招募中心</h2>
    <p class="desc">创建数字员工档案，进入培训阶段。</p>
    <div class="card form-card">
      <form @submit.prevent="submit">
        <div class="form-row">
          <label>员工姓名</label>
          <input v-model="form.display_name" placeholder="如：小美" required />
        </div>
        <div class="form-row">
          <label>岗位</label>
          <select v-model="form.role_title">
            <option value="twitter_operator">Twitter 运营</option>
            <option value="content_creator">内容创作</option>
            <option value="community_manager">社群管理</option>
          </select>
        </div>
        <div class="form-row">
          <label>平台</label>
          <select v-model="form.platform">
            <option value="twitter">Twitter / X</option>
            <option value="general">通用</option>
          </select>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '创建中…' : '招募员工' }}</button>
      </form>
    </div>
    <p v-if="created" class="success">已创建 {{ created.display_name }}（{{ created.code }}），<router-link :to="`/employees/${created.id}`">去培训</router-link></p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { api } from '../api'

const form = reactive({ display_name: '', role_title: 'twitter_operator', platform: 'twitter' })
const loading = ref(false)
const error = ref('')
const created = ref(null)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    created.value = await api('/employees', { method: 'POST', body: JSON.stringify(form) })
    await api(`/employees/${created.value.id}/stage`, {
      method: 'POST',
      body: JSON.stringify({ stage: 'training' }),
    })
    form.display_name = ''
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.desc { color: var(--muted); margin-bottom: 1rem; }
.form-card { max-width: 480px; }
.success { margin-top: 1rem; color: var(--success); }
</style>
