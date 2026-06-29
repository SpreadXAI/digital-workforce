<template>
  <div class="login-page">
    <div class="card login-card">
      <h1>数字员工平台</h1>
      <p class="subtitle">招募 · 派活 · 执行</p>
      <form @submit.prevent="submit">
        <div class="form-row">
          <label>邮箱</label>
          <input v-model="email" type="email" required />
        </div>
        <div class="form-row">
          <label>密码</label>
          <input v-model="password" type="password" required />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, setToken, loadTeams } from '../api'

const router = useRouter()
const email = ref('qa@spreadx.ai')
const password = ref('Dw@Test2026')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    setToken(data.access_token)
    await loadTeams()
    const invite = new URLSearchParams(window.location.search).get('invite')
    if (invite) {
      await api('/teams/invites/accept', { method: 'POST', body: JSON.stringify({ token: invite }) })
    }
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card { width: 380px; }
h1 { margin-bottom: 0.25rem; }
.subtitle { color: var(--muted); margin-bottom: 1.5rem; font-size: 0.9rem; }
button { width: 100%; margin-top: 0.5rem; }
</style>
