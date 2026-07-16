import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App.vue'
import { api } from './api'

const overview = {
  total_detections: 0, warning_count: 0, open_alert_count: 0,
  online_devices: 1, total_devices: 1, average_ppm: 0, peak_ppm: 0,
  gas_counts: {}, trend: [],
}

function response(data: unknown) {
  return Promise.resolve(new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  }))
}

function installFetchMock() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input, options) => {
    const path = String(input)
    if (path.endsWith('/api/demo/login')) {
      const role = JSON.parse(String(options?.body)).role as 'user' | 'admin'
      return response({ status: 'success', token: `demo-${role}`, user: { id: `${role}-1`, name: role === 'admin' ? '平台管理员' : '张同学', role, devices: ['dev-01'], status: 'active' } })
    }
    if (path.endsWith('/api/overview')) return response({ status: 'success', data: overview })
    if (path.endsWith('/api/detections')) return response({ status: 'success', data: [] })
    if (path.endsWith('/api/alerts')) return response({ status: 'success', data: [] })
    if (path.endsWith('/api/devices')) return response({ status: 'success', data: [] })
    if (path.endsWith('/api/recommendations')) return response({ status: 'success', data: [] })
    if (path.endsWith('/api/history/summary')) return response({ status: 'success', summary: '暂无记录', source: 'local' })
    if (path.endsWith('/api/admin/alert-rules')) return response({ status: 'success', data: {} })
    if (path.endsWith('/api/admin/users')) return response({ status: 'success', data: [] })
    return Promise.reject(new Error(`Unexpected request: ${path}`))
  })
}

describe('App role workspaces', () => {
  beforeEach(() => {
    api.logout()
    vi.restoreAllMocks()
  })

  it('binds user data requests to the demo token and avoids admin APIs', async () => {
    const fetchMock = installFetchMock()
    const wrapper = mount(App)
    await wrapper.findAll('button.role-option')[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('环境状态，一眼掌握')
    const protectedCalls = fetchMock.mock.calls.filter(([input]) => !String(input).endsWith('/api/demo/login'))
    expect(protectedCalls.every(([, options]) => new Headers(options?.headers).get('Authorization') === 'Bearer demo-user')).toBe(true)
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/api/admin/'))).toBe(false)
  })

  it('keeps all six administrator tasks reachable in mobile navigation', async () => {
    installFetchMock()
    const wrapper = mount(App)
    await wrapper.findAll('button.role-option')[1].trigger('click')
    await flushPromises()

    const labels = wrapper.findAll('.mobile-nav button').map(button => button.text())
    expect(labels).toHaveLength(6)
    expect(labels).toContain('AI 助手')
  })
})
