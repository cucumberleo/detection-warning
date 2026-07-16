<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '../api'
import LineChart from '../components/LineChart.vue'
import StatusBadge from '../components/StatusBadge.vue'
import type { Detection, GasType } from '../types'

const props = defineProps<{ detections: Detection[]; summary: string }>()
const filter = ref<'all' | GasType>('all')
const exporting = ref(false)
const error = ref('')
const filtered = computed(() => filter.value === 'all' ? props.detections : props.detections.filter(item => item.gas_type === filter.value))
const chronological = computed(() => [...filtered.value].reverse())
const fmt = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))

async function exportCsv() {
  exporting.value = true
  error.value = ''
  try {
    const blob = await api.exportCsv()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'gas-detections.csv'
    link.click()
    URL.revokeObjectURL(url)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '导出失败'
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="page-stack">
    <section class="analysis-hero">
      <div><span class="eyebrow">INSIGHT SUMMARY</span><h2>历史数据摘要</h2><p>{{ summary || '正在整理历史检测数据…' }}</p></div>
      <button class="button button--accent" :disabled="exporting" @click="exportCsv">{{ exporting ? '导出中…' : '导出 CSV' }}</button>
      <p v-if="error" class="error-message" role="alert">{{ error }}</p>
    </section>
    <article class="panel">
      <div class="panel-heading panel-heading--wrap"><div><span class="eyebrow">HISTORY TREND</span><h3>浓度变化</h3></div><div class="segmented"><button v-for="item in ['all', 'NH3', 'Toluene', 'HCHO', 'TEA']" :key="item" :class="{ active: filter === item }" @click="filter = item as typeof filter">{{ item === 'all' ? '全部' : item }}</button></div></div>
      <LineChart :values="chronological.map(item => item.concentration_ppm)" :labels="chronological.map(item => fmt(item.created_at))" unit="ppm" :height="270" />
    </article>
    <article class="panel">
      <div class="panel-heading"><div><span class="eyebrow">DETECTION ARCHIVE</span><h3>检测记录</h3></div><span class="panel-value">{{ filtered.length }} 条</span></div>
      <div class="table-wrap"><table><thead><tr><th>时间</th><th>气体 / 设备</th><th>浓度</th><th>响应值</th><th>置信度</th><th>算法</th><th>状态</th></tr></thead><tbody><tr v-for="record in filtered" :key="record.id"><td>{{ fmt(record.created_at) }}</td><td><b>{{ record.gas_type }}</b><small>{{ record.device_id }}</small></td><td>{{ record.concentration_ppm.toFixed(1) }} ppm</td><td>{{ record.response.toFixed(3) }}</td><td>{{ Math.round(record.confidence * 100) }}%</td><td><code>{{ record.algorithm_version }}</code></td><td><StatusBadge :status="record.status" /></td></tr><tr v-if="!filtered.length"><td colspan="7" class="empty-cell">当前筛选条件下暂无记录</td></tr></tbody></table></div>
    </article>
  </div>
</template>
