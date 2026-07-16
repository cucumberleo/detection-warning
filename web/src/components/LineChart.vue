<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ values: number[]; labels?: string[]; unit?: string; height?: number }>(), {
  labels: () => [], unit: 'ppm', height: 220,
})
const width = 760
const padding = { top: 18, right: 20, bottom: 34, left: 48 }
const min = computed(() => props.values.length ? Math.min(...props.values) : 0)
const max = computed(() => props.values.length ? Math.max(...props.values) : 1)
const range = computed(() => Math.max(max.value - min.value, 0.001))
const coordinates = computed(() => props.values.map((value, index) => {
  const chartWidth = width - padding.left - padding.right
  const chartHeight = props.height - padding.top - padding.bottom
  const x = padding.left + (props.values.length === 1 ? chartWidth / 2 : (index / (props.values.length - 1)) * chartWidth)
  const y = padding.top + (1 - (value - min.value) / range.value) * chartHeight
  return { x, y }
}))
const points = computed(() => coordinates.value.map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '))
const area = computed(() => points.value ? `${padding.left},${props.height - padding.bottom} ${points.value} ${width - padding.right},${props.height - padding.bottom}` : '')
const lastPoint = computed(() => coordinates.value.at(-1))
</script>

<template>
  <div class="line-chart" :style="{ height: `${height}px` }">
    <div v-if="!values.length" class="empty-inline">暂无可绘制数据</div>
    <svg v-else :viewBox="`0 0 ${width} ${height}`" role="img" :aria-label="`趋势图，单位 ${unit}`">
      <defs><linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#46ad7b" stop-opacity=".28"/><stop offset="1" stop-color="#46ad7b" stop-opacity="0"/></linearGradient></defs>
      <g class="chart-grid"><line v-for="step in 5" :key="step" :x1="padding.left" :x2="width - padding.right" :y1="padding.top + ((step - 1) / 4) * (height - padding.top - padding.bottom)" :y2="padding.top + ((step - 1) / 4) * (height - padding.top - padding.bottom)"/></g>
      <text :x="padding.left - 8" :y="padding.top + 4" text-anchor="end">{{ max.toFixed(1) }}</text>
      <text :x="padding.left - 8" :y="height - padding.bottom + 4" text-anchor="end">{{ min.toFixed(1) }}</text>
      <text :x="padding.left" :y="height - 9">{{ labels[0] ?? '开始' }}</text>
      <text :x="width - padding.right" :y="height - 9" text-anchor="end">{{ labels[labels.length - 1] ?? '当前' }}</text>
      <polygon :points="area" fill="url(#chart-fill)"/><polyline :points="points" fill="none" stroke="#207455" stroke-width="3" vector-effect="non-scaling-stroke"/>
      <circle v-if="lastPoint" :cx="lastPoint.x" :cy="lastPoint.y" r="5" fill="#f8fbf9" stroke="#207455" stroke-width="3"/>
    </svg>
  </div>
</template>
