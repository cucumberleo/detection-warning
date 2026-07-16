<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { api } from '../api'
import type { Role } from '../types'

const props = defineProps<{ role: Role }>()
interface Message { type: 'user' | 'assistant'; text: string; tools?: string[]; range?: string }
const messages = ref<Message[]>([{ type: 'assistant', text: '你好，我可以基于当前可见数据回答预警、浓度趋势和设备状态问题。' }])
const input = ref('')
const sending = ref(false)
const chat = ref<HTMLElement>()
const suggestions = ['当前有哪些待确认预警？', '最近浓度趋势如何？', '哪些设备在线？']

async function send(message = input.value) {
  const text = message.trim()
  if (!text || sending.value) return
  messages.value.push({ type: 'user', text })
  input.value = ''
  sending.value = true
  await nextTick()
  chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  try {
    const response = await api.chat(props.role, text)
    messages.value.push({ type: 'assistant', text: response.answer, tools: response.tools, range: response.data_range })
  } catch (cause) {
    messages.value.push({ type: 'assistant', text: cause instanceof Error ? cause.message : '助手暂时不可用' })
  } finally {
    sending.value = false
    await nextTick()
    chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>

<template>
  <section class="assistant-layout">
    <aside class="assistant-context"><span class="eyebrow">DATA-GROUNDED</span><h2>气体监测助手</h2><p>回答仅使用当前角色可见的检测、预警和设备统计，不提供未经数据支持的安全结论。</p><div class="assistant-scope"><span>当前身份</span><b>{{ role === 'admin' ? '管理员 · 全局数据' : '普通用户 · 授权设备' }}</b></div><div><span class="eyebrow">试着这样问</span><button v-for="suggestion in suggestions" :key="suggestion" @click="send(suggestion)">{{ suggestion }}</button></div></aside>
    <article class="panel chat-panel"><div ref="chat" class="chat-messages" aria-live="polite"><div v-for="(message, index) in messages" :key="index" class="chat-message" :class="`chat-message--${message.type}`"><span>{{ message.type === 'assistant' ? 'AI' : '你' }}</span><div><p>{{ message.text }}</p><small v-if="message.tools">工具：{{ message.tools.join(' · ') }}<br />范围：{{ message.range }}</small></div></div><div v-if="sending" class="chat-message chat-message--assistant"><span>AI</span><div class="typing"><i></i><i></i><i></i></div></div></div><form class="chat-compose" @submit.prevent="send()"><label class="sr-only" for="chat-input">输入问题</label><input id="chat-input" v-model="input" placeholder="询问预警、趋势或设备状态…" maxlength="500" /><button class="button button--primary" :disabled="sending || !input.trim()">发送</button></form></article>
  </section>
</template>
