<template>
  <div class="panel">
    <div id="demoDiv">
      <div class="temperature">
        <div class="inhouse">
          <img src="../../public/assets/weather/inweather.png" alt="humidity" />
          <span>Humidity</span>
          <h3>{{ humidityText }} %</h3>
        </div>
        <div class="outhouse">
          <img src="../../public/assets/weather/outerweather.png" alt="temperature" />
          <span>Temp</span>
          <h3>{{ temperatureText }} C</h3>
        </div>
      </div>

      <div class="meta-row">
        <span>{{ regionText }}</span>
        <span>{{ weatherText }}</span>
        <span>{{ realtimeStatus }}</span>
        <span>{{ updateLabel }}</span>
      </div>

      <svg class="trend-svg" viewBox="0 0 360 120" preserveAspectRatio="none" aria-label="weather trend">
        <line x1="24" y1="12" x2="24" y2="100" stroke="rgba(168,198,232,0.48)" stroke-width="1" />
        <line x1="24" y1="100" x2="344" y2="100" stroke="rgba(168,198,232,0.48)" stroke-width="1" />
        <polyline :points="humidityLine" fill="none" stroke="#53d5a5" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
        <polyline :points="temperatureLine" fill="none" stroke="#f8cb71" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>

      <div class="weather">
        <div class="day" v-for="(item, index) in day" :key="index">
          <h4>{{ item.date.substring(5) }}</h4>
          <img :src="getimg(item.dayweather)" />
          <span>{{ item.nighttemp }} ~ {{ item.daytemp }} C</span>
        </div>
      </div>
    </div>
    <div class="panel-footer"></div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'

interface WeatherDay {
  date: string
  dayweather: string
  daytemp: string
  nighttemp: string
}

interface WeatherData {
  monitorId: number
  temperature: number
  humidity: number
  weather: string
  regionName?: string
  createTime: string
}

interface TrendPoint {
  time: number
  temperature: number
  humidity: number
}

const appStore = useAppStore()
const day = ref<WeatherDay[]>([])
const weatherText = ref('--')
const regionText = ref('--')
const updateLabel = ref('--')
const dataMode = ref<'live' | 'cached' | 'fallback'>('fallback')
const targetTemperature = ref(24)
const targetHumidity = ref(52)
const displayTemperature = ref(24)
const displayHumidity = ref(52)
const trend = ref<TrendPoint[]>([])

const POLL_MS = 60 * 1000
const TOLERANCE_MS = 60 * 60 * 1000
const SMOOTH_MS = 2000
const TREND_SIZE = 24

let pollTimer: number | null = null
let smoothTimer: number | null = null

const toNumber = (n: unknown, fallback: number) => {
  const value = Number(n)
  return Number.isFinite(value) ? value : fallback
}

const parseTime = (raw: string | number | Date | undefined) => {
  if (!raw) return null
  const date = raw instanceof Date ? raw : new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

const isFresh = (createTime: string) => {
  const ts = parseTime(createTime)
  if (!ts) return false
  return Math.abs(Date.now() - ts.getTime()) <= TOLERANCE_MS
}

const randomDrift = (value: number, min: number, max: number, span = 1.2) => {
  const next = value + (Math.random() * 2 - 1) * span
  return Math.min(Math.max(next, min), max)
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

const applyCurrentData = (data: WeatherData) => {
  targetTemperature.value = toNumber(data.temperature, targetTemperature.value)
  targetHumidity.value = toNumber(data.humidity, targetHumidity.value)
  weatherText.value = data.weather || '--'
  regionText.value = data.regionName || '--'
  updateLabel.value = data.createTime || '--'
  dataMode.value = isFresh(data.createTime) ? 'live' : 'cached'
}

const applyFallbackCurrent = () => {
  targetTemperature.value = randomDrift(targetTemperature.value, 15, 38)
  targetHumidity.value = randomDrift(targetHumidity.value, 20, 95)
  weatherText.value = weatherText.value === '--' ? '晴' : weatherText.value
  regionText.value = regionText.value === '--' ? '本地缓存' : regionText.value
  updateLabel.value = `${new Date().toLocaleTimeString()} (离线更新)`
  dataMode.value = 'fallback'
}

const buildFallbackForecast = () => {
  const base = new Date()
  const fallbackWeather = weatherText.value === '--' ? '晴' : weatherText.value
  day.value = Array.from({ length: 3 }, (_, idx) => {
    const next = new Date(base)
    next.setDate(base.getDate() + idx)
    const month = String(next.getMonth() + 1).padStart(2, '0')
    const date = String(next.getDate()).padStart(2, '0')
    const high = Math.round(targetTemperature.value + 2 + idx)
    const low = Math.round(targetTemperature.value - 3 + idx)
    return {
      date: `${next.getFullYear()}-${month}-${date}`,
      dayweather: fallbackWeather,
      daytemp: String(high),
      nighttemp: String(low),
    }
  })
}

const fetchWeatherData = async () => {
  try {
    const monitorId = await ensureMonitorId()
    if (!monitorId) {
      applyFallbackCurrent()
      buildFallbackForecast()
      return
    }

    const [currentRes, forecastRes] = await Promise.all([
      axios.get(`/weather/newest/${monitorId}`),
      axios.get(`/weather/forecast/${monitorId}`),
    ])

    const currentPayload: WeatherData | null = currentRes?.data?.code === '00000' ? currentRes.data.data : null
    const forecastPayload: WeatherDay[] = Array.isArray(forecastRes?.data?.data) ? forecastRes.data.data : []

    if (currentPayload) {
      applyCurrentData(currentPayload)
    } else {
      applyFallbackCurrent()
    }

    if (forecastPayload.length) {
      day.value = forecastPayload
    } else {
      buildFallbackForecast()
    }
  } catch {
    applyFallbackCurrent()
    buildFallbackForecast()
  }
}

const smoothStep = () => {
  displayTemperature.value += (targetTemperature.value - displayTemperature.value) * 0.28
  displayHumidity.value += (targetHumidity.value - displayHumidity.value) * 0.28
  const nextPoint: TrendPoint = {
    time: Date.now(),
    temperature: displayTemperature.value,
    humidity: displayHumidity.value,
  }
  trend.value = [...trend.value, nextPoint].slice(-TREND_SIZE)
}

const buildLine = (metric: 'temperature' | 'humidity') => {
  if (!trend.value.length) return ''
  const left = 24
  const right = 344
  const top = 12
  const bottom = 100
  const points = trend.value
  const values = points.map(item => item[metric])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = Math.max(max - min, 1)
  const step = points.length > 1 ? (right - left) / (points.length - 1) : 0
  return points
    .map((item, idx) => {
      const x = left + idx * step
      const y = bottom - ((item[metric] - min) / span) * (bottom - top)
      return `${x},${y}`
    })
    .join(' ')
}

const humidityLine = computed(() => buildLine('humidity'))
const temperatureLine = computed(() => buildLine('temperature'))
const humidityText = computed(() => Math.round(displayHumidity.value))
const temperatureText = computed(() => displayTemperature.value.toFixed(1))
const realtimeStatus = computed(() => {
  if (dataMode.value === 'live') return 'Backend Live'
  if (dataMode.value === 'cached') return 'Backend Cached'
  return 'Local Fallback'
})

const getimg = (state: string): string => {
  const raw = String(state || '')
  const normalized = raw.toLowerCase()
  if (normalized.includes('cloud') || raw.includes('\u591A\u4E91')) {
    return require('../../public/assets/weather/cloud.png')
  }
  if (normalized.includes('light rain') || raw.includes('\u5C0F\u96E8') || raw.includes('\u6BDB\u6BDB\u96E8')) {
    return require('../../public/assets/weather/smallrain.png')
  }
  if (normalized.includes('moderate rain') || raw === '\u96E8') {
    return require('../../public/assets/weather/midrain.png')
  }
  if (normalized.includes('heavy rain') || raw.includes('\u5927\u96E8')) {
    return require('../../public/assets/weather/bigrain.png')
  }
  if (normalized.includes('overcast') || raw.includes('\u9634') || raw.includes('\u96FE')) {
    return require('../../public/assets/weather/overcastsky.png')
  }
  if (normalized.includes('storm') || raw.includes('\u66B4\u96E8')) {
    return require('../../public/assets/weather/rainstorm.png')
  }
  if (normalized.includes('thunder') || raw.includes('\u96F7\u9635\u96E8')) {
    return require('../../public/assets/weather/thundershower.png')
  }
  return require('../../public/assets/weather/sun.png')
}

onMounted(() => {
  void fetchWeatherData()
  smoothStep()
  pollTimer = window.setInterval(() => {
    void fetchWeatherData()
  }, POLL_MS)
  smoothTimer = window.setInterval(smoothStep, SMOOTH_MS)
})

onUnmounted(() => {
  if (pollTimer !== null) window.clearInterval(pollTimer)
  if (smoothTimer !== null) window.clearInterval(smoothTimer)
})
</script>

<style scoped>
#demoDiv {
  width: 100%;
  height: 100%;
  color: white;
}

h2 {
  color: white;
}

.temperature span {
  font-size: 2rem;
  color: white;
  margin-left: 0.5rem;
}

.temperature {
  width: 30rem;
  height: 8rem;
  display: flex;
}

.temperature div {
  width: 50%;
  height: 80%;
  padding-top: 1rem;
}

.inhouse h3 {
  color: #4b9dd1;
}

.outhouse h3 {
  color: #a04157;
}

.temperature img {
  width: 2rem;
  height: 2rem;
}

h3 {
  margin-top: 0.8rem;
  font-size: 2rem;
}

.weather {
  margin-top: 0.8rem;
  width: 100%;
  display: flex;
  color: white;
}

.meta-row {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: rgba(214, 230, 255, 0.9);
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.trend-svg {
  width: 100%;
  height: 110px;
  margin-bottom: 6px;
}

.day {
  flex: 1;
  border-right: 0.25rem solid skyblue;
  font-size: 1.6rem;
}

.day:nth-child(3) {
  border-right: none;
}

.day img {
  display: block;
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto 0.3rem;
}

h4 {
  font-size: 1.7rem;
  margin-bottom: 0.5rem;
}
</style>
