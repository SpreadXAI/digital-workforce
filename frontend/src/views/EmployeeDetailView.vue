<template>
  <div v-if="employee">
    <div class="header">
      <h2>{{ employee.display_name }} <span class="code">{{ employee.code }}</span></h2>
      <span :class="['badge', employee.stage]">{{ STAGE_LABELS[employee.stage] }}</span>
    </div>

    <div class="grid">
      <div class="card">
        <h3>培训配置</h3>
        <div class="form-row">
          <label>人设</label>
          <textarea v-model="edit.persona" />
        </div>
        <div class="form-row">
          <label>Playbook / SOP</label>
          <textarea v-model="edit.playbook" />
        </div>
        <div class="form-row">
          <label>凭证 Cookie（JSON 键值，如 COOKIE）</label>
          <textarea v-model="credentialsText" placeholder='{"COOKIE": "..."}' />
        </div>
        <button @click="save" :disabled="saving">保存</button>
        <p v-if="msg" class="msg">{{ msg }}</p>
      </div>

      <div class="card">
        <h3>生命周期</h3>
        <div class="stage-actions">
          <button v-if="employee.stage === 'training'" @click="setStage('ready')">培训完成 → 待上岗</button>
          <button v-if="employee.stage === 'ready'" @click="setStage('active')">确认上岗</button>
          <button v-if="employee.stage === 'active'" class="secondary" @click="setStage('suspended')">暂停</button>
          <button v-if="employee.stage === 'suspended'" @click="setStage('active')">恢复上岗</button>
          <button v-if="['active','ready'].includes(employee.stage)" class="secondary" @click="setStage('training')">再培训</button>
        </div>
        <p v-if="employee.tactile_agent_id" class="meta">Tactile Agent: {{ employee.tactile_agent_id }}</p>
      </div>
    </div>

    <div class="card section">
      <h3>试跑</h3>
      <div class="form-row">
        <textarea v-model="trialInstruction" placeholder="输入试跑指令…" />
      </div>
      <button @click="trialRun" :disabled="trialLoading">试跑</button>
    </div>

    <div class="card section">
      <h3>Skill 绑定</h3>
      <div v-if="catalog.length" class="skill-list">
        <div v-for="s in catalog" :key="s.id" class="skill-row">
          <span>{{ s.name }} ({{ s.id }})</span>
          <button class="secondary" @click="bindSkill(s)">绑定</button>
        </div>
      </div>
      <p v-else class="muted">Skill 目录未配置或为空</p>
      <ul v-if="employee.skills.length" class="bound">
        <li v-for="s in employee.skills" :key="s.id">{{ s.name || s.slug }} — skill_id {{ s.skill_id }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, STAGE_LABELS } from '../api'

const route = useRoute()
const employee = ref(null)
const edit = reactive({ persona: '', playbook: '' })
const credentialsText = ref('')
const msg = ref('')
const saving = ref(false)
const trialInstruction = ref('发一条测试推文')
const trialLoading = ref(false)
const catalog = ref([])

async function load() {
  employee.value = await api(`/employees/${route.params.id}`)
  edit.persona = employee.value.persona
  edit.playbook = employee.value.playbook
  credentialsText.value = employee.value.has_credentials ? '{"COOKIE":"..."}' : ''
}

async function save() {
  saving.value = true
  msg.value = ''
  try {
    let credentials = null
    if (credentialsText.value.trim()) {
      credentials = JSON.parse(credentialsText.value)
    }
    employee.value = await api(`/employees/${route.params.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ ...edit, credentials }),
    })
    msg.value = '已保存'
  } catch (e) {
    msg.value = e.message
  } finally {
    saving.value = false
  }
}

async function setStage(stage) {
  employee.value = await api(`/employees/${route.params.id}/stage`, {
    method: 'POST',
    body: JSON.stringify({ stage }),
  })
}

async function trialRun() {
  trialLoading.value = true
  try {
    await api(`/employees/${route.params.id}/trial-run`, {
      method: 'POST',
      body: JSON.stringify({ instruction: trialInstruction.value }),
    })
    msg.value = '试跑已派发'
  } catch (e) {
    msg.value = e.message
  } finally {
    trialLoading.value = false
  }
}

async function bindSkill(s) {
  employee.value = await api(`/employees/${route.params.id}/skills`, {
    method: 'POST',
    body: JSON.stringify({
      skill_id: s.id,
      version_id: s.raw?.version_id || s.id,
      slug: s.slug,
      name: s.name,
    }),
  })
}

onMounted(async () => {
  await load()
  try {
    catalog.value = await api('/skills/catalog')
  } catch {
    catalog.value = []
  }
})
</script>

<style scoped>
.header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
.code { color: var(--muted); font-size: 0.9rem; font-weight: 400; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.section { margin-top: 1rem; }
h3 { margin-bottom: 1rem; font-size: 1rem; }
.stage-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.meta { margin-top: 1rem; color: var(--muted); font-size: 0.85rem; }
.msg { margin-top: 0.5rem; color: var(--success); }
.skill-row { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
.bound { margin-top: 1rem; padding-left: 1.25rem; color: var(--muted); }
.muted { color: var(--muted); }
</style>
