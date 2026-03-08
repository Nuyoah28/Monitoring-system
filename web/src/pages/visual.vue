<template>
  <DashboardLayout @open-profile="goProfile">
    <div class="col">
      <article class="card">
        <h3>告警指标</h3>
        <div class="kpi-grid">
          <div class="kpi" v-for="k in kpis" :key="k.name">
            <div class="name">{{ k.name }}</div>
            <div class="num" :style="{ color: k.color || 'inherit' }">{{ k.value }}</div>
          </div>
        </div>
      </article>

      <article class="card">
        <AlarmList />
      </article>

      <article class="card">
        <h3>分类统计图</h3>
        <PieChart1 />
      </article>
    </div>

    <div class="col">
      <article class="card">
        <div class="card-head">
          <h3>实时监控</h3>
          <button class="btn view-all-btn" type="button" @click="openMonitorModal">查看全部</button>
        </div>
        <div class="monitor-grid">
          <div
            v-for="tile in cameraTiles"
            :key="tile"
            class="video-tile"
            @click="openFocus(tile)"
          >
            {{ tile }}
          </div>
        </div>
      </article>

      <div class="split-row">
        <article class="card">
          <h3>小区地图及其监测点</h3>
          <div class="map-square">
            <div class="map-canvas">
              <span
                v-for="point in mapPoints"
                :key="point.camera"
                class="point"
                :class="point.className"
                :title="point.title"
                @click="updateLinkedVideo(point.camera)"
              ></span>
            </div>
          </div>
        </article>

        <article class="card slim-card">
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
          <div class="linked-video">{{ linkedVideo }}</div>
        </article>
      </div>
    </div>

  <div class="col">
    <article class="card">
      <h3>AI Agent 对话</h3>
      <div class="chat">
          助手：你好，我可以帮你筛选告警并生成处置建议。<br />
          你：请列出未处理明火相关告警。<br />
          助手：当前 1 条，位于地库入口，建议立即通知巡检。<br />
          你：下发“消防通道堵塞”检测词汇。<br />
          助手：已提交算法端，等待模型回执。
      </div>
    </article>

      <article class="card">
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
        <div class="focus-screen">{{ focusText }}</div>
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
            @click="openFocus(item.name)"
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/DashboardLayout.vue'
import { useAlarmStore, type AlarmItem } from '@/stores/alarm'
import AlarmList from '@/components/alarmlist.vue'
import PieChart1 from '@/components/piechart1.vue'
import axios from 'axios'

const router = useRouter()
const alarmStore = useAlarmStore()

const focusVisible = ref(false)
const focusText = ref('监控大屏')
const linkedVideo = ref('联动视频：1号机位 - 北门实时画面')
const monitorModalVisible = ref(false)
const monitors = ref<Array<{ name: string; department?: string; status?: number | string }>>([])
const keyword = ref('')
const alarms = ref<AlarmItem[]>([])
// 详情展示暂不使用，保留以便后续扩展
const selectedAlarm = ref<AlarmItem | null>(null)

const kpis = ref([
  { name: '今日告警', value: 0 },
  { name: '待处理', value: 0, color: '#ff8d8d' },
  { name: '近30天', value: 0 },
  { name: '近一年', value: 0 },
])

const cameraTiles = ref<string[]>([
  '1号机位 - 北门实时画面',
  '2号机位 - 车库入口实时画面',
  '3号机位 - 东侧步道实时画面',
])

const mapPoints = ref([
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

const fetchAlarms = async () => {
  const { data: res } = await axios.get('/alarm/query', {
    params: { pageNum: 1, pageSize: 10 },
  })
  if (res.code !== '00000') return
  const list: AlarmItem[] = res.data?.list || []
  alarmStore.setAlarmList(list)
  alarms.value = list.map(item => ({
    ...item,
    name: item.name || item.eventName || '未命名告警',
    department: item.department || item.location || '未标注位置',
    date: item.date || item.time || item.createTime || '--',
    deal: item.deal || item.processingContent || item.statusText || '未处理',
  }))

  const today = list.length
  const pending = list.filter(item => item.deal !== '完成' && item.status !== 1).length
  kpis.value = [
    { name: '今日告警', value: today },
    { name: '待处理', value: pending, color: '#ff8d8d' },
    { name: '近30天', value: res.data?.monthTotal ?? today },
    { name: '近一年', value: res.data?.yearTotal ?? today },
  ]
}

const fetchMonitors = async () => {
  try {
    const [{ data: listRes }, { data: mapRes }] = await Promise.all([
      axios.get('/monitor'),
      axios.get('/monitor/map'),
    ])

    if (listRes.code === '00000') {
      const monitorList: Array<{ name: string; department?: string; status?: number | string }> = listRes.data || []
      monitors.value = monitorList
      if (monitorList.length) {
        cameraTiles.value = monitorList.slice(0, 3).map(item => item.name)
        if (monitorList[0]) {
          linkedVideo.value = '联动视频：' + monitorList[0].name
        }
      }
    }

    if (mapRes.code === '00000') {
      const points: Array<{ name: string; location?: string; longitude?: number; latitude?: number }> = mapRes.data || []
      mapPoints.value = points.slice(0, 3).map((item, idx) => ({
        title: item.location || item.name,
        camera: item.name,
        className: `p${idx + 1}`,
        style:
          item.longitude !== undefined && item.latitude !== undefined
            ? { left: `${item.longitude}%`, top: `${item.latitude}%` }
            : undefined,
      }))
    }
  } catch (e) {
    // 静态降级
  }
}

const goProfile = () => {
  router.push('/home')
}

const openFocus = (camera: string) => {
  focusText.value = camera + '（大屏预览）'
  focusVisible.value = true
}

const closeFocus = () => {
  focusVisible.value = false
}

const updateLinkedVideo = (camera: string) => {
  linkedVideo.value = '联动视频：' + camera
}

const openMonitorModal = () => {
  monitorModalVisible.value = true
}

const closeMonitorModal = () => {
  monitorModalVisible.value = false
}

const selectAlarm = (alarm: AlarmItem) => {
  selectedAlarm.value = alarm
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

onMounted(() => {
  fetchAlarms()
  fetchMonitors()
})
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

.row-sub {
  color: var(--sub);
  font-size: 12px;
  margin-top: 2px;
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
</style>
  
