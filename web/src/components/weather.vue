<template>
  <div class="panel">
    <div id="demoDiv">
      <div class="temperature">
        <div class="inhouse">
          <img src="../../public/assets/weather/inweather.png" alt="室内温度" />
          <span>湿度</span>
          <h3>{{ humidityText }} %</h3>
        </div>
        <div class="outhouse">
          <img src="../../public/assets/weather/outerweather.png" alt="室外温度" />
          <span>温度</span>
          <h3>{{ temperatureText }} °C</h3>
        </div>
      </div>

      <div class="meta-row">
        <span>{{ weatherText }}</span>
        <span>{{ realtimeStatus }}</span>
        <span>{{ updateLabel }}</span>
      </div>

      <svg class="trend-svg" viewBox="0 0 360 120" preserveAspectRatio="none" aria-label="天气趋势图">
        <line x1="24" y1="12" x2="24" y2="100" stroke="rgba(168,198,232,0.48)" stroke-width="1" />
        <line x1="24" y1="100" x2="344" y2="100" stroke="rgba(168,198,232,0.48)" stroke-width="1" />
        <polyline :points="humidityLine" fill="none" stroke="#53d5a5" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
        <polyline :points="temperatureLine" fill="none" stroke="#f8cb71" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      </svg>

      <div class="weather">
        <div class="day" v-for="(item, index) in day" :key="index">
          <h4>{{ item.date.substring(5) }}</h4>
          <img :src="getimg(item.dayweather)" />
          <span>{{ item.nighttemp }} ~ {{ item.daytemp }} °C</span>
        </div>
      </div>
    </div>
    <div class="panel-footer"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import axios from 'axios'
import { useAlarmStore } from '@/stores/alarm'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

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
  createTime: string
}

interface TrendPoint {
  time: number
  temperature: number
  humidity: number
}

const alarmStore = useAlarmStore()
const appStore = useAppStore()
const userStore = useUserStore()
const { getFutureWeather } = storeToRefs(alarmStore)

const day = computed<WeatherDay[]>(() => getFutureWeather.value)

const weatherText = ref('--')
const updateLabel = ref('--')
const isServerFresh = ref(false)
const targetTemperature = ref(24)
const targetHumidity = ref(52)
const displayTemperature = ref(24)
const displayHumidity = ref(52)
const trend = ref<TrendPoint[]>([])

const POLL_MS = 60 * 1000
const TOLERANCE_MS = 60 * 1000
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
  const { data } = await axios.get('/api/v1/monitor')
  const list = data?.data || []
  return list[0]?.id || 0
}

const applyFreshData = (data: WeatherData) => {
  targetTemperature.value = toNumber(data.temperature, targetTemperature.value)
  targetHumidity.value = toNumber(data.humidity, targetHumidity.value)
  weatherText.value = data.weather || '--'
  updateLabel.value = data.createTime || '--'
  isServerFresh.value = true
}

const applyFallbackData = () => {
  targetTemperature.value = randomDrift(targetTemperature.value, 15, 38)
  targetHumidity.value = randomDrift(targetHumidity.value, 20, 95)
  weatherText.value = weatherText.value === '--' ? '晴' : weatherText.value
  updateLabel.value = `${new Date().toLocaleTimeString()} (本地平滑补偿)`
  isServerFresh.value = false
}

const fetchWeatherData = async () => {
  try {
    const monitorId = await ensureMonitorId()
    if (!monitorId) {
      applyFallbackData()
      return
    }
    const response = await axios.get(`/api/v1/weather/newest/${monitorId}`, {
      headers: {
        Authorization: userStore.token,
      },
    })
    const payload: WeatherData | null = response?.data?.code === '00000' ? response.data.data : null
    if (payload && isFresh(payload.createTime)) {
      applyFreshData(payload)
      return
    }
    applyFallbackData()
  } catch {
    applyFallbackData()
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
const realtimeStatus = computed(() => (isServerFresh.value ? '后端实时' : '本地平滑补偿'))

const getimg = (state: string): string => {
  if (state === '多云') return require('../../public/assets/weather/cloud.png')
  if (state === '小雨') return require('../../public/assets/weather/smallrain.png')
  if (state === '中雨') return require('../../public/assets/weather/midrain.png')
  if (state === '大雨') return require('../../public/assets/weather/bigrain.png')
  if (state === '阴') return require('../../public/assets/weather/overcastsky.png')
  if (state === '暴雨') return require('../../public/assets/weather/rainstorm.png')
  if (state === '雷阵雨') return require('../../public/assets/weather/thundershower.png')
  return require('../../public/assets/weather/sun.png')
}

onMounted(() => {
  fetchWeatherData()
  smoothStep()
  pollTimer = window.setInterval(fetchWeatherData, POLL_MS)
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
  color: #4B9DD1;
}

.outhouse h3 {
  color: #A04157;
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
  margin: 0 auto;
  margin-bottom: 0.3rem;
}

h4 {
  font-size: 1.7rem;
  margin-bottom: 0.5rem;
}
</style>
