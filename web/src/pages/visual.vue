<template>
  <DashboardLayout @open-profile="goProfile">
    <div class="col left-col">
      <article class="card">
        <h3>告警指标</h3>
        <div class="kpi-grid">
          <div class="kpi" v-for="k in kpis" :key="k.name">
            <div class="name">{{ k.name }}</div>
            <div class="num" :style="{ color: k.color || 'inherit' }">{{ k.value }}</div>
          </div>
        </div>
      </article>

      <article class="card alarm-list-card">
        <AlarmList />
      </article>

      <article class="card pie-card">
        <h3>分类统计图</h3>
        <PieChart1 />
      </article>

    </div>

    <div class="col mid-col">
      <article class="card monitor-main-card">
        <div class="card-head">
          <h3>实时监控</h3>
          <button class="btn view-all-btn" type="button" @click="openMonitorModal">查看全部</button>
        </div>
        <div class="monitor-grid">
          <div
            v-for="tile in cameraTiles"
            :key="tile.name"
            class="video-tile"
            @click="openFocus(tile)"
          >
            <video
              :ref="(el) => setTileVideoRef(tile.name, el as HTMLVideoElement | null)"
              class="tile-video"
              muted
              autoplay
              playsinline
            ></video>
            <div class="tile-overlay">
              <div class="tile-title">{{ tile.name }}</div>
              <div class="tile-sub">{{ tile.streamUrl ? '实时画面' : '未配置流地址' }}</div>
            </div>
          </div>
        </div>
      </article>

      <div class="split-row">
        <article class="card map-card">
          <h3>小区地图及其监测点</h3>
          <div class="map-square">
            <MapPanZoom :points="mapPoints" @point-click="onMapPointClick" />
          </div>
        </article>

        <article class="card slim-card dispatch-card">
          <h3>开放词汇检测下发</h3>
          <div class="slim-line">
            <input
              v-model="keyword"
              placeholder="输入检测目标，回车或点击下发"
              @keyup.enter="pushKeyword()"
            />
            <button class="btn primary" type="button" @click="pushKeyword()">下发词汇</button>
          </div>
          <div class="chip-row">
            <span
              v-for="tag in keywordTags"
              :key="tag"
              class="chip"
              @click="pushKeyword(tag)"
            >
              {{ tag }}
              <i class="close" @click.stop="removeTag(tag)">×</i>
            </span>
          </div>
          <div class="linked-video">
            <video
              ref="linkedVideoRef"
              class="linked-video-player"
              muted
              autoplay
              playsinline
            ></video>
            <div class="linked-video-label">{{ linkedVideo }}</div>
            <div v-if="!linkedStreamUrl" class="linked-video-empty">未配置联动视频流</div>
          </div>
        </article>
      </div>
    </div>

  <div class="col right-col">

      <article class="card env-chart-card">
        <h3>环境质量折线图</h3>
        <div class="chart-wrap">
          <svg width="100%" height="190" viewBox="0 0 300 190" preserveAspectRatio="none" aria-label="天气质量指标折线图">
            <polyline points="18,152 55,138 92,125 129,118 166,110 203,98 240,94 278,88" fill="none" stroke="#63b8ff" stroke-width="2.5" />
            <polyline points="18,146 55,142 92,136 129,128 166,123 203,120 240,112 278,106" fill="none" stroke="#53d5a5" stroke-width="2.5" />
            <polyline points="18,138 55,130 92,126 129,134 166,128 203,122 240,118 278,112" fill="none" stroke="#f8cb71" stroke-width="2.5" />
            <line x1="18" y1="160" x2="282" y2="160" stroke="rgba(168,198,232,0.6)" stroke-width="1" />
            <line x1="18" y1="45" x2="18" y2="160" stroke="rgba(168,198,232,0.6)" stroke-width="1" />
            <text x="6" y="162" fill="#a8c6e8" font-size="9">0</text>
            <text x="4" y="122" fill="#a8c6e8" font-size="9">50</text>
            <text x="2" y="82" fill="#a8c6e8" font-size="9">100</text>
            <text x="0" y="46" fill="#a8c6e8" font-size="9">150</text>
          </svg>
          <div class="legend">
            <span><i class="dot" style="background:#63b8ff;"></i>AQI</span>
            <span><i class="dot" style="background:#53d5a5;"></i>湿度</span>
            <span><i class="dot" style="background:#f8cb71;"></i>PM2.5</span>
          </div>
        </div>
      </article>

      <article class="card">
        <h3>车位检测</h3>
        <div class="kpi-grid">
          <div class="kpi" v-for="p in parking" :key="p.name">
            <div class="name">{{ p.name }}</div>
            <div class="num">{{ p.value }}</div>
          </div>
        </div>
      </article>
    </div>

    <div class="focus-modal" :style="{ display: focusVisible ? 'flex' : 'none' }" :aria-hidden="focusVisible ? 'false' : 'true'">
      <div class="focus-shell">
        <div class="focus-screen">
          <video
            ref="focusVideoRef"
            class="focus-video"
            controls
            muted
            autoplay
            playsinline
          ></video>
          <div v-if="!focusStreamUrl" class="focus-empty">{{ focusText }}</div>
        </div>
        <aside class="focus-panel">
          <h4 class="focus-title">实时调控面板</h4>
          <div class="ctrl-grid">
            <button class="btn" type="button">云台上</button>
            <button class="btn" type="button">云台下</button>
            <button class="btn" type="button">云台左</button>
            <button class="btn" type="button">云台右</button>
            <button class="btn" type="button">变焦+</button>
            <button class="btn" type="button">变焦-</button>
            <button class="btn" type="button">抓拍</button>
            <button class="btn" type="button">录像</button>
          </div>
          <button class="btn primary focus-close" type="button" @click="closeFocus">关闭大屏</button>
        </aside>
      </div>
    </div>

    <div class="focus-modal" :style="{ display: monitorModalVisible ? 'flex' : 'none' }" :aria-hidden="monitorModalVisible ? 'false' : 'true'">
      <div class="monitor-shell">
        <header class="monitor-head">
          <div>
            <h4>全部监控点</h4>
            <p class="muted">查看在线/离线状态，点击可联动大屏</p>
          </div>
          <button class="btn" type="button" @click="closeMonitorModal">关闭</button>
        </header>
        <div class="monitor-list">
          <div
            v-for="item in monitors"
            :key="item.name"
            class="monitor-row"
            @click="openFocus(item)"
          >
            <div>
              <div class="row-title">{{ item.name }}</div>
              <div class="row-sub">{{ item.department || '未标注区域' }}</div>
            </div>
            <span class="status" :class="{ online: item.status === 1 || item.status === 'online' }">
              {{ item.status === 1 || item.status === 'online' ? '在线' : '离线' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </DashboardLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/DashboardLayout.vue'
import { useAlarmStore } from '@/stores/alarm'
import AlarmList from '@/components/alarmlist.vue'
import PieChart1 from '@/components/piechart1.vue'
import MapPanZoom from '@/components/MapPanZoom.vue'
import axios from 'axios'
import flvjs from 'flv.js'
import { rtmpAddressList } from '@/config/config'
import { S } from 'vue-router/dist/router-CWoNjPRp.mjs'

interface MonitorStreamItem {
  id?: number | string
  name: string
  department?: string
  status?: number | string
  streamUrl?: string
}

interface MapPointItem {
  title: string
  camera: string
  className: string
  streamUrl?: string
  style?: {
    left?: string
    top?: string
  }
}

const router = useRouter()
const alarmStore = useAlarmStore()

const focusVisible = ref(false)
const focusText = ref('监控大屏')
const focusStreamUrl = ref('')
const focusVideoRef = ref<HTMLVideoElement | null>(null)
let focusFlvPlayer: flvjs.Player | null = null
const tileVideoRefs = new Map<string, HTMLVideoElement>()
const tileFlvPlayers = new Map<string, flvjs.Player>()
const linkedVideo = ref('联动视频：1号机位 - 北门实时画面')
const linkedStreamUrl = ref('')
const linkedVideoRef = ref<HTMLVideoElement | null>(null)
let linkedFlvPlayer: flvjs.Player | null = null
const monitorModalVisible = ref(false)
const monitors = ref<MonitorStreamItem[]>([])
const keyword = ref('')

const withNoCache = (url: string) => {
  if (!url) return url
  const [base, hash = ''] = url.split('#')
  const connector = base.includes('?') ? '&' : '?'
  const nextUrl = `${base}${connector}_t=${Date.now()}`
  return hash ? `${nextUrl}#${hash}` : nextUrl
}

const kpis = computed(() => {
  const list = alarmStore.getAlarmList || []
  const now = new Date()
  const nowTime = now.getTime()
  const dayMs = 24 * 60 * 60 * 1000

  const parseAlarmTime = (item: any) => {
    const raw = item.date || item.time || item.createTime
    if (!raw) return null
    if (raw instanceof Date) return Number.isNaN(raw.getTime()) ? null : raw

    if (typeof raw === 'number') {
      const date = new Date(raw)
      return Number.isNaN(date.getTime()) ? null : date
    }

    if (typeof raw === 'string') {
      const trimmed = raw.trim()
      if (!trimmed) return null
      const normalized =
        trimmed.includes('T') || trimmed.includes('/') ? trimmed : trimmed.replace(/-/g, '/')
      const date = new Date(normalized)
      return Number.isNaN(date.getTime()) ? null : date
    }

    return null
  }

  const isToday = (date: Date) => {
    return (
      date.getFullYear() === now.getFullYear() &&
      date.getMonth() === now.getMonth() &&
      date.getDate() === now.getDate()
    )
  }

  const today = list.filter(item => {
    const date = parseAlarmTime(item)
    return date ? isToday(date) : false
  }).length

  const recent30Days = list.filter(item => {
    const date = parseAlarmTime(item)
    if (!date) return false
    const diff = nowTime - date.getTime()
    return diff >= 0 && diff <= dayMs * 30
  }).length

  const recentYear = list.filter(item => {
    const date = parseAlarmTime(item)
    if (!date) return false
    const diff = nowTime - date.getTime()
    return diff >= 0 && diff <= dayMs * 365
  }).length

  const pending = list.filter(item => item.deal !== '完成' && item.status !== 1).length
  return [
    { name: '今日告警', value: today },
    { name: '待处理', value: pending, color: '#ff8d8d' },
    { name: '近30天', value: recent30Days },
    { name: '近一年', value: recentYear },
  ]
})

const cameraTiles = ref<MonitorStreamItem[]>([
  { name: '1号机位 - 北门实时画面', streamUrl: rtmpAddressList[1] },
  { name: '2号机位 - 车库入口实时画面', streamUrl: rtmpAddressList[2] },
  { name: '3号机位 - 东侧步道实时画面', streamUrl: rtmpAddressList[3] },
])

const mapPoints = ref<MapPointItem[]>([
  { title: '北门监测点', camera: '1号机位 - 北门实时画面', className: 'p1' },
  { title: '中庭监测点', camera: '3号机位 - 东侧步道实时画面', className: 'p2' },
  { title: '车库监测点', camera: '2号机位 - 车库入口实时画面', className: 'p3' },
])

const keywordTags = ref(['人行道违停', '垃圾袋', '戴帽子的人', '消防通道堵塞'])

const parking = ref([
  { name: '地库 A 区剩余', value: 38 },
  { name: '地库 B 区剩余', value: 21 },
  { name: '地面东侧剩余', value: 15 },
  { name: '地面西侧剩余', value: 9 },
])

const isDev = process.env.NODE_ENV !== 'production'
const debugLog = (...args: any[]) => {
  if (!isDev) return
  console.log('[visual-debug]', ...args)
}

const fetchMonitors = async () => {
  try {
    const [{ data: listRes }, { data: mapRes }] = await Promise.all([
      axios.get('/monitor'),
      axios.get('/monitor/map'),
    ])

    let monitorList: MonitorStreamItem[] = []

    if (listRes.code === '00000') {
      monitorList = (listRes.data || []).map((item: any) => ({
        id: item.id,
        name: item.name,
        department: item.department,
        status: item.status,
        streamUrl:rtmpAddressList[item.id],//根据id获取流地址
        //streamUrl: item.video || item.streamUrl || item.flvUrl || item.rtmpUrl || ''
      }))
      monitors.value = monitorList
      console.log('监控列表：', monitorList)
      if (monitorList.length) {
        cameraTiles.value = monitorList.slice(0, 3)
        if (monitorList[0]) {
          linkedVideo.value = '联动视频：' + monitorList[0].name
          linkedStreamUrl.value = monitorList[0].streamUrl || ''
          nextTick(() => {
            if (linkedStreamUrl.value) {
              initLinkedPlayer(linkedStreamUrl.value)
            }
          })
        }
        nextTick(() => {
          initTilePlayers()
        })
      }
    }

    if (mapRes.code === '00000') {
      const points: Array<{
        id?: number | string
        monitorId?: number | string
        name: string
        location?: string
        longitude?: number
        latitude?: number
      }> = mapRes.data || []
      mapPoints.value = points.slice(0, 3).map((item, idx) => ({
        ...(() => {
          const key = item.monitorId ?? item.id
          const matched =
            monitorList.find(m => key !== undefined && m.id === key) ||
            monitorList[idx] ||
            monitorList.find(m => m.name === item.name) ||
            monitorList.find(m => item.name && m.name.includes(item.name)) ||
            monitorList.find(m => item.name && item.name.includes(m.name))
          return {
            camera: matched?.name || item.name || item.location || `监测点${idx + 1}`,
            streamUrl: matched?.streamUrl || '',
          }
        })(),
        title: item.location || item.name,
        className: `p${idx + 1}`,
        style:
          item.longitude !== undefined && item.latitude !== undefined
            ? { left: `${item.longitude}%`, top: `${item.latitude}%` }
            : undefined,
      }))

      debugLog(
        'map points mapped',
        mapPoints.value.map((point, idx) => ({
          idx,
          title: point.title,
          camera: point.camera,
          streamUrl: point.streamUrl,
        }))
      )
      debugLog(
        'monitor list mapped',
        monitorList.map((item, idx) => ({
          idx,
          id: item.id,
          name: item.name,
          streamUrl: item.streamUrl,
        }))
      )
    }
  } catch (e) {
    // 静态降级
  }
}

const goProfile = () => {
  router.push('/home')
}

const destroyFocusPlayer = () => {
  if (focusFlvPlayer) {
    focusFlvPlayer.unload()
    focusFlvPlayer.destroy()
    focusFlvPlayer = null
  }

  const videoEl = focusVideoRef.value
  if (videoEl) {
    videoEl.pause()
    videoEl.removeAttribute('src')
    videoEl.load()
  }
}

const destroyLinkedPlayer = () => {
  if (linkedFlvPlayer) {
    linkedFlvPlayer.unload()
    linkedFlvPlayer.destroy()
    linkedFlvPlayer = null
  }

  const videoEl = linkedVideoRef.value
  if (videoEl) {
    videoEl.pause()
    videoEl.removeAttribute('src')
    videoEl.load()
  }
}

const initLinkedPlayer = (url: string) => {
  const videoEl = linkedVideoRef.value
  if (!videoEl || !url) return
  const playUrl = withNoCache(url)

  destroyLinkedPlayer()

  if (flvjs.isSupported() && url.includes('.flv')) {
    linkedFlvPlayer = flvjs.createPlayer(
      { type: 'flv', url: playUrl },
      {
        enableStashBuffer: false,
        lazyLoad: false,
        deferLoadAfterSourceOpen: false,
        autoCleanupSourceBuffer: true,
      } as any,
    )
    linkedFlvPlayer.attachMediaElement(videoEl)
    linkedFlvPlayer.load()
    linkedFlvPlayer.play().catch(() => {})
    return
  }

  videoEl.src = playUrl
  videoEl.play().catch(() => {})
}

const setTileVideoRef = (name: string, el: HTMLVideoElement | null) => {
  if (el) {
    tileVideoRefs.set(name, el)
    return
  }
  tileVideoRefs.delete(name)
}

const destroyTilePlayers = () => {
  tileFlvPlayers.forEach(player => {
    player.unload()
    player.destroy()
  })
  tileFlvPlayers.clear()

  tileVideoRefs.forEach(videoEl => {
    videoEl.pause()
    videoEl.removeAttribute('src')
    videoEl.load()
  })
}

const initTilePlayers = () => {
  destroyTilePlayers()

  cameraTiles.value.forEach(tile => {
    const videoEl = tileVideoRefs.get(tile.name)
    const url = tile.streamUrl || ''
    const playUrl = withNoCache(url)
    if (!videoEl || !url) return

    if (flvjs.isSupported() && url.includes('.flv')) {
      const player = flvjs.createPlayer(
        { type: 'flv', url: playUrl },
        {
          enableStashBuffer: false,
          lazyLoad: false,
          deferLoadAfterSourceOpen: false,
          autoCleanupSourceBuffer: true,
        } as any,
      )
      player.attachMediaElement(videoEl)
      player.load()
      player.play().catch(() => {})
      tileFlvPlayers.set(tile.name, player)
      return
    }

    videoEl.src = playUrl
    videoEl.play().catch(() => {})
  })
}

const initFocusPlayer = (url: string) => {
  const videoEl = focusVideoRef.value
  if (!videoEl || !url) return
  const playUrl = withNoCache(url)

  destroyFocusPlayer()

  if (flvjs.isSupported() && url.includes('.flv')) {
    focusFlvPlayer = flvjs.createPlayer(
      { type: 'flv', url: playUrl },
      {
        enableStashBuffer: false,
        lazyLoad: false,
        deferLoadAfterSourceOpen: false,
        autoCleanupSourceBuffer: true,
      } as any,
    )
    focusFlvPlayer.attachMediaElement(videoEl)
    focusFlvPlayer.load()
    focusFlvPlayer.play().catch(() => {})
    return
  }

  videoEl.src = playUrl
  videoEl.play().catch(() => {})
}

const openFocus = (camera: MonitorStreamItem) => {
  focusText.value = camera.name + '（大屏预览）'
  focusStreamUrl.value = camera.streamUrl || rtmpAddressList[0]
  focusVisible.value = true
  nextTick(() => {
    if (focusStreamUrl.value) {
      initFocusPlayer(focusStreamUrl.value)
    }
  })
}

const closeFocus = () => {
  focusVisible.value = false
  focusStreamUrl.value = ''
  destroyFocusPlayer()
}

const updateLinkedVideo = (camera: string, streamUrl?: string) => {
  debugLog('updateLinkedVideo input', { camera, streamUrl })
  const target =
    monitors.value.find(item => item.name === camera) ||
    monitors.value.find(item => item.name.includes(camera)) ||
    monitors.value.find(item => camera.includes(item.name)) ||
    cameraTiles.value.find(item => item.name === camera)

  const displayName = target?.name || camera
  linkedVideo.value = '联动视频：' + displayName
  linkedStreamUrl.value = streamUrl || target?.streamUrl || ''

  debugLog('updateLinkedVideo matched', {
    displayName,
    matchedName: target?.name,
    matchedId: target?.id,
    resolvedUrl: linkedStreamUrl.value,
  })

  if (!linkedStreamUrl.value) {
    const fallback =
      monitors.value.find(item => item.streamUrl) ||
      cameraTiles.value.find(item => item.streamUrl)
    if (fallback) {
      linkedVideo.value = '联动视频：' + fallback.name
      linkedStreamUrl.value = fallback.streamUrl || ''
      debugLog('updateLinkedVideo fallback', {
        fallbackName: fallback.name,
        fallbackId: fallback.id,
        fallbackUrl: fallback.streamUrl,
      })
    }
  }

  nextTick(() => {
    if (linkedStreamUrl.value) {
      initLinkedPlayer(linkedStreamUrl.value)
      return
    }
    destroyLinkedPlayer()
  })
}

const openMonitorModal = () => {
  monitorModalVisible.value = true
}

const closeMonitorModal = () => {
  monitorModalVisible.value = false
}

const pushKeyword = async (value?: string) => {
  const msg = (value ?? keyword.value).trim()
  if (!msg) return
  await axios.post('/cbs', { message: msg })
  if (value === undefined && msg && !keywordTags.value.includes(msg)) {
    keywordTags.value.push(msg)
  }
  if (value === undefined) {
    keyword.value = ''
  }
}

const removeTag = (tag: string) => {
  keywordTags.value = keywordTags.value.filter(t => t !== tag)
}

const onMapPointClick = (point: MapPointItem) => {
  debugLog('map point clicked', {
    title: point.title,
    camera: point.camera,
    streamUrl: point.streamUrl,
  })
  updateLinkedVideo(point.camera || point.title, point.streamUrl)
}

onMounted(() => {
  fetchMonitors()
  nextTick(() => {
    initTilePlayers()
    if (!linkedStreamUrl.value && cameraTiles.value[0]?.streamUrl) {
      linkedStreamUrl.value = cameraTiles.value[0].streamUrl || ''
    }
    if (linkedStreamUrl.value) {
      initLinkedPlayer(linkedStreamUrl.value)
    }
  })
})

onUnmounted(() => {
  destroyFocusPlayer()
  destroyTilePlayers()
  destroyLinkedPlayer()
})

watch(
  cameraTiles,
  () => {
    nextTick(() => {
      initTilePlayers()
    })
  },
  { deep: true }
)
</script>

<style scoped>
.alarm.active {
  border-left-color: var(--accent);
  background: rgba(99, 184, 255, 0.12);
}

.alarm-detail {
  display: grid;
  gap: 6px;
  font-size: 12px;
  color: var(--sub);
}

.alarm-detail .label {
  display: inline-block;
  width: 72px;
  color: var(--text);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.monitor-shell {
  background: #0a1b2f;
  border: 1px solid rgba(99, 184, 255, 0.3);
  border-radius: 10px;
  padding: 18px;
  min-width: 360px;
  max-width: 640px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--text);
}

.monitor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.monitor-head h4 {
  margin: 0;
}

.monitor-head .muted {
  color: var(--sub);
  margin: 4px 0 0;
  font-size: 12px;
}

.monitor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
  padding-right: 4px;
}

.monitor-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(99, 184, 255, 0.2);
  border-radius: 8px;
  background: rgba(13, 30, 52, 0.8);
  cursor: pointer;
}

.monitor-row:hover {
  border-color: var(--accent);
}

.row-title {
  font-weight: 600;
}

.tile-title {
  font-weight: 600;
  text-align: center;
}

.tile-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: rgba(6, 18, 34, 0.75);
}

.tile-overlay {
  position: absolute;
  inset: auto 0 0;
  background: linear-gradient(180deg, rgba(3, 10, 18, 0), rgba(3, 10, 18, 0.72));
  padding: 24px 10px 8px;
}

.tile-sub {
  margin-top: 6px;
  color: var(--sub);
  font-size: 12px;
  text-align: center;
}

.row-sub {
  color: var(--sub);
  font-size: 12px;
  margin-top: 2px;
}

.focus-screen {
  position: relative;
  overflow: hidden;
}

.focus-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: rgba(6, 18, 34, 0.7);
}

.focus-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--text);
  font-size: 15px;
  pointer-events: none;
}

.status {
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(255, 141, 141, 0.15);
  color: #ff8d8d;
  border: 1px solid rgba(255, 141, 141, 0.4);
  font-size: 12px;
}

.status.online {
  background: rgba(83, 213, 165, 0.18);
  color: #53d5a5;
  border-color: rgba(83, 213, 165, 0.45);
}

.space-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}


.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(99, 184, 255, 0.15);
  border: 1px solid rgba(99, 184, 255, 0.4);
  color: var(--text);
  border-radius: 12px;
  font-size: 12px;
  cursor: pointer;
}

.chip .close {
  font-style: normal;
  color: var(--sub);
  cursor: pointer;
}

.chip:hover {
  border-color: var(--accent);
}

.view-all-btn {
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(99, 184, 255, 0.24), rgba(99, 184, 255, 0.5));
  border: 1px solid rgba(99, 184, 255, 0.8);
  color: #e9f4ff;
  border-radius: 6px;
  font-size: 12px;
  letter-spacing: 0.2px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
  margin-left: auto;
  width: auto;
  height: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.view-all-btn:hover {
  border-color: #63b8ff;
  box-shadow: 0 5px 10px rgba(0, 0, 0, 0.16);
}

.right-col {
  gap: 6px;
}

.right-col .card {
  padding: 8px;
}

.left-col {
  gap: 6px;
}

.left-col .card {
  padding: 8px;
}

.alarm-list-card {
  flex: 0 0 30rem;
  max-height: 31rem;
  min-height: 0;
  overflow: hidden;
}

.monitor-main-card {
  flex: 0.88;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.mid-col :deep(.split-row) {
  flex: 1.22;
  min-height: 0;
}

.mid-col :deep(.split-row > .card) {
  height: 100%;
  min-height: 0;
}

.monitor-main-card :deep(.monitor-grid) {
  flex: 1;
  min-height: 0;
}

.map-card,
.dispatch-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.map-card .map-square {
  flex: 1;
  min-height: 0;
  display: flex;
}

.map-card .map-canvas {
  height: 100%;
  min-height: 0;
  aspect-ratio: auto;
}

.dispatch-card .linked-video {
  margin-top: auto;
  flex: 1;
  min-height: 0;
  aspect-ratio: auto;
  position: relative;
  overflow: hidden;
}

.linked-video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: rgba(6, 18, 34, 0.75);
}

.linked-video-label {
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(3, 10, 18, 0.62);
  color: var(--text);
  font-size: 12px;
  line-height: 1.35;
}

.linked-video-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--sub);
  font-size: 12px;
  pointer-events: none;
}

.pie-card {
  min-height: 164px;
  padding-bottom: 4px;
}

.pie-card :deep(.pie-panel) {
  margin-top: -10px;
}

.left-col :deep(.pie-card .chart) {
  height: 164px;
}

.env-chart-card {
  padding: 7px 8px;
}

.left-col .alarm-list-card + .pie-card {
  margin-top: 0;
}

.env-chart-card :deep(.chart-wrap) {
  padding: 0 6px 4px;
  position: relative;
}

.env-chart-card :deep(.chart-wrap svg) {
  height: 132px;
  margin-top: -10px;
}

.env-chart-card :deep(.legend) {
  position: absolute;
  top: 0;
  right: 8px;
  margin-top: 0;
  gap: 4px;
  font-size: 11px;
  flex-direction: column;
  align-items: center;
  align-items: flex-end;
  background: rgba(18, 42, 68, 0.4);
  padding: 2px 6px;
  border-radius: 6px;
}

:deep(.dash) {
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  overflow-x: hidden;
  padding: 8px 8px 6px;
  gap: 6px;
}

:deep(.head) {
  padding: 8px 10px;
  gap: 8px;
}

:deep(.status-grid) {
  gap: 6px;
}

:deep(.pill) {
  padding: 5px 8px;
}

:deep(.grid) {
  grid-template-columns: 330px minmax(0, 1fr) 260px;
  height: 100%;
  min-height: 0;
  gap: 6px;
}

:deep(.grid > .col) {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  gap: 6px;
}

:deep(.monitor-grid .video-tile) {
  min-height: 168px;
  position: relative;
  overflow: hidden;
}

:deep(.map-canvas) {
  min-height: 210px;
}

:deep(.linked-video) {
  margin-top: auto;
}

@media (max-width: 1240px) {
  :deep(.grid) {
    grid-template-columns: 1fr;
    height: auto;
  }

  :deep(.dash) {
    height: auto;
    max-height: none;
    overflow: auto;
  }
}
</style>
  
