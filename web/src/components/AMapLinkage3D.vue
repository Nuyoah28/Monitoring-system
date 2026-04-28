<template>
  <div class="amap-shell">
    <div ref="mapRef" class="amap-root"></div>
    <div v-if="loadError" class="amap-error">地图加载失败，请检查网络或高德 Key 配置</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { amapConfig, type FixedMapPoint, type LngLat } from '@/config/config'

interface MapPointItem {
  id?: number | string
  monitorId?: number | string
  title: string
  camera: string
  department?: string
  className: string
  streamUrl?: string
  longitude?: number
  latitude?: number
  style?: {
    left?: string
    top?: string
  }
}

interface AlarmCountItem {
  camera: string
  count: number
}

type AMapLike = any

const props = defineProps<{
  points: MapPointItem[]
  alarmCounts?: AlarmCountItem[]
}>()

const emit = defineEmits<{
  (e: 'point-click', point: MapPointItem): void
}>()

const AMAP_KEY = amapConfig.key
const DEFAULT_CENTER: LngLat = amapConfig.defaultCenter
const FIXED_POINTS: FixedMapPoint[] = [...amapConfig.fixedPoints]
const AMAP_VERSION = amapConfig.version

const mapRef = ref<HTMLDivElement | null>(null)
const loadError = ref(false)
const isLoadingAmap = ref(false)
let mapInstance: AMapLike = null
let markers: AMapLike[] = []
let detachRuntimeGuards: (() => void) | null = null

const pluginsList = ['AMap.Scale']

const parsePercent = (input?: string) => {
  if (!input || !input.endsWith('%')) return null
  const value = Number.parseFloat(input)
  return Number.isFinite(value) ? value : null
}

const buildFallbackLngLat = (index: number): [number, number] => {
  if (index < FIXED_POINTS.length) {
    const fixed = FIXED_POINTS[index]
    return [fixed.longitude, fixed.latitude]
  }
  const dynamicIndex = index - FIXED_POINTS.length
  const cols = 4
  const row = Math.floor(dynamicIndex / cols)
  const col = dynamicIndex % cols
  const xOffset = (col - (cols - 1) / 2) * 0.00045
  const yOffset = (1.5 - row) * 0.00033
  return [DEFAULT_CENTER[0] + xOffset, DEFAULT_CENTER[1] + yOffset]
}

const normalizeLngLat = (point: MapPointItem, index: number): [number, number] => {
  if (typeof point.longitude === 'number' && typeof point.latitude === 'number') {
    return [point.longitude, point.latitude]
  }

  const left = parsePercent(point.style?.left)
  const top = parsePercent(point.style?.top)
  if (left !== null && top !== null) {
    const lng = DEFAULT_CENTER[0] - 0.02 + (left / 100) * 0.04
    const lat = DEFAULT_CENTER[1] - 0.015 + ((100 - top) / 100) * 0.03
    return [lng, lat]
  }

  return buildFallbackLngLat(index)
}

const loadAmapScript = async () => {
  if ((window as any).AMap) return
  isLoadingAmap.value = true

  await new Promise<void>((resolve, reject) => {
    const existed = document.getElementById('amap-jsapi-v2') as HTMLScriptElement | null
    if (existed) {
      existed.addEventListener('load', () => resolve(), { once: true })
      existed.addEventListener('error', () => reject(new Error('AMap script load failed')), { once: true })
      return
    }

    const script = document.createElement('script')
    script.id = 'amap-jsapi-v2'
    script.charset = 'utf-8'
    script.async = true
    script.defer = true
    script.crossOrigin = 'anonymous'
    script.src = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${AMAP_KEY}&plugin=${pluginsList.join(',')}`
    script.onload = () => {
      isLoadingAmap.value = false
      resolve()
    }
    script.onerror = () => {
      isLoadingAmap.value = false
      reject(new Error('AMap script load failed'))
    }
    document.head.appendChild(script)
  })
}

const installRuntimeGuards = () => {
  const onError = (event: ErrorEvent) => {
    const file = event.filename || ''
    const message = event.message || ''
    const isAmapError = file.includes('webapi.amap.com') || (message === 'Script error.' && isLoadingAmap.value)
    if (!isAmapError) return
    loadError.value = true
    isLoadingAmap.value = false
    event.preventDefault()
    event.stopImmediatePropagation()
  }

  const onReject = (event: PromiseRejectionEvent) => {
    const reason = String(event.reason || '')
    if (!reason.includes('AMap') && !reason.includes('webapi.amap.com')) return
    loadError.value = true
    isLoadingAmap.value = false
    event.preventDefault()
  }

  window.addEventListener('error', onError, true)
  window.addEventListener('unhandledrejection', onReject)
  detachRuntimeGuards = () => {
    window.removeEventListener('error', onError, true)
    window.removeEventListener('unhandledrejection', onReject)
    detachRuntimeGuards = null
  }
}

const clearMarkers = () => {
  if (!mapInstance || !markers.length) return
  mapInstance.remove(markers)
  markers = []
}

const getAlarmCount = (cameraName: string): number => {
  if (!props.alarmCounts || !cameraName) return 0
  const normalize = (value: string) => String(value || '').replace(/\s+/g, '').toLowerCase()
  const current = normalize(cameraName)
  const found = props.alarmCounts.find((item) => normalize(item.camera) === current) ||
    props.alarmCounts.find((item) => {
      const target = normalize(item.camera)
      return current.includes(target) || target.includes(current)
    })
  return found?.count || 0
}

const renderMarkers = () => {
  if (!mapInstance || !(window as any).AMap) return
  clearMarkers()

  const AMap = (window as any).AMap
  const pointsToRender: MapPointItem[] = (props.points && props.points.length)
    ? props.points
    : FIXED_POINTS.map(item => ({
      title: item.title,
      camera: item.camera,
      className: 'fixed',
      longitude: item.longitude,
      latitude: item.latitude,
    }))

  markers = pointsToRender.map((point, index) => {
    const position = normalizeLngLat(point, index)
    const alarmCount = getAlarmCount(point.camera)

    const markerContent = document.createElement('div')
    markerContent.className = 'marker-wrapper'

    if (alarmCount > 0) {
      markerContent.innerHTML = `
        <div class="marker-dot breathing">
          <span class="marker-count">${alarmCount > 99 ? '99+' : alarmCount}</span>
        </div>
      `
    } else {
      markerContent.innerHTML = `
        <div class="marker-dot normal"></div>
      `
    }

    const marker = new AMap.Marker({
      position,
      title: point.title,
      offset: new AMap.Pixel(-6, -6),
      content: markerContent,
    })
    marker.setLabel({
      direction: 'right',
      offset: new AMap.Pixel(12, 0),
      content: `<span style="color:#16a34a;font-size:12px;white-space:nowrap;">${point.camera || point.title || `监测点 ${index + 1}`}</span>`,
    })
    marker.on('click', () => emit('point-click', point))
    return marker
  })

  mapInstance.add(markers)
  if (markers.length > 1 && typeof mapInstance.setFitView === 'function') {
    mapInstance.setFitView(markers, false, [36, 36, 36, 36])
    return
  }
  mapInstance.setCenter(DEFAULT_CENTER)
  mapInstance.setZoom(19)
}

const initMap = async () => {
  if (!mapRef.value) return
  await loadAmapScript()
  const AMap = (window as any).AMap

  mapInstance = new AMap.Map(mapRef.value, {
    viewMode: '3D',
    zooms: [3, 22],
    zoom: 19,
    pitch: 45,
    rotation: 0,
    center: DEFAULT_CENTER,
    resizeEnable: true,
    mapStyle: 'amap://styles/normal',
  })

  if (AMap.ControlBar) {
    mapInstance.addControl(new AMap.ControlBar({ position: { right: '10px', top: '10px' } }))
  }
  if (AMap.Scale) {
    mapInstance.addControl(new AMap.Scale())
  }
  renderMarkers()
  window.setTimeout(() => {
    if (mapInstance && typeof mapInstance.resize === 'function') {
      mapInstance.resize()
    }
  }, 120)
}

onMounted(() => {
  installRuntimeGuards()
  initMap().catch((err) => {
    loadError.value = true
    isLoadingAmap.value = false
    console.error('AMap init failed:', err)
  })
})

watch(
  () => props.points,
  () => {
    renderMarkers()
  },
  { deep: true },
)

watch(
  () => props.alarmCounts,
  () => {
    renderMarkers()
  },
  { deep: true },
)

onUnmounted(() => {
  clearMarkers()
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
  if (detachRuntimeGuards) {
    detachRuntimeGuards()
  }
})
</script>

<style scoped>
.amap-shell {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.amap-root {
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.amap-error {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #d6e6ff;
  background: rgba(10, 27, 47, 0.72);
  font-size: 12px;
}

.amap-root :deep(.amap-point-dot) {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.9);
  background: radial-gradient(circle at 35% 35%, #7fcbff, #2e86d1);
  box-shadow: 0 0 10px rgba(99, 184, 255, 0.82);
}

.amap-root :deep(.amap-logo),
.amap-root :deep(.amap-copyright) {
  opacity: 0.8;
}

.amap-root :deep(.marker-wrapper) {
  position: relative;
  width: 20px;
  height: 20px;
}

.amap-root :deep(.marker-dot) {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 10px rgba(99, 184, 255, 0.82);
}

.amap-root :deep(.marker-dot.normal) {
  background: radial-gradient(circle at 35% 35%, #7fcbff, #2e86d1);
}

.amap-root :deep(.marker-dot.breathing) {
  background: radial-gradient(circle at 35% 35%, #ff6b6b, #c92a2a);
  animation: breathe 2s ease-in-out infinite;
}

.amap-root :deep(.marker-dot.breathing::after) {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: rgba(255, 107, 107, 0.4);
  animation: pulse 2s ease-in-out infinite;
  z-index: -1;
}

.amap-root :deep(.marker-count) {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

@keyframes breathe {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.15);
    opacity: 0.85;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.8);
    opacity: 0;
  }
}
</style>
