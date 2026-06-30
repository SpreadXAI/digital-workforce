<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">数字员工平台</div>

      <div class="team-box" v-if="teams.length">
        <label>当前团队</label>
        <select :value="currentTeamId" @change="switchTeam">
          <option v-for="t in teams" :key="t.id" :value="t.id">
            {{ t.name }}{{ t.is_personal ? '（个人）' : '' }}
          </option>
        </select>
        <button class="secondary sm invite-btn" @click="showInvite = true">邀请成员</button>
      </div>

      <div v-if="pendingInvites.length" class="pending-invites">
        <p class="invite-title">待接受邀请</p>
        <div v-for="inv in pendingInvites" :key="inv.id" class="invite-row">
          <span>团队 #{{ inv.team_id }}</span>
          <button class="sm" @click="acceptInvite(inv.token)">加入</button>
        </div>
      </div>

      <nav>
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </router-link>
      </nav>
      <button class="logout secondary" @click="logout">退出</button>
    </aside>
    <main class="content">
      <router-view :key="teamKey" />
    </main>

    <!-- 邀请弹窗 -->
    <div v-if="showInvite" class="modal" @click.self="showInvite = false">
      <div class="card modal-body">
        <h3>邀请成员加入团队</h3>
        <p class="hint">对方需已注册账号，邮箱需完全一致。</p>
        <div class="form-row">
          <label>成员邮箱</label>
          <input v-model="inviteEmail" type="email" placeholder="user@example.com" />
        </div>
        <p v-if="inviteLink" class="invite-link">
          邀请链接（可复制发给对方）：<br />
          <code>{{ inviteLink }}</code>
        </p>
        <p v-if="inviteError" class="error">{{ inviteError }}</p>
        <div class="modal-actions">
          <button @click="sendInvite" :disabled="inviteLoading">发送邀请</button>
          <button class="secondary" @click="showInvite = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NAV, ADMIN_NAV, api, clearToken, getTeamId, loadCurrentUser, loadTeams, setTeamId } from '../api'

const router = useRouter()
const route = useRoute()
const teams = ref([])
const pendingInvites = ref([])
const currentTeamId = ref(getTeamId())
const teamKey = computed(() => `${currentTeamId.value}-${route.path}`)
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteLink = ref('')
const inviteError = ref('')
const inviteLoading = ref(false)
const isAdmin = ref(false)
const navItems = ref([...NAV])

async function refreshTeams() {
  teams.value = await loadTeams()
  currentTeamId.value = getTeamId()
  try {
    pendingInvites.value = await api('/teams/invites/mine')
  } catch {
    pendingInvites.value = []
  }
}

function switchTeam(ev) {
  setTeamId(Number(ev.target.value))
  currentTeamId.value = getTeamId()
}

async function sendInvite() {
  inviteError.value = ''
  inviteLink.value = ''
  inviteLoading.value = true
  try {
    const inv = await api('/teams/invites', {
      method: 'POST',
      body: JSON.stringify({ email: inviteEmail.value }),
    })
    const base = window.location.origin
    inviteLink.value = `${base}/login?invite=${inv.token}`
    inviteEmail.value = ''
  } catch (e) {
    inviteError.value = e.message
  } finally {
    inviteLoading.value = false
  }
}

async function acceptInvite(token) {
  const team = await api('/teams/invites/accept', {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
  setTeamId(team.id)
  await refreshTeams()
}

function logout() {
  clearToken()
  router.push('/login')
}

onMounted(async () => {
  try {
    const user = await loadCurrentUser()
    isAdmin.value = !!user.is_admin
    if (isAdmin.value) navItems.value = [...NAV, ADMIN_NAV]
  } catch {
    isAdmin.value = false
  }
  await refreshTeams()
  const token = route.query.invite
  if (token && typeof token === 'string') {
    try {
      await acceptInvite(token)
      router.replace({ path: route.path })
    } catch (e) {
      inviteError.value = e.message
      showInvite.value = true
    }
  }
})
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 250px;
  background: linear-gradient(180deg, #fffaf5 0%, #f8efe6 100%);
  border-right: 1px solid var(--border);
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm);
}
.brand {
  font-size: 1.15rem;
  font-weight: 800;
  margin-bottom: 1rem;
  color: var(--accent);
  letter-spacing: 0.02em;
}
.team-box { margin-bottom: 1rem; }
.team-box label { display: block; font-size: 0.75rem; color: var(--muted); margin-bottom: 0.35rem; font-weight: 600; }
.team-box select { width: 100%; margin-bottom: 0.5rem; }
.invite-btn { width: 100%; }
.pending-invites {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--surface-elevated);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}
.invite-title { font-size: 0.75rem; color: var(--muted); margin-bottom: 0.5rem; font-weight: 600; }
.invite-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; margin-bottom: 0.35rem; }
.nav-item {
  display: block;
  padding: 0.7rem 0.85rem;
  border-radius: 999px;
  color: var(--text-soft);
  margin-bottom: 0.35rem;
  text-decoration: none;
  font-weight: 600;
}
.nav-item:hover, .nav-item.router-link-active {
  background: var(--accent-soft);
  color: var(--accent-hover);
  text-decoration: none;
}
.logout { margin-top: auto; }
.content {
  flex: 1;
  padding: 2rem;
  overflow: auto;
  background: transparent;
}
.modal {
  position: fixed;
  inset: 0;
  background: rgba(61, 44, 33, 0.35);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal-body { width: 440px; max-width: 90vw; }
.hint { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.invite-link { font-size: 0.8rem; color: var(--success); margin: 0.75rem 0; word-break: break-all; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
button.sm { padding: 0.25rem 0.55rem; font-size: 0.75rem; }
.error { color: var(--danger); font-size: 0.85rem; }
</style>
