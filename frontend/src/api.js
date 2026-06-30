const TOKEN_KEY = 'dw_token'
const TEAM_KEY = 'dw_team_id'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(TEAM_KEY)
}

export function getTeamId() {
  const v = localStorage.getItem(TEAM_KEY)
  return v ? Number(v) : null
}

export function setTeamId(id) {
  localStorage.setItem(TEAM_KEY, String(id))
}

export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const teamId = getTeamId()
  if (teamId) headers['X-Team-Id'] = String(teamId)

  const res = await fetch(`/api${path}`, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  if (res.status === 204) return null
  return res.json()
}

export async function loadTeams() {
  const teams = await api('/teams')
  if (!teams.length) return teams
  const current = getTeamId()
  const exists = teams.some((t) => t.id === current)
  if (!exists) {
    const personal = teams.find((t) => t.is_personal) || teams[0]
    setTeamId(personal.id)
  }
  return teams
}

export const EMPLOYEE_TYPE_LABELS = {
  twitter_operator: '运营号',
  twitter_engagement: '互动号',
}

export const TASK_STATUS_LABELS = {
  pending: '待执行',
  running: '执行中',
  completed: '已完成',
  failed: '失败',
}

export const STAGE_LABELS = {
  training: '待上岗',
  ready: '待上岗',
  active: '可干活',
  suspended: '已暂停',
}

export const NAV = [
  { path: '/', label: '总览' },
  { path: '/recruit', label: '员工管理' },
  { path: '/tasks', label: '批量派活' },
  { path: '/logs', label: '执行日志' },
]

export const ADMIN_NAV = { path: '/admin', label: '管理台' }

export async function loadCurrentUser() {
  return api('/auth/me')
}
