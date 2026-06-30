<template>
  <div class="settings-page">
    <h1 class="page-title">设置</h1>
    <p class="page-desc">团队邀请与平台对接配置</p>

    <section class="card section-card">
      <h2>团队</h2>
      <p class="section-desc">邀请成员加入当前团队，对方需已注册且邮箱完全一致。</p>

      <div v-if="pendingInvites.length" class="pending-invites">
        <h3>待处理邀请</h3>
        <div v-for="inv in pendingInvites" :key="inv.id" class="invite-row">
          <span>团队 #{{ inv.team_id }}</span>
          <button type="button" class="secondary sm" @click="acceptInvite(inv.token)">加入</button>
        </div>
      </div>

      <div class="form-row">
        <label>成员邮箱</label>
        <input v-model="inviteEmail" type="email" placeholder="user@example.com" />
      </div>
      <p v-if="inviteLink" class="invite-link">
        邀请链接（可复制发给对方）：<br />
        <code>{{ inviteLink }}</code>
      </p>
      <p v-if="inviteError" class="error">{{ inviteError }}</p>
      <button type="button" :disabled="inviteLoading || !inviteEmail.trim()" @click="sendInvite">
        {{ inviteLoading ? '发送中…' : '发送邀请' }}
      </button>
    </section>

    <section v-if="isAdmin" id="cloud-agent-lab" class="card section-card">
      <h2>Cloud Agent Lab</h2>
      <p class="section-desc">Gateway 对接配置（全员共用一个 Agent）。保存后写入数据库，刷新或重启服务均会保留。</p>
      <CloudAgentLabSettings />
    </section>

    <p v-else-if="!isAdmin" class="muted-note">Cloud Agent Lab 配置仅管理员可见。</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CloudAgentLabSettings from '../components/CloudAgentLabSettings.vue'
import { api, loadCurrentUser, setTeamId } from '../api'

const route = useRoute()
const router = useRouter()
const isAdmin = ref(false)
const pendingInvites = ref([])
const inviteEmail = ref('')
const inviteLink = ref('')
const inviteError = ref('')
const inviteLoading = ref(false)

async function loadInvites() {
  try {
    pendingInvites.value = await api('/teams/invites/mine')
  } catch {
    pendingInvites.value = []
  }
}

async function sendInvite() {
  inviteError.value = ''
  inviteLink.value = ''
  inviteLoading.value = true
  try {
    const inv = await api('/teams/invites', {
      method: 'POST',
      body: JSON.stringify({ email: inviteEmail.value.trim() }),
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
  await loadInvites()
}

onMounted(async () => {
  try {
    const user = await loadCurrentUser()
    isAdmin.value = !!user?.is_admin
  } catch {
    isAdmin.value = false
  }
  await loadInvites()

  const token = route.query.invite
  if (token && typeof token === 'string') {
    try {
      await acceptInvite(token)
      router.replace({ path: '/settings' })
    } catch (e) {
      inviteError.value = e.message
    }
  }

  if (route.hash === '#cloud-agent-lab' && isAdmin.value) {
    document.getElementById('cloud-agent-lab')?.scrollIntoView({ behavior: 'smooth' })
  }
})
</script>

<style scoped>
.settings-page { max-width: 720px; }
.page-desc { color: var(--muted); margin-bottom: 1.5rem; }
.section-card { margin-bottom: 1rem; }
.section-card h2 {
  font-size: 1rem;
  margin-bottom: 0.35rem;
}
.section-desc {
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}
.pending-invites {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.pending-invites h3 {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
}
.invite-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.35rem 0;
  font-size: 0.9rem;
}
.invite-link {
  font-size: 0.85rem;
  color: var(--success);
  margin: 0.75rem 0;
  word-break: break-all;
}
.muted-note {
  color: var(--muted);
  font-size: 0.9rem;
}
.error { color: var(--danger); font-size: 0.9rem; margin: 0.5rem 0; }
button.sm { padding: 0.25rem 0.6rem; font-size: 0.8rem; }
</style>
