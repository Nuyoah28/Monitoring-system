<template>
  <div class="dash">
    <header class="head">
      <div class="brand-copy">
        <div class="brand-mark" aria-hidden="true">
          <span></span>
        </div>
        <div>
          <h1>Community Vision</h1>
          <p>AI-driven community safety dashboard</p>
        </div>
      </div>
      <div class="pill pill-weather">{{ weatherPillText }}</div>
      <div class="pill pill-duty">Duty: <span class="status-online">Online</span></div>
      <div class="pill pill-time">{{ nowTime }}</div>
      <button class="top-user user-entry" type="button" @click="$emit('open-profile')">
        <div class="avatar">OPS</div>
        <div class="meta">
          <strong>Operator</strong>
          <span>Security Console</span>
        </div>
      </button>
    </header>

    <section class="grid">
      <slot />
    </section>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const nowTime = ref('System Time --')
const weatherSummary = ref('Weather: loading...')
const timer = ref<number | null>(null)
const weatherTimer = ref<number | null>(null)
const pad = (n: number) => String(n).padStart(2, '0')

const weatherPillText = computed(() => weatherSummary.value)

const clock = () => {
  const d = new Date()
  nowTime.value =
    'System Time ' +
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

const ensureMonitorId = async () => {
  if (appStore.getMonitorId && appStore.getMonitorId !== 0) return appStore.getMonitorId
  const { data } = await axios.get('/monitor')
  const list = data?.data || []
  const monitorId = Number(list[0]?.id || 0)
  if (monitorId) {
    appStore.setMonitorId(monitorId)
  }
  return monitorId
}

const fetchWeatherSummary = async () => {
  try {
    const monitorId = await ensureMonitorId()
    if (!monitorId) {
      weatherSummary.value = 'Weather: no monitor selected'
      return
    }

    const response = await axios.get(`/weather/newest/${monitorId}`)
    const payload = response?.data?.code === '00000' ? response.data.data : null
    if (!payload) {
      weatherSummary.value = 'Weather: no data'
      return
    }

    const regionName = payload.regionName ? `${payload.regionName} / ` : ''
    const weather = payload.weather || '--'
    const temperature = Number(payload.temperature ?? 0).toFixed(1)
    const humidity = Math.round(Number(payload.humidity ?? 0))
    weatherSummary.value = `Weather: ${regionName}${weather} ${temperature}C / RH ${humidity}%`
  } catch {
    weatherSummary.value = 'Weather: load failed'
  }
}

onMounted(() => {
  clock()
  timer.value = window.setInterval(clock, 1000)
  void fetchWeatherSummary()
  weatherTimer.value = window.setInterval(() => {
    void fetchWeatherSummary()
  }, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (timer.value) {
    clearInterval(timer.value)
  }
  if (weatherTimer.value) {
    clearInterval(weatherTimer.value)
  }
})

watch(
  () => appStore.getMonitorId,
  (monitorId, prevMonitorId) => {
    if (monitorId && monitorId !== prevMonitorId) {
      void fetchWeatherSummary()
    }
  }
)
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
