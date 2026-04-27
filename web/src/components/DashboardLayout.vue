<template>
  <div class="dash">
    <header class="head">
      <div class="brand-copy">
        <div class="brand-mark" aria-hidden="true">
          <span></span>
        </div>
        <div>
          <h1>社区智眼</h1>
          <p>AI 驱动的智慧社区安防态势感知平台</p>
        </div>
      </div>
      <div class="pill pill-weather">当前天气：多云 26C / 湿度58% / AQI 72</div>
      <div class="pill pill-duty">值班状态：<span class="status-online">在线</span></div>
      <div class="pill pill-time">{{ nowTime }}</div>
      <button class="top-user user-entry" type="button" @click="$emit('open-profile')">
        <div class="avatar">安防</div>
        <div class="meta">
          <strong>张三</strong>
          <span>社区安防值班员</span>
        </div>
      </button>
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
  min-height: 100vh;
  min-height: 100dvh;
  height: auto;
  grid-template-rows: auto minmax(0, 1fr);
  align-content: start;
  overflow: visible;
}

.head {
  grid-template-columns: 1fr auto auto auto auto;
  gap: 12px;
}

.brand-copy {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.brand-mark {
  position: relative;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(126, 232, 255, 0.34);
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.36), transparent 24%),
    linear-gradient(135deg, rgba(126, 232, 255, 0.92), rgba(66, 121, 255, 0.86));
  box-shadow:
    0 18px 32px rgba(60, 138, 255, 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.brand-mark::before,
.brand-mark::after,
.brand-mark span {
  content: '';
  position: absolute;
  inset: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid rgba(5, 22, 41, 0.45);
}

.brand-mark::before {
  width: 28px;
  height: 28px;
}

.brand-mark::after {
  width: 16px;
  height: 16px;
}

.brand-mark span {
  width: 6px;
  height: 6px;
  background: rgba(5, 22, 41, 0.85);
  border: none;
}

.pill-weather,
.pill-duty,
.pill-time {
  align-self: stretch;
  display: inline-flex;
  align-items: center;
}

.status-online {
  color: var(--ok);
  font-weight: 700;
}

.user-entry {
  position: static;
  justify-self: end;
  min-width: auto;
  grid-template-columns: 36px auto;
  gap: 10px;
  padding: 6px 10px;
  cursor: pointer;
  appearance: none;
  width: auto;
  text-align: left;
}

.user-entry .meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-entry .meta strong {
  color: #f3f8ff;
  font-size: 13px;
  font-weight: 600;
}

.user-entry .meta span {
  color: var(--sub);
  font-size: 11px;
}

.top-user {
  border-radius: 18px;
}

.top-user .meta {
  white-space: nowrap;
}

.top-user .avatar {
  width: 36px;
  height: 36px;
  font-size: 11px;
  border-radius: 12px;
}

.user-entry:hover {
  border-color: rgba(126, 232, 255, 0.42);
  transform: translateY(-1px);
}

@media (max-width: 1240px) {
  .head {
    grid-template-columns: 1fr;
  }

  .brand-copy {
    align-items: flex-start;
  }

  .user-entry {
    position: static;
    justify-self: stretch;
  }
}

@media (max-width: 760px) {
  .brand-copy {
    gap: 12px;
  }

  .brand-mark {
    width: 46px;
    height: 46px;
  }
}
</style>
