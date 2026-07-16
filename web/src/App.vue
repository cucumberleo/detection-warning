<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from './api'
import AppIcon from './components/AppIcon.vue'
import AdminView from './views/AdminView.vue'
import AlertsView from './views/AlertsView.vue'
import AnalyticsView from './views/AnalyticsView.vue'
import AssistantView from './views/AssistantView.vue'
import DashboardView from './views/DashboardView.vue'
import MonitorView from './views/MonitorView.vue'
import type { Alert, AlertRule, Detection, Device, GasType, Overview, Page, PlatformUser, Recommendation, Role, SessionUser } from './types'

const role = ref<Role | null>(null)
const page = ref<Page>('dashboard')
const session = ref<SessionUser | null>(null)
const loading = ref(false)
const error = ref('')
const toast = ref('')
const overview = ref<Overview>({ total_detections: 0, warning_count: 0, open_alert_count: 0, online_devices: 0, total_devices: 0, average_ppm: 0, peak_ppm: 0, gas_counts: {}, trend: [] })
const detections = ref<Detection[]>([])
const alerts = ref<Alert[]>([])
const devices = ref<Device[]>([])
const users = ref<PlatformUser[]>([])
const rules = ref({} as Record<GasType, AlertRule>)
const recommendations = ref<Recommendation[]>([])
const summary = ref('')

const userNav: Array<{ page: Page; label: string }> = [
  { page: 'dashboard', label: '概览' }, { page: 'monitor', label: '检测控制' },
  { page: 'alerts', label: '预警中心' }, { page: 'analytics', label: '历史分析' },
  { page: 'assistant', label: 'AI 助手' },
]
const adminNav: Array<{ page: Page; label: string }> = [
  { page: 'dashboard', label: '全局概览' }, { page: 'monitor', label: '检测控制' },
  { page: 'alerts', label: '预警管理' }, { page: 'analytics', label: '数据分析' },
  { page: 'resources', label: '用户与设备' }, { page: 'assistant', label: 'AI 助手' },
]
const navigation = computed(() => role.value === 'admin' ? adminNav : userNav)
const pageTitle = computed(() => navigation.value.find(item => item.page === page.value)?.label ?? '工作台')

function notify(message: string) {
  toast.value = message
  window.setTimeout(() => { if (toast.value === message) toast.value = '' }, 2800)
}

async function loadData(silent = false) {
  if (!role.value) return
  if (!silent) loading.value = true
  error.value = ''
  try {
    const nextRules = role.value === 'admin' ? api.rules() : Promise.resolve({} as Record<GasType, AlertRule>)
    const [nextOverview, nextDetections, nextAlerts, nextDevices, loadedRules, nextRecommendations, nextSummary] = await Promise.all([
      api.overview(), api.detections(), api.alerts(), api.devices(), nextRules,
      api.recommendations(), api.summary(),
    ])
    overview.value = nextOverview
    detections.value = nextDetections
    alerts.value = nextAlerts
    devices.value = nextDevices
    rules.value = loadedRules
    recommendations.value = nextRecommendations
    summary.value = nextSummary.summary
    users.value = role.value === 'admin' ? await api.users() : []
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '平台数据加载失败'
  } finally {
    loading.value = false
  }
}

async function enter(nextRole: Role) {
  loading.value = true
  error.value = ''
  try {
    const response = await api.login(nextRole)
    role.value = nextRole
    session.value = response.user
    page.value = 'dashboard'
    await loadData()
  } catch (cause) {
    api.logout()
    role.value = null
    error.value = cause instanceof Error ? cause.message : '登录失败'
    loading.value = false
  }
}

function leave() {
  api.logout()
  role.value = null
  session.value = null
  page.value = 'dashboard'
  error.value = ''
}

async function onDetectionCompleted() {
  await loadData(true)
  notify('检测完成，历史与预警状态已更新')
}

async function acknowledge(alertId: string) {
  try {
    await api.acknowledge(alertId)
    await loadData(true)
    notify('预警已确认并记录处理时间')
  } catch (cause) {
    notify(cause instanceof Error ? cause.message : '确认失败')
  }
}

function updateRules(nextRules: Record<GasType, AlertRule>) {
  rules.value = nextRules
  notify('预警阈值已保存')
}
</script>

<template>
  <div v-if="!role" class="login-page">
    <section class="login-story">
      <div class="brand brand--light"><span class="brand-mark"><i></i><i></i><i></i></span><span>气体智测<small>GAS SENSE PLATFORM</small></span></div>
      <div class="login-story__copy"><span class="eyebrow eyebrow--light">PHOTOVOLTAIC SELF-POWERED SENSOR</span><h1>让每一次微弱响应，<br /><em>都成为清晰的判断。</em></h1><p>将设备、检测响应曲线、信号处理、历史分析与预警闭环整合在一个现代 Web 工作台中。</p></div>
      <div class="sensor-visual" aria-hidden="true"><div class="sensor-visual__grid"></div><svg viewBox="0 0 800 220"><path d="M0 140 C80 125 120 155 180 135 S280 112 330 128 S420 178 470 105 S565 40 620 90 S715 164 800 62"/><path class="sensor-visual__echo" d="M0 150 C80 135 120 165 180 145 S280 122 330 138 S420 188 470 115 S565 50 620 100 S715 174 800 72"/></svg></div>
      <footer><span>BASELINE-WEB-V1</span><span>FASTAPI · VUE 3 · SQLITE</span></footer>
    </section>
    <section class="login-panel">
      <div class="login-panel__inner"><span class="eyebrow">SELECT WORKSPACE</span><h2>选择演示身份</h2><p>两种身份共享同一数据源，服务端按演示令牌限制可见范围和操作入口。</p>
        <div class="role-list">
          <button class="role-option" :disabled="loading" @click="enter('user')"><span class="role-option__icon"><AppIcon name="monitor" :size="25" /></span><span><b>普通用户</b><small>监测授权设备、处理个人预警与查看趋势</small></span><AppIcon name="arrow" /></button>
          <button class="role-option" :disabled="loading" @click="enter('admin')"><span class="role-option__icon role-option__icon--admin"><AppIcon name="resources" :size="25" /></span><span><b>平台管理员</b><small>管理全局设备、用户权限与预警阈值</small></span><AppIcon name="arrow" /></button>
        </div>
        <p v-if="error" class="error-message" role="alert">{{ error }}</p>
        <div v-if="loading" class="login-loading"><span class="spinner"></span>正在进入工作台…</div>
        <div class="demo-note"><i></i><span><b>演示环境</b>当前使用本地 SQLite 与可复现模拟曲线，不代表真实安全检测结论。</span></div>
      </div>
    </section>
  </div>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark"><i></i><i></i><i></i></span><span>气体智测<small>GAS SENSE</small></span></div>
      <nav aria-label="主导航"><button v-for="item in navigation" :key="item.page" :class="{ active: page === item.page }" @click="page = item.page"><AppIcon :name="item.page" />{{ item.label }}<span v-if="item.page === 'alerts' && overview.open_alert_count" class="nav-count">{{ overview.open_alert_count }}</span></button></nav>
      <div class="sidebar__bottom"><div class="identity-avatar">{{ session?.name.slice(0, 1) }}</div><div><b>{{ session?.name }}</b><small>{{ role === 'admin' ? '平台管理员' : '普通用户' }}</small></div><button class="icon-button" aria-label="切换身份" title="切换身份" @click="leave"><AppIcon name="arrow" /></button></div>
    </aside>

    <main class="workspace">
      <header class="topbar"><div><span class="eyebrow">{{ role === 'admin' ? 'ADMIN CONSOLE' : 'USER CONSOLE' }}</span><h1>{{ pageTitle }}</h1></div><div class="topbar__actions"><span class="system-health"><i></i>系统运行正常</span><button class="icon-button icon-button--border" aria-label="刷新数据" title="刷新数据" @click="loadData()"><AppIcon name="refresh" /></button></div></header>
      <div v-if="loading" class="loading-page"><span class="spinner spinner--dark"></span><p>正在同步平台数据…</p></div>
      <div v-else-if="error" class="error-state"><span>!</span><h2>数据暂时不可用</h2><p>{{ error }}</p><button class="button button--primary" @click="loadData()">重新加载</button></div>
      <Transition name="page" mode="out-in">
        <div v-if="!loading && !error" :key="page">
          <DashboardView v-if="page === 'dashboard'" :role="role" :overview="overview" :detections="detections" :alerts="alerts" :recommendations="recommendations" @go="page = $event" />
          <MonitorView v-else-if="page === 'monitor'" :devices="devices" @completed="onDetectionCompleted" />
          <AlertsView v-else-if="page === 'alerts'" :role="role" :alerts="alerts" :rules="rules" @acknowledge="acknowledge" @rules-updated="updateRules" />
          <AnalyticsView v-else-if="page === 'analytics'" :detections="detections" :summary="summary" />
          <AdminView v-else-if="page === 'resources'" :users="users" :devices="devices" />
          <AssistantView v-else :role="role" />
        </div>
      </Transition>
    </main>

    <nav class="mobile-nav" aria-label="移动端导航"><button v-for="item in navigation" :key="item.page" :class="{ active: page === item.page }" @click="page = item.page"><AppIcon :name="item.page" :size="19" /><span>{{ item.label }}</span></button></nav>
    <Transition name="toast"><div v-if="toast" class="toast" role="status"><i></i>{{ toast }}</div></Transition>
  </div>
</template>
