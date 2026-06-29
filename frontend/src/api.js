const TOKEN_KEY = 'dw_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

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

export const EMPLOYEE_TYPE_LABELS = {
  twitter_operator: '运营号',
  twitter_engagement: '互动号',
}

export const STAGE_LABELS = {
  recruiting: '招募中',
  training: '培训中',
  ready: '待上岗',
  active: '在岗',
  suspended: '已暂停',
}

export const NAV = [
  { path: '/', label: '总览' },
  { path: '/recruit', label: '招募中心' },
  { path: '/train', label: '培训中心' },
  { path: '/roster', label: '员工名册' },
  { path: '/tasks', label: '任务中心' },
  { path: '/logs', label: '执行日志' },
]
