import type { Alert, AlertRule, Detection, Device, GasType, Overview, PlatformUser, Recommendation, Role, SessionUser } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
interface Envelope<T> { status: string; data: T }

let demoToken = ''

function authorizedHeaders(extra: HeadersInit | undefined): HeadersInit {
  const headers = new Headers(extra)
  headers.set('Content-Type', 'application/json')
  if (demoToken) headers.set('Authorization', `Bearer ${demoToken}`)
  return headers
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: authorizedHeaders(options.headers),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = typeof payload.detail === 'string' ? payload.detail : '请求失败，请稍后重试'
    throw new Error(message)
  }
  return payload as T
}

export const api = {
  login: async (role: Role) => {
    const response = await request<{ status: string; token: string; user: SessionUser }>('/api/demo/login', {
      method: 'POST', body: JSON.stringify({ role }),
    })
    demoToken = response.token
    return response
  },
  logout: () => { demoToken = '' },
  overview: async () => (await request<Envelope<Overview>>('/api/overview')).data,
  detections: async () => (await request<Envelope<Detection[]>>('/api/detections')).data,
  alerts: async () => (await request<Envelope<Alert[]>>('/api/alerts')).data,
  recommendations: async () => (await request<Envelope<Recommendation[]>>('/api/recommendations')).data,
  devices: async () => (await request<Envelope<Device[]>>('/api/devices')).data,
  users: async () => (await request<Envelope<PlatformUser[]>>('/api/admin/users')).data,
  rules: async () => (await request<Envelope<Record<GasType, AlertRule>>>('/api/admin/alert-rules')).data,
  updateRules: async (rules: Partial<Record<GasType, AlertRule>>) => (await request<Envelope<Record<GasType, AlertRule>>>('/api/admin/alert-rules', { method: 'PUT', body: JSON.stringify(rules) })).data,
  simulate: async (payload: { device_id: string; gas_type: GasType; scenario: 'safe' | 'warning' }) => (await request<Envelope<Detection>>('/api/detections/simulate', { method: 'POST', body: JSON.stringify(payload) })).data,
  acknowledge: async (alertId: string) => (await request<Envelope<Alert>>(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' })).data,
  summary: () => request<{ status: string; summary: string; source: string }>('/api/history/summary'),
  chat: async (message: string) => (await request<Envelope<{ answer: string; tools: string[]; data_range: string }>>('/api/agent/chat', { method: 'POST', body: JSON.stringify({ message }) })).data,
  exportCsv: async () => {
    const response = await fetch(`${API_BASE}/api/detections/export`, { headers: authorizedHeaders(undefined) })
    if (!response.ok) throw new Error('导出失败，请重新登录后再试')
    return response.blob()
  },
}
