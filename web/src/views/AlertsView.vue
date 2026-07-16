<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { api } from '../api'
import StatusBadge from '../components/StatusBadge.vue'
import type { Alert, AlertRule, GasType, Role } from '../types'

const props = defineProps<{ role: Role; alerts: Alert[]; rules: Record<GasType, AlertRule> }>()
const emit = defineEmits<{ acknowledge: [alertId: string]; rulesUpdated: [rules: Record<GasType, AlertRule>] }>()
const gases: GasType[] = ['NH3', 'Toluene', 'HCHO', 'TEA']
const draft = reactive({} as Record<GasType, AlertRule>)
const saving = ref(false)
const error = ref('')
watch(() => props.rules, value => Object.assign(draft, structuredClone(value)), { immediate: true, deep: true })
const fmt = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))

async function saveRules() {
  saving.value = true
  error.value = ''
  try {
    emit('rulesUpdated', await api.updateRules(draft))
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '保存失败'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page-stack">
    <section class="alert-summary">
      <div><span class="alert-summary__value">{{ alerts.filter(item => item.status === 'open').length }}</span><span>条待确认预警</span></div>
      <p>预警只代表超过当前配置阈值，不替代现场安全判断。请结合设备状态、曲线质量和复测结果处置。</p>
    </section>
    <section class="content-grid" :class="{ 'content-grid--wide': role === 'admin' }">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">ALERT EVENTS</span><h3>{{ role === 'admin' ? '全局预警事件' : '我的预警' }}</h3></div><span class="panel-value">{{ alerts.length }} 条</span></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>发生时间</th><th>气体 / 设备</th><th>浓度</th><th>等级</th><th>状态</th><th></th></tr></thead>
            <tbody>
              <tr v-for="alert in alerts" :key="alert.id"><td>{{ fmt(alert.created_at) }}</td><td><b>{{ alert.gas_type }}</b><small>{{ alert.device_id }}</small></td><td>{{ alert.concentration_ppm.toFixed(1) }} ppm</td><td><StatusBadge :status="alert.severity" /></td><td><StatusBadge :status="alert.status" /></td><td><button v-if="alert.status === 'open'" class="button button--small" @click="emit('acknowledge', alert.id)">确认</button></td></tr>
              <tr v-if="!alerts.length"><td colspan="6" class="empty-cell">当前没有预警事件</td></tr>
            </tbody>
          </table>
        </div>
      </article>

      <article v-if="role === 'admin'" class="panel rules-panel">
        <div class="panel-heading"><div><span class="eyebrow">THRESHOLDS</span><h3>预警阈值</h3></div></div>
        <form class="rule-list" @submit.prevent="saveRules">
          <template v-for="gas in gases" :key="gas">
            <div v-if="draft[gas]" class="rule-row">
              <div><b>{{ gas }}</b><small>浓度达到阈值时创建预警</small></div>
              <label><span class="sr-only">{{ gas }} 阈值</span><input v-model.number="draft[gas].threshold" type="number" min="0.1" max="1000" step="0.1" /><em>ppm</em></label>
              <select v-model="draft[gas].severity" :aria-label="`${gas} 风险等级`"><option value="low">低风险</option><option value="medium">中风险</option><option value="high">高风险</option></select>
            </div>
          </template>
          <p v-if="error" class="error-message">{{ error }}</p>
          <button class="button button--primary" :disabled="saving">{{ saving ? '保存中…' : '保存全部阈值' }}</button>
        </form>
      </article>
    </section>
  </div>
</template>
