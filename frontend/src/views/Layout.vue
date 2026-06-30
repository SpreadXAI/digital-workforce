<template>
  <div class="layout layout--console">
    <div class="app-shell">
      <aside class="app-shell__sidenav">
        <div class="app-shell__panel">
          <header class="app-shell__brand">
            <div class="app-shell__brand-stack">
              <button type="button" class="app-shell__logo" @click="router.push('/')">
                <span class="app-shell__logo-mark">DW</span>
                <span class="app-shell__logo-text">
                  <span class="app-shell__logo-title">数字员工平台</span>
                  <span class="app-shell__logo-sub">{{ currentTeamName }}</span>
                </span>
              </button>
            </div>
            <div v-if="teams.length > 1" class="app-shell__team-switch">
              <select :value="currentTeamId" @change="switchTeam">
                <option v-for="t in teams" :key="t.id" :value="t.id">
                  {{ t.name }}{{ t.is_personal ? '（个人）' : '' }}
                </option>
              </select>
            </div>
          </header>

          <nav class="app-shell__nav" aria-label="主功能">
            <template v-for="group in visibleNavGroups" :key="group.title">
              <div class="app-shell__nav-title">{{ group.title }}</div>
              <router-link
                v-for="item in group.items"
                :key="item.path"
                :to="item.path"
                class="app-shell__nav-item app-shell__nav-item--link"
                :class="{ 'app-shell__nav-item--active': isActive(item.path) }"
              >
                <span class="app-shell__nav-icon" v-html="iconSvg(item.icon)" />
                <span class="app-shell__nav-label">{{ item.label }}</span>
              </router-link>
            </template>

            <div v-if="pendingInvites.length" class="app-shell__invites">
              <div class="app-shell__nav-title">邀请</div>
              <div v-for="inv in pendingInvites" :key="inv.id" class="app-shell__invite-row">
                <span>团队 #{{ inv.team_id }}</span>
                <button type="button" class="app-shell__invite-btn" @click="acceptInvite(inv.token)">加入</button>
              </div>
            </div>

            <button type="button" class="app-shell__nav-item app-shell__nav-item--link invite-link" @click="showInvite = true">
              <span class="app-shell__nav-icon" v-html="iconSvg('invite')" />
              <span class="app-shell__nav-label">邀请成员</span>
            </button>
          </nav>

          <footer class="app-shell__foot">
            <button type="button" class="app-shell__foot-row" @click="logout">
              <span class="app-shell__avatar">{{ userInitial }}</span>
              <span class="app-shell__user-meta">
                <span class="app-shell__user-name">{{ userName }}</span>
                <span class="app-shell__user-action">退出登录</span>
              </span>
            </button>
          </footer>
        </div>
      </aside>

      <main class="app-shell__main">
        <div class="app-shell__content">
          <router-view :key="teamKey" />
        </div>
      </main>
    </div>

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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NAV_GROUPS, api, clearToken, getTeamId, loadCurrentUser, loadTeams, setTeamId } from '../api'

const ICONS = {
  dashboard:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="8" height="8" rx="1.5"/><rect x="13" y="3" width="8" height="5" rx="1.5"/><rect x="13" y="10" width="8" height="11" rx="1.5"/><rect x="3" y="13" width="8" height="8" rx="1.5"/></svg>',
  users:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="8" r="3.5"/><path d="M3 19c0-3 2.7-5 6-5s6 2 6 5"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 19c.3-2.2 2-3.5 4-3.5"/></svg>',
  tasks:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16M4 12h10M4 17h14"/><path d="M17 15l2 2 4-4"/></svg>',
  logs:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M7 4h10v16H7z"/><path d="M9 8h6M9 12h6M9 16h4"/></svg>',
  settings:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  invite:
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 11c1.7 0 3-1.3 3-3s-1.3-3-3-3-3 1.3-3 3 1.3 3 3 3z"/><path d="M8 13c1.7 0 3-1.3 3-3S9.7 7 8 7 5 8.3 5 10s1.3 3 3 3z"/><path d="M8 15c-2.7 0-5 1.3-5 3v1h7"/><path d="M16 13c-1.6 0-3 .7-3.9 1.8 1.3.9 2.2 2.3 2.4 4.2H21v-1c0-1.7-2.3-3-5-3z"/></svg>',
}

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
const currentUser = ref(null)

const currentTeamName = computed(() => {
  const team = teams.value.find((t) => t.id === currentTeamId.value)
  return team?.name || '工作空间'
})

const userName = computed(() => currentUser.value?.display_name || currentUser.value?.email || '用户')
const userInitial = computed(() => (userName.value[0] || 'U').toUpperCase())

const visibleNavGroups = computed(() =>
  NAV_GROUPS.filter((g) => !g.adminOnly || isAdmin.value)
)

function iconSvg(name) {
  return ICONS[name] || ICONS.dashboard
}

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(`${path}/`)
}

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
    inviteLink.value = `${window.location.origin}/login?invite=${inv.token}`
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
    currentUser.value = await loadCurrentUser()
    isAdmin.value = !!currentUser.value?.is_admin
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
.layout--console {
  max-width: none;
  margin: 0;
  padding: 0;
  min-height: 100vh;
}

.app-shell {
  height: 100vh;
  height: 100dvh;
  display: flex;
  overflow: hidden;
  background: #f2f2f4;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #18181b;
  letter-spacing: -0.01em;
}

.app-shell__sidenav {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.app-shell__panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #fff;
  border-right: 1px solid rgba(154, 139, 122, 0.14);
}

.app-shell__brand {
  flex-shrink: 0;
  padding: 12px 8px 12px 14px;
  border-bottom: 1px solid rgba(154, 139, 122, 0.14);
}

.app-shell__brand-stack {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 40px;
}

.app-shell__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
}

.app-shell__logo:hover { opacity: 0.88; }

.app-shell__logo-mark {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.app-shell__logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.app-shell__logo-title {
  font-size: 13px;
  font-weight: 600;
  color: #18181b;
  line-height: 1.2;
}

.app-shell__logo-sub {
  font-size: 12px;
  color: #71717a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-shell__team-switch {
  margin-top: 8px;
}

.app-shell__team-switch select {
  font-size: 12px;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid rgba(154, 139, 122, 0.2);
  background: #fafafa;
  color: #52525b;
}

.app-shell__nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 4px 10px 16px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.app-shell__nav-title {
  font-size: 11px;
  font-weight: 500;
  color: #a1a1aa;
  padding: 12px 10px 6px;
  letter-spacing: 0.3px;
}

.app-shell__nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  margin: 0;
  padding: 7px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font: inherit;
  font-size: 13px;
  font-weight: 400;
  color: #52525b;
  text-align: left;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.12s ease, color 0.12s ease;
}

.app-shell__nav-item:hover {
  background: #f4f1ec;
  color: #52525b;
  text-decoration: none;
}

.app-shell__nav-item--active {
  background: #f8f6f3;
  color: #8a7b6a;
  font-weight: 500;
}

.app-shell__nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #a1a1aa;
  display: inline-flex;
}

.app-shell__nav-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.app-shell__nav-item--active .app-shell__nav-icon { color: #8a7b6a; }

.app-shell__nav-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.app-shell__invites {
  margin-top: 4px;
}

.app-shell__invite-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  font-size: 12px;
  color: #71717a;
}

.app-shell__invite-btn {
  padding: 2px 8px;
  font-size: 11px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4f46e5;
  border: none;
  cursor: pointer;
}

.invite-link { margin-top: 4px; }

.app-shell__foot {
  flex-shrink: 0;
  padding: 6px 10px 12px 14px;
  border-top: 1px solid rgba(154, 139, 122, 0.14);
}

.app-shell__foot-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 6px 4px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font: inherit;
  color: inherit;
}

.app-shell__foot-row:hover { background: #f4f1ec; }

.app-shell__avatar {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #e4e4e7;
  color: #52525b;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.app-shell__user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 1px;
}

.app-shell__user-name {
  font-size: 13px;
  font-weight: 500;
  color: #18181b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-shell__user-action {
  font-size: 11px;
  color: #a1a1aa;
}

.app-shell__main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.app-shell__content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fafafa;
  padding: 24px 28px 32px;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(24, 24, 27, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-body { width: 440px; max-width: 90vw; }
.hint { color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }
.invite-link { font-size: 0.8rem; color: var(--success); margin: 0.75rem 0; word-break: break-all; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.error { color: var(--danger); font-size: 0.85rem; }
</style>
