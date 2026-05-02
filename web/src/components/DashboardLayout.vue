<template>
  <div class="dash">
    <header class="head">
      <div class="brand-copy">
        <div class="brand-logo-box" aria-hidden="true">
          <img class="brand-logo" src="/assets/logo.png" alt="" />
        </div>
        <div>
          <h1>社区智眼</h1>
          <p>智慧社区监控预警平台</p>
        </div>
      </div>
      <div class="pill pill-weather">{{ weatherPillText }}</div>
      <div class="pill pill-duty">值守：<span class="status-online">在线</span></div>
      <div class="pill pill-time">{{ nowTime }}</div>
      <button class="top-user user-entry" type="button" @click="$emit('open-profile')">
        <div class="avatar">值守</div>
        <div class="meta">
          <strong>社区安防值班员</strong>
          <span>安防控制台</span>
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
const nowTime = ref('系统时间 --')
const weatherSummary = ref('天气：加载中...')
const timer = ref<number | null>(null)
const weatherTimer = ref<number | null>(null)
const pad = (n: number) => String(n).padStart(2, '0')

const weatherPillText = computed(() => weatherSummary.value)

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
      weatherSummary.value = '天气：未选择监控点'
      return
    }

    const response = await axios.get(`/weather/newest/${monitorId}`)
    const payload = response?.data?.code === '00000' ? response.data.data : null
    if (!payload) {
      weatherSummary.value = '天气：暂无数据'
      return
    }

    const regionName = payload.regionName ? `${payload.regionName} / ` : ''
    const weather = payload.weather || '--'
    const temperature = Number(payload.temperature ?? 0).toFixed(1)
    const humidity = Math.round(Number(payload.humidity ?? 0))
    weatherSummary.value = `天气：${regionName}${weather} ${temperature}℃ / 湿度 ${humidity}%`
  } catch {
    weatherSummary.value = '天气：加载失败'
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
  min-height: 0;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  grid-template-rows: auto minmax(0, 1fr);
  align-content: stretch;
  overflow: hidden;
}

.head {
  grid-template-columns: minmax(0, 1fr) auto auto auto auto;
  gap: 10px;
}

.brand-copy {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-logo-box {
  position: relative;
  z-index: 1;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  border-radius: 14px;
  border: 1px solid rgba(126, 232, 255, 0.48);
  background:
    radial-gradient(circle at 28% 24%, rgba(126, 232, 255, 0.28), transparent 46%),
    linear-gradient(135deg, rgba(25, 70, 112, 0.98), rgba(8, 24, 43, 0.94));
  box-shadow:
    0 14px 26px rgba(60, 138, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 0 0 1px rgba(255, 255, 255, 0.03);
  display: grid;
  place-items: center;
  overflow: hidden;
}

.brand-logo {
  width: 34px;
  height: 34px;
  display: block;
  object-fit: contain;
  opacity: 1;
  filter:
    drop-shadow(0 0 12px rgba(126, 232, 255, 0.34))
    drop-shadow(0 0 4px rgba(255, 255, 255, 0.12));
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
  grid-template-columns: 32px auto;
  gap: 8px;
  padding: 5px 9px;
  cursor: pointer;
  appearance: none;
  width: auto;
  text-align: left;
  border-color: rgba(126, 232, 255, 0.38);
  background:
    radial-gradient(circle at 20% 18%, rgba(126, 232, 255, 0.1), transparent 36%),
    linear-gradient(180deg, rgba(22, 56, 89, 0.96), rgba(10, 28, 46, 0.92));
  box-shadow:
    0 10px 22px rgba(4, 12, 20, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.user-entry .meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-entry .meta strong {
  color: #f7fcff;
  font-size: 13px;
  font-weight: 600;
}

.user-entry .meta span {
  color: rgba(214, 230, 255, 0.78);
  font-size: 11px;
}

.top-user {
  border-radius: 15px;
}

.top-user .meta {
  white-space: nowrap;
}

.top-user .avatar {
  width: 32px;
  height: 32px;
  font-size: 10px;
  border-radius: 10px;
  border: 1px solid rgba(126, 232, 255, 0.36);
  background:
    radial-gradient(circle at 35% 30%, rgba(126, 232, 255, 0.72), rgba(35, 85, 126, 0.86)),
    linear-gradient(180deg, rgba(37, 98, 146, 0.96), rgba(18, 58, 92, 0.96));
  box-shadow:
    0 0 12px rgba(126, 232, 255, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.user-entry:hover {
  border-color: rgba(126, 232, 255, 0.72);
  box-shadow:
    0 14px 24px rgba(31, 135, 206, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

@media (max-width: 1240px) {
  .head {
    grid-template-columns: minmax(0, 1fr) auto auto auto auto;
  }

  .brand-copy {
    align-items: center;
  }

  .pill-weather {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .pill-time {
    max-width: 210px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .user-entry {
    position: static;
    justify-self: end;
  }
}

@media (max-width: 980px) {
  .head {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .brand-copy {
    grid-column: 1 / -1;
  }

  .pill-weather,
  .pill-duty,
  .pill-time,
  .user-entry {
    justify-self: stretch;
  }

  .pill-weather,
  .pill-time {
    max-width: none;
  }
}

@media (max-width: 760px) {
  .brand-copy {
    gap: 10px;
  }

  .brand-logo-box {
    width: 38px;
    height: 38px;
    flex-basis: 38px;
  }

  .brand-logo {
    width: 30px;
    height: 30px;
  }
}
</style>
