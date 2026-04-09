<template>
  <div class="dash">
    <header class="head">
      <div>
        <h1>社区智眼</h1>
      </div>
      <div class="pill">当前天气：多云 26C / 湿度58% / AQI 72</div>
      <div class="pill">值班状态：<span style="color:var(--ok);">在线</span></div>
      <div class="pill">{{ nowTime }}</div>
      <div class="top-user" @click="$emit('open-profile')" style="cursor:pointer">
        <div class="avatar">安防</div>
        <div class="meta">张三 - 社区安防值班员</div>
      </div>
    </header>

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
.dash {
  height: 100vh;
  height: 100dvh;
  min-height: 100vh;
  min-height: 100dvh;
  grid-template-rows: auto 1fr;
  overflow: hidden;
}

.head {
  grid-template-columns: 1fr auto auto auto auto;
  gap: 8px;
}

.top-user {
  position: static;
  justify-self: end;
  min-width: auto;
  grid-template-columns: 36px auto;
  gap: 6px;
  padding: 4px 6px;
}

.top-user .meta {
  line-height: 1.2;
  white-space: nowrap;
}

.top-user .avatar {
  width: 36px;
  height: 36px;
  font-size: 11px;
}

@media (max-width: 1240px) {
  .head {
    grid-template-columns: 1fr;
  }

  .top-user {
    position: static;
  }
}
</style>
