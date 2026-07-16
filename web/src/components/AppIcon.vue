<script setup lang="ts">
defineProps<{ name: string; size?: number }>()
</script>

<template>
  <svg class="app-icon" :width="size ?? 20" :height="size ?? 20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'dashboard'">
      <rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>
    </template>
    <path v-else-if="name === 'monitor'" d="M3 12h3l2.2-6 3.4 12 2.8-8 1.8 4H21"/>
    <template v-else-if="name === 'alerts'"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></template>
    <template v-else-if="name === 'analytics'"><path d="M4 19V9M10 19V4M16 19v-7M22 19H2"/></template>
    <template v-else-if="name === 'resources'"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M8 9h8M8 14h5"/></template>
    <template v-else-if="name === 'assistant'"><path d="M12 3a7 7 0 0 0-7 7v5a3 3 0 0 0 3 3h1l3 3 3-3h1a3 3 0 0 0 3-3v-5a7 7 0 0 0-7-7Z"/><circle cx="9" cy="11" r="1" fill="currentColor" stroke="none"/><circle cx="15" cy="11" r="1" fill="currentColor" stroke="none"/></template>
    <template v-else-if="name === 'refresh'"><path d="M20 6v5h-5M4 18v-5h5"/><path d="M18.5 9A7 7 0 0 0 6 6.5L4 11M5.5 15A7 7 0 0 0 18 17.5l2-4.5"/></template>
    <path v-else-if="name === 'arrow'" d="m9 18 6-6-6-6"/>
    <template v-else><circle cx="12" cy="12" r="9"/><path d="M12 8v4l3 2"/></template>
  </svg>
</template>
