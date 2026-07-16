<script setup lang="ts">
import StatusBadge from '../components/StatusBadge.vue'
import type { Device, PlatformUser } from '../types'

defineProps<{ users: PlatformUser[]; devices: Device[] }>()
</script>

<template>
  <div class="page-stack">
    <section class="content-grid">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">DEVICE FLEET</span><h3>设备状态</h3></div><span class="panel-value">{{ devices.filter(item => item.status === 'online').length }} 台在线</span></div>
        <div class="device-grid"><article v-for="device in devices" :key="device.id" class="device-card"><div><span class="device-dot" :class="device.status"></span><StatusBadge :status="device.status" /></div><h4>{{ device.name }}</h4><p>{{ device.material }}</p><dl><div><dt>位置</dt><dd>{{ device.location }}</dd></div><div><dt>信号质量</dt><dd>{{ device.signal_quality }}%</dd></div></dl></article></div>
      </article>
    </section>
    <article class="panel">
      <div class="panel-heading"><div><span class="eyebrow">ACCESS CONTROL</span><h3>用户与设备授权</h3></div><span class="panel-value">Demo RBAC 范围</span></div>
      <div class="table-wrap"><table><thead><tr><th>用户</th><th>角色</th><th>授权设备</th><th>状态</th></tr></thead><tbody><tr v-for="user in users" :key="user.id"><td><b>{{ user.name }}</b><small>{{ user.id }}</small></td><td>{{ user.role === 'admin' ? '管理员' : '普通用户' }}</td><td><span class="token" v-for="device in user.devices" :key="device">{{ device }}</span></td><td><StatusBadge :status="user.status" /></td></tr></tbody></table></div>
    </article>
  </div>
</template>
