<template>
  <DashboardLayout @open-profile="goProfile">
    <div class="page-shell">
      <section class="nav-bar">
        <div class="nav-left">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="nav-btn"
            :class="{ active: activeTab === tab.key }"
            type="button"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="nav-current">{{ currentTabLabel }}</div>
      </section>

      <section class="content-shell">
        <section v-show="activeTab === 'alarm'" class="panel alarm-panel">
          <div class="alarm-left card">
            <div class="panel-headline small">
              <h3>最新报警明细</h3>
              <div class="table-filters">
                <input v-model.trim="alarmKeyword" placeholder="搜索事件/区域" />
                <select v-model="alarmDealFilter">
                  <option value="all">全部</option>
                  <option value="pending">未处理</option>
                  <option value="done">已处理</option>
                </select>
                <button class="mini-action chart-mini-action" type="button" @click="activeTab = 'video'">
                  <span class="mini-icon video-icon" aria-hidden="true"></span>
                  <span>联动视频</span>
                </button>
                <button class="mini-action chart-mini-action" type="button" @click="activeTab = 'agent'">
                  <span class="mini-icon agent-icon" aria-hidden="true"></span>
                  <span>交给 Agent</span>
                </button>
              </div>
            </div>
            <div class="table-wrap detail-table-wrap">
              <table class="info-table">
                <thead>
                  <tr>
                    <th>事件</th>
                    <th>区域</th>
                    <th>时间</th>
                    <th>等级</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in filteredAlarmRows" :key="`${row.eventName}-${idx}`" :class="severityClass(row.level)" @click="openAlarmDetail(row)">
                    <td>{{ row.eventName }}</td>
                    <td>{{ row.department }}</td>
                    <td>{{ row.date }}</td>
                    <td><span class="level-chip" :class="severityClass(row.level)">{{ severityText(row.level) }}</span></td>
                    <td><span class="state-chip" :class="row.deal.includes('已') ? 'done' : 'pending'">{{ row.deal }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="alarm-right">
            <article class="card chart-card">
              <div class="panel-headline small">
                <h3>告警统计</h3>
                <span>处理率 {{ alarmCompletionRate }}%</span>
              </div>
              <div class="kpi-grid">
                <div class="kpi" v-for="k in kpis" :key="k.name">
                  <div class="name">{{ k.name }}</div>
                  <div class="num" :style="{ color: k.color || 'inherit' }">{{ k.value }}</div>
                </div>
              </div>
              <div class="severity-list">
                <div class="severity-row" v-for="item in alarmSeverityStats" :key="item.label">
                  <span>{{ item.label }}</span>
                  <div class="trend-bar"><i :style="{ width: `${item.percent}%` }"></i></div>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </article>

            <article class="card">
              <div class="panel-headline small">
                <h3>类别图表</h3>
                <div class="chart-filter">
                  <span>时间段</span>
                  <select v-model="chartTimeRange">
                    <option value="day">今日</option>
                    <option value="week">近7天</option>
                    <option value="month">近30天</option>
                  </select>
                </div>
              </div>
              <div class="chart-panel">
                <div class="chart-item">
                  <h4>报警类别分布</h4>
                  <PieChart1 />
                </div>
                <div class="chart-item">
                  <h4>报警趋势</h4>
                  <LineChart />
                </div>
              </div>
            </article>

            <article class="card">
              <div class="panel-headline small">
                <h3>快速处置建议</h3>
                <span>{{ filteredAlarmRows.length }} 条记录</span>
              </div>
              <ul class="advice-list">
                <li v-for="item in alarmSuggestions" :key="item">{{ item }}</li>
              </ul>
            </article>
          </div>
        </section>

        <dialog1 v-if="alarmDialogVisible" :item="currentAlarmItem" @updateDialogVisible1="alarmDialogVisible = $event" />

        <section v-show="activeTab === 'video'" class="panel video-panel">
          <article class="card video-main">
            <div class="panel-headline">
              <h3>监控视频总览</h3>
              <button class="btn" type="button" @click="openMonitorModal">全部监控点</button>
            </div>
            <div class="monitor-grid monitor-grid-large">
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

          <article class="card video-side">
            <h3>点位地图联动</h3>
            <div class="map-square">
              <AMapLinkage3D :points="mapPoints" @point-click="onMapPointClick" />
            </div>
            <div class="video-stats-grid">
              <div class="mini-kpi"><span>在线</span><strong>{{ onlineCount }}</strong></div>
              <div class="mini-kpi"><span>离线</span><strong>{{ offlineCount }}</strong></div>
              <div class="mini-kpi"><span>总监控点</span><strong>{{ monitors.length }}</strong></div>
              <div class="mini-kpi"><span>当前预览</span><strong>{{ cameraTiles.length }}</strong></div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'env'" class="panel env-panel">
          <article v-for="metric in envTrendMetrics" :key="metric.key" class="card env-metric-card">
            <div class="panel-headline small env-metric-head">
              <h3>{{ metric.label }}趋势</h3>
              <div v-if="metric.key === 'aqi'" class="chart-filter">
                <span>时间段</span>
                <select v-model="envTrendRange">
                  <option value="day">今日</option>
                  <option value="week">近7天</option>
                  <option value="month">近30天</option>
                </select>
              </div>
              <span v-else>{{ metric.unit }}</span>
            </div>
            <div class="env-trend-item single">
              <svg
                class="env-trend-svg"
                viewBox="0 0 360 156"
                preserveAspectRatio="none"
                :aria-label="`${metric.label} 折线图`"
              >
                <line x1="40" y1="128" x2="344" y2="128" stroke="rgba(168,198,232,0.62)" stroke-width="1" />
                <line x1="40" y1="16" x2="40" y2="128" stroke="rgba(168,198,232,0.62)" stroke-width="1" />
                <line
                  v-for="tick in envTrendCharts[metric.key].yTicks"
                  :key="`${metric.key}-y-${tick.value}`"
                  x1="40"
                  :y1="tick.y"
                  x2="344"
                  :y2="tick.y"
                  stroke="rgba(168,198,232,0.16)"
                  stroke-width="1"
                />
                <text
                  v-for="tick in envTrendCharts[metric.key].yTicks"
                  :key="`${metric.key}-yl-${tick.value}`"
                  x="34"
                  :y="tick.y + 4"
                  text-anchor="end"
                  fill="rgba(214, 230, 255, 0.86)"
                  font-size="10"
                >
                  {{ tick.value }}
                </text>
                <text
                  v-for="tick in envTrendCharts[metric.key].xTicks"
                  :key="`${metric.key}-x-${tick.label}`"
                  :x="tick.x"
                  y="144"
                  text-anchor="middle"
                  fill="rgba(214, 230, 255, 0.78)"
                  font-size="10"
                >
                  {{ tick.label }}
                </text>
                <path :d="envTrendCharts[metric.key].areaPath" :fill="metric.areaColor" />
                <polyline
                  :points="envTrendCharts[metric.key].points"
                  fill="none"
                  :stroke="metric.color"
                  stroke-width="2.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  v-for="(dot, idx) in envTrendCharts[metric.key].dots"
                  :key="`${metric.key}-dot-${idx}`"
                  :cx="dot.x"
                  :cy="dot.y"
                  r="2.6"
                  :fill="metric.color"
                  stroke="rgba(255,255,255,0.82)"
                  stroke-width="0.8"
                />
              </svg>
            </div>
          </article>

          <article class="card env-slot-card">
            <h3>车位占用数据</h3>
            <div class="bar-grid">
              <div class="bar-row" v-for="item in parkingBars" :key="item.name">
                <span>{{ item.name }}</span>
                <div class="bar"><i :style="{ width: `${item.percent}%` }"></i></div>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'agent'" class="panel agent-panel">
          <div class="main-col">
            <article class="card hero-card">
              <div class="section-head hero-head">
                <div>
                  <h3>数字助手</h3>
                  <p>数字助手常驻在线，支持语音或文字发起交互，可联动平台能力完成告警查询、监控查看与智能问答。</p>
                </div>
                <div class="hero-head-side">
                  <div class="service-strip">
                    <span v-for="item in serviceHighlights" :key="item" class="service-chip">{{ item }}</span>
                  </div>
                  <span class="status-pill" :class="currentStageStatus">{{ agentStatusLabel }}</span>
                </div>
              </div>

              <div class="hero-shell">
                <div class="hero-stage">
                  <VirtualAgentStage
                    :key="agentStageKey"
                    :status="currentStageStatus"
                    :conversation-active="isRealtimeConversationActive"
                    :preview-text="agentPreview"
                  />
                </div>
                <ChatPanel
                  layout="stage"
                  :quick-replies="chatQuickReplies"
                  @streaming-change="handleStreamingChange"
                  @assistant-preview="handleAssistantPreview"
                  @user-submit="handleUserSubmit"
                  @voice-state-change="handleVoiceStateChange"
                  @realtime-change="handleRealtimeConversationChange"
                />
              </div>
            </article>
          </div>

          <aside class="side-col">
            <article class="card side-card task-card">
              <div class="card-title-row">
                <h3>待办事项</h3>
                <span class="inline-tag">未处理优先</span>
              </div>
              <div class="task-list">
                <div v-for="task in pendingTasks" :key="task" class="task-item">{{ task }}</div>
              </div>
            </article>

            <article class="card side-card summary-card">
              <div class="card-title-row">
                <div>
                  <h3>周期总结</h3>
                  <p class="card-subtitle">自动整理最近一周或最近一月的报警情况和处理建议。</p>
                </div>
                <button class="mini-action" type="button" @click="refreshSummaryNow">刷新</button>
              </div>

              <div class="summary-toolbar">
                <div class="summary-tabs">
                  <button
                    v-for="option in summaryOptions"
                    :key="option.value"
                    class="summary-tab"
                    :class="{ active: activeSummaryRange === option.value }"
                    type="button"
                    @click="activeSummaryRange = option.value"
                  >
                    {{ option.label }}
                  </button>
                </div>
                <span class="summary-updated">更新于 {{ summaryUpdatedLabel }}</span>
              </div>

              <div class="summary-kpis">
                <div class="summary-kpi"><span>总数</span><strong>{{ selectedSummaryView.total }}</strong></div>
                <div class="summary-kpi"><span>已处理</span><strong>{{ selectedSummaryView.handled }}</strong></div>
                <div class="summary-kpi"><span>未处理</span><strong>{{ selectedSummaryView.pending }}</strong></div>
                <div class="summary-kpi"><span>高等级</span><strong>{{ selectedSummaryView.highLevel }}</strong></div>
              </div>

              <p class="summary-overview">{{ selectedSummaryView.overview }}</p>

              <div class="summary-section">
                <button class="summary-head" type="button" @click="toggleSummarySection('trend')">
                  <span>趋势详情</span>
                  <span>{{ summarySectionsOpen.trend ? '收起' : '展开' }}</span>
                </button>
                <div v-show="summarySectionsOpen.trend" class="summary-body">
                  <div v-for="item in selectedTrendRows" :key="item.label" class="trend-row">
                    <span>{{ item.label }}</span>
                    <div class="trend-bar"><i :style="{ width: `${getTrendWidth(item.value, selectedTrendMax)}%` }"></i></div>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>

              <div class="summary-section">
                <button class="summary-head" type="button" @click="toggleSummarySection('focus')">
                  <span>重点关注</span>
                  <span>{{ summarySectionsOpen.focus ? '收起' : '展开' }}</span>
                </button>
                <div v-show="summarySectionsOpen.focus" class="summary-body">
                  <div class="focus-grid">
                    <div class="focus-card"><span>峰值时段</span><strong>{{ selectedSummaryView.peakPeriod }}</strong></div>
                    <div class="focus-card"><span>重点区域</span><strong>{{ selectedSummaryView.topArea }}</strong></div>
                  </div>
                  <div class="focus-tags">
                    <span class="focus-tag">{{ selectedSummaryView.topType }} {{ selectedSummaryView.topTypeCount }} 次</span>
                  </div>
                </div>
              </div>

              <div class="summary-section">
                <button class="summary-head" type="button" @click="toggleSummarySection('advice')">
                  <span>处理建议</span>
                  <span>{{ summarySectionsOpen.advice ? '收起' : '展开' }}</span>
                </button>
                <div v-show="summarySectionsOpen.advice" class="summary-body">
                  <ul class="advice-list">
                    <li v-for="item in selectedSummaryView.suggestions" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </article>
          </aside>
        </section>
      </section>
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
import { computed, nextTick, onBeforeUnmount, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/DashboardLayout.vue'
import PieChart1 from '@/components/piechart1.vue'
import LineChart from '@/components/LineChart.vue'
import AMapLinkage3D from '@/components/AMapLinkage3D.vue'
import VirtualAgentStage from '@/components/VirtualAgentStage.vue'
import ChatPanel from '@/components/chat_panel.vue'
import dialog1 from '@/components/dialog1.vue'
import axios from 'axios'
import flvjs from 'flv.js'
import { rtmpAddressList } from '@/config/config'
import { useAlarmStore } from '@/stores/alarm'

type ModuleTab = 'alarm' | 'video' | 'env' | 'agent'
type AgentStageStatus = 'idle' | 'listening' | 'thinking' | 'speaking'
type VoiceInteractionState = 'idle' | 'listening' | 'speaking'

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
  longitude?: number
  latitude?: number
  style?: {
    left?: string
    top?: string
  }
}

const router = useRouter()
const alarmStore = useAlarmStore()

const tabs: Array<{ key: ModuleTab; label: string }> = [
  { key: 'alarm', label: '报警消息' },
  { key: 'video', label: '监控视频' },
  { key: 'env', label: '环境和车位' },
  { key: 'agent', label: 'Agent' },
]
const activeTab = ref<ModuleTab>('video')
const agentStageKey = ref(0)
const currentTabLabel = computed(() => tabs.find(item => item.key === activeTab.value)?.label || '导航')

const focusVisible = ref(false)
const alarmDialogVisible = ref(false)
const currentAlarmItem = ref<any>(null)

const openAlarmDetail = (row: any) => {
  currentAlarmItem.value = row
  alarmDialogVisible.value = true
}

const focusText = ref('监控大屏')
const focusStreamUrl = ref('')
const focusVideoRef = ref<HTMLVideoElement | null>(null)
let focusFlvPlayer: flvjs.Player | null = null
const tileVideoRefs = new Map<string, HTMLVideoElement>()
const tileFlvPlayers = new Map<string, flvjs.Player>()
const monitorModalVisible = ref(false)
const monitors = ref<MonitorStreamItem[]>([])

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

const withNoCache = (url: string) => {
  if (!url) return url
  const [base, hash = ''] = url.split('#')
  const connector = base.includes('?') ? '&' : '?'
  const nextUrl = `${base}${connector}_t=${Date.now()}`
  return hash ? `${nextUrl}#${hash}` : nextUrl
}

const alarmPageNum = ref(1)
const alarmPageSize = ref(60)

const fetchAlarmList = async () => {
  try {
    const { data } = await axios.get('/alarm/query', {
      params: {
        pageNum: alarmPageNum.value,
        pageSize: alarmPageSize.value,
        status: 0,
      },
    })
    console.log('报警API返回:', data)
    const list = data?.data?.alarmList || data?.data?.list || []
    if (Array.isArray(list) && list.length > 0) {
      alarmStore.setAlarmList(list)
      alarmStore.updateStatisticsFromAlarms()
    } else {
      console.log('后端返回空数据，使用模拟数据')
      useMockData()
    }
  } catch (e) {
    console.log('请求失败，使用模拟数据', e)
    useMockData()
  }
}

const useMockData = () => {
  const mockAlarms = [
    {
      eventName: '电动车进楼检测',
      department: '北门入口',
      date: new Date().toLocaleString(),
      level: '2',
      deal: '未处理',
      location: '北门',
      createTime: new Date().toISOString(),
      video: 'http://localhost:8848/video/电动车进楼.mp4'
    },
    {
      eventName: '烟雾火灾告警',
      department: '车库入口',
      date: new Date().toLocaleString(),
      level: '3',
      deal: '未处理',
      location: '车库',
      createTime: new Date().toISOString(),
      video: 'http://localhost:8848/video/火灾烟雾.mp4'
    },
    {
      eventName: '垃圾桶溢出告警',
      department: '东侧步道',
      date: new Date().toLocaleString(),
      level: '1',
      deal: '未处理',
      location: '东侧',
      createTime: new Date().toISOString(),
      video: 'http://localhost:8848/video/垃圾桶溢出.mp4'
    }
  ]
  alarmStore.setAlarmList(mockAlarms)
  alarmStore.updateStatisticsFromAlarms()
  console.log('使用模拟报警数据（演示模式）')
}

// 隐藏遥控器通信
let simChannel: BroadcastChannel | null = null;
onMounted(() => {
  if (window.BroadcastChannel) {
    simChannel = new BroadcastChannel('demonstration_channel');
    simChannel.onmessage = (event) => {
      if (event.data && event.data.action === 'trigger_alarm') {
        _handleSimulate(event.data.type);
      }
    };
  }
});

onUnmounted(() => {
  if (simChannel) {
    simChannel.close();
  }
});

const _handleSimulate = (type: string) => {
  let newAlarm: any = null;
  const now = new Date();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  const h = String(now.getHours()).padStart(2, '0');
  const min = String(now.getMinutes()).padStart(2, '0');
  const t = `${m}-${d} ${h}:${min}`;
  const iso = now.toISOString();
  
  if (type === 'bike') {
    newAlarm = {
      eventName: '电动车进楼',
      department: '北门入口',
      date: now.toLocaleString(),
      level: 2,
      location: '北门',
      createTime: iso,
      video: 'http://localhost:8848/video/电动车进楼.mp4',
      id: Date.now(), name: '模拟触发', deal: '未处理', content: '前端大屏测试触发', phone: '13800000000'
    };
  } else if (type === 'fire') {
    newAlarm = {
      eventName: '明火',
      department: '车库入口',
      date: now.toLocaleString(),
      level: 3,
      location: '车库',
      createTime: iso,
      video: 'http://localhost:8848/video/火灾烟雾.mp4',
      id: Date.now(), name: '模拟触发', deal: '未处理', content: '前端大屏测试触发', phone: '13800000000'
    };
  } else if (type === 'garbage') {
    newAlarm = {
      eventName: '垃圾',
      department: '东侧步道',
      date: now.toLocaleString(),
      level: 1,
      location: '东侧',
      createTime: iso,
      video: 'http://localhost:8848/video/垃圾桶溢出.mp4',
      id: Date.now(), name: '模拟触发', deal: '未处理', content: '前端大屏测试触发', phone: '13800000000'
    };
  }

  if (newAlarm) {
    const list = [...(alarmStore.getAlarmList || [])];
    list.unshift(newAlarm);
    alarmStore.setAlarmList(list);
    alarmStore.updateStatisticsFromAlarms();
    
    // 触发全局报警事件，例如播放提示音或动画
    const bus = (window as any).$bus;
    if (bus) bus.$emit('alarm');
    
    import('element-plus').then(({ ElMessage }) => {
      ElMessage({ message: '收到大屏模拟指挥指令：' + newAlarm.eventName, type: 'warning' });
    });
  }
};

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
      const normalized = trimmed.includes('T') || trimmed.includes('/') ? trimmed : trimmed.replace(/-/g, '/')
      const date = new Date(normalized)
      return Number.isNaN(date.getTime()) ? null : date
    }
    return null
  }

  const isToday = (date: Date) => (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )

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

const alarmTableRows = computed(() => {
  const rows = (alarmStore.getAlarmList || []).slice(0, 10)
  if (!rows.length) {
    return [{ eventName: '暂无报警', department: '--', date: '--', level: 1, deal: '已处理' }]
  }
  return rows.map((item: any) => ({
    ...item,
    eventName: item.eventName || '未知事件',
    department: item.department || item.location || '未标注',
    date: item.date || item.time || item.createTime || '--',
    level: Number(item.level || 1),
    deal: item.deal || '未处理',
  }))
})

const alarmKeyword = ref('')
const alarmDealFilter = ref<'all' | 'pending' | 'done'>('all')
const chartTimeRange = ref<'day' | 'week' | 'month'>('week')

const filteredAlarmRows = computed(() => {
  const keyword = alarmKeyword.value.toLowerCase()
  return alarmTableRows.value.filter((row) => {
    const eventName = String(row.eventName || '').toLowerCase()
    const department = String(row.department || '').toLowerCase()
    const matchKeyword =
      !keyword ||
      eventName.includes(keyword) ||
      department.includes(keyword)
    if (!matchKeyword) return false

    if (alarmDealFilter.value === 'pending') return !row.deal.includes('已')
    if (alarmDealFilter.value === 'done') return row.deal.includes('已')
    return true
  })
})

const alarmCompletionRate = computed(() => {
  const total = alarmTableRows.value.length
  if (!total) return 0
  const done = alarmTableRows.value.filter(item => item.deal.includes('已')).length
  return Math.round((done / total) * 100)
})

const alarmSeverityStats = computed(() => {
  const list = alarmStore.getAlarmList || []
  const groups = [
    { label: '高等级', check: (n: number) => n >= 3 },
    { label: '中等级', check: (n: number) => n === 2 },
    { label: '低等级', check: (n: number) => n <= 1 },
  ]
  const max = Math.max(list.length, 1)
  return groups.map(group => {
    const count = list.filter((item: any) => group.check(Number(item.level || 1))).length
    return {
      label: group.label,
      count,
      percent: Math.max(Math.round((count / max) * 100), count > 0 ? 12 : 0),
    }
  })
})

const alarmSuggestions = computed(() => {
  const high = alarmSeverityStats.value.find(item => item.label === '高等级')?.count || 0
  const pending = filteredAlarmRows.value.filter(item => !item.deal.includes('已')).length
  const topArea = filteredAlarmRows.value[0]?.department || '重点区域'
  const result: string[] = []
  if (high > 0) result.push(`当前有 ${high} 条高等级报警，建议优先复核并完成闭环。`)
  if (pending > 0) result.push(`仍有 ${pending} 条未处理报警，建议按时间顺序分批处置。`)
  result.push(`今日重点关注 ${topArea}，建议联动该区域视频进行二次确认。`)
  return result
})

const severityClass = (level: number) => {
  if (level >= 3) return 'high'
  if (level === 2) return 'mid'
  return 'low'
}

const severityText = (level: number) => {
  if (level >= 3) return '高'
  if (level === 2) return '中'
  return '低'
}

const parkingBars = ref([
  { name: '地库A区', value: 38, percent: 78 },
  { name: '地库B区', value: 21, percent: 52 },
  { name: '地面东侧', value: 15, percent: 46 },
  { name: '地面西侧', value: 9, percent: 28 },
])

const envTrendRange = ref<'day' | 'week' | 'month'>('week')

const envTrendMetrics = [
  { key: 'aqi', label: 'AQI', unit: '指数', color: '#63b8ff', areaColor: 'rgba(99,184,255,0.22)' },
  { key: 'humidity', label: '湿度', unit: '%', color: '#53d5a5', areaColor: 'rgba(83,213,165,0.20)' },
  { key: 'pm25', label: 'PM2.5', unit: 'ug/m3', color: '#f8cb71', areaColor: 'rgba(248,203,113,0.18)' },
] as const

type EnvMetricKey = typeof envTrendMetrics[number]['key']

interface EnvPoint {
  label: string
  aqi: number
  humidity: number
  pm25: number
}

const envTrendData: Record<'day' | 'week' | 'month', EnvPoint[]> = {
  day: [
    { label: '00:00', aqi: 74, humidity: 61, pm25: 46 },
    { label: '04:00', aqi: 78, humidity: 64, pm25: 49 },
    { label: '08:00', aqi: 71, humidity: 59, pm25: 44 },
    { label: '12:00', aqi: 83, humidity: 55, pm25: 53 },
    { label: '16:00', aqi: 88, humidity: 52, pm25: 58 },
    { label: '20:00', aqi: 79, humidity: 57, pm25: 50 },
    { label: '24:00', aqi: 73, humidity: 60, pm25: 45 },
  ],
  week: [
    { label: '周一', aqi: 76, humidity: 62, pm25: 47 },
    { label: '周二', aqi: 82, humidity: 59, pm25: 52 },
    { label: '周三', aqi: 78, humidity: 57, pm25: 49 },
    { label: '周四', aqi: 86, humidity: 55, pm25: 56 },
    { label: '周五', aqi: 81, humidity: 58, pm25: 51 },
    { label: '周六', aqi: 74, humidity: 63, pm25: 45 },
    { label: '周日', aqi: 72, humidity: 64, pm25: 43 },
  ],
  month: [
    { label: '4/01', aqi: 79, humidity: 60, pm25: 51 },
    { label: '4/05', aqi: 75, humidity: 62, pm25: 47 },
    { label: '4/10', aqi: 83, humidity: 58, pm25: 55 },
    { label: '4/15', aqi: 88, humidity: 54, pm25: 60 },
    { label: '4/20', aqi: 80, humidity: 57, pm25: 52 },
    { label: '4/25', aqi: 73, humidity: 63, pm25: 44 },
    { label: '4/30', aqi: 77, humidity: 61, pm25: 48 },
  ],
}

const envTrendSeries = computed(() => envTrendData[envTrendRange.value])

interface TrendTick {
  value: number
  y: number
}

interface TrendXTick {
  label: string
  x: number
}

interface TrendRenderData {
  points: string
  areaPath: string
  dots: Array<{ x: number; y: number }>
  yTicks: TrendTick[]
  xTicks: TrendXTick[]
}

const buildTrendRender = (metric: EnvMetricKey): TrendRenderData => {
  const series = envTrendSeries.value
  const left = 40
  const right = 344
  const top = 16
  const bottom = 128
  const width = right - left
  const height = bottom - top
  const values = series.map(item => item[metric])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const diff = Math.max(max - min, 1)
  const pad = Math.max(Math.round(diff * 0.2), 2)
  const yMin = Math.max(min - pad, 0)
  const yMax = max + pad
  const yDiff = Math.max(yMax - yMin, 1)
  const stepX = series.length > 1 ? width / (series.length - 1) : 0

  const dots = series.map((item, idx) => {
    const x = left + idx * stepX
    const y = bottom - ((item[metric] - yMin) / yDiff) * height
    return { x, y }
  })

  const points = dots.map(dot => `${dot.x},${dot.y}`).join(' ')
  const areaPath = `${points} ${right},${bottom} ${left},${bottom}`
  const yTicks = Array.from({ length: 5 }, (_, idx) => {
    const ratio = idx / 4
    const value = Math.round(yMax - ratio * yDiff)
    return { value, y: top + ratio * height }
  })
  const xTicks = series.map((item, idx) => ({ label: item.label, x: left + idx * stepX }))

  return { points, areaPath: `M ${areaPath} Z`, dots, yTicks, xTicks }
}

const envTrendCharts = computed<Record<EnvMetricKey, TrendRenderData>>(() => ({
  aqi: buildTrendRender('aqi'),
  humidity: buildTrendRender('humidity'),
  pm25: buildTrendRender('pm25'),
}))

const onlineCount = computed(() => monitors.value.filter(item => item.status === 1 || item.status === 'online').length)
const offlineCount = computed(() => Math.max(monitors.value.length - onlineCount.value, 0))

type SummaryRange = 'week' | 'month'
interface SummaryRow {
  label: string
  value: number
}
interface AgentSummary {
  total: number
  handled: number
  pending: number
  highLevel: number
  topType: string
  topTypeCount: number
  peakPeriod: string
  topArea: string
  overview: string
  trend: SummaryRow[]
  suggestions: string[]
}

const summaryOptions = [
  { label: '最近一周', value: 'week' as const },
  { label: '最近一月', value: 'month' as const },
]
const activeSummaryRange = ref<SummaryRange>('week')

const buildSummary = (label: string, days: number): AgentSummary => {
  const list = alarmStore.getAlarmList || []
  const now = new Date().getTime()
  const threshold = now - days * 24 * 60 * 60 * 1000

  const parseTime = (item: any) => {
    // 优先使用带有年份的 createTime
    const raw = item.createTime || item.date || item.time
    if (!raw) return 0
    
    // 如果日期字符串明显缺少年份（如 04-07 12:00），尝试补全
    let dateStr = String(raw)
    if (/^\d{2}-\d{2}/.test(dateStr) && !dateStr.includes(String(new Date().getFullYear()))) {
       dateStr = `${new Date().getFullYear()}-${dateStr}`
    }

    const date = new Date(dateStr).getTime()
    return Number.isNaN(date) ? 0 : date
  }

  const scoped = list.filter((item: any) => {
    const t = parseTime(item)
    return t > 0 && t >= threshold
  })

  const total = scoped.length
  const handled = scoped.filter((item: any) => String(item.deal || '').includes('已') || item.status === 1).length
  const pending = Math.max(total - handled, 0)
  const highLevel = scoped.filter((item: any) => Number(item.level || 0) >= 3).length

  const areaCount = new Map<string, number>()
  const typeCount = new Map<string, number>()
  scoped.forEach((item: any) => {
    const area = item.department || item.location || '未标注'
    const type = item.eventName || '未知事件'
    areaCount.set(area, (areaCount.get(area) || 0) + 1)
    typeCount.set(type, (typeCount.get(type) || 0) + 1)
  })

  const topArea = [...areaCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || '暂无'
  const sortedTypes = [...typeCount.entries()].sort((a, b) => b[1] - a[1])
  const topType = sortedTypes[0]?.[0] || '暂无'
  const topTypeCount = sortedTypes[0]?.[1] || 0

  const trendBucket = new Map<string, number>()
  scoped.forEach((item: any) => {
    const t = parseTime(item)
    if (!t) return
    const d = new Date(t)
    const key = `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    trendBucket.set(key, (trendBucket.get(key) || 0) + 1)
  })

  const trend = [...trendBucket.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-6)
    .map(([label, value]) => ({ label, value }))

  const peakPeriod = trend.length ? [...trend].sort((a, b) => b.value - a.value)[0].label : '暂无数据'

  const suggestions: string[] = []
  if (!total) {
    suggestions.push(`${label}暂无报警，建议持续巡检。`)
  } else {
    if (pending > handled) suggestions.push('未处理报警偏多，建议优先处置高等级与积压事件。')
    if (highLevel > 0) suggestions.push(`存在 ${highLevel} 条高等级报警，请安排人工复核。`)
    suggestions.push(`高发类型为“${topType}”，重点区域集中在 ${topArea}。`)
  }

  return {
    total,
    handled,
    pending,
    highLevel,
    topType,
    topTypeCount,
    peakPeriod,
    topArea,
    trend,
    overview: total
      ? `${label}记录报警 ${total} 条，已处理 ${handled} 条，未处理 ${pending} 条。`
      : `${label}暂无可用报警数据。`,
    suggestions,
  }
}

const summaryData = computed(() => ({
  week: buildSummary('最近一周', 7),
  month: buildSummary('最近一月', 30),
}))
const selectedSummaryView = computed(() => summaryData.value[activeSummaryRange.value])
const selectedTrendRows = computed(() => selectedSummaryView.value.trend.length ? selectedSummaryView.value.trend : [{ label: '--', value: 0 }])
const selectedTrendMax = computed(() => selectedTrendRows.value.reduce((max, item) => Math.max(max, item.value), 1))
const summaryUpdatedLabel = ref('--:--')
const summarySectionsOpen = ref({ trend: true, focus: false, advice: true })

const pendingTasks = computed(() => {
  const rows = alarmTableRows.value.filter(item => !item.deal.includes('已')).slice(0, 4)
  if (!rows.length) {
    return ['当前无待处理报警，建议继续关注实时对话与巡检联动。']
  }
  return rows.map(item => `${item.department} 存在 ${item.eventName} 报警，请尽快复核。`)
})

const getTrendWidth = (value: number, max: number) => (max ? Math.max((value / max) * 100, value > 0 ? 12 : 0) : 0)

const toggleSummarySection = (key: 'trend' | 'focus' | 'advice') => {
  summarySectionsOpen.value[key] = !summarySectionsOpen.value[key]
}

const refreshSummaryNow = () => {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  summaryUpdatedLabel.value = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const agentStatus = ref<AgentStageStatus>('idle')
const voiceInteractionState = ref<VoiceInteractionState>('idle')
const agentPreview = ref('您好，我是晓卫，可以通过对话帮您查询告警、监控点与环境状态。')
const isChatStreaming = ref(false)
const isRealtimeConversationActive = ref(false)
const chatQuickReplies = ['未处理告警有多少', '查看最近告警', '查询1号监控点天气', '介绍一下你的服务']
const serviceHighlights = ['实时语音', '连续对话', '监控联动', '周期总结']
let statusTimer: number | null = null

const currentStageStatus = computed<AgentStageStatus>(() => {
  if (voiceInteractionState.value === 'speaking') return 'speaking'
  if (voiceInteractionState.value === 'listening') return 'listening'
  return agentStatus.value
})

const agentStatusLabel = computed(() => {
  if (currentStageStatus.value === 'listening') return '正在倾听'
  if (currentStageStatus.value === 'thinking') return '正在处理'
  if (currentStageStatus.value === 'speaking') return '正在回复'
  return '待命中'
})

const clearStatusTimer = (): void => {
  if (statusTimer !== null) {
    window.clearTimeout(statusTimer)
    statusTimer = null
  }
}

const queueIdle = (delay = 2200): void => {
  clearStatusTimer()
  statusTimer = window.setTimeout(() => {
    agentStatus.value = 'idle'
  }, delay)
}

const handleStreamingChange = (value: boolean): void => {
  isChatStreaming.value = value
  clearStatusTimer()
  if (value) {
    agentStatus.value = 'thinking'
    agentPreview.value = '已接收您的请求，正在调用平台能力整理结果。'
    return
  }
  agentStatus.value = 'speaking'
  if (voiceInteractionState.value !== 'speaking') queueIdle()
}

const handleAssistantPreview = (text: string): void => {
  if (!text.trim()) return
  agentPreview.value = '最新回复已生成，请在右侧消息区查看完整内容。'
  if (!isChatStreaming.value && voiceInteractionState.value !== 'speaking') {
    agentStatus.value = 'speaking'
    queueIdle()
  }
}

const handleUserSubmit = (): void => {
  agentStatus.value = 'listening'
  agentPreview.value = '已收到您的问题，正在准备联动查询与回答。'
}

const handleVoiceStateChange = (state: VoiceInteractionState): void => {
  voiceInteractionState.value = state
  if (state === 'listening') {
    clearStatusTimer()
    agentPreview.value = '正在倾听您的语音输入，请继续说话。'
    return
  }
  if (state === 'speaking') {
    clearStatusTimer()
    return
  }
  if (!isChatStreaming.value && agentStatus.value === 'speaking') queueIdle()
}

const handleRealtimeConversationChange = (value: boolean): void => {
  isRealtimeConversationActive.value = value
  if (value) {
    clearStatusTimer()
    agentStatus.value = 'listening'
    return
  }
  if (!isChatStreaming.value && voiceInteractionState.value === 'idle') {
    agentStatus.value = 'idle'
    queueIdle(1600)
  }
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
        streamUrl: rtmpAddressList[item.id],
      }))
      monitors.value = monitorList
      if (monitorList.length) {
        cameraTiles.value = monitorList.slice(0, 6)
        nextTick(() => {
          initTilePlayers()
        })
      }
    }

    if (mapRes.code === '00000') {
      const points: Array<{ id?: number | string; monitorId?: number | string; name: string; location?: string; longitude?: number; latitude?: number }> = mapRes.data || []
      mapPoints.value = points.slice(0, 6).map((item, idx) => ({
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
        className: `p${(idx % 3) + 1}`,
        longitude: item.longitude,
        latitude: item.latitude,
        style: item.longitude !== undefined && item.latitude !== undefined
          ? { left: `${item.longitude}%`, top: `${item.latitude}%` }
          : undefined,
      }))
    }
  } catch (e) {
    void e
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
      player.on(flvjs.Events.ERROR, () => {
        player.unload()
        player.destroy()
        tileFlvPlayers.delete(tile.name)
      })
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

const onMapPointClick = (point: MapPointItem) => {
  const target =
    monitors.value.find(item => item.name === point.camera) ||
    monitors.value.find(item => item.name.includes(point.camera)) ||
    cameraTiles.value.find(item => item.name === point.camera)
  if (target) {
    activeTab.value = 'video'
    openFocus(target)
  }
}

const openMonitorModal = () => {
  monitorModalVisible.value = true
}

const closeMonitorModal = () => {
  monitorModalVisible.value = false
}

onMounted(() => {
  fetchAlarmList()
  fetchMonitors()
  refreshSummaryNow()
  if (activeTab.value === 'agent') {
    nextTick(() => {
      window.dispatchEvent(new Event('resize'))
    })
  }
  nextTick(() => {
    initTilePlayers()
  })
})

onBeforeUnmount(() => {
  clearStatusTimer()
})

onUnmounted(() => {
  destroyFocusPlayer()
  destroyTilePlayers()
})

watch(
  cameraTiles,
  () => {
    nextTick(() => {
      initTilePlayers()
    })
  },
  { deep: true },
)

watch(activeTab, (tab) => {
  if (tab === 'alarm') {
    alarmStore.setAlarmList([])  // 清空旧数据
    nextTick(() => {
      fetchAlarmList()
      window.dispatchEvent(new Event('resize'))
    })
  }

  if (tab === 'agent') {
    agentStageKey.value += 1
    nextTick(() => {
      window.dispatchEvent(new Event('resize'))
    })
  }
})
</script>

<style scoped>
.page-shell :deep(*) {
  min-width: 0;
}

:deep(.grid) {
  grid-template-columns: 1fr;
  height: 100%;
  min-height: 0;
}

:deep(.grid > *) {
  min-width: 0;
}

.page-shell {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 8px;
  min-height: 0;
  height: 100%;
}

.nav-bar {
  border: 1px solid rgba(126, 197, 255, 0.38);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(15, 42, 70, 0.95), rgba(12, 34, 58, 0.92));
  padding: 8px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.nav-left {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-btn {
  border: 1px solid rgba(126, 197, 255, 0.34);
  background: linear-gradient(180deg, rgba(17, 47, 75, 0.82), rgba(14, 39, 64, 0.8));
  color: #eaf6ff;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
}

.nav-btn.active,
.nav-btn:hover {
  border-color: rgba(126, 197, 255, 0.75);
  background: linear-gradient(180deg, rgba(31, 77, 116, 0.95), rgba(21, 58, 90, 0.95));
}

.nav-current {
  font-size: 18px;
  font-weight: 600;
  color: #d9ecff;
  letter-spacing: 0.02em;
}

.content-shell {
  min-height: 0;
  height: 100%;
}

.panel {
  min-height: 0;
  height: 100%;
}

.panel .card {
  background:
    radial-gradient(circle at 10% -10%, rgba(126, 197, 255, 0.08), transparent 38%),
    linear-gradient(180deg, rgba(17, 46, 75, 0.82), rgba(13, 33, 56, 0.82));
  box-shadow: inset 0 0 0 1px rgba(126, 197, 255, 0.08);
}

.alarm-panel {
  display: grid;
  grid-template-columns: 0.58fr 1.42fr;
  gap: 8px;
}

.alarm-left,
.alarm-right,
.video-main,
.video-side,
.agent-main-card {
  min-height: 0;
}

.alarm-left {
  display: flex;
  flex-direction: column;
}

.alarm-right {
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 8px;
  min-height: 0;
}

.severity-list {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.severity-row {
  display: grid;
  grid-template-columns: 3.6rem 1fr 2rem;
  gap: 6px;
  align-items: center;
  font-size: 12px;
}

.quick-actions {
  display: flex;
  gap: 6px;
}

.chart-actions {
  gap: 10px;
}

.chart-filter {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--sub);
  font-size: 12px;
}

.chart-filter select {
  border: 1px solid rgba(126, 197, 255, 0.32);
  border-radius: 6px;
  background: rgba(17, 47, 75, 0.66);
  color: #eaf6ff;
  font-size: 11px;
  padding: 4px 8px;
}

.chart-mini-action {
  min-width: 108px;
  padding: 5px 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  border-radius: 999px;
}

.mini-icon {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  border: 1px solid rgba(126, 197, 255, 0.55);
  background: radial-gradient(circle at 35% 30%, rgba(126, 197, 255, 0.55), rgba(35, 85, 126, 0.78));
  position: relative;
  flex: 0 0 17px;
}

.video-icon::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 4px;
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 6px solid rgba(233, 246, 255, 0.95);
}

.agent-icon::before,
.agent-icon::after {
  content: '';
  position: absolute;
  top: 7px;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(233, 246, 255, 0.95);
}

.agent-icon::before {
  left: 4px;
  box-shadow: 5px 0 0 rgba(233, 246, 255, 0.95), 10px 0 0 rgba(233, 246, 255, 0.95);
}

.mini-action {
  border: 1px solid rgba(126, 197, 255, 0.32);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  color: #d9edff;
  background: rgba(17, 47, 75, 0.7);
  cursor: pointer;
}

.table-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.table-filters input {
  width: 9.6rem;
}

.table-filters input,
.table-filters select {
  border: 1px solid rgba(126, 197, 255, 0.32);
  border-radius: 6px;
  background: rgba(17, 47, 75, 0.66);
  color: #eaf6ff;
  font-size: 11px;
  padding: 4px 8px;
}

.info-table tbody tr.high {
  background: rgba(255, 141, 141, 0.08);
}

.info-table tbody tr.mid {
  background: rgba(248, 203, 113, 0.08);
}

.info-table tbody tr.low {
  background: rgba(83, 213, 165, 0.08);
}

.level-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.45rem;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  border: 1px solid transparent;
}

.level-chip.high {
  color: #ff8d8d;
  border-color: rgba(255, 141, 141, 0.5);
  background: rgba(255, 141, 141, 0.15);
}

.level-chip.mid {
  color: #f8cb71;
  border-color: rgba(248, 203, 113, 0.5);
  background: rgba(248, 203, 113, 0.15);
}

.level-chip.low {
  color: #7ce7bc;
  border-color: rgba(83, 213, 165, 0.5);
  background: rgba(83, 213, 165, 0.15);
}

.chart-panel {
  min-height: 230px;
  height: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
  gap: 12px;
}

.chart-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-card .chart-panel {
  flex: 1;
}

.chart-item {
  min-height: 0;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 6px;
}

.chart-item h4 {
  font-size: 14px;
  color: var(--text);
  margin-bottom: 8px;
  font-weight: 500;
}

.chart-item :deep(.pie-panel),
.chart-item :deep(.line-panel) {
  height: 100%;
  min-height: 0;
}

.chart-item :deep(.chart) {
  height: 100% !important;
  width: 100%;
}

.panel-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.panel-headline span {
  color: var(--sub);
  font-size: 12px;
}

.video-panel {
  display: grid;
  grid-template-columns: 1.65fr 1fr;
  gap: 8px;
}

.video-main {
  display: flex;
  flex-direction: column;
}

.monitor-grid-large {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  flex: 1;
  min-height: 0;
}

.monitor-grid {
  display: grid;
  gap: 8px;
}

.video-tile {
  position: relative;
  overflow: hidden;
  min-height: 170px;
  border-radius: 8px;
  border: 1px dashed rgba(107, 176, 255, 0.55);
  background: rgba(7, 21, 38, 0.8);
}

.tile-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tile-overlay {
  position: absolute;
  inset: auto 0 0;
  background: linear-gradient(180deg, rgba(3, 10, 18, 0), rgba(3, 10, 18, 0.72));
  padding: 18px 10px 8px;
}

.tile-title {
  font-weight: 600;
  text-align: center;
}

.tile-sub {
  margin-top: 4px;
  color: var(--sub);
  font-size: 12px;
  text-align: center;
}

.video-side {
  display: flex;
  flex-direction: column;
}

.map-square {
  border: 1px dashed rgba(107, 176, 255, 0.55);
  border-radius: 8px;
  padding: 0;
  background: linear-gradient(145deg, rgba(30, 67, 105, 0.86), rgba(22, 51, 83, 0.92));
  min-height: 280px;
  overflow: hidden;
}

.video-stats-grid {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.mini-kpi {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 8px;
  background: rgba(17, 47, 75, 0.56);
  padding: 8px;
}

.mini-kpi span {
  display: block;
  color: var(--sub);
  font-size: 12px;
}

.mini-kpi strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
}

.env-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.env-slot-card {
  min-height: 0;
}

.env-metric-card {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.env-metric-head {
  margin-bottom: 4px;
}

.chart-wrap {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(24, 56, 92, 0.66);
  padding: 8px;
}

.env-trend-item {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 10px;
  background: rgba(12, 40, 68, 0.48);
  padding: 6px 8px 4px;
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.env-trend-item.single {
  height: 100%;
}

.env-trend-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 2px;
}

.env-trend-title span {
  font-size: 12px;
  color: #d6ecff;
  font-weight: 600;
}

.env-trend-title em {
  font-style: normal;
  font-size: 11px;
  color: rgba(214, 230, 255, 0.72);
}

.env-trend-svg {
  width: 100%;
  height: 100%;
  min-height: 72px;
}

.legend {
  display: flex;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--sub);
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.bar-grid {
  display: grid;
  gap: 9px;
}

.bar-row {
  display: grid;
  grid-template-columns: 4.6rem 1fr 2rem;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.bar i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, rgba(126, 197, 255, 0.88), rgba(83, 213, 165, 0.86));
}


.agent-panel {
  display: grid;
  grid-template-columns: minmax(0, 2.1fr) minmax(20rem, 0.78fr);
  gap: 8px;
  align-items: stretch;
}

.main-col,
.side-col,
.side-card,
.monitor-card,
.overview-card {
  min-height: 0;
}

.main-col,
.side-col {
  display: grid;
  gap: 0.85rem;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.main-col {
  grid-template-rows: 1fr;
  min-height: 30rem;
}

.side-col {
  display: grid;
  grid-template-rows: minmax(8rem, 0.34fr) minmax(18rem, 1fr);
  gap: 0.85rem;
}

.agent-main-card {
  display: flex;
  flex-direction: column;
}

.hero-card {
  gap: 0.95rem;
  padding: 1rem;
  background:
    radial-gradient(circle at 12% 0%, rgba(126, 197, 255, 0.12), transparent 26%),
    linear-gradient(180deg, rgba(18, 48, 79, 0.86), rgba(11, 28, 48, 0.8));
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.08),
    0 20px 44px rgba(4, 12, 24, 0.16);
}

.summary-card,
.side-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(17, 46, 75, 0.82), rgba(13, 33, 56, 0.8));
  box-shadow: inset 0 0 0 1px rgba(126, 197, 255, 0.07);
}

.card-title-row,
.summary-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.card-title-row h3 {
  margin: 0 0 0.24rem;
}

.card-subtitle {
  margin: 0;
  color: var(--sub);
  line-height: 1.58;
  font-size: 0.88rem;
  max-width: 42rem;
}

.inline-tag,
.summary-updated,
.summary-tab,
.mini-action,
.summary-head,
.focus-tag {
  border: 1px solid rgba(126, 197, 255, 0.22);
  background: rgba(17, 47, 75, 0.78);
  color: #eaf6ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.42rem 0.8rem;
  border-radius: 999px;
  font-size: 0.78rem;
}

.summary-toolbar {
  margin: 0.15rem 0 0.7rem;
  align-items: center;
}

.summary-tab,
.mini-action,
.summary-head {
  cursor: pointer;
  transition: all 0.2s ease;
}

.summary-tab.active,
.summary-tab:hover,
.mini-action:hover,
.summary-head:hover {
  border-color: rgba(126, 197, 255, 0.42);
  background: rgba(34, 79, 118, 0.92);
}

.summary-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.66rem 0.8rem;
  border-radius: 12px;
  font-size: 0.82rem;
}

.summary-body {
  margin-top: 0.45rem;
}

.summary-section + .summary-section {
  margin-top: 0.62rem;
}

.summary-kpis,
.focus-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.summary-kpi,
.focus-card {
  padding: 0.78rem 0.84rem;
  border-radius: 14px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background: rgba(14, 42, 67, 0.56);
}

.focus-card span {
  display: block;
  margin-bottom: 0.24rem;
  color: rgba(196, 221, 242, 0.7);
  font-size: 0.75rem;
}


.hero-card {
  padding: 1.2rem;
  gap: 1.1rem;
}

.section-head,
.hero-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
}

.hero-head {
  align-items: center;
}

.hero-head h3 {
  margin: 0 0 0.24rem;
}

.hero-head p {
  margin: 0;
  color: var(--sub);
  line-height: 1.58;
  font-size: 0.88rem;
  max-width: 42rem;
}

.hero-head-side,
.service-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.service-chip,
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(126, 197, 255, 0.22);
  background: rgba(17, 47, 75, 0.78);
  color: #eaf6ff;
  border-radius: 999px;
  padding: 0.42rem 0.8rem;
  font-size: 0.78rem;
}

.status-pill.listening {
  border-color: rgba(248, 203, 113, 0.42);
  color: #f8cb71;
}

.status-pill.thinking,
.status-pill.speaking {
  border-color: rgba(83, 213, 165, 0.42);
  color: #8de7c0;
}

.hero-shell {
  position: relative;
  flex: 1;
  min-height: 32rem;
  height: 100%;
  overflow: hidden;
  border-radius: 30px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background:
    radial-gradient(circle at 80% 14%, rgba(126, 197, 255, 0.08), transparent 24%),
    radial-gradient(circle at 0% 100%, rgba(83, 213, 165, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(8, 25, 43, 0.96), rgba(7, 18, 32, 0.98));
  box-shadow: 0 22px 48px rgba(3, 10, 20, 0.28);
}

.hero-shell::before,
.hero-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-shell::before {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 24%),
    radial-gradient(circle at 20% 18%, rgba(126, 197, 255, 0.12), transparent 22%);
}

.hero-shell::after {
  inset: auto -8% -42% 44%;
  height: 72%;
  background: radial-gradient(circle, rgba(126, 197, 255, 0.12), rgba(126, 197, 255, 0));
  filter: blur(34px);
}

.hero-stage {
  height: 100%;
  min-height: 0;
  padding: 0.85rem;
}

.hero-card {
  min-height: 0;
}

.hero-shell :deep(.virtual-agent),
.hero-shell :deep(.stage-shell),
.hero-shell :deep(.digital-human-viewport),
.hero-shell :deep(.viewport-root) {
  height: 100% !important;
  min-height: 100% !important;
}

.hero-shell :deep(.chat-panel.stage) {
  background: transparent;
}

.hero-shell :deep(.chat-messages) {
  top: 5.6rem;
  left: 1.6rem;
  bottom: 1.7rem;
  width: min(19.5rem, calc(100% - 25rem));
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(9, 28, 47, 0.56), rgba(6, 18, 33, 0.42));
}

.hero-shell :deep(.chat-input) {
  right: 1.6rem;
  bottom: 1.7rem;
  width: min(19rem, 33vw);
  border-radius: 24px;
}

.hero-shell :deep(.realtime-banner) {
  right: 1.6rem;
  bottom: 12.4rem;
  width: min(19rem, 33vw);
  border-radius: 18px;
}

.hero-shell :deep(.chat-content) {
  font-size: 0.78rem;
}

.hero-shell :deep(.chat-input) {
  border-top: 1px solid rgba(126, 197, 255, 0.16);
}

.hero-shell :deep(.virtual-agent) {
  height: 100%;
}

.hero-shell :deep(.stage-shell) {
  min-height: 100%;
  height: 100%;
}

.hero-shell :deep(.digital-human-root),
.hero-shell :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
}

.panel-headline.small {
  margin-bottom: 6px;
}

.task-list {
  display: grid;
  gap: 8px;
  overflow: auto;
  min-height: 0;
}

.task-item {
  border-left: 3px solid var(--warn);
  border-radius: 8px;
  background: rgba(248, 203, 113, 0.12);
  padding: 8px 9px;
  font-size: 12px;
  line-height: 1.5;
}

.summary-card {
  overflow: auto;
}

.summary-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.summary-tab {
  border: 1px solid rgba(126, 197, 255, 0.3);
  background: rgba(17, 47, 75, 0.62);
  color: #eaf6ff;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.summary-tab.active {
  border-color: rgba(126, 197, 255, 0.64);
  background: rgba(34, 79, 118, 0.9);
}

.summary-kpis {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}

.summary-kpi {
  border: 1px solid rgba(126, 197, 255, 0.2);
  border-radius: 8px;
  background: rgba(17, 47, 75, 0.48);
  padding: 7px;
}

.summary-kpi span {
  display: block;
  color: var(--sub);
  font-size: 11px;
}

.summary-kpi strong {
  display: block;
  margin-top: 3px;
  font-size: 18px;
}

.summary-overview {
  margin: 8px 0;
  border: 1px solid rgba(126, 197, 255, 0.2);
  border-radius: 8px;
  background: rgba(17, 47, 75, 0.42);
  padding: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.trend-rows {
  display: grid;
  gap: 6px;
}

.trend-row {
  display: grid;
  grid-template-columns: 3.6rem 1fr 2rem;
  gap: 6px;
  align-items: center;
  font-size: 12px;
}

.trend-bar {
  height: 7px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.trend-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(126, 197, 255, 0.88), rgba(83, 213, 165, 0.88));
}

.focus-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0;
}

.focus-tag {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  color: #d6ecff;
  background: rgba(17, 47, 75, 0.5);
}

.advice-list {
  margin: 0;
  padding-left: 1.1rem;
  color: #ebf6ff;
  line-height: 1.62;
  font-size: 0.84rem;
}

.table-wrap {
  overflow: auto;
  max-height: 100%;
}

.detail-table-wrap {
  flex: 1;
  min-height: 0;
  margin-top: 4px;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.info-table th,
.info-table td {
  border-bottom: 1px solid rgba(126, 197, 255, 0.16);
  padding: 8px 6px;
  text-align: left;
}

.info-table th {
  color: #cde8ff;
  font-weight: 600;
}

.state-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
}

.state-chip.done {
  color: #6ce2b2;
  border: 1px solid rgba(108, 226, 178, 0.45);
  background: rgba(108, 226, 178, 0.12);
}

.state-chip.pending {
  color: #f8cb71;
  border: 1px solid rgba(248, 203, 113, 0.45);
  background: rgba(248, 203, 113, 0.12);
}

.btn {
  border: 1px solid var(--line);
  border-radius: 7px;
  padding: 5px 9px;
  font-size: 12px;
  color: var(--text);
  background: rgba(26, 60, 97, 0.82);
  cursor: pointer;
}

.btn.primary {
  border-color: rgba(99, 184, 255, 0.84);
  background: rgba(126, 197, 255, 0.22);
}

.focus-modal {
  position: fixed;
  inset: 0;
  background: rgba(3, 12, 24, 0.74);
  display: none;
  align-items: center;
  justify-content: center;
  padding: 18px;
  z-index: 12000;
}

.focus-shell {
  width: min(1100px, 96vw);
  border: 1px solid var(--line);
  border-radius: 10px;
  background: rgba(8, 30, 58, 0.95);
  padding: 10px;
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 10px;
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

.focus-panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(9, 34, 63, 0.82);
  padding: 9px;
}

.focus-title {
  margin: 0 0 8px;
  font-size: 13px;
}

.ctrl-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.focus-close {
  margin-top: 10px;
  width: 100%;
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

.muted {
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

@media (max-width: 1400px) {
  .alarm-panel,
  .video-panel,
  .env-panel,
  .agent-panel {
    grid-template-columns: 1fr;
  }

  .env-chart-card,
  .env-slot-card,
  .env-table-card {
    grid-column: auto;
    grid-row: auto;
  }

  .main-col,
  .side-col {
    height: auto;
    overflow: visible;
    grid-template-rows: auto;
  }

  .hero-shell {
    min-height: 28rem;
  }

  .hero-shell {
    min-height: 34rem;
  }

  .section-head,
  .hero-head,
  .card-title-row,
  .summary-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 900px) {
  .monitor-grid-large {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .nav-current {
    font-size: 15px;
  }

  .video-stats-grid {
    grid-template-columns: 1fr;
  }

  .summary-kpis,
  .focus-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .monitor-grid-large {
    grid-template-columns: 1fr;
  }

  .focus-shell {
    grid-template-columns: 1fr;
  }
}
</style>
