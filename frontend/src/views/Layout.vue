<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">数字员工平台</div>
      <nav>
        <router-link v-for="item in NAV" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </router-link>
      </nav>
      <button class="logout secondary" @click="logout">退出</button>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { NAV, clearToken } from '../api'
import { useRouter } from 'vue-router'

const router = useRouter()
function logout() {
  clearToken()
  router.push('/login')
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 220px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
}
.brand { font-size: 1.1rem; font-weight: 700; margin-bottom: 2rem; }
.nav-item {
  display: block;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  color: var(--muted);
  margin-bottom: 0.25rem;
  text-decoration: none;
}
.nav-item:hover, .nav-item.router-link-active {
  background: var(--bg);
  color: var(--text);
  text-decoration: none;
}
.logout { margin-top: auto; }
.content { flex: 1; padding: 2rem; overflow: auto; }
</style>
