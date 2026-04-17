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
                :class="{ 'tile-breathing': true, 'tile-alert': tileHasAlert(tile.name) }"
                @click="openFocus(tile)"
              >
                <video
                  :ref="(el) => setTileVideoRef(tile.name, el as HTMLVideoElement | null)"
                  class="tile-video"
                  muted
                  autoplay
                  playsinline
                ></video>
                <div v-if="!tile.streamUrl" class="tile-empty-state">
                  <svg class="tile-cam-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9A2.25 2.25 0 0013.5 5.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"/></svg>
                  <span>等待接入</span>
                </div>
                <div class="tile-overlay">
                  <div class="tile-title">{{ tile.name }}</div>
                  <div class="tile-sub">{{ tile.streamUrl ? '实时画面' : '未配置流地址' }}</div>
                </div>
              </div>
            </div>
          </article>

          <article class="card video-side">
            <h3 class="map-title">点位地图联动 <span class="live-dot"></span></h3>
            <div class="map-square">
              <AMapLinkage3D :points="mapPoints" @point-click="onMapPointClick" />
            </div>
            <div class="video-stats-grid">
              <div class="mini-kpi kpi-online"><span>在线</span><strong>{{ onlineCount }}</strong></div>
              <div class="mini-kpi kpi-offline"><span>离线</span><strong>{{ offlineCount }}</strong></div>
              <div class="mini-kpi kpi-total"><span>总监控点</span><strong>{{ monitors.length }}</strong></div>
              <div class="mini-kpi kpi-preview"><span>当前预览</span><strong>{{ cameraTiles.length }}</strong></div>
            </div>
            <div class="event-stream">
              <div class="event-stream-head">
                <span class="event-stream-title">AI 实时事件</span>
                <span class="event-stream-count">{{ recentEvents.length }} 条</span>
              </div>
              <div class="event-stream-list">
                <div v-for="(ev, idx) in recentEvents" :key="idx" class="event-item" :class="'event-' + ev.severity">
                  <span class="event-time">{{ ev.time }}</span>
                  <span class="event-dot" :class="'dot-' + ev.severity"></span>
                  <span class="event-text">{{ ev.text }}</span>
                </div>
                <div v-if="!recentEvents.length" class="event-item event-empty">
                  <span class="event-text">暂无事件，系统运行正常</span>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'env'" class="panel env-panel">
          <article class="card env-overview-card">
            <div class="env-overview-head">
              <div>
                <p class="panel-overline">ENVIRONMENT COMMAND</p>
                <h3>环境态势总览</h3>
                <p class="env-overview-copy">{{ envSituationSummary }}</p>
              </div>
              <div class="env-overview-status">
                <span class="overview-pill" :class="envSituationTone">{{ envSituationLabel }}</span>
                <span class="env-overview-updated">最新样本 {{ latestEnvSampleLabel }}</span>
              </div>
            </div>

            <div class="env-overview-grid">
              <article
                v-for="item in envOverviewCards"
                :key="item.label"
                class="env-overview-stat"
                :class="item.tone"
              >
                <div class="env-overview-top">
                  <span>{{ item.label }}</span>
                  <em>{{ item.badge }}</em>
                </div>
                <div class="env-overview-value">
                  <strong>{{ item.value }}</strong>
                  <span>{{ item.unit }}</span>
                </div>
                <div class="env-overview-meter">
                  <i :style="{ width: `${item.progress}%`, background: item.color }"></i>
                </div>
                <p>{{ item.detail }}</p>
              </article>
            </div>
          </article>

          <article
            v-for="metric in envTrendMetrics"
            :key="metric.key"
            class="card env-metric-card"
            :class="`env-metric-${metric.key}`"
          >
            <div class="panel-headline small env-metric-head">
              <p class="panel-overline env-metric-kicker">TREND WATCH</p>
              <h3>{{ metric.label }}趋势</h3>
              <div class="env-live-badge" :style="{ color: metric.color }">
                <strong>{{ envCurrentValues[metric.key] }}</strong>
                <span>{{ metric.unit }}</span>
              </div>
              <div v-if="metric.key === 'aqi'" class="chart-filter">
                <span>时间段</span>
                <select v-model="envTrendRange">
                  <option value="day">今日</option>
                  <option value="week">近7天</option>
                  <option value="month">近30天</option>
                </select>
              </div>
              <span v-else>{{ metric.unit }}</span>
              <span class="overview-pill metric-pill" :class="envMetricSignals[metric.key].tone">{{ envMetricSignals[metric.key].label }}</span>
              <span class="env-metric-note">{{ envMetricSignals[metric.key].note }}</span>
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
            <p class="panel-overline">PARKING ANALYTICS</p>
            <h3>车位占用数据</h3>
            <div class="env-slot-meta">
              <span class="overview-pill" :class="parkingOccupancyTone">{{ parkingOccupancyLabel }}</span>
              <span class="parking-head-text">峰值区域 {{ busiestParkingZone.name }}</span>
            </div>
            <div class="parking-dashboard">
              <div class="parking-ring-wrap">
                <svg class="parking-ring" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(126,197,255,0.12)" stroke-width="10" />
                  <circle cx="60" cy="60" r="50" fill="none"
                    :stroke="parkingOccupancyColor"
                    stroke-width="10"
                    stroke-linecap="round"
                    :stroke-dasharray="`${parkingOccupancy * 3.14} 314`"
                    transform="rotate(-90 60 60)"
                    style="transition: stroke-dasharray 0.6s ease"
                  />
                  <text x="60" y="54" text-anchor="middle" fill="#eaf6ff" font-size="22" font-weight="700">{{ parkingOccupancy }}%</text>
                  <text x="60" y="72" text-anchor="middle" fill="rgba(214,230,255,0.6)" font-size="10">占用率</text>
                </svg>
                <div class="parking-summary">
                  <span>总量 <strong>{{ parkingTotal }}</strong></span>
                  <span>已用 <strong>{{ parkingUsed }}</strong></span>
                  <span>空闲 <strong>{{ parkingFree }}</strong></span>
                </div>
              </div>
              <div class="parking-detail-stack">
                <div class="parking-stat-grid">
                  <article class="parking-stat-card">
                    <span>当前占用率</span>
                    <strong>{{ parkingOccupancy }}%</strong>
                    <p>整体车位压力 {{ parkingOccupancyLabel }}</p>
                  </article>
                  <article class="parking-stat-card">
                    <span>空闲引导</span>
                    <strong>{{ parkingFree }}</strong>
                    <p>优先分流至 {{ busiestParkingZone.name }}</p>
                  </article>
                </div>

                <div class="bar-grid parking-zone-grid">
                  <div class="bar-row parking-bar-row" v-for="item in parkingZoneCards" :key="item.name">
                    <div class="bar-copy">
                      <span>{{ item.name }}</span>
                      <em>{{ item.statusText }}</em>
                    </div>
                    <div class="bar"><i :style="{ width: `${item.percent}%`, background: item.color }"></i></div>
                    <div class="bar-value">
                      <strong>{{ item.value }}</strong>
                      <small>{{ item.free }} 空闲</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </article>

          <article class="card env-comfort-card">
            <div class="comfort-head">
              <h3>环境舒适度</h3>
              <span class="comfort-label" :style="{ color: comfortColor }">{{ comfortLabel }}</span>
            </div>
            <div class="comfort-layout">
              <div class="comfort-score-panel">
                <div class="comfort-score" :style="{ '--score-color': comfortColor }">
                  <strong>{{ comfortScore }}</strong>
                  <span>/ 100</span>
                </div>
                <p class="comfort-score-note">当前舒适度{{ comfortLabel }}，建议结合空气质量与湿度变化持续联动巡检。</p>
              </div>
              <div class="comfort-factor-panel">
                <div class="comfort-factors">
                  <div class="comfort-factor">
                    <span>AQI</span>
                    <div class="comfort-bar"><i :style="{ width: `${Math.min(100, envCurrentValues.aqi)}%`, background: '#63b8ff' }"></i></div>
                  </div>
                  <div class="comfort-factor">
                    <span>湿度</span>
                    <div class="comfort-bar"><i :style="{ width: `${envCurrentValues.humidity}%`, background: '#53d5a5' }"></i></div>
                  </div>
                  <div class="comfort-factor">
                    <span>PM2.5</span>
                    <div class="comfort-bar"><i :style="{ width: `${Math.min(100, envCurrentValues.pm25 * 1.2)}%`, background: '#f8cb71' }"></i></div>
                  </div>
                </div>
                <div class="comfort-tips">
                  <span v-for="tip in comfortTips" :key="tip" class="comfort-tip">{{ tip }}</span>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'agent'" class="panel agent-panel">
            <article class="card hero-card hero-card-clean">
              <div class="section-head hero-head hero-head-clean">
                <div class="hero-head-primary">
                  <p class="panel-overline">AI AGENT</p>
                  <h3>数字助手</h3>
                  <p>数字助手常驻在线，支持语音或文字发起交互，可联动平台能力完成告警查询、监控查看与智能问答。</p>
                  <div class="service-strip service-strip-compact">
                    <span v-for="item in serviceHighlights" :key="item" class="service-chip">{{ item }}</span>
                  </div>
                </div>
                <div class="hero-head-side">
                  <span class="status-pill" :class="currentStageStatus">{{ agentStatusLabel }}</span>
                  <span class="status-pill subtle">{{ agentConversationLabel }}</span>
                </div>
              </div>

              <div class="agent-brief-bar">
                <span class="agent-brief-label">当前提示</span>
                <p>{{ agentPreview }}</p>
              </div>

              <div class="hero-shell hero-shell-clean">
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

          <aside v-if="false" class="side-col">
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

// ====== 新增：视频页 AI 事件流 ======
const recentEvents = computed(() => {
  const list = alarmStore.getAlarmList || []
  return list.slice(0, 5).map((item: any) => {
    const raw = item.date || item.createTime || ''
    let time = '--:--'
    if (raw) {
      const d = new Date(raw)
      if (!isNaN(d.getTime())) {
        time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      }
    }
    const level = Number(item.level || 1)
    const severity = level >= 3 ? 'high' : level === 2 ? 'mid' : 'low'
    return {
      time,
      text: `${item.department || '未标注'} ${item.eventName || '事件'}`,
      severity,
    }
  })
})

const tileHasAlert = (tileName: string) => {
  const list = alarmStore.getAlarmList || []
  return list.some((item: any) => {
    const dept = String(item.department || '').toLowerCase()
    const name = tileName.toLowerCase()
    return dept && name.includes(dept.slice(0, 2))
  })
}

// ====== 新增：环境实时数值 ======
const envCurrentValues = computed(() => {
  const series = envTrendSeries.value
  const last = series[series.length - 1]
  return {
    aqi: last?.aqi ?? 0,
    humidity: last?.humidity ?? 0,
    pm25: last?.pm25 ?? 0,
  }
})

// ====== 新增：车位仪表盘 ======
const parkingTotal = 160
const parkingUsed = computed(() => parkingBars.value.reduce((sum, item) => sum + item.value, 0))
const parkingFree = computed(() => Math.max(parkingTotal - parkingUsed.value, 0))
const parkingOccupancy = computed(() => Math.round((parkingUsed.value / parkingTotal) * 100))
const parkingOccupancyColor = computed(() => {
  const pct = parkingOccupancy.value
  if (pct > 80) return '#ff8d8d'
  if (pct > 50) return '#f8cb71'
  return '#53d5a5'
})

// ====== 新增：环境舒适度评分 ======
const comfortScore = computed(() => {
  const { aqi, humidity, pm25 } = envCurrentValues.value
  const aqiScore = Math.max(0, 100 - aqi)
  const humScore = humidity >= 40 && humidity <= 70 ? 100 : Math.max(0, 100 - Math.abs(humidity - 55) * 2)
  const pmScore = Math.max(0, 100 - pm25)
  return Math.round(aqiScore * 0.4 + humScore * 0.3 + pmScore * 0.3)
})
const comfortColor = computed(() => {
  const s = comfortScore.value
  if (s >= 80) return '#53d5a5'
  if (s >= 60) return '#f8cb71'
  return '#ff8d8d'
})
const comfortLabel = computed(() => {
  const s = comfortScore.value
  if (s >= 80) return '优良'
  if (s >= 60) return '一般'
  return '较差'
})

type StatusTone = 'good' | 'warn' | 'alert' | 'info'

interface MetricSignal {
  label: string
  note: string
  tone: StatusTone
}

const latestEnvSampleLabel = computed(() => {
  const series = envTrendSeries.value
  return series[series.length - 1]?.label || '--'
})

const buildMetricSignal = (key: EnvMetricKey, value: number): MetricSignal => {
  if (key === 'aqi') {
    if (value <= 75) return { label: '稳定', note: '空气质量保持在安全区间', tone: 'good' }
    if (value <= 90) return { label: '关注', note: '建议加强新风与巡检频率', tone: 'warn' }
    return { label: '预警', note: '建议检查通风与污染源状态', tone: 'alert' }
  }

  if (key === 'humidity') {
    if (value >= 45 && value <= 65) return { label: '舒适', note: '湿度处于舒适区间', tone: 'good' }
    if (value >= 35 && value <= 75) return { label: '波动', note: '可视情况联动除湿或加湿', tone: 'warn' }
    return { label: '异常', note: '建议联动空调与新风设备', tone: 'alert' }
  }

  if (value <= 45) return { label: '良好', note: '颗粒物控制平稳', tone: 'good' }
  if (value <= 60) return { label: '关注', note: '建议增加局部清洁频率', tone: 'warn' }
  return { label: '偏高', note: '建议加强净化和地库通风', tone: 'alert' }
}

const envMetricSignals = computed<Record<EnvMetricKey, MetricSignal>>(() => ({
  aqi: buildMetricSignal('aqi', envCurrentValues.value.aqi),
  humidity: buildMetricSignal('humidity', envCurrentValues.value.humidity),
  pm25: buildMetricSignal('pm25', envCurrentValues.value.pm25),
}))

const parkingZoneCards = computed(() => parkingBars.value.map((item) => {
  const estimatedTotal = item.percent > 0 ? Math.max(item.value, Math.round(item.value / (item.percent / 100))) : item.value
  const free = Math.max(estimatedTotal - item.value, 0)
  let tone: StatusTone = 'good'
  let statusText = '余量充足'
  let color = 'linear-gradient(90deg, rgba(126, 197, 255, 0.9), rgba(83, 213, 165, 0.85))'

  if (item.percent >= 80) {
    tone = 'alert'
    statusText = '接近满载'
    color = 'linear-gradient(90deg, rgba(255, 164, 164, 0.95), rgba(255, 108, 108, 0.88))'
  } else if (item.percent >= 60) {
    tone = 'warn'
    statusText = '建议分流'
    color = 'linear-gradient(90deg, rgba(248, 216, 132, 0.95), rgba(248, 203, 113, 0.88))'
  }

  return {
    ...item,
    estimatedTotal,
    free,
    tone,
    statusText,
    color,
  }
}))

const busiestParkingZone = computed(() => {
  const zones = parkingZoneCards.value
  if (!zones.length) {
    return {
      name: '--',
      percent: 0,
      estimatedTotal: 0,
      free: 0,
      value: 0,
      tone: 'info' as StatusTone,
      statusText: '--',
      color: 'linear-gradient(90deg, rgba(126, 197, 255, 0.9), rgba(83, 213, 165, 0.85))',
    }
  }
  return zones.reduce((max, item) => (item.percent > max.percent ? item : max), zones[0])
})

const parkingOccupancyTone = computed<StatusTone>(() => {
  if (parkingOccupancy.value >= 80) return 'alert'
  if (parkingOccupancy.value >= 60) return 'warn'
  return 'good'
})

const parkingOccupancyLabel = computed(() => {
  if (parkingOccupancy.value >= 80) return '接近满载'
  if (parkingOccupancy.value >= 60) return '压力偏高'
  return '余量充足'
})

const envSituationTone = computed<StatusTone>(() => {
  if (comfortScore.value < 60 || parkingOccupancy.value >= 85) return 'alert'
  if (comfortScore.value < 80 || parkingOccupancy.value >= 65) return 'warn'
  return 'good'
})

const envSituationLabel = computed(() => {
  if (envSituationTone.value === 'alert') return '需要干预'
  if (envSituationTone.value === 'warn') return '建议关注'
  return '运行平稳'
})

const envSituationSummary = computed(() => {
  const zoneName = busiestParkingZone.value.name
  return `当前舒适度 ${comfortScore.value} 分，环境指标整体 ${comfortLabel.value}，车位调度建议优先关注 ${zoneName}。`
})

const envOverviewCards = computed(() => [
  {
    label: 'AQI',
    value: envCurrentValues.value.aqi,
    unit: '指数',
    badge: envMetricSignals.value.aqi.label,
    detail: envMetricSignals.value.aqi.note,
    tone: envMetricSignals.value.aqi.tone,
    progress: Math.min(100, Math.round((envCurrentValues.value.aqi / 120) * 100)),
    color: 'linear-gradient(90deg, rgba(126, 232, 255, 0.95), rgba(99, 184, 255, 0.88))',
  },
  {
    label: '湿度',
    value: envCurrentValues.value.humidity,
    unit: '%',
    badge: envMetricSignals.value.humidity.label,
    detail: envMetricSignals.value.humidity.note,
    tone: envMetricSignals.value.humidity.tone,
    progress: Math.min(100, envCurrentValues.value.humidity),
    color: 'linear-gradient(90deg, rgba(118, 235, 191, 0.95), rgba(83, 213, 165, 0.88))',
  },
  {
    label: 'PM2.5',
    value: envCurrentValues.value.pm25,
    unit: 'ug/m3',
    badge: envMetricSignals.value.pm25.label,
    detail: envMetricSignals.value.pm25.note,
    tone: envMetricSignals.value.pm25.tone,
    progress: Math.min(100, Math.round(envCurrentValues.value.pm25 * 1.6)),
    color: 'linear-gradient(90deg, rgba(248, 216, 132, 0.95), rgba(248, 203, 113, 0.88))',
  },
  {
    label: '空闲车位',
    value: parkingFree.value,
    unit: '个',
    badge: parkingOccupancyLabel.value,
    detail: `峰值区域 ${busiestParkingZone.value.name}，可继续做余量分流`,
    tone: parkingOccupancyTone.value,
    progress: Math.min(100, Math.round((parkingFree.value / parkingTotal) * 100)),
    color: 'linear-gradient(90deg, rgba(149, 223, 255, 0.95), rgba(86, 189, 255, 0.86))',
  },
])

const comfortTips = computed(() => {
  const tips: string[] = []
  if (envMetricSignals.value.aqi.tone !== 'good') tips.push('建议提高新风与巡检频率')
  if (envMetricSignals.value.humidity.tone !== 'good') tips.push('湿度波动明显，注意联动空调除湿')
  if (envMetricSignals.value.pm25.tone !== 'good') tips.push('建议加强地库清洁与空气净化')
  if (parkingOccupancy.value >= 75) tips.push(`车位压力偏高，优先引导至 ${busiestParkingZone.value.name} 之外区域`)
  if (!tips.length) tips.push('当前环境指标平稳，可保持现有巡检节奏')
  return tips.slice(0, 3)
})

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
const chatQuickReplies = ['未处理告警有多少', '查看最近告警', '查询车库环境状态']
const serviceHighlights = ['语音问答', '告警联动', '监控查询']
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

const pendingAlarmCount = computed(() => {
  const list = alarmStore.getAlarmList || []
  return list.filter((item: any) => item.deal !== '完成' && item.status !== 1).length
})

const summaryHandleRate = computed(() => {
  const total = selectedSummaryView.value.total
  if (!total) return 0
  return Math.round((selectedSummaryView.value.handled / total) * 100)
})

const agentConversationLabel = computed(() => {
  if (isRealtimeConversationActive.value) return '实时会话已开启'
  if (currentStageStatus.value === 'listening') return '等待语音输入'
  if (currentStageStatus.value === 'thinking') return '正在联动平台能力'
  if (currentStageStatus.value === 'speaking') return '结果正在播报'
  return '文本 / 单次语音'
})

const agentInsightCards = computed(() => [
  {
    label: '会话模式',
    value: isRealtimeConversationActive.value ? '实时语音' : '文本协同',
    detail: '支持连续对话、告警查询与联动问答',
    tone: isRealtimeConversationActive.value ? 'good' : 'info',
  },
  {
    label: '待处理告警',
    value: String(pendingAlarmCount.value),
    detail: pendingAlarmCount.value ? '建议优先闭环高等级事件' : '当前无积压，可继续巡检',
    tone: pendingAlarmCount.value >= 4 ? 'alert' : pendingAlarmCount.value > 0 ? 'warn' : 'good',
  },
  {
    label: '周期处置率',
    value: `${summaryHandleRate.value}%`,
    detail: `${activeSummaryRange.value === 'week' ? '最近一周' : '最近一月'}摘要已同步`,
    tone: summaryHandleRate.value >= 85 ? 'good' : summaryHandleRate.value >= 60 ? 'warn' : 'info',
  },
  {
    label: '重点区域',
    value: selectedSummaryView.value.topArea || '--',
    detail: `高优先事件 ${selectedSummaryView.value.highLevel} 起`,
    tone: selectedSummaryView.value.highLevel > 0 ? 'warn' : 'info',
  },
])

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
  height: auto;
  min-height: 0;
  align-content: start;
}

:deep(.grid > *) {
  min-width: 0;
}

.page-shell {
  display: grid;
  grid-template-rows: auto auto;
  gap: 14px;
  min-height: 0;
  min-height: 100%;
  height: auto;
  align-content: start;
}

.nav-bar {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(12, 31, 52, 0.96), rgba(8, 20, 35, 0.92));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 18px 32px rgba(2, 10, 20, 0.22);
  padding: 14px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.nav-bar::before,
.nav-bar::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.nav-bar::before {
  inset: 0 auto auto 0;
  width: 38%;
  height: 1px;
  background: linear-gradient(90deg, rgba(126, 232, 255, 0.6), rgba(126, 232, 255, 0));
}

.nav-bar::after {
  inset: auto 8% -72px auto;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(103, 190, 255, 0.16), transparent 70%);
  filter: blur(10px);
}

.nav-left {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.nav-btn {
  position: relative;
  border: 1px solid rgba(126, 197, 255, 0.2);
  background:
    linear-gradient(180deg, rgba(15, 39, 64, 0.82), rgba(9, 25, 42, 0.84));
  color: #eaf6ff;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 13px;
  letter-spacing: 0.08em;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.nav-btn.active,
.nav-btn:hover {
  border-color: rgba(126, 232, 255, 0.42);
  background:
    linear-gradient(180deg, rgba(33, 94, 143, 0.96), rgba(18, 55, 88, 0.92));
  color: #faffff;
  transform: translateY(-1px);
  box-shadow:
    0 18px 28px rgba(2, 10, 20, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.nav-current {
  padding: 10px 16px;
  border-radius: 18px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(17, 47, 75, 0.34);
  font-family: var(--font-data);
  font-size: 24px;
  font-weight: 700;
  color: #d9ecff;
  letter-spacing: 0.08em;
  text-shadow: 0 0 16px rgba(103, 190, 255, 0.22);
}

.content-shell {
  min-height: 0;
  height: auto;
}

.panel {
  min-height: 0;
  height: auto;
}

.panel .card {
  background:
    radial-gradient(circle at 12% -10%, rgba(126, 197, 255, 0.12), transparent 34%),
    linear-gradient(180deg, rgba(14, 33, 56, 0.88), rgba(8, 20, 35, 0.92));
  border-radius: 24px;
  border-color: rgba(126, 197, 255, 0.18);
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.05),
    0 18px 34px rgba(2, 10, 20, 0.2);
  padding: 18px;
}

.alarm-panel {
  display: grid;
  grid-template-columns: 0.58fr 1.42fr;
  gap: 14px;
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
  gap: 14px;
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
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 14px;
  background: rgba(9, 25, 42, 0.76);
  color: #eaf6ff;
  font-size: 12px;
  padding: 8px 12px;
}

.chart-mini-action {
  min-width: 118px;
  padding: 8px 14px;
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
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  color: #d9edff;
  background: rgba(17, 47, 75, 0.58);
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.table-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.table-filters input {
  width: 11rem;
}

.table-filters input,
.table-filters select {
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 16px;
  background: rgba(9, 25, 42, 0.76);
  color: #eaf6ff;
  font-size: 12px;
  padding: 9px 12px;
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
  padding: 4px 10px;
  font-size: 11px;
  border: 1px solid transparent;
  letter-spacing: 0.06em;
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
  min-height: 260px;
  height: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
  gap: 14px;
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
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  border-radius: 20px;
  background: rgba(9, 24, 42, 0.52);
}

.chart-item h4 {
  font-size: 14px;
  color: var(--text);
  margin: 0;
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
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(126, 197, 255, 0.12);
}

.panel-headline span {
  color: var(--sub);
  font-size: 12px;
}

.video-panel {
  display: grid;
  grid-template-columns: 1.65fr 1fr;
  gap: 14px;
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
  min-height: 190px;
  border-radius: 22px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background:
    radial-gradient(circle at 20% 16%, rgba(126, 197, 255, 0.14), transparent 28%),
    linear-gradient(145deg, rgba(12, 31, 52, 0.96), rgba(7, 18, 32, 0.98));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 16px 28px rgba(2, 10, 20, 0.16);
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
  background:
    linear-gradient(180deg, rgba(3, 10, 18, 0), rgba(3, 10, 18, 0.84));
  padding: 28px 16px 14px;
  backdrop-filter: blur(6px);
}

.tile-title {
  font-weight: 600;
  text-align: center;
  font-size: 15px;
  letter-spacing: 0.06em;
}

.tile-sub {
  margin-top: 6px;
  color: var(--sub);
  font-size: 12px;
  text-align: center;
}

.video-side {
  display: flex;
  flex-direction: column;
}

.map-square {
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 22px;
  padding: 0;
  background:
    radial-gradient(circle at 20% 12%, rgba(126, 197, 255, 0.1), transparent 28%),
    linear-gradient(145deg, rgba(12, 31, 52, 0.96), rgba(7, 18, 32, 0.98));
  min-height: 320px;
  overflow: hidden;
}

.video-stats-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.mini-kpi {
  min-height: 92px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(16, 40, 66, 0.72), rgba(9, 22, 39, 0.8));
  padding: 14px 14px 14px 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.mini-kpi span {
  display: block;
  color: var(--sub);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.mini-kpi strong {
  display: block;
  margin-top: 8px;
  font-family: var(--font-data);
  font-size: 28px;
  letter-spacing: 0.08em;
}

.panel-overline {
  margin: 0 0 0.45rem;
  font-size: 0.68rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(183, 219, 247, 0.58);
}

.overview-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.42rem 0.82rem;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(14, 42, 67, 0.5);
  color: #eaf6ff;
  font-size: 0.76rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  white-space: nowrap;
}

.overview-pill.good {
  color: #9ff0c8;
  border-color: rgba(83, 213, 165, 0.32);
  background: rgba(36, 84, 67, 0.28);
}

.overview-pill.warn {
  color: #ffe4a2;
  border-color: rgba(248, 203, 113, 0.34);
  background: rgba(96, 74, 33, 0.28);
}

.overview-pill.alert {
  color: #ffc0c0;
  border-color: rgba(255, 141, 141, 0.36);
  background: rgba(98, 42, 42, 0.26);
}

.overview-pill.info {
  color: #dff1ff;
}

.env-overview-card {
  grid-column: 1 / -1;
  display: grid;
  gap: 1.2rem;
  padding: 1.35rem 1.4rem 1.45rem;
  background:
    radial-gradient(circle at 0% 0%, rgba(126, 197, 255, 0.18), transparent 24%),
    radial-gradient(circle at 100% 100%, rgba(83, 213, 165, 0.1), transparent 20%),
    linear-gradient(135deg, rgba(15, 37, 61, 0.96), rgba(8, 21, 36, 0.92));
  border-color: rgba(126, 197, 255, 0.22);
}

.env-overview-head,
.env-overview-status,
.env-slot-meta {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.9rem;
}

.env-overview-status {
  flex-direction: column;
  align-items: flex-end;
}

.env-overview-copy,
.env-overview-updated,
.env-metric-note,
.parking-head-text {
  margin: 0;
  color: rgba(214, 230, 255, 0.72);
  font-size: 0.82rem;
  line-height: 1.55;
}

.env-overview-updated {
  font-size: 0.74rem;
  color: rgba(183, 219, 247, 0.52);
}

.env-overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.env-overview-stat {
  min-height: 11rem;
  padding: 1.15rem 1.1rem 1.05rem;
  border-radius: 20px;
  border: 1px solid rgba(126, 197, 255, 0.14);
  background:
    linear-gradient(180deg, rgba(16, 43, 70, 0.62), rgba(9, 24, 40, 0.7));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 12px 28px rgba(3, 10, 20, 0.16);
}

.env-overview-stat.good {
  border-color: rgba(83, 213, 165, 0.22);
}

.env-overview-stat.warn {
  border-color: rgba(248, 203, 113, 0.24);
}

.env-overview-stat.alert {
  border-color: rgba(255, 141, 141, 0.24);
}

.env-overview-top,
.env-overview-value {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
}

.env-overview-top span {
  color: rgba(214, 230, 255, 0.76);
  font-size: 0.8rem;
}

.env-overview-top em {
  font-style: normal;
  color: rgba(214, 230, 255, 0.54);
  font-size: 0.72rem;
}

.env-overview-value {
  margin: 0.68rem 0 0.65rem;
}

.env-overview-value strong {
  font-size: 2rem;
  font-family: var(--font-data);
  letter-spacing: 0.08em;
  color: #f3fbff;
}

.env-overview-value span {
  color: rgba(183, 219, 247, 0.66);
  font-size: 0.78rem;
}

.env-overview-meter {
  height: 0.42rem;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.env-overview-meter i {
  display: block;
  height: 100%;
  border-radius: inherit;
  box-shadow: 0 0 18px rgba(126, 197, 255, 0.24);
}

.env-overview-stat p {
  margin: 0.72rem 0 0;
  color: rgba(214, 230, 255, 0.66);
  font-size: 0.78rem;
  line-height: 1.6;
}

.env-panel {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  align-items: start;
}

.env-slot-card {
  min-height: 0;
  grid-column: span 2;
  padding: 1.3rem 1.35rem 1.35rem;
}

.env-comfort-card {
  min-height: 0;
  padding: 1.25rem 1.35rem 1.3rem;
}

.env-metric-card {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  min-height: 17.5rem;
  overflow: hidden;
  padding: 1rem 1.05rem 1rem;
  background:
    radial-gradient(circle at 100% 0%, rgba(126, 197, 255, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(14, 34, 58, 0.92), rgba(8, 20, 35, 0.96));
}

.env-metric-head {
  margin-bottom: 0.95rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem 0.95rem;
}

.env-metric-kicker {
  width: 100%;
  margin-bottom: 0;
}

.env-metric-head h3 {
  margin: 0;
}

.metric-pill {
  margin-left: auto;
}

.env-metric-note {
  width: 100%;
  font-size: 0.78rem;
}

.chart-wrap {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(12, 30, 50, 0.68);
  padding: 12px;
}

.env-trend-item {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 20px;
  background:
    radial-gradient(circle at 50% 0%, rgba(126, 197, 255, 0.08), transparent 30%),
    rgba(12, 40, 68, 0.48);
  padding: 0.95rem 1rem 0.72rem;
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.env-trend-item.single {
  height: auto;
  min-height: 13.25rem;
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
  height: auto;
  min-height: 156px;
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
  gap: 0.7rem;
}

.bar-row {
  display: grid;
  grid-template-columns: minmax(5.2rem, 6rem) 1fr auto;
  gap: 0.8rem;
  align-items: center;
  font-size: 12px;
  padding: 0.78rem 0.9rem;
  border-radius: 18px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background: rgba(13, 36, 58, 0.48);
}

.bar-row span {
  color: #e7f5ff;
  font-weight: 600;
}

.bar-row strong {
  color: #f3fbff;
  font-family: var(--font-data);
  letter-spacing: 0.08em;
  font-size: 1rem;
}

.bar {
  height: 0.62rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.bar i {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, rgba(126, 197, 255, 0.88), rgba(83, 213, 165, 0.86));
  border-radius: inherit;
  box-shadow: 0 0 18px rgba(126, 197, 255, 0.2);
}

/* ====== 1. 视频卡片呼吸灯 ====== */
@keyframes tile-breathe {
  0%, 100% { border-color: rgba(107, 176, 255, 0.35); box-shadow: 0 0 0 0 rgba(99, 184, 255, 0); }
  50% { border-color: rgba(107, 176, 255, 0.65); box-shadow: 0 0 12px 0 rgba(99, 184, 255, 0.15); }
}

@keyframes tile-alert-pulse {
  0%, 100% { border-color: rgba(255, 120, 120, 0.5); box-shadow: 0 0 0 0 rgba(255, 100, 100, 0); }
  50% { border-color: rgba(255, 100, 100, 0.85); box-shadow: 0 0 18px 0 rgba(255, 80, 80, 0.25); }
}

.tile-breathing {
  animation: tile-breathe 3.5s ease-in-out infinite;
  border-style: solid;
}

.tile-alert {
  animation: tile-alert-pulse 1.8s ease-in-out infinite;
}

.tile-empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: rgba(168, 198, 232, 0.4);
  pointer-events: none;
}

.tile-cam-icon {
  width: 42px;
  height: 42px;
  opacity: 0.5;
}

.tile-empty-state span {
  font-size: 12px;
  letter-spacing: 1px;
}

/* ====== 2. 地图标题脉冲点 ====== */
@keyframes live-pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.8); opacity: 0.4; }
  100% { transform: scale(1); opacity: 1; }
}

.map-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #53d5a5;
  border-radius: 50%;
  animation: live-pulse 2s ease-in-out infinite;
  box-shadow: 0 0 6px rgba(83, 213, 165, 0.6);
}

/* ====== 3. KPI 彩色竖线 ====== */
.mini-kpi {
  position: relative;
  padding-left: 14px;
  font-variant-numeric: tabular-nums;
}

.mini-kpi::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 2px;
}

.kpi-online::before { background: #53d5a5; }
.kpi-offline::before { background: #ff8d8d; }
.kpi-total::before { background: #63b8ff; }
.kpi-preview::before { background: #a78bfa; }

/* ====== 4. AI 事件流 ====== */
.event-stream {
  margin-top: 14px;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(12, 30, 50, 0.74), rgba(8, 20, 35, 0.82));
  padding: 12px 14px;
  max-height: 240px;
  display: flex;
  flex-direction: column;
}

.event-stream-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.event-stream-title {
  font-size: 12px;
  font-weight: 600;
  color: #cde8ff;
}

.event-stream-count {
  font-size: 11px;
  color: var(--sub);
}

.event-stream-list {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(126, 197, 255, 0.08);
  background: rgba(17, 47, 75, 0.4);
  font-size: 11px;
  transition: background 0.2s, border-color 0.2s ease;
}

.event-item:hover {
  background: rgba(34, 79, 118, 0.58);
  border-color: rgba(126, 197, 255, 0.18);
}

.event-time {
  color: rgba(214, 230, 255, 0.6);
  font-variant-numeric: tabular-nums;
  min-width: 36px;
}

.event-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-low { background: #53d5a5; }
.dot-mid { background: #f8cb71; }
.dot-high { background: #ff8d8d; }

.event-text {
  color: #d6ecff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-empty {
  justify-content: center;
  color: rgba(214, 230, 255, 0.4);
}

/* ====== 5. 环境实时数值徽章 ====== */
.env-live-badge {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.env-live-badge strong {
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.env-live-badge span {
  font-size: 11px;
  opacity: 0.7;
}

/* ====== 6. 车位圆环仪表盘 ====== */
.parking-dashboard {
  display: grid;
  grid-template-columns: minmax(12rem, 13rem) minmax(0, 1fr);
  gap: 1rem;
  align-items: stretch;
}

.parking-ring-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1.35rem 1.1rem;
  border-radius: 24px;
  border: 1px solid rgba(126, 197, 255, 0.14);
  background:
    radial-gradient(circle at 50% 0%, rgba(126, 197, 255, 0.12), transparent 30%),
    rgba(12, 35, 58, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 16px 30px rgba(3, 10, 20, 0.14);
}

.parking-ring {
  width: 112px;
  height: 112px;
  filter: drop-shadow(0 0 18px rgba(126, 197, 255, 0.18));
}

.parking-summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.65rem;
  font-size: 11px;
  color: var(--sub);
}

.parking-summary span {
  padding: 0.4rem 0.72rem;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background: rgba(13, 36, 58, 0.42);
}

.parking-summary strong {
  color: #eaf6ff;
  margin-left: 2px;
}

.env-slot-meta {
  margin-bottom: 1rem;
}

.parking-stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.parking-stat-card {
  min-height: 8.4rem;
  padding: 1rem 1.05rem;
  border-radius: 20px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(16, 42, 68, 0.62), rgba(10, 27, 45, 0.72));
}

.parking-stat-card span,
.parking-stat-card p {
  color: rgba(214, 230, 255, 0.68);
  font-size: 0.76rem;
}

.parking-stat-card strong {
  display: block;
  margin: 0.45rem 0 0.32rem;
  font-size: 1.55rem;
  font-family: var(--font-data);
  letter-spacing: 0.08em;
  color: #f4fbff;
}

.parking-stat-card p {
  margin: 0;
  line-height: 1.5;
}

.parking-detail-stack {
  display: grid;
  gap: 1rem;
  min-height: 0;
  align-content: start;
}

.parking-zone-grid {
  gap: 0.85rem;
}

.parking-bar-row {
  grid-template-columns: minmax(7rem, 8.5rem) 1fr auto;
  gap: 1rem;
  padding: 0.95rem 1rem;
}

.bar-copy {
  display: grid;
  gap: 0.26rem;
  min-width: 0;
}

.bar-copy span {
  font-size: 0.82rem;
}

.bar-copy em {
  font-style: normal;
  color: rgba(214, 230, 255, 0.56);
  font-size: 0.72rem;
  line-height: 1.4;
}

.bar-value {
  display: grid;
  justify-items: end;
  gap: 0.22rem;
}

.bar-value small {
  color: rgba(214, 230, 255, 0.58);
  font-size: 0.72rem;
  white-space: nowrap;
}

/* ====== 7. 环境舒适度评分卡 ====== */
.env-comfort-card {
  background:
    radial-gradient(circle at 20% 10%, rgba(83, 213, 165, 0.12), transparent 40%),
    linear-gradient(180deg, rgba(14, 33, 56, 0.9), rgba(8, 20, 35, 0.94));
  border: 1px solid rgba(83, 213, 165, 0.16);
}

.comfort-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.comfort-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.9rem;
  align-items: stretch;
}

.comfort-score-panel,
.comfort-factor-panel {
  border-radius: 24px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(14, 39, 64, 0.56), rgba(9, 24, 40, 0.62));
}

.comfort-score-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 1rem 1.05rem;
}

.comfort-factor-panel {
  padding: 0.95rem 1rem 0.95rem;
}

.comfort-label {
  font-size: 13px;
  font-weight: 600;
}

.comfort-score {
  text-align: left;
  min-width: 7rem;
}

.comfort-score strong {
  font-size: 36px;
  font-weight: 800;
  color: var(--score-color);
  font-variant-numeric: tabular-nums;
}

.comfort-score span {
  font-size: 14px;
  color: rgba(214, 230, 255, 0.45);
  margin-left: 2px;
}

.comfort-score-note {
  margin: 0.95rem 0 0;
  color: rgba(214, 230, 255, 0.68);
  font-size: 0.82rem;
  line-height: 1.7;
}

.comfort-factors {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.comfort-factor {
  display: grid;
  grid-template-columns: 4rem 1fr;
  gap: 0.85rem;
  align-items: center;
  font-size: 12px;
  color: var(--sub);
}

.comfort-bar {
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.comfort-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.4s ease;
}

.comfort-tips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 1rem;
}

.comfort-tip {
  display: inline-flex;
  align-items: center;
  padding: 0.46rem 0.8rem;
  border-radius: 999px;
  border: 1px solid rgba(83, 213, 165, 0.18);
  background: rgba(27, 73, 56, 0.22);
  color: rgba(224, 244, 236, 0.86);
  font-size: 0.76rem;
}


.agent-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 14px;
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
  gap: 1rem;
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
  gap: 1rem;
}

.agent-main-card {
  display: flex;
  flex-direction: column;
}

.hero-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.2rem;
  background:
    radial-gradient(circle at 12% 0%, rgba(126, 197, 255, 0.18), transparent 26%),
    radial-gradient(circle at 90% 18%, rgba(75, 230, 168, 0.08), transparent 22%),
    linear-gradient(180deg, rgba(18, 48, 79, 0.92), rgba(11, 28, 48, 0.88));
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.08),
    0 24px 44px rgba(4, 12, 24, 0.2);
}

.summary-card,
.side-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(14, 33, 56, 0.88), rgba(8, 20, 35, 0.92));
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.05),
    0 18px 32px rgba(2, 10, 20, 0.16);
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
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(17, 47, 75, 0.58);
  color: #eaf6ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.88rem;
  border-radius: 999px;
  font-size: 0.78rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
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
  border-color: rgba(126, 232, 255, 0.34);
  background: rgba(34, 79, 118, 0.72);
}

.summary-head {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.82rem 0.95rem;
  border-radius: 18px;
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
  padding: 0.9rem 0.95rem;
  border-radius: 18px;
  border: 1px solid rgba(126, 197, 255, 0.1);
  background: rgba(14, 42, 67, 0.44);
}

.focus-card span {
  display: block;
  margin-bottom: 0.24rem;
  color: rgba(196, 221, 242, 0.7);
  font-size: 0.75rem;
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
  color: rgba(214, 230, 255, 0.74);
  line-height: 1.58;
  font-size: 0.88rem;
  max-width: 34rem;
}

.hero-head-primary {
  min-width: 0;
}

.hero-card-clean {
  gap: 0.9rem;
  padding: 1rem;
  background:
    radial-gradient(circle at 12% 0%, rgba(126, 197, 255, 0.14), transparent 24%),
    linear-gradient(180deg, rgba(16, 41, 67, 0.92), rgba(8, 22, 39, 0.94));
}

.hero-head-clean {
  align-items: flex-end;
  padding-bottom: 0.2rem;
  border-bottom: 1px solid rgba(126, 197, 255, 0.12);
}

.hero-head-clean .hero-head-side {
  flex-direction: row;
  align-items: center;
}

.service-strip-compact {
  margin-top: 0.82rem;
}

.agent-brief-bar {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.8rem;
  align-items: start;
  padding: 0.88rem 1rem;
  border-radius: 20px;
  border: 1px solid rgba(126, 197, 255, 0.12);
  background: linear-gradient(180deg, rgba(11, 31, 52, 0.72), rgba(8, 22, 39, 0.58));
}

.agent-brief-label {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0 0.8rem;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(15, 42, 67, 0.52);
  color: rgba(214, 230, 255, 0.84);
  font-size: 0.74rem;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.agent-brief-bar p {
  margin: 0;
  padding-top: 0.08rem;
  color: rgba(221, 239, 252, 0.86);
  font-size: 0.82rem;
  line-height: 1.62;
}

.agent-insight-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.75rem;
}

.agent-insight-card {
  padding: 0.95rem 1rem;
  border-radius: 20px;
  border: 1px solid rgba(126, 197, 255, 0.14);
  background:
    linear-gradient(180deg, rgba(14, 42, 67, 0.58), rgba(8, 23, 38, 0.72));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.03),
    0 16px 28px rgba(3, 10, 20, 0.14);
}

.agent-insight-card span,
.agent-insight-card p {
  color: rgba(214, 230, 255, 0.66);
  font-size: 0.76rem;
}

.agent-insight-card strong {
  display: block;
  margin: 0.45rem 0 0.3rem;
  font-size: 1.42rem;
  color: #f4fbff;
  letter-spacing: 0.04em;
}

.agent-insight-card p {
  margin: 0;
  line-height: 1.55;
}

.agent-insight-card.good {
  border-color: rgba(83, 213, 165, 0.22);
}

.agent-insight-card.warn {
  border-color: rgba(248, 203, 113, 0.24);
}

.agent-insight-card.alert {
  border-color: rgba(255, 141, 141, 0.28);
}

.hero-head-side,
.service-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
}

.hero-head-side {
  flex-direction: column;
  align-items: flex-end;
}

.hero-status-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.45rem;
}

.service-chip,
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(17, 47, 75, 0.54);
  color: #eaf6ff;
  border-radius: 999px;
  padding: 0.48rem 0.82rem;
  font-size: 0.78rem;
}

.status-pill.listening {
  border-color: rgba(248, 203, 113, 0.42);
  color: #f8cb71;
}

.status-pill.subtle {
  background: rgba(13, 35, 58, 0.62);
  color: rgba(214, 230, 255, 0.78);
}

.status-pill.thinking,
.status-pill.speaking {
  border-color: rgba(83, 213, 165, 0.42);
  color: #8de7c0;
}

.hero-shell {
  position: relative;
  flex: 1;
  min-height: 34rem;
  height: 100%;
  overflow: hidden;
  border-radius: 32px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  background:
    radial-gradient(circle at 80% 14%, rgba(126, 197, 255, 0.16), transparent 24%),
    radial-gradient(circle at 0% 100%, rgba(83, 213, 165, 0.1), transparent 28%),
    radial-gradient(circle at 50% 100%, rgba(126, 197, 255, 0.1), transparent 35%),
    linear-gradient(180deg, rgba(8, 25, 43, 0.98), rgba(7, 18, 32, 0.98));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 22px 48px rgba(3, 10, 20, 0.28);
}

.hero-shell-clean {
  min-height: 33rem;
  border-radius: 28px;
}

.hero-card-clean .service-chip,
.hero-card-clean .status-pill {
  padding: 0.42rem 0.74rem;
  font-size: 0.74rem;
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
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), transparent 24%),
    radial-gradient(circle at 20% 18%, rgba(126, 197, 255, 0.16), transparent 22%),
    linear-gradient(rgba(126, 197, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(126, 197, 255, 0.04) 1px, transparent 1px);
  background-size: auto, auto, 2.6rem 2.6rem, 2.6rem 2.6rem;
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
  border: 1px solid rgba(126, 197, 255, 0.14);
  background: linear-gradient(180deg, rgba(9, 28, 47, 0.64), rgba(6, 18, 33, 0.48));
  backdrop-filter: blur(8px);
}

.hero-shell :deep(.chat-input) {
  right: 1.6rem;
  bottom: 1.7rem;
  width: min(19rem, 33vw);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(9, 28, 47, 0.82), rgba(6, 18, 33, 0.74));
  backdrop-filter: blur(8px);
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
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(92, 71, 26, 0.3), rgba(46, 34, 11, 0.18)),
    rgba(248, 203, 113, 0.08);
  padding: 0.85rem 0.9rem 0.85rem 1rem;
  font-size: 12px;
  line-height: 1.6;
  color: #f4ebcb;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
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
  border: 1px solid rgba(126, 197, 255, 0.18);
  background: rgba(17, 47, 75, 0.48);
  color: #eaf6ff;
  border-radius: 999px;
  padding: 6px 12px;
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
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 18px;
  background: rgba(17, 47, 75, 0.36);
  padding: 12px;
}

.summary-kpi span {
  display: block;
  color: var(--sub);
  font-size: 11px;
}

.summary-kpi strong {
  display: block;
  margin-top: 6px;
  font-family: var(--font-data);
  font-size: 22px;
  letter-spacing: 0.08em;
}

.summary-overview {
  margin: 10px 0;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 18px;
  background: rgba(17, 47, 75, 0.32);
  padding: 12px 14px;
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
  height: 8px;
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
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 11px;
  color: #d6ecff;
  background: rgba(17, 47, 75, 0.36);
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
  font-size: 13px;
}

.info-table th,
.info-table td {
  border-bottom: 1px solid rgba(126, 197, 255, 0.16);
  padding: 12px 10px;
  text-align: left;
}

.info-table th {
  color: #cde8ff;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgba(9, 25, 42, 0.92);
  backdrop-filter: blur(8px);
}

.info-table tbody tr {
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.info-table tbody tr:hover {
  background: rgba(34, 79, 118, 0.22);
}

.state-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  letter-spacing: 0.06em;
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
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 12px;
  color: var(--text);
  background: linear-gradient(180deg, rgba(16, 44, 70, 0.92), rgba(10, 26, 43, 0.88));
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
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(9, 25, 43, 0.97), rgba(7, 18, 32, 0.98));
  padding: 14px;
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 14px;
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
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 20px;
  background: rgba(10, 24, 42, 0.84);
  padding: 12px;
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
  background: linear-gradient(180deg, rgba(9, 25, 43, 0.97), rgba(7, 18, 32, 0.98));
  border: 1px solid rgba(99, 184, 255, 0.18);
  border-radius: 28px;
  padding: 20px;
  min-width: 360px;
  max-width: 720px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  gap: 14px;
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
  padding: 12px 14px;
  border: 1px solid rgba(99, 184, 255, 0.14);
  border-radius: 18px;
  background: rgba(13, 30, 52, 0.72);
  cursor: pointer;
}

.monitor-row:hover {
  border-color: rgba(126, 232, 255, 0.34);
  background: rgba(17, 47, 75, 0.56);
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
  .agent-panel {
    grid-template-columns: 1fr;
  }

  .env-panel {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .env-overview-grid,
  .agent-insight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-head,
  .hero-head,
  .card-title-row,
  .summary-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-head-side,
  .hero-status-row,
  .env-overview-status {
    align-items: flex-start;
  }

  .hero-head-clean .hero-head-side {
    flex-direction: row;
  }

  .nav-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 900px) {
  .monitor-grid-large {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .nav-current {
    font-size: 18px;
  }

  .video-stats-grid {
    grid-template-columns: 1fr;
  }

  .env-overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .env-panel {
    grid-template-columns: 1fr;
  }

  .parking-dashboard {
    grid-template-columns: 1fr;
  }

  .parking-ring-wrap {
    align-items: flex-start;
  }

  .parking-summary {
    justify-content: flex-start;
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

  .page-shell {
    gap: 12px;
  }

  .env-overview-grid,
  .parking-stat-grid,
  .agent-insight-grid,
  .comfort-layout,
  .agent-brief-bar {
    grid-template-columns: 1fr;
  }

  .nav-bar,
  .panel .card {
    padding: 14px;
  }

  .table-filters,
  .panel-headline,
  .chart-filter,
  .hero-head-side {
    width: 100%;
  }

  .hero-head-clean .hero-head-side {
    flex-direction: column;
    align-items: flex-start;
  }

  .agent-brief-label {
    width: fit-content;
  }

  .table-filters > * {
    width: 100%;
  }

  .chart-panel,
  .hero-shell :deep(.chat-messages),
  .hero-shell :deep(.chat-input),
  .hero-shell :deep(.realtime-banner) {
    width: 100%;
  }

  .bar-row {
    grid-template-columns: 1fr;
  }

  .bar-value {
    justify-items: start;
  }

  .chart-panel {
    grid-template-columns: 1fr;
  }
}
</style>
