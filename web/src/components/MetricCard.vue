<script setup lang="ts">
defineProps<{ label: string; value: string | number; note: string; tone?: 'default' | 'warning' | 'good' }>()
</script>

<template>
  <article class="metric-card" :class="`metric-card--${tone ?? 'default'}`">
    <div class="metric-card__top"><span>{{ label }}</span><i></i></div>
    <strong>{{ value }}</strong>
    <p>{{ note }}</p>
  </article>
</template>
