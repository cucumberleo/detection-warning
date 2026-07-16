<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '../api'
import LineChart from '../components/LineChart.vue'
import StatusBadge from '../components/StatusBadge.vue'
import type { Detection, Device, GasType } from '../types'

const props = defineProps<{ devices: Device[] }>()
const emit = defineEmits<{ completed: [detection: Detection] }>()
const deviceId = ref('dev-01')
const gasType = ref<GasType>('NH3')
const scenario = ref<'safe' | 'warning'>('warning')
const detecting = ref(false)
const result = ref<Detection | null>(null)
const error = ref('')
const selectedDevice = computed(() => props.devices.find(device => device.id === deviceId.value))

async function startDetection() {
  detecting.value = true
  error.value = ''
  result.value = null
  try {
    await new Promise(resolve => setTimeout(resolve, 450))
    result.value = await api.simulate({ device_id: deviceId.value, gas_type: gasType.value, scenario: scenario.value })
    emit('completed', result.value)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '检测失败'
  } finally {
    detecting.value = false
  }
}
</script>

<template>
  <div class="page-stack">
    <section class="monitor-layout">
      <article class="panel monitor-control">
        <div class="panel-heading"><div><span class="eyebrow">LIVE DETECTION</span><h3>实时监测</h3></div><span class="connection-state"><i></i>{{ selectedDevice?.status === 'online' ? '设备就绪' : '等待连接' }}</span></div>
        <p class="section-copy">选择设备和气体场景，平台会模拟完整的信号处理、浓度换算、落库与预警判定链路。</p>
        <form class="form-stack" @submit.prevent="startDetection">
          <label><span>监测设备</span><select v-model="deviceId"><option v-for="device in devices" :key="device.id" :value="device.id" :disabled="device.status === 'offline'">{{ device.name }} · {{ device.location }}{{ device.status === 'offline' ? '（离线）' : '' }}</option></select></label>
          <div class="form-row"><label><span>目标气体</span><select v-model="gasType"><option>NH3</option><option>Toluene</option><option>HCHO</option><option>TEA</option></select></label><label><span>演示场景</span><select v-model="scenario"><option value="safe">安全浓度</option><option value="warning">超限浓度</option></select></label></div>
          <div class="device-inline" v-if="selectedDevice"><span><i class="signal-bars"></i><b>信号质量 {{ selectedDevice.signal_quality }}%</b></span><small>{{ selectedDevice.material }}</small></div>
          <button class="button button--primary button--large" :disabled="detecting || selectedDevice?.status !== 'online'"><span v-if="detecting" class="spinner"></span>{{ detecting ? '正在分析信号…' : '开始一次监测' }}</button>
        </form>
        <p v-if="error" class="error-message" role="alert">{{ error }}</p>
      </article>

      <article class="panel live-panel">
        <div class="panel-heading"><div><span class="eyebrow">SENSOR CURRENT</span><h3>传感器响应曲线</h3></div><span class="panel-value">{{ result ? result.curve.unit : 'nA' }}</span></div>
        <div v-if="detecting" class="detecting-state"><div class="scan-line"></div><span>采集与滤波处理中</span></div>
        <LineChart v-else :values="result?.curve.values ?? []" :labels="result ? [String(result.curve.time[0]), String(result.curve.time.at(-1))] : []" unit="nA" :height="260" />
        <div v-if="result" class="result-strip">
          <div><span>识别结果</span><strong>{{ result.gas_type }}</strong></div><div><span>浓度</span><strong>{{ result.concentration_ppm.toFixed(1) }} <small>ppm</small></strong></div><div><span>置信度</span><strong>{{ Math.round(result.confidence * 100) }}%</strong></div><div><span>判定</span><StatusBadge :status="result.status" /></div>
        </div>
        <div v-else-if="!detecting" class="chart-placeholder"><span>等待检测数据</span><small>完成一次监测后显示响应曲线与判定结果</small></div>
      </article>
    </section>

    <section class="panel pipeline-panel">
      <div class="panel-heading"><div><span class="eyebrow">PROCESSING PIPELINE</span><h3>算法处理链路</h3></div><span class="panel-value">baseline-web-v1</span></div>
      <ol class="pipeline"><li><span>01</span><b>信号采集</b><small>时序电流输入</small></li><li><span>02</span><b>噪声抑制</b><small>中值与均值滤波</small></li><li><span>03</span><b>特征提取</b><small>基线与峰谷匹配</small></li><li><span>04</span><b>浓度换算</b><small>标定参数反演</small></li><li><span>05</span><b>风险判定</b><small>阈值与事件落库</small></li></ol>
    </section>
  </div>
</template>
