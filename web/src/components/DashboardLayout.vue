<template>
  <div class="dash">
    <header class="head">
      <div>
        <h1>智慧社区安防系统 </h1>
      </div>
      <div class="pill">值班状态：<span style="color:var(--ok);">在线</span></div>
      <div class="pill">{{ nowTime }}</div>
      <div class="top-user" @click="$emit('open-profile')" style="cursor:pointer">
        <div class="avatar">安防</div>
        <div class="meta">张三<br />社区安防值班员 / 视频调度</div>
      </div>
    </header>

    <div class="status-grid">
      <div class="pill">算法端：运行中</div>
      <div class="pill">摄像头在线：24 / 26</div>
      <div class="pill">今日处置完成率：81%</div>
      <div class="pill">当前天气：多云 26C / 湿度58% / AQI 72</div>
    </div>

    <section class="grid">
      <slot />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const nowTime = ref('系统时间 --')
const timer = ref<number | null>(null)
const pad = (n: number) => String(n).padStart(2, '0')

const clock = () => {
  const d = new Date()
  nowTime.value =
    '系统时间 ' +
    d.getFullYear() +
    '-' +
    pad(d.getMonth() + 1) +
    '-' +
    pad(d.getDate()) +
    ' ' +
    pad(d.getHours()) +
    ':' +
    pad(d.getMinutes()) +
    ':' +
    pad(d.getSeconds())
}

onMounted(() => {
  clock()
  timer.value = window.setInterval(clock, 1000)
})

onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
})
</script>

<style scoped>
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

@media (max-width: 1240px) {
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
