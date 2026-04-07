<template>
  <div class="amap-shell">
    <div ref="mapRef" class="amap-root"></div>
    <div v-if="loadError" class="amap-error">地图加载失败，请检查网络或高德 Key 配置</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

interface MapPointItem {
  title: string
  camera: string
  className: string
  streamUrl?: string
  longitude?: number
  latitude?: number
  style?: {
    left?: string
    top?: string
  }
}

interface FixedPointItem {
  title: string
  camera: string
  longitude: number
  latitude: number
}

type AMapLike = any

const props = defineProps<{
  points: MapPointItem[]
}>()

const emit = defineEmits<{
  (e: 'point-click', point: MapPointItem): void
}>()

const AMAP_KEY = 'd8250863b36679ef600aa2c28bb90ab0'
const DEFAULT_CENTER: [number, number] = [117.01187872107023, 39.1443426861701]
const FIXED_POINTS: FixedPointItem[] = [
  {
    title: '三号楼监测点',
    camera: '三号楼监测点',
    longitude: 117.01280287680027,
    latitude: 39.144625636831215,
  },
  {
    title: '九号楼监测点',
    camera: '九号楼监测点',
    longitude: 117.0122804687718,
    latitude: 39.143983680256035,
  },
  {
    title: '南门监测点',
    camera: '南门监测点',
    longitude: 117.01346569650909,
    latitude: 39.14355698741387,
  },
]
const mapRef = ref<HTMLDivElement | null>(null)
const loadError = ref(false)
const isLoadingAmap = ref(false)
let mapInstance: AMapLike = null
let markers: AMapLike[] = []
let detachRuntimeGuards: (() => void) | null = null

const pluginsList = ['AMap.Scale']
const AMAP_VERSION = '1.4.15'

const parsePercent = (input?: string) => {
  if (!input || !input.endsWith('%')) return null
  const value = Number.parseFloat(input)
  return Number.isFinite(value) ? value : null
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

  const fallback: Array<[number, number]> = FIXED_POINTS.map(item => [item.longitude, item.latitude])
  return fallback[index % fallback.length]
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

const renderMarkers = () => {
  if (!mapInstance || !(window as any).AMap) return
  clearMarkers()

  const AMap = (window as any).AMap
  const pointsToRender: MapPointItem[] = FIXED_POINTS.map(item => ({
    title: item.title,
    camera: item.camera,
    className: 'fixed',
    longitude: item.longitude,
    latitude: item.latitude,
  }))

  markers = pointsToRender.map((point, index) => {
    const position = normalizeLngLat(point, index)
    const marker = new AMap.Marker({
      position,
      title: point.title,
      offset: new AMap.Pixel(-6, -6),
    })
    marker.setLabel({
      direction: 'right',
      offset: new AMap.Pixel(6, 0),
      content: `<span style="color:#d6ecff;font-size:12px;white-space:nowrap;">${point.title}</span>`,
    })
    marker.on('click', () => emit('point-click', point))
    return marker
  })

  mapInstance.add(markers)
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
</style>
