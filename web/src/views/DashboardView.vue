<script setup lang="ts">
import AppIcon from '../components/AppIcon.vue'
import LineChart from '../components/LineChart.vue'
import MetricCard from '../components/MetricCard.vue'
import StatusBadge from '../components/StatusBadge.vue'
import type { Alert, Detection, Overview, Page, Recommendation, Role } from '../types'

defineProps<{ role: Role; overview: Overview; detections: Detection[]; alerts: Alert[]; recommendations: Recommendation[] }>()
const emit = defineEmits<{ go: [page: Page] }>()
const fmt = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
</script>

<template>
  <div class="page-stack">
    <section class="hero-panel">
      <div>
        <span class="eyebrow">{{ role === 'admin' ? 'PLATFORM OVERVIEW' : 'TODAY AT A GLANCE' }}</span>
        <h2>{{ role === 'admin' ? '全局运行态势' : '环境状态，一眼掌握' }}</h2>
        <p>{{ overview.open_alert_count ? `有 ${overview.open_alert_count} 条预警等待确认，建议优先复核。` : '当前没有待确认预警，监测系统运行平稳。' }}</p>
      </div>
      <button class="button button--accent" @click="emit('go', overview.open_alert_count ? 'alerts' : 'monitor')">
        {{ overview.open_alert_count ? '处理预警' : '开始监测' }}<AppIcon name="arrow" :size="17" />
      </button>
    </section>

    <section class="metric-grid" aria-label="核心指标">
      <MetricCard label="检测记录" :value="overview.total_detections" note="当前可见范围" />
      <MetricCard label="平均浓度" :value="`${overview.average_ppm.toFixed(1)} ppm`" note="基于历史记录" />
      <MetricCard label="待确认预警" :value="overview.open_alert_count" note="需要人工复核" :tone="overview.open_alert_count ? 'warning' : 'good'" />
      <MetricCard label="在线设备" :value="`${overview.online_devices} / 3`" note="设备连接状态" tone="good" />
    </section>

    <section class="content-grid content-grid--wide">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">CONCENTRATION</span><h3>近期浓度趋势</h3></div><span class="panel-value">峰值 {{ overview.peak_ppm.toFixed(1) }} ppm</span></div>
        <LineChart :values="overview.trend.map(item => item.value)" :labels="overview.trend.map(item => fmt(item.label))" unit="ppm" />
      </article>
      <article class="panel action-panel">
        <div class="panel-heading"><div><span class="eyebrow">NEXT BEST ACTION</span><h3>{{ role === 'admin' ? '运行建议' : '为你推荐' }}</h3></div></div>
        <button v-for="item in recommendations" :key="item.module" class="recommendation" @click="emit('go', item.module as Page)">
          <span class="recommendation__score">{{ Math.round(item.score * 100) }}</span>
          <span><b>{{ item.title }}</b><small>{{ item.reason }}</small></span><AppIcon name="arrow" :size="16" />
        </button>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">RECENT ACTIVITY</span><h3>最近检测</h3></div><button class="text-button" @click="emit('go', 'analytics')">查看全部</button></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>时间</th><th>气体 / 设备</th><th>浓度</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="record in detections.slice(0, 5)" :key="record.id"><td>{{ fmt(record.created_at) }}</td><td><b>{{ record.gas_type }}</b><small>{{ record.device_id }}</small></td><td>{{ record.concentration_ppm.toFixed(1) }} ppm</td><td><StatusBadge :status="record.status" /></td></tr>
              <tr v-if="!detections.length"><td colspan="4" class="empty-cell">暂无检测记录</td></tr>
            </tbody>
          </table>
        </div>
      </article>
      <article class="panel risk-panel">
        <div class="risk-orbit" :class="{ 'risk-orbit--alert': overview.open_alert_count }"><span>{{ overview.open_alert_count ? '需关注' : '平稳' }}</span></div>
        <div><span class="eyebrow">RISK STATUS</span><h3>环境风险状态</h3><p>{{ overview.open_alert_count ? '检测到未闭环预警，请检查设备现场并完成确认。' : '未发现未处理的超限事件，请继续保持常规监测。' }}</p></div>
      </article>
    </section>
  </div>
</template>
