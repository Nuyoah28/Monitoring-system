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
            <div
              ref="alarmTableWrapRef"
              class="table-wrap detail-table-wrap"
              @mouseenter="pauseAlarmAutoScroll"
              @mouseleave="resumeAlarmAutoScroll"
            >
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
                    <td>
                      <span
                        class="state-chip"
                        :class="[row.deal.includes('已') ? 'done' : 'pending', { clickable: !row.deal.includes('已') }]"
                        :title="row.deal.includes('已') ? '已处理' : '点击处理'"
                        @click.stop="openProcessDialog(row)"
                      >
                        {{ row.deal.includes('已') ? row.deal : '去处理' }}
                      </span>
                    </td>
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
        <div
          v-if="processDialogVisible"
          class="process-modal-mask"
          role="dialog"
          aria-modal="true"
          @click.self="closeProcessDialog"
        >
          <div class="process-modal-card">
            <h4>处理报警</h4>
            <p class="process-meta">{{ processingRow?.eventName || '报警事件' }} · {{ processingRow?.department || '未标注区域' }}</p>
            <textarea
              v-model.trim="processingContent"
              class="process-textarea"
              rows="4"
              maxlength="120"
              placeholder="请输入处理说明（必填）"
            ></textarea>
            <div class="process-actions">
              <button class="mini-action" type="button" @click="closeProcessDialog">取消</button>
              <button class="btn" type="button" :disabled="processingSubmitting" @click="submitProcessDialog">
                {{ processingSubmitting ? '提交中...' : '确认处理' }}
              </button>
            </div>
          </div>
        </div>

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
              <AMapLinkage3D :points="mapPoints" :alarm-counts="mapAlarmCounts" @point-click="onMapPointClick" />
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
                <div
                  v-for="ev in recentEvents"
                  :key="ev.id"
                  class="event-item"
                  :class="['event-' + ev.severity, { 'event-item-pending': ev.isPending, 'event-item-done': !ev.isPending }]"
                >
                  <span class="event-time">{{ ev.time }}</span>
                  <span class="event-dot" :class="['dot-' + ev.severity, { 'dot-pulse': ev.isPending }]"></span>
                  <span class="event-text">{{ ev.text }}</span>
                  <span class="event-deal" :class="ev.isPending ? 'pending' : 'done'">{{ ev.dealText }}</span>
                </div>
                <div v-if="!recentEvents.length" class="event-item event-empty">
                  <span class="event-text">暂无事件，系统运行正常</span>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'env'" class="panel env-panel">
          <article v-for="metric in envTrendMetrics" :key="metric.key" class="card env-metric-card">
            <div class="panel-headline small env-metric-head">
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

          <article class="card env-dual-card">
            <div class="panel-headline small">
              <h3>环境与车位快览</h3>
              <span>{{ envParkingDataModeLabel }} · {{ envParkingRefreshSeconds }}s 刷新</span>
            </div>
            <div class="dual-card-grid">
              <section class="dual-mini-block">
                <header>
                  <strong>AQI日内波动</strong>
                  <span>{{ envCurrentValues.aqi }} 指数</span>
                </header>
                <div class="dual-mini-chart">
                  <div v-for="(point, idx) in aqiMiniBars" :key="`${point.label}-${idx}`" class="mini-col">
                    <i :style="{ height: `${point.height}%` }"></i>
                    <span>{{ showParkingTrendLabel(idx, aqiMiniBars.length) ? point.label : '' }}</span>
                  </div>
                </div>
              </section>
              <section class="dual-mini-block">
                <header>
                  <strong>车位占用动态</strong>
                  <span>{{ parkingOccupancy }}%</span>
                </header>
                <div class="dual-mini-chart">
                  <div v-for="(point, idx) in parkingMiniBars" :key="`${point.label}-${idx}`" class="mini-col">
                    <i class="parking" :style="{ height: `${point.height}%` }"></i>
                    <span>{{ showParkingTrendLabel(idx, parkingMiniBars.length) ? point.label : '' }}</span>
                  </div>
                </div>
              </section>
            </div>
          </article>

          <article class="card env-slot-card">
            <h3>车位占用数据</h3>
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
                  <span>已用 <strong>{{ parkingUsed }}</strong></span>
                  <span>空闲 <strong>{{ parkingFree }}</strong></span>
                </div>
              </div>
              <div class="bar-grid">
                <div class="bar-row" v-for="item in parkingBars" :key="item.name">
                  <span>{{ item.name }}</span>
                  <div class="bar"><i :style="{ width: `${item.percent}%` }"></i></div>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
            </div>
            <div class="parking-map">
              <div class="parking-map-head">
                <h4>车位地图（示意）</h4>
                <span>总车位 {{ parkingTotal }} · 已占 {{ parkingUsed }} · 空闲 {{ parkingFree }}</span>
              </div>
              <div class="parking-zone-grid">
                <div v-for="zone in parkingMapZones" :key="zone.name" class="parking-zone-card">
                  <div class="zone-top">
                    <strong>{{ zone.name }}</strong>
                    <span>{{ zone.used }}/{{ zone.capacity }}</span>
                  </div>
                  <div class="zone-slots">
                    <i v-for="slot in zone.sampleSlots" :key="slot.id" :class="{ busy: slot.busy }"></i>
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
            <div class="comfort-score-wrap">
              <div class="comfort-score" :style="{ '--score-color': comfortColor }">
                <strong>{{ comfortScore }}</strong>
                <span>/ 100</span>
              </div>
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

interface RecentEventItem {
  id: string
  time: string
  text: string
  severity: 'low' | 'mid' | 'high'
  isPending: boolean
  dealText: string
  timestamp: number
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
const processDialogVisible = ref(false)
const processingRow = ref<any>(null)
const processingContent = ref('')
const processingSubmitting = ref(false)
const alarmTableWrapRef = ref<HTMLDivElement | null>(null)

const openAlarmDetail = (row: any) => {
  currentAlarmItem.value = row
  alarmDialogVisible.value = true
}

const openProcessDialog = (row: any) => {
  if (!row || row.deal?.includes('已')) return
  processingRow.value = row
  processingContent.value = ''
  processDialogVisible.value = true
}

const closeProcessDialog = () => {
  processDialogVisible.value = false
  processingRow.value = null
  processingContent.value = ''
  processingSubmitting.value = false
}

const submitProcessDialog = async () => {
  const current = processingRow.value
  const content = processingContent.value.trim()
  if (!current?.id || !content) {
    const { ElMessage } = await import('element-plus')
    ElMessage.warning('请填写处理说明后再提交')
    return
  }
  if (processingSubmitting.value) return
  processingSubmitting.value = true
  try {
    const { data } = await axios.put('/alarm/update', {
      id: current.id,
      status: true,
      processingContent: content,
    })
    if (data?.code === '00000') {
      const { ElMessage } = await import('element-plus')
      ElMessage.success('报警已标记为已处理')
      closeProcessDialog()
      await fetchAlarmList()
      await fetchRecentEventStream()
      return
    }
    const { ElMessage } = await import('element-plus')
    ElMessage.error(data?.message || '处理失败，请稍后重试')
  } catch (err) {
    void err
    const { ElMessage } = await import('element-plus')
    ElMessage.error('处理失败，请检查网络或登录状态')
  } finally {
    processingSubmitting.value = false
  }
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

const RECENT_EVENT_LIMIT = 6
const RECENT_EVENT_POLL_MS = 8000
const RECENT_EVENT_DONE_REMOVE_MS = 12000
const recentEvents = ref<RecentEventItem[]>([])
const recentEventInitialized = ref(false)
let recentEventPollTimer: number | null = null
const recentEventResolvedAt = new Map<string, number>()

const withNoCache = (url: string) => {
  if (!url) return url
  const [base, hash = ''] = url.split('#')
  const connector = base.includes('?') ? '&' : '?'
  const nextUrl = `${base}${connector}_t=${Date.now()}`
  return hash ? `${nextUrl}#${hash}` : nextUrl
}

const parseAlarmTimestamp = (item: any): number => {
  const raw = item?.createTime || item?.date || item?.time || ''
  if (!raw) return 0
  const normalized = String(raw).trim()
  if (!normalized) return 0
  const mmddTimeMatch = normalized.match(/^(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$/)
  if (mmddTimeMatch) {
    const [, month, day, hour, minute] = mmddTimeMatch
    const year = new Date().getFullYear()
    const timestamp = new Date(`${year}-${month}-${day}T${hour}:${minute}:00`).getTime()
    return Number.isNaN(timestamp) ? 0 : timestamp
  }
  const value = new Date(normalized).getTime()
  if (!Number.isNaN(value)) return value
  const fallbackValue = new Date(normalized.replace(/-/g, '/')).getTime()
  return Number.isNaN(fallbackValue) ? 0 : fallbackValue
}

const toSeverity = (value: unknown): 'low' | 'mid' | 'high' => {
  const level = Number(value || 1)
  if (level >= 3) return 'high'
  if (level === 2) return 'mid'
  return 'low'
}

const toTimeLabel = (timestamp: number): string => {
  if (!timestamp) return '--:--'
  const d = new Date(timestamp)
  if (Number.isNaN(d.getTime())) return '--:--'
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const isAlarmPending = (item: any): boolean => {
  const dealText = String(item?.deal || item?.statusText || '')
  const hasDoneText = dealText.includes('已') || dealText.includes('完成')
  if (hasDoneText) return false
  if (item?.status === 1 || item?.status === true) return false
  return true
}

const syncRecentEvents = (rawList: any[]): void => {
  if (!Array.isArray(rawList)) return
  const seenIds = new Set<string>()
  const now = Date.now()

  const normalized = rawList
    .filter(item => item && item.caseType !== 13)
    .map((item, idx) => {
      const timestamp = parseAlarmTimestamp(item)
      const fallbackId = `${item?.eventName || '事件'}-${timestamp}-${idx}`
      const id = String(item?.id ?? fallbackId)
      return {
        ...item,
        __id: id,
        __ts: timestamp,
      }
    })
    .sort((a, b) => {
      if (b.__ts !== a.__ts) return b.__ts - a.__ts
      return Number(b.id || 0) - Number(a.id || 0)
    })
    .filter(item => {
      if (seenIds.has(item.__id)) return false
      seenIds.add(item.__id)
      return true
    })

  const mapped = normalized.map(item => {
    const pending = isAlarmPending(item)
    if (pending) {
      recentEventResolvedAt.delete(item.__id)
    } else if (!recentEventResolvedAt.has(item.__id)) {
      recentEventResolvedAt.set(item.__id, now)
    }
    return {
      id: item.__id,
      time: toTimeLabel(item.__ts),
      text: `${item.department || item.location || '未标注'} ${item.eventName || '事件'}`,
      severity: toSeverity(item.level),
      isPending: pending,
      dealText: pending ? '未处理' : '已处理',
      timestamp: item.__ts,
    }
  })

  const visibleEvents: RecentEventItem[] = mapped
    .filter(item => {
      if (item.isPending) return true
      const resolvedAt = recentEventResolvedAt.get(item.id)
      return resolvedAt === undefined ? false : now - resolvedAt < RECENT_EVENT_DONE_REMOVE_MS
    })
    .slice(0, RECENT_EVENT_LIMIT)

  recentEvents.value = visibleEvents

  const visibleIds = new Set(mapped.map(item => item.id))
  for (const id of recentEventResolvedAt.keys()) {
    if (!visibleIds.has(id)) {
      recentEventResolvedAt.delete(id)
    }
  }
}

const alarmPageNum = ref(1)
const alarmPageSize = ref(200)

const fetchAlarmList = async () => {
  try {
    const { data } = await axios.get('/alarm/query', {
      params: {
        pageNum: alarmPageNum.value,
        pageSize: alarmPageSize.value,
      },
    })
    console.log('报警API返回:', data)
    const list = data?.data?.alarmList || data?.data?.list || []
    if (Array.isArray(list)) {
      alarmStore.setAlarmList(list)
      alarmStore.updateStatisticsFromAlarms()
    } else {
      alarmStore.setAlarmList([])
      alarmStore.resetStatistics()
    }
  } catch (e) {
    console.log('请求失败，使用模拟数据', e)
    useMockData()
  }
}

const ALARM_AUTO_SCROLL_INTERVAL_MS = 45
const ALARM_AUTO_SCROLL_STEP = 0.58
let alarmAutoScrollTimer: number | null = null
const alarmAutoScrollPaused = ref(false)

const stopAlarmAutoScroll = () => {
  if (alarmAutoScrollTimer !== null) {
    window.clearInterval(alarmAutoScrollTimer)
    alarmAutoScrollTimer = null
  }
}

const startAlarmAutoScroll = () => {
  stopAlarmAutoScroll()
  const wrapEl = alarmTableWrapRef.value
  if (!wrapEl || activeTab.value !== 'alarm') return
  if (filteredAlarmRows.value.length < 7) return
  if (wrapEl.scrollHeight - wrapEl.clientHeight < 12) return
  alarmAutoScrollTimer = window.setInterval(() => {
    if (alarmAutoScrollPaused.value) return
    const el = alarmTableWrapRef.value
    if (!el) return
    const maxScrollTop = el.scrollHeight - el.clientHeight
    if (maxScrollTop < 12) return
    if (el.scrollTop >= maxScrollTop - 1) {
      el.scrollTop = 0
      return
    }
    el.scrollTop += ALARM_AUTO_SCROLL_STEP
  }, ALARM_AUTO_SCROLL_INTERVAL_MS)
}

const pauseAlarmAutoScroll = () => {
  alarmAutoScrollPaused.value = true
}

const resumeAlarmAutoScroll = () => {
  alarmAutoScrollPaused.value = false
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

const fetchRecentEventStream = async (): Promise<void> => {
  try {
    const { data } = await axios.get('/alarm/query', {
      params: {
        pageNum: 1,
        pageSize: 30,
      },
    })
    const list = data?.data?.alarmList || data?.data?.list || []
    if (Array.isArray(list) && list.length) {
      syncRecentEvents(list)
      recentEventInitialized.value = true
    }
  } catch (e) {
    if (!recentEventInitialized.value) {
      const fallbackList = alarmStore.getAlarmList || []
      if (Array.isArray(fallbackList) && fallbackList.length) {
        syncRecentEvents(fallbackList)
        recentEventInitialized.value = true
      }
    }
  }
}

const startRecentEventPolling = (): void => {
  if (recentEventPollTimer !== null) {
    window.clearInterval(recentEventPollTimer)
  }
  void fetchRecentEventStream()
  recentEventPollTimer = window.setInterval(() => {
    void fetchRecentEventStream()
  }, RECENT_EVENT_POLL_MS)
}

const stopRecentEventPolling = (): void => {
  if (recentEventPollTimer !== null) {
    window.clearInterval(recentEventPollTimer)
    recentEventPollTimer = null
  }
  recentEventResolvedAt.clear()
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
    syncRecentEvents(list);
    recentEventInitialized.value = true;
    
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
  const rows = alarmStore.getAlarmList || []
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

const ENV_PARKING_DATA_MODE: 'mock' | 'api' = 'mock'
const ENV_PARKING_REFRESH_MS = 6000
const envParkingRefreshSeconds = Math.round(ENV_PARKING_REFRESH_MS / 1000)
const envParkingDataModeLabel = computed(() => (ENV_PARKING_DATA_MODE === 'mock' ? '模拟数据' : '实时接口'))

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))
const randDelta = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min
const pad2 = (n: number) => String(n).padStart(2, '0')
const toHmLabel = (date: Date) => `${pad2(date.getHours())}:${pad2(date.getMinutes())}`

interface ParkingZone {
  name: string
  capacity: number
  used: number
}

interface ParkingDayPoint {
  label: string
  occupancy: number
  used: number
}

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

const envTrendDataState = ref<Record<'day' | 'week' | 'month', EnvPoint[]>>({
  day: [
    { label: '00:00', aqi: 72, humidity: 63, pm25: 42 },
    { label: '04:00', aqi: 76, humidity: 64, pm25: 46 },
    { label: '08:00', aqi: 79, humidity: 58, pm25: 48 },
    { label: '12:00', aqi: 84, humidity: 54, pm25: 55 },
    { label: '16:00', aqi: 87, humidity: 52, pm25: 59 },
    { label: '20:00', aqi: 80, humidity: 57, pm25: 50 },
    { label: '24:00', aqi: 75, humidity: 61, pm25: 45 },
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
})

const envTrendSeries = computed(() => envTrendDataState.value[envTrendRange.value])

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

const parkingZoneState = ref<ParkingZone[]>([
  { name: '地库A区', capacity: 62, used: 38 },
  { name: '地库B区', capacity: 44, used: 23 },
  { name: '地面东侧', capacity: 30, used: 16 },
  { name: '地面西侧', capacity: 24, used: 11 },
])

const parkingBars = computed(() => parkingZoneState.value.map((item) => ({
  name: item.name,
  value: item.used,
  percent: Math.round((item.used / Math.max(item.capacity, 1)) * 100),
})))

const parkingDayTrend = ref<ParkingDayPoint[]>([
  { label: '00:00', occupancy: 41, used: 66 },
  { label: '04:00', occupancy: 37, used: 59 },
  { label: '08:00', occupancy: 55, used: 88 },
  { label: '12:00', occupancy: 67, used: 107 },
  { label: '16:00', occupancy: 73, used: 117 },
  { label: '20:00', occupancy: 61, used: 98 },
  { label: '24:00', occupancy: 48, used: 77 },
])

const parkingTrendBars = computed(() => parkingDayTrend.value.slice(-8))
const aqiMiniBars = computed(() => {
  const series = envTrendDataState.value.day.slice(-8)
  if (!series.length) return []
  const values = series.map(item => item.aqi)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const diff = Math.max(max - min, 1)
  return series.map((item) => ({
    label: item.label,
    height: clamp(Math.round(((item.aqi - min) / diff) * 80 + 20), 16, 100),
  }))
})
const parkingMiniBars = computed(() => parkingTrendBars.value.map((item) => ({
  label: item.label,
  height: clamp(item.occupancy, 16, 100),
})))
const showParkingTrendLabel = (idx: number, total: number): boolean => {
  if (idx === total - 1) return true
  return idx % 2 === 0
}
const parkingMapZones = computed(() => parkingZoneState.value.map((zone) => {
  const sampleCount = Math.min(zone.capacity, 24)
  const ratio = zone.capacity > 0 ? zone.used / zone.capacity : 0
  const busyCount = Math.round(ratio * sampleCount)
  return {
    ...zone,
    sampleSlots: Array.from({ length: sampleCount }, (_, idx) => ({
      id: `${zone.name}-${idx}`,
      busy: idx < busyCount,
    })),
  }
}))

const syncEnvParkingFromApi = async (): Promise<boolean> => {
  if (ENV_PARKING_DATA_MODE !== 'api') return false
  try {
    // 预留后端接口位：接入后将返回值写入 envTrendDataState / parkingZoneState / parkingDayTrend
    await Promise.all([
      axios.get('/env/realtime'),
      axios.get('/env/trend', { params: { range: envTrendRange.value } }),
      axios.get('/parking/realtime'),
      axios.get('/parking/trend', { params: { range: 'day' } }),
    ])
    return true
  } catch (error) {
    void error
    return false
  }
}

const stepMockEnvParking = () => {
  const now = new Date()
  const daySeries = envTrendDataState.value.day
  const last = daySeries[daySeries.length - 1] || { label: '00:00', aqi: 72, humidity: 62, pm25: 44 }
  const nextPoint: EnvPoint = {
    label: toHmLabel(now),
    aqi: clamp(last.aqi + randDelta(-4, 5), 45, 135),
    humidity: clamp(last.humidity + randDelta(-3, 3), 35, 82),
    pm25: clamp(last.pm25 + randDelta(-4, 4), 18, 96),
  }
  daySeries.push(nextPoint)
  if (daySeries.length > 24) daySeries.shift()

  ;(['week', 'month'] as const).forEach((range) => {
    const scoped = envTrendDataState.value[range]
    if (!scoped.length) return
    const idx = scoped.length - 1
    const prev = scoped[idx]
    scoped[idx] = {
      ...prev,
      aqi: clamp(Math.round((prev.aqi * 4 + nextPoint.aqi) / 5 + randDelta(-1, 1)), 45, 135),
      humidity: clamp(Math.round((prev.humidity * 4 + nextPoint.humidity) / 5 + randDelta(-1, 1)), 35, 82),
      pm25: clamp(Math.round((prev.pm25 * 4 + nextPoint.pm25) / 5 + randDelta(-1, 1)), 18, 96),
    }
  })

  const hour = now.getHours()
  const trafficBias = (hour >= 7 && hour <= 10) || (hour >= 17 && hour <= 21) ? 1 : -1
  parkingZoneState.value = parkingZoneState.value.map((zone) => {
    const nextUsed = clamp(zone.used + randDelta(-2, 2) + trafficBias, 4, zone.capacity - 1)
    return { ...zone, used: nextUsed }
  })

  const total = parkingZoneState.value.reduce((sum, zone) => sum + zone.capacity, 0)
  const used = parkingZoneState.value.reduce((sum, zone) => sum + zone.used, 0)
  const occupancy = total > 0 ? Math.round((used / total) * 100) : 0
  parkingDayTrend.value.push({ label: toHmLabel(now), occupancy, used })
  if (parkingDayTrend.value.length > 24) parkingDayTrend.value.shift()
}

const refreshEnvParkingData = async () => {
  const synced = await syncEnvParkingFromApi()
  if (!synced) stepMockEnvParking()
}

let envParkingTimer: number | null = null
const startEnvParkingRefresh = () => {
  if (envParkingTimer !== null) return
  void refreshEnvParkingData()
  envParkingTimer = window.setInterval(() => {
    void refreshEnvParkingData()
  }, ENV_PARKING_REFRESH_MS)
}

const stopEnvParkingRefresh = () => {
  if (envParkingTimer === null) return
  window.clearInterval(envParkingTimer)
  envParkingTimer = null
}

const onlineCount = computed(() => monitors.value.filter(item => item.status === 1 || item.status === 'online').length)
const offlineCount = computed(() => Math.max(monitors.value.length - onlineCount.value, 0))

const tileHasAlert = (tileName: string) => {
  const list = alarmStore.getAlarmList || []
  return list.some((item: any) => {
    const dept = String(item.department || '').toLowerCase()
    const name = tileName.toLowerCase()
    return dept && name.includes(dept.slice(0, 2))
  })
}

const normalizeName = (value: unknown): string => String(value || '').replace(/\s+/g, '').toLowerCase()

const mapAlarmCounts = computed(() => {
  const list = alarmStore.getAlarmList || []
  const monitorList = monitors.value || []
  const countsByCamera: Record<string, number> = {}
  const countsByArea: Record<string, number> = {}

  list.forEach((item: any) => {
    const pending = !(item?.status === 1 || item?.status === true || String(item?.deal || '').includes('已'))
    if (!pending) return

    const cameraName = String(item?.name || '').trim()
    if (cameraName) {
      countsByCamera[cameraName] = (countsByCamera[cameraName] || 0) + 1
      return
    }

    const dept = String(item?.department || item?.location || '').trim()
    if (!dept) return
    const deptKey = normalizeName(dept)
    const matched = monitorList.find((monitor) => {
      const monitorName = normalizeName(monitor.name)
      const monitorDept = normalizeName(monitor.department)
      return (
        deptKey === monitorDept ||
        (monitorName && (monitorName.includes(deptKey) || deptKey.includes(monitorName)))
      )
    })
    if (matched?.name) {
      countsByCamera[matched.name] = (countsByCamera[matched.name] || 0) + 1
      return
    }

    countsByArea[dept] = (countsByArea[dept] || 0) + 1
  })

  return [
    ...Object.entries(countsByCamera).map(([camera, count]) => ({ camera, count })),
    ...Object.entries(countsByArea).map(([camera, count]) => ({ camera, count })),
  ]
})

const ALARM_REFRESH_INTERVAL_MS = 10000
let alarmCountRefreshTimer: number | null = null

const startAlarmCountRefresh = () => {
  if (alarmCountRefreshTimer !== null) return
  alarmCountRefreshTimer = window.setInterval(() => {
    void fetchAlarmList()
  }, ALARM_REFRESH_INTERVAL_MS)
}

const stopAlarmCountRefresh = () => {
  if (alarmCountRefreshTimer !== null) {
    window.clearInterval(alarmCountRefreshTimer)
    alarmCountRefreshTimer = null
  }
}

// ====== 环境实时数值 ======
const envCurrentValues = computed(() => {
  const series = envTrendDataState.value.day
  const last = series[series.length - 1]
  return {
    aqi: last?.aqi ?? 0,
    humidity: last?.humidity ?? 0,
    pm25: last?.pm25 ?? 0,
  }
})

// ====== 车位仪表盘 ======
const parkingTotal = computed(() => parkingZoneState.value.reduce((sum, item) => sum + item.capacity, 0))
const parkingUsed = computed(() => parkingZoneState.value.reduce((sum, item) => sum + item.used, 0))
const parkingFree = computed(() => Math.max(parkingTotal.value - parkingUsed.value, 0))
const parkingOccupancy = computed(() => {
  if (!parkingTotal.value) return 0
  return Math.round((parkingUsed.value / parkingTotal.value) * 100)
})
const parkingOccupancyColor = computed(() => {
  const pct = parkingOccupancy.value
  if (pct > 80) return '#ff8d8d'
  if (pct > 50) return '#f8cb71'
  return '#53d5a5'
})

// ====== 环境舒适度评分 ======
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

const MAP_BASE_CENTER: [number, number] = [117.01187872107023, 39.1443426861701]
const MAP_FALLBACK_SPOTS: Array<[number, number]> = [
  [117.01278, 39.14495],
  [117.01305, 39.1444],
  [117.01268, 39.14382],
  [117.01195, 39.14365],
  [117.0112, 39.14388],
  [117.01072, 39.14442],
  [117.01098, 39.14502],
  [117.01178, 39.14516],
  [117.0123, 39.14468],
  [117.01222, 39.1441],
]

const hashCode = (text: string): number => {
  let hash = 0
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0
  }
  return hash
}

const inferPseudoLngLat = (camera: string, department: string, index: number): [number, number] => {
  const merged = `${department || ''} ${camera || ''}`
  const text = merged.replace(/\s+/g, '')
  const baseLng = MAP_BASE_CENTER[0]
  const baseLat = MAP_BASE_CENTER[1]

  let lng = MAP_FALLBACK_SPOTS[index % MAP_FALLBACK_SPOTS.length][0]
  let lat = MAP_FALLBACK_SPOTS[index % MAP_FALLBACK_SPOTS.length][1]

  if (/东门|东侧|东区|东/.test(text)) {
    lng = baseLng + 0.00095
    lat = baseLat + 0.00025
  } else if (/西门|西侧|西区|西/.test(text)) {
    lng = baseLng - 0.00095
    lat = baseLat + 0.00018
  } else if (/南门|南侧|南区|南/.test(text)) {
    lng = baseLng + 0.00012
    lat = baseLat - 0.00095
  } else if (/北门|北侧|北区|北/.test(text)) {
    lng = baseLng + 0.00012
    lat = baseLat + 0.00095
  } else if (/车库|停车/.test(text)) {
    lng = baseLng - 0.00055
    lat = baseLat - 0.00078
  } else if (/电梯/.test(text)) {
    lng = baseLng + 0.0006
    lat = baseLat - 0.00028
  } else if (/楼道/.test(text)) {
    lng = baseLng + 0.00025
    lat = baseLat + 0.00008
  } else {
    const buildingMatch = text.match(/(\d+)号楼/)
    if (buildingMatch) {
      const buildingNo = Number(buildingMatch[1])
      const angle = ((buildingNo * 47) % 360) * (Math.PI / 180)
      const radiusLng = 0.00086
      const radiusLat = 0.00064
      lng = baseLng + Math.cos(angle) * radiusLng
      lat = baseLat + Math.sin(angle) * radiusLat
    }
  }

  const h = hashCode(text || `idx-${index}`)
  const jitterLng = ((h % 17) - 8) * 0.000018
  const jitterLat = (((Math.floor(h / 17) % 17) - 8) * 0.000014)
  return [lng + jitterLng, lat + jitterLat]
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
      const rawMap = mapRes.data
      const points: Array<{ id?: number | string; monitorId?: number | string; name?: string; area?: string; location?: string; longitude?: number; latitude?: number }> =
        Array.isArray(rawMap) ? rawMap : (rawMap?.monitorPosList || [])
      const source = points.length
        ? points
        : monitorList.map(item => ({ id: item.id, name: item.name, area: item.department }))

      mapPoints.value = source.map((item, idx) => {
        const key = item.monitorId ?? item.id
        const matched =
          monitorList.find(m => key !== undefined && m.id === key) ||
          monitorList.find(m => item.name && m.name === item.name) ||
          monitorList.find(m => item.area && m.department === item.area) ||
          monitorList.find(m => item.name && m.name.includes(item.name)) ||
          monitorList.find(m => item.name && item.name.includes(m.name))
        const camera = matched?.name || item.name || item.area || item.location || `监测点${idx + 1}`
        const department = matched?.department || item.area || item.location || ''
        const hasGeo = typeof item.longitude === 'number' && typeof item.latitude === 'number'
        const [fallbackLng, fallbackLat] = inferPseudoLngLat(camera, department, idx)
        return {
          id: key ?? matched?.id ?? idx + 1,
          monitorId: matched?.id ?? key,
          camera,
          department,
          streamUrl: matched?.streamUrl || '',
          title: item.location || item.area || item.name || `监测点${idx + 1}`,
          className: `p${(idx % 3) + 1}`,
          longitude: hasGeo ? item.longitude : fallbackLng,
          latitude: hasGeo ? item.latitude : fallbackLat,
        }
      })
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

watch(
  () => alarmStore.getAlarmList,
  (list) => {
    if (!recentEventInitialized.value && Array.isArray(list) && list.length > 0) {
      syncRecentEvents(list)
      recentEventInitialized.value = true
    }
  },
  { deep: true },
)

onMounted(() => {
  fetchAlarmList()
  fetchMonitors()
  startRecentEventPolling()
  startAlarmCountRefresh()
  startEnvParkingRefresh()
  refreshSummaryNow()
  if (activeTab.value === 'agent') {
    nextTick(() => {
      window.dispatchEvent(new Event('resize'))
    })
  }
  nextTick(() => {
    initTilePlayers()
    startAlarmAutoScroll()
  })
})

onBeforeUnmount(() => {
  clearStatusTimer()
  stopRecentEventPolling()
  stopAlarmCountRefresh()
  stopEnvParkingRefresh()
  stopAlarmAutoScroll()
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

watch(
  [filteredAlarmRows, activeTab],
  () => {
    nextTick(() => {
      startAlarmAutoScroll()
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
  padding: 8px 8px 8px 14px;
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
  grid-auto-rows: minmax(228px, auto);
  gap: 10px;
  align-content: start;
}

.env-slot-card {
  min-height: 0;
  display: grid;
  grid-template-rows: auto auto;
  gap: 12px;
}

.env-metric-card {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 248px;
}

.env-dual-card {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 248px;
}

.dual-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  min-height: 0;
}

.dual-mini-block {
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 10px;
  background: rgba(10, 36, 61, 0.58);
  padding: 8px 9px;
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 0;
}

.dual-mini-block header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.dual-mini-block strong {
  font-size: 12px;
  color: #d8ecff;
}

.dual-mini-block span {
  font-size: 11px;
  color: rgba(214, 230, 255, 0.72);
}

.dual-mini-chart {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  align-items: end;
  gap: 3px;
  min-height: 88px;
}

.mini-col {
  display: grid;
  justify-items: center;
  gap: 2px;
}

.mini-col i {
  width: 100%;
  min-height: 7px;
  border-radius: 6px 6px 2px 2px;
  background: linear-gradient(180deg, rgba(99, 184, 255, 0.95), rgba(99, 184, 255, 0.38));
}

.mini-col i.parking {
  background: linear-gradient(180deg, rgba(83, 213, 165, 0.95), rgba(83, 213, 165, 0.35));
}

.mini-col span {
  min-height: 10px;
  font-size: 10px;
  line-height: 1;
  color: rgba(214, 230, 255, 0.52);
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
  margin-top: 10px;
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 10px;
  background: rgba(10, 30, 52, 0.6);
  padding: 8px 10px;
  height: 220px;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.event-stream-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
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
  min-height: 0;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 2px;
}

.event-stream-list::-webkit-scrollbar {
  width: 6px;
}

.event-stream-list::-webkit-scrollbar-track {
  background: rgba(126, 197, 255, 0.08);
  border-radius: 999px;
}

.event-stream-list::-webkit-scrollbar-thumb {
  background: rgba(126, 197, 255, 0.48);
  border-radius: 999px;
}

.event-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 6px;
  background: rgba(17, 47, 75, 0.5);
  font-size: 11px;
  transition: background 0.2s;
}

.event-item-pending {
  border: 1px solid rgba(255, 141, 141, 0.72);
  background: rgba(86, 26, 38, 0.6);
  animation: event-breathe 1.2s ease-in-out infinite;
}

.event-item-done {
  opacity: 0.76;
}

.event-item:hover {
  background: rgba(34, 79, 118, 0.7);
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

.dot-pulse {
  animation: event-dot-pulse 0.9s ease-in-out infinite;
  box-shadow: 0 0 12px currentColor;
}

.dot-low { background: #53d5a5; }
.dot-mid { background: #f8cb71; }
.dot-high { background: #ff8d8d; }

.event-text {
  color: #d6ecff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.event-deal {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 1px 7px;
  font-size: 10px;
  flex-shrink: 0;
}

.event-deal.pending {
  color: #ff9fa9;
  border: 1px solid rgba(255, 123, 136, 0.58);
  background: rgba(255, 78, 102, 0.2);
}

.event-deal.done {
  color: #6ce2b2;
  border: 1px solid rgba(108, 226, 178, 0.45);
  background: rgba(108, 226, 178, 0.12);
}

.event-empty {
  justify-content: center;
  color: rgba(214, 230, 255, 0.4);
}

@keyframes event-breathe {
  0%, 100% {
    box-shadow: 0 0 0 rgba(255, 128, 146, 0);
  }
  50% {
    box-shadow: 0 0 20px rgba(255, 98, 122, 0.45);
  }
}

@keyframes event-dot-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.85);
    opacity: 0.4;
  }
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
  grid-template-columns: auto 1fr;
  gap: 16px;
  align-items: center;
}

.parking-ring-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.parking-ring {
  width: 110px;
  height: 110px;
}

.parking-summary {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--sub);
}

.parking-summary strong {
  color: #eaf6ff;
  margin-left: 2px;
}

.parking-day-trend {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 10px;
  background: rgba(11, 39, 66, 0.58);
  padding: 8px 10px 6px;
}

.parking-day-trend-head {
  display: flex;
  justify-content: space-between;
  color: rgba(214, 230, 255, 0.8);
  font-size: 11px;
  margin-bottom: 6px;
}

.parking-day-trend-bars {
  height: 74px;
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  align-items: end;
  gap: 4px;
}

.trend-col {
  display: grid;
  justify-items: center;
  gap: 3px;
}

.trend-col i {
  width: 100%;
  border-radius: 6px 6px 2px 2px;
  min-height: 5px;
  background: linear-gradient(180deg, rgba(126, 197, 255, 0.95), rgba(83, 213, 165, 0.9));
  box-shadow: 0 0 10px rgba(83, 213, 165, 0.22);
}

.trend-col span {
  color: rgba(214, 230, 255, 0.55);
  font-size: 10px;
  line-height: 1;
  min-height: 10px;
}

.parking-map {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 10px;
  background: rgba(10, 33, 55, 0.62);
  padding: 8px 10px;
}

.parking-map-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.parking-map-head h4 {
  margin: 0;
  font-size: 13px;
}

.parking-map-head span {
  color: var(--sub);
  font-size: 11px;
}

.parking-zone-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.parking-zone-card {
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 8px;
  padding: 6px;
  background: rgba(12, 40, 68, 0.52);
}

.zone-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(214, 230, 255, 0.84);
  margin-bottom: 5px;
}

.zone-top strong {
  font-size: 12px;
}

.zone-slots {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 3px;
}

.zone-slots i {
  height: 6px;
  border-radius: 2px;
  background: rgba(83, 213, 165, 0.25);
  border: 1px solid rgba(83, 213, 165, 0.3);
}

.zone-slots i.busy {
  background: rgba(255, 128, 146, 0.35);
  border-color: rgba(255, 128, 146, 0.45);
}

/* ====== 7. 环境舒适度评分卡 ====== */
.env-comfort-card {
  background:
    radial-gradient(circle at 20% 10%, rgba(83, 213, 165, 0.08), transparent 40%),
    linear-gradient(180deg, rgba(17, 46, 75, 0.82), rgba(13, 33, 56, 0.8));
  border: 1px solid rgba(83, 213, 165, 0.18);
}

.comfort-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.comfort-label {
  font-size: 13px;
  font-weight: 600;
}

.comfort-score-wrap {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  align-items: center;
}

.comfort-score {
  text-align: center;
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

.comfort-factors {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comfort-factor {
  display: grid;
  grid-template-columns: 3.4rem 1fr;
  gap: 8px;
  align-items: center;
  font-size: 11px;
  color: var(--sub);
}

.comfort-bar {
  height: 6px;
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
  position: sticky;
  top: 0;
  z-index: 2;
  background: rgba(13, 44, 73, 0.95);
  backdrop-filter: blur(2px);
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
  color: #ff9fa9;
  border: 1px solid rgba(255, 123, 136, 0.58);
  background: rgba(255, 78, 102, 0.2);
}

.state-chip.clickable {
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.16s ease;
}

.state-chip.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 10px rgba(255, 120, 132, 0.24);
}

.process-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 13000;
  background: rgba(2, 10, 20, 0.62);
  display: grid;
  place-items: center;
  padding: 16px;
}

.process-modal-card {
  width: min(420px, 92vw);
  border-radius: 14px;
  border: 1px solid rgba(118, 183, 255, 0.3);
  background: linear-gradient(180deg, rgba(14, 43, 74, 0.95), rgba(9, 31, 54, 0.95));
  box-shadow: 0 22px 48px rgba(3, 16, 30, 0.48);
  padding: 14px;
}

.process-modal-card h4 {
  margin: 0;
  font-size: 16px;
  color: #eaf5ff;
}

.process-meta {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #9ec5e8;
}

.process-textarea {
  width: 100%;
  resize: vertical;
  min-height: 84px;
  border-radius: 10px;
  border: 1px solid rgba(126, 197, 255, 0.3);
  background: rgba(7, 28, 50, 0.8);
  color: #dff0ff;
  font-size: 12px;
  line-height: 1.5;
  padding: 10px;
  outline: none;
}

.process-textarea:focus {
  border-color: rgba(126, 197, 255, 0.7);
  box-shadow: 0 0 0 2px rgba(88, 157, 225, 0.2);
}

.process-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.process-actions .btn[disabled] {
  opacity: 0.65;
  cursor: not-allowed;
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

  .dual-card-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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

  .parking-dashboard {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .parking-zone-grid {
    grid-template-columns: 1fr;
  }

  .dual-card-grid {
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
