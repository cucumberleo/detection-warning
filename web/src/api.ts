import type { Alert, AlertRule, Detection, Device, GasType, Overview, PlatformUser, Recommendation, Role, SessionUser } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? ''
interface Envelope<T> { status: string; data: T }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = typeof payload.detail === 'string' ? payload.detail : '请求失败，请稍后重试'
    throw new Error(message)
  }
  return payload as T
}

export const api = {
  login: (role: Role) => request<{ status: string; token: string; user: SessionUser }>('/api/demo/login', { method: 'POST', body: JSON.stringify({ role }) }),
  overview: async (role: Role) => (await request<Envelope<Overview>>(`/api/overview?role=${role}`)).data,
  detections: async (role: Role) => (await request<Envelope<Detection[]>>(`/api/detections?role=${role}`)).data,
  alerts: async (role: Role) => (await request<Envelope<Alert[]>>(`/api/alerts?role=${role}`)).data,
  recommendations: async (role: Role) => (await request<Envelope<Recommendation[]>>(`/api/recommendations?role=${role}`)).data,
  devices: async () => (await request<Envelope<Device[]>>('/api/admin/devices')).data,
  users: async () => (await request<Envelope<PlatformUser[]>>('/api/admin/users')).data,
  rules: async () => (await request<Envelope<Record<GasType, AlertRule>>>('/api/admin/alert-rules')).data,
  updateRules: async (rules: Partial<Record<GasType, AlertRule>>) => (await request<Envelope<Record<GasType, AlertRule>>>('/api/admin/alert-rules', { method: 'PUT', body: JSON.stringify(rules) })).data,
  simulate: async (payload: { device_id: string; gas_type: GasType; scenario: 'safe' | 'warning' }) => (await request<Envelope<Detection>>('/api/detections/simulate', { method: 'POST', body: JSON.stringify(payload) })).data,
  acknowledge: async (alertId: string) => (await request<Envelope<Alert>>(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' })).data,
  summary: (role: Role) => request<{ status: string; summary: string; source: string }>(`/api/history/summary?role=${role}`),
  chat: async (role: Role, message: string) => (await request<Envelope<{ answer: string; tools: string[]; data_range: string }>>('/api/agent/chat', { method: 'POST', body: JSON.stringify({ role, message }) })).data,
  exportUrl: (role: Role) => `${API_BASE}/api/detections/export?role=${role}`,
}
