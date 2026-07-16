<script setup lang="ts">
const props = defineProps<{ status: string }>()
const labels: Record<string, string> = {
  safe: '安全', warning: '预警', open: '待确认', acknowledged: '已确认',
  high: '高风险', medium: '中风险', low: '低风险', online: '在线', offline: '离线', active: '正常',
}
</script>

<template><span class="status-badge" :class="`status-badge--${props.status}`">{{ labels[props.status] ?? props.status }}</span></template>
