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
        <div class="nav-current" :class="{ 'video-current': activeTab === 'video' }">
          <template v-if="activeTab === 'video'">
            <span class="nav-current-title">视频巡检</span>
            <span class="nav-metric">总点位 <b>{{ monitors.length || cameraTiles.length }}</b></span>
            <span class="nav-metric ok">在线 <b>{{ monitors.length ? onlineCount : cameraTiles.length }}</b></span>
            <span class="nav-metric muted">离线 <b>{{ offlineCount }}</b></span>
            <span class="nav-metric warn">未处理 <b>{{ pendingAlertCount }}</b></span>
            <button class="mini-action nav-mini-action" type="button" @click="openMonitorModal">全部点位</button>
          </template>
          <template v-else>{{ currentTabLabel }}</template>
        </div>
      </section>

      <section class="content-shell">
        <section v-show="activeTab === 'alarm'" class="panel alarm-panel">
          <div class="alarm-left card">
            <div class="alarm-list-head">
              <div>
                <h3>报警处置队列</h3>
                <p>未处理与高等级报警优先</p>
              </div>
              <span class="queue-count">{{ filteredAlarmRows.length }} 条</span>
            </div>
            <div class="table-filters alarm-table-filters">
              <input v-model.trim="alarmKeyword" placeholder="搜索事件/区域" />
              <select v-model="alarmDealFilter">
                <option value="pending">未处理优先</option>
                <option value="all">全部</option>
                <option value="done">已处理</option>
              </select>
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
                  <tr
                    v-for="(row, idx) in filteredAlarmRows"
                    :key="alarmRowKey(row, idx)"
                    :class="[severityClass(row.level), { selected: isSelectedAlarm(row), pending: !row.deal.includes('已') }]"
                    @click="selectAlarmRow(row)"
                  >
                    <td :title="row.eventName">{{ row.eventName }}</td>
                    <td :title="row.department">{{ row.department }}</td>
                    <td :title="formatAlarmFullTime(row)">{{ formatAlarmListTime(row) }}</td>
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
            <article class="card alarm-overview-card" :class="alarmSituationTone">
              <div class="panel-headline small overview-head">
                <div>
                  <h3>当前风险态势</h3>
                  <p>未处理、高等级和重点类型汇总</p>
                </div>
                <span class="alarm-situation-pill">{{ alarmSituationStatus }}</span>
              </div>
              <div class="alarm-overview-layout">
                <section class="alarm-now-card">
                  <span>当前发生</span>
                  <strong>{{ alarmSituationTitle }}</strong>
                  <p>{{ alarmSituationDesc }}</p>
                </section>
                <section class="alarm-kpi-strip">
                  <div v-for="k in alarmCommandKpis" :key="k.name" class="alarm-kpi" :class="k.tone">
                    <span>{{ k.name }}</span>
                    <strong :title="`${k.name}：${k.value}`">{{ k.value }}</strong>
                  </div>
                </section>
              </div>
              <div class="alarm-type-overview" @mouseleave="showAlarmTypeOther = false">
                <div class="alarm-type-title">
                  <span>事件类型 Top</span>
                  <strong>{{ activeAlarmAreaCount }} 个区域有记录</strong>
                </div>
                <div class="alarm-type-list">
                  <button
                    v-for="item in alarmTypeStats"
                    :key="item.name"
                    class="alarm-type-item"
                    :class="{ clickable: item.isOther }"
                    type="button"
                    @click="toggleAlarmTypeOther(item)"
                  >
                    <span>{{ item.name }}</span>
                    <div class="trend-bar"><i :style="{ width: `${item.percent}%` }"></i></div>
                    <strong>{{ item.count }}</strong>
                  </button>
                  <div v-if="showAlarmTypeOther && alarmTypeOtherItems.length" class="alarm-type-popover">
                    <div class="alarm-type-popover-head">
                      <span>其他类型明细</span>
                      <strong>{{ alarmTypeOtherCount }} 条</strong>
                    </div>
                    <div class="alarm-type-popover-list">
                      <div v-for="item in alarmTypeOtherItems" :key="item.name" class="alarm-type-popover-row">
                        <span>{{ item.name }}</span>
                        <strong>{{ item.count }}</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <div class="alarm-bottom-row">
              <article class="card selected-alarm-card selected-alarm-compact" :class="selectedAlarmTone">
                <div class="panel-headline small command-head">
                  <h3>选中报警处置</h3>
                  <span class="state-chip" :class="selectedAlarmIsPending ? 'pending' : 'done'">
                    {{ selectedAlarmView.deal }}
                  </span>
                </div>
                <div class="selected-alarm-main">
                  <span class="alarm-eyebrow">当前选中</span>
                  <h4>{{ selectedAlarmView.eventName }}</h4>
                  <span class="level-chip" :class="severityClass(selectedAlarmView.level)">
                    {{ severityText(selectedAlarmView.level) }}等级
                  </span>
                </div>
                <div class="selected-alarm-grid">
                  <div><span>区域</span><strong>{{ selectedAlarmView.department }}</strong></div>
                  <div><span>时间</span><strong>{{ selectedAlarmView.date }}</strong></div>
                  <div><span>状态</span><strong>{{ selectedAlarmView.deal }}</strong></div>
                  <div><span>联系人</span><strong>{{ selectedAlarmView.phone || '--' }}</strong></div>
                </div>
                <p class="selected-alarm-note">{{ selectedAlarmHint }}</p>
                <div class="alarm-action-row">
                  <button class="mini-action primary" type="button" @click="openSelectedAlarmVideo">
                    <span class="mini-icon video-icon" aria-hidden="true"></span>
                    <span>报警视频片段</span>
                  </button>
                  <button class="mini-action danger" type="button" :disabled="!selectedAlarmIsPending" @click="processSelectedAlarm">
                    标记处理
                  </button>
                </div>
                <div class="ai-advice-card">
                  <span>AI 分析建议</span>
                  <strong>处置参考</strong>
                </div>
                <p class="ai-advice-text">{{ selectedAlarmAiAdvice }}</p>
              </article>
            </div>
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

        <section v-show="activeTab === 'analysis'" class="panel analysis-panel">
          <article class="card analysis-hero-card">
            <div class="panel-headline analysis-headline">
              <div>
                <h3>告警态势分析</h3>
                <p>复盘报警规律、时间分布和重复隐患点，辅助后续预防和治理。</p>
              </div>
              <div class="analysis-range-tabs">
                <button
                  v-for="option in analysisRangeOptions"
                  :key="option.value"
                  class="analysis-range-btn"
                  :class="{ active: analysisRange === option.value }"
                  type="button"
                  @click="analysisRange = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <div class="analysis-kpi-grid">
              <div v-for="item in analysisKpis" :key="item.name" class="analysis-kpi" :class="item.tone">
                <span>{{ item.name }}</span>
                <strong>{{ item.value }}</strong>
                <em>{{ item.desc }}</em>
              </div>
            </div>
          </article>

          <article class="card analysis-type-card">
            <div class="panel-headline small">
              <h3>报警类型分布</h3>
              <span class="analysis-sub-label">全部类型 / 占比 / 高等级</span>
            </div>
            <div class="analysis-type-stage">
              <div class="analysis-donut-wrap" @mouseleave="activeAnalysisTypeIndex = null">
                <svg class="analysis-donut-svg" viewBox="0 0 120 120" aria-label="报警类型占比图">
                  <circle cx="60" cy="60" r="42" class="analysis-donut-track" />
                  <circle
                    v-for="(segment, idx) in analysisTypeSegments"
                    :key="segment.eventType"
                    cx="60"
                    cy="60"
                    r="42"
                    class="analysis-donut-segment"
                    :class="{ active: activeAnalysisTypeIndex === idx }"
                    :stroke="segment.color"
                    :stroke-dasharray="`${segment.length} ${segment.gap}`"
                    :stroke-dashoffset="segment.offset"
                    @mouseenter="activeAnalysisTypeIndex = idx"
                    @click="activeAnalysisTypeIndex = idx"
                  >
                    <title>{{ segment.eventType }}：{{ segment.eventCount }} 次，占比 {{ segment.percent }}%</title>
                  </circle>
                </svg>
                <div class="analysis-donut-core">
                  <strong>{{ activeAnalysisTypeInfo.eventType }}</strong>
                  <span>{{ activeAnalysisTypeInfo.percent }}% · {{ activeAnalysisTypeInfo.eventCount }} 次</span>
                </div>
              </div>
              <div class="analysis-type-grid">
                <div
                  v-for="(item, idx) in analysisTypeDistribution"
                  :key="item.eventType"
                  class="analysis-type-cardlet"
                  :class="{ active: activeAnalysisTypeIndex === idx }"
                  :style="{ '--type-color': item.color }"
                  @mouseenter="activeAnalysisTypeIndex = idx"
                  @click="activeAnalysisTypeIndex = idx"
                >
                  <div class="analysis-type-cardlet-head">
                    <span>{{ item.eventType }}</span>
                    <strong>{{ item.percent }}%</strong>
                  </div>
                  <div class="analysis-type-cardlet-meta">
                    <em>{{ item.eventCount }} 次</em>
                    <em>高 {{ item.highCount }}</em>
                    <em>{{ item.areaCount }} 区</em>
                  </div>
                </div>
              </div>
              <div v-if="!analysisTypeDistribution.length" class="analysis-empty-state">暂无类型数据</div>
            </div>
          </article>

          <article class="card analysis-trend-card">
            <div class="panel-headline small">
              <h3>报警趋势</h3>
              <span class="analysis-sub-label">{{ analysisRangeLabel }}</span>
            </div>
            <div class="analysis-sparkline-card">
              <svg class="analysis-sparkline" viewBox="0 0 100 48" preserveAspectRatio="none">
                <path :d="analysisTrendAreaPath" class="analysis-spark-area" />
                <path :d="analysisTrendLinePath" class="analysis-spark-line" />
                <circle
                  v-for="point in analysisTrendSvgPoints"
                  :key="`${point.x}-${point.y}`"
                  :cx="point.x"
                  :cy="point.y"
                  r="1.5"
                  class="analysis-spark-dot"
                />
              </svg>
              <div class="analysis-trend-snapshot">
                <div>
                  <span>峰值</span>
                  <strong>{{ analysisPeakPoint.value }} 条</strong>
                  <em>{{ analysisPeakPoint.label }}</em>
                </div>
                <div>
                  <span>环比</span>
                  <strong :class="analysisDeltaTone">{{ analysisDeltaText }}</strong>
                  <em>较上一周期</em>
                </div>
              </div>
            </div>
          </article>

          <article class="card analysis-cross-card">
            <div class="panel-headline small">
              <h3>类型 × 区域热力矩阵</h3>
              <span class="analysis-sub-label">看清哪类问题集中在哪</span>
            </div>
            <div class="analysis-cross-table">
              <div class="analysis-cross-head">
                <span>区域 / 类型</span>
                <strong v-for="type in analysisCrossTypes" :key="type">{{ type }}</strong>
              </div>
              <div v-for="row in analysisCrossRows" :key="row.area" class="analysis-cross-row">
                <span>{{ row.area }}</span>
                <strong
                  v-for="type in analysisCrossTypes"
                  :key="type"
                  :class="{ hot: row.values[type] > 0 }"
                  :style="{ background: getCrossHeat(row.values[type], analysisCrossMax) }"
                >
                  {{ row.values[type] || '-' }}
                </strong>
              </div>
              <div v-if="!analysisCrossRows.length" class="analysis-empty-state">暂无交叉数据</div>
            </div>
          </article>

          <article class="card analysis-insight-card">
            <div class="panel-headline small">
              <h3>时段与重复隐患</h3>
              <span class="analysis-sub-label">辅助治理建议</span>
            </div>
            <div class="analysis-insight-body">
              <div class="analysis-time-orbit" :style="{ background: analysisTimeConicStyle }">
                <div>
                  <strong>{{ analysisPeakBucket?.label || '暂无' }}</strong>
                  <span>高发时段</span>
                </div>
              </div>
              <div class="analysis-insight-copy">
                <div class="analysis-time-pills">
                  <span v-for="item in analysisTimeBuckets" :key="item.label" :class="{ active: item.isPeak }">
                    {{ item.label }} {{ item.count }}
                  </span>
                </div>
                <p class="analysis-mini-summary">{{ analysisSummary }}</p>
                <div class="analysis-repeat-list compact">
                  <div v-for="item in analysisRepeatPointVisible" :key="item.area" class="analysis-repeat-item">
                    <div>
                      <span>{{ item.area }}</span>
                      <em>{{ item.topType }}</em>
                    </div>
                    <strong>{{ item.count }} 次</strong>
                  </div>
                  <div v-if="!analysisRepeatPointData.length" class="analysis-empty-state">暂无重复点位</div>
                </div>
              </div>
            </div>
          </article>
        </section>

        <section v-show="activeTab === 'video'" class="panel video-panel">
          <article class="card video-main">
            <div class="panel-headline video-headline">
              <div class="video-title-row">
                <h3>实时视频墙</h3>
                <span class="video-subtitle">点击画面可进入大屏预览</span>
              </div>
              <span class="inline-status">当前预览 {{ cameraTiles.length }} 路</span>
            </div>
            <TransitionGroup name="tile-flow" tag="div" class="monitor-grid monitor-grid-large">
              <div
                v-for="tile in cameraTiles"
                :key="monitorKey(tile)"
                class="video-tile"
                :class="{
                  'tile-online': tileStatus(tile).tone === 'online',
                  'tile-alert': tileStatus(tile).tone === 'alert',
                  'tile-offline': tileStatus(tile).tone === 'offline',
                  'tile-selected': selectedMonitorName === tile.name
                }"
                @click="selectPreviewTile(tile)"
                @dblclick="openFocus(tile)"
              >
                <video
                  :ref="(el) => setTileVideoRef(tile.name, el as HTMLVideoElement | null)"
                  class="tile-video"
                  muted
                  autoplay
                  playsinline
                ></video>
                <div v-if="tileStatus(tile).tone === 'offline'" class="tile-offline-state">
                  <svg class="tile-cam-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9A2.25 2.25 0 0013.5 5.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"/></svg>
                  <span>设备离线</span>
                </div>
                <div class="tile-status-badge" :class="tileStatus(tile).tone">
                  <i></i>
                  <span>{{ tileStatus(tile).label }}</span>
                </div>
                <div v-if="tilePendingCount(tile) > 0" class="tile-pending-badge">
                  未处理 {{ tilePendingCount(tile) }}
                </div>
                <div class="tile-overlay">
                  <div class="tile-copy">
                    <div class="tile-title">{{ tileDisplayName(tile) }}</div>
                    <div class="tile-sub">{{ tileSubtitle(tile) }}</div>
                  </div>
                  <button class="tile-focus-btn" type="button" @click.stop="openFocus(tile)">大屏</button>
                </div>
              </div>
            </TransitionGroup>
          </article>

          <aside class="video-side">
            <article class="card video-map-card">
              <div class="panel-headline map-headline">
                <h3 class="map-title">点位地图联动 <span class="live-dot"></span></h3>
                <div class="map-legend" aria-label="地图图例">
                  <span><i class="legend-dot normal"></i>正常</span>
                  <span><i class="legend-dot alert"></i>报警</span>
                </div>
              </div>
              <div class="map-square">
                <AMapLinkage3D :points="mapPoints" :alarm-counts="mapAlarmCounts" @point-click="onMapPointClick" />
              </div>
              <div class="map-insight-strip">
                <div class="map-insight-main">
                  <div class="monitor-insight-title">
                    <strong>{{ selectedMonitorOverview.name }}</strong>
                    <span class="risk-pill" :class="selectedMonitorRisk.tone">{{ selectedMonitorRisk.label }}</span>
                  </div>
                  <div class="monitor-health-row">
                    <span>{{ selectedMonitorOverview.department }}</span>
                    <span class="meta-separator">·</span>
                    <span :class="['insight-pending-text', selectedMonitorAlertStats.pending ? 'bad' : 'ok']">
                      未处理
                      {{ selectedMonitorAlertStats.pending }} 条
                    </span>
                  </div>
                </div>
              </div>
            </article>

            <article class="card ai-alarm-card">
              <div class="event-stream">
                <div class="event-stream-head">
                  <span class="event-stream-title">AI 实时报警时间轴</span>
                  <span class="event-stream-count">{{ recentEvents.length }} 条</span>
                </div>
                <TransitionGroup
                  v-if="recentEvents.length"
                  name="event-flow"
                  tag="div"
                  class="event-stream-list"
                >
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
                </TransitionGroup>
                <div v-else class="event-stream-list event-stream-empty-list">
                  <div class="event-item event-empty">
                    <span class="event-text">暂无事件，系统运行正常</span>
                  </div>
                </div>
              </div>
            </article>
          </aside>
        </section>

        <section v-show="activeTab === 'env'" class="panel env-panel">
          <article class="card env-overview-card">
            <div class="panel-headline env-overview-head">
              <div>
                <h3>环境车位总览</h3>
                <p>重点关注环境异常、车位余量和高占用区域。</p>
              </div>
              <div class="analysis-range-tabs">
                <button
                  v-for="option in envRangeOptions"
                  :key="option.value"
                  class="analysis-range-btn"
                  :class="{ active: envTrendRange === option.value }"
                  type="button"
                  @click="envTrendRange = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <div class="env-overview-body">
              <div class="env-priority-card" :class="envPriorityState.tone">
                <span>当前重点</span>
                <strong>{{ envPriorityState.title }}</strong>
                <p>{{ envPriorityState.desc }}</p>
              </div>
              <div class="env-kpi-grid">
                <div v-for="item in envOverviewKpis" :key="item.name" class="env-kpi" :class="item.tone">
                  <span>{{ item.name }}</span>
                  <strong>{{ item.value }}</strong>
                  <em>{{ item.desc }}</em>
                </div>
              </div>
            </div>
          </article>

          <article class="card env-status-card">
            <div class="panel-headline small">
              <h3>环境实时状态</h3>
              <span>{{ envParkingDataModeLabel }} · {{ envParkingRefreshSeconds }}s 刷新</span>
            </div>
            <div class="env-status-grid">
              <div v-for="item in envStatusCards" :key="item.key" class="env-status-item" :class="item.tone">
                <div class="env-status-top">
                  <span>{{ item.label }}</span>
                  <em>{{ item.status }}</em>
                </div>
                <strong>{{ item.value }}<small>{{ item.unit }}</small></strong>
                <div class="env-status-bar"><i :style="{ width: `${item.percent}%`, background: item.color }"></i></div>
              </div>
            </div>
          </article>

          <article class="card env-trend-card">
            <div class="panel-headline small env-trend-head">
              <div>
                <h3>环境趋势</h3>
                <span>{{ envTrendMetricConfig.desc }} · {{ envRangeLabel }}</span>
              </div>
              <div class="env-trend-switch">
                <button
                  v-for="metric in envTrendMetrics"
                  :key="metric.key"
                  class="env-trend-switch-btn"
                  :class="{ active: envTrendMetricKey === metric.key }"
                  type="button"
                  @click="envTrendMetricKey = metric.key"
                >
                  {{ metric.label }}
                </button>
              </div>
            </div>
            <div class="env-inline-insight" :class="envPriorityState.tone">
              <span>运行研判</span>
              <strong>{{ comfortLabel }}</strong>
              <p>{{ envParkingSummary }}</p>
            </div>
            <div class="env-trend-main">
              <svg class="env-trend-svg single" viewBox="0 0 360 168" preserveAspectRatio="xMidYMid meet" :aria-label="`${envTrendMetricConfig.label} 趋势图`">
                <line x1="40" y1="136" x2="344" y2="136" stroke="rgba(168,198,232,0.62)" stroke-width="1" />
                <line x1="40" y1="10" x2="40" y2="136" stroke="rgba(168,198,232,0.62)" stroke-width="1" />
                <line
                  v-for="tick in envTrendSelectedRender.yTicks"
                  :key="`${envTrendMetricKey}-y-${tick.value}`"
                  x1="40"
                  :y1="tick.y"
                  x2="344"
                  :y2="tick.y"
                  stroke="rgba(168,198,232,0.16)"
                  stroke-width="1"
                />
                <text
                  v-for="tick in envTrendSelectedRender.yTicks"
                  :key="`${envTrendMetricKey}-yl-${tick.value}`"
                  x="34"
                  :y="tick.y + 4"
                  text-anchor="end"
                  fill="rgba(214, 230, 255, 0.86)"
                  font-size="10"
                >
                  {{ tick.value }}
                </text>
                <text
                  v-for="tick in envTrendSelectedRender.xTicks"
                  :key="`${envTrendMetricKey}-x-${tick.label}`"
                  :x="tick.x"
                  y="156"
                  text-anchor="middle"
                  fill="rgba(214, 230, 255, 0.78)"
                  font-size="10"
                >
                  {{ tick.label }}
                </text>
                <path :d="envTrendSelectedRender.areaPath" :fill="envTrendMetricConfig.areaColor" />
                <polyline
                  :points="envTrendSelectedRender.points"
                  fill="none"
                  :stroke="envTrendMetricConfig.color"
                  stroke-width="2.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <circle
                  v-for="(dot, idx) in envTrendSelectedRender.dots"
                  :key="`${envTrendMetricKey}-dot-${idx}`"
                  :cx="dot.x"
                  :cy="dot.y"
                  r="2.6"
                  :fill="envTrendMetricConfig.color"
                  stroke="rgba(255,255,255,0.82)"
                  stroke-width="0.8"
                />
              </svg>
              <div class="env-trend-footer">
                <div class="env-trend-mini">
                  <span>当前</span>
                  <strong>{{ envTrendSelectedValue }}</strong>
                  <em>{{ envTrendMetricConfig.label }}</em>
                </div>
                <div class="env-trend-mini">
                  <span>峰值</span>
                  <strong>{{ envTrendSelectedPeak }}</strong>
                  <em>本周期最高</em>
                </div>
                <div class="env-trend-mini">
                  <span>变化</span>
                  <strong :class="envTrendSelectedDeltaTone">{{ envTrendSelectedDeltaText }}</strong>
                  <em>{{ envTrendSelectedDeltaDesc }}</em>
                </div>
              </div>
            </div>
          </article>

          <article class="card env-parking-card">
            <div class="panel-headline small">
              <h3>车位占用与高压区</h3>
              <div class="parking-head-right">
                <div class="traffic-flow-inline">
                  <span>车流量检测</span>
                  <em>{{ trafficFlowReserve.status }}</em>
                  <strong>今日 {{ trafficFlowReserve.today }}</strong>
                  <strong>入口 {{ trafficFlowReserve.inCount }}</strong>
                  <strong>出口 {{ trafficFlowReserve.outCount }}</strong>
                </div>
                <span>总车位 {{ parkingTotal }} · {{ parkingPressureLabel }}</span>
              </div>
            </div>
            <div class="parking-pressure-card" :class="parkingPressureTone">
              <div class="parking-pressure-main">
                <span>{{ parkingPressureLabel }}</span>
                <strong>{{ parkingOccupancy }}<small>%</small></strong>
                <em>{{ parkingPressureDesc }}</em>
              </div>
              <div class="parking-pressure-track">
                <div class="parking-pressure-meter" :style="{ '--parking-percent': `${parkingOccupancy}%` }">
                  <i></i>
                  <b></b>
                </div>
                <div class="parking-pressure-scale">
                  <span>宽松</span>
                  <span>繁忙</span>
                  <span>紧张</span>
                </div>
              </div>
              <div class="parking-pressure-stats">
                <div>
                  <span>已用</span>
                  <strong>{{ parkingUsed }}</strong>
                </div>
                <div>
                  <span>空闲</span>
                  <strong>{{ parkingFree }}</strong>
                </div>
                <div class="hot">
                  <span>高压区</span>
                  <strong>{{ parkingTopZone?.name || '暂无' }}</strong>
                  <em>{{ parkingTopZone?.percent || 0 }}%</em>
                </div>
              </div>
            </div>
            <div class="parking-zone-list compact">
              <div v-for="zone in parkingZoneCards" :key="zone.name" class="parking-zone-row" :class="zone.tone">
                <div class="parking-zone-name">
                  <span>{{ zone.name }}</span>
                  <em>{{ zone.used }}/{{ zone.capacity }} 已用</em>
                </div>
                <div class="parking-zone-bar"><i :style="{ width: `${zone.percent}%` }"></i></div>
                <div class="parking-zone-count">
                  <strong>{{ zone.percent }}%</strong>
                  <em>余 {{ zone.free }}</em>
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
                <button
                  v-for="task in pendingTasks"
                  :key="task.key"
                  class="task-item"
                  type="button"
                  :disabled="!task.alarm"
                  @click="goPendingTask(task)"
                >
                  {{ task.text }}
                </button>
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
          <section class="focus-state-card" :class="focusPanelState.tone">
            <header class="focus-state-head">
              <span>当前点位态势</span>
              <strong>{{ focusPanelState.label }}</strong>
            </header>
            <div class="focus-state-list">
              <div class="focus-state-row">
                <span>点位</span>
                <strong>{{ focusPanelInfo.pointName }}</strong>
              </div>
              <div class="focus-state-row">
                <span>状态</span>
                <strong>{{ focusPanelInfo.statusLabel }}</strong>
              </div>
              <div class="focus-state-row">
                <span>事件</span>
                <strong>{{ focusPanelInfo.eventName }}</strong>
              </div>
              <div class="focus-state-row">
                <span>时间</span>
                <strong>{{ focusPanelInfo.timeLabel }}</strong>
              </div>
              <div class="focus-state-row">
                <span>处理状态</span>
                <strong>{{ focusPanelInfo.dealText }}</strong>
              </div>
            </div>
            <div v-if="focusPendingAlarms.length > 1" class="focus-alarm-switch">
              <div class="focus-switch-head">
                <span>未处理报警</span>
                <strong>{{ focusPendingAlarms.length }} 条</strong>
              </div>
              <button
                v-for="alarm in focusVisibleAlarms"
                :key="focusAlarmKey(alarm)"
                class="focus-alarm-option"
                :class="{ active: focusAlarmKey(alarm) === focusActiveAlarmKey }"
                type="button"
                @click="selectFocusAlarm(alarm)"
              >
                <span>{{ alarm.eventName || alarm.name || '报警事件' }}</span>
                <em>{{ toTimeLabel(parseAlarmTimestamp(alarm)) }}</em>
              </button>
              <p v-if="focusHiddenAlarmCount > 0" class="focus-switch-more">
                还有 {{ focusHiddenAlarmCount }} 条，请到报警列表查看
              </p>
            </div>
            <div class="focus-action-row">
              <button class="btn" type="button" :disabled="!focusActivePendingAlarm" @click="viewFocusAlarm">查看报警</button>
              <button class="btn" type="button" :disabled="!focusActivePendingAlarm" @click="processFocusAlarm">标记处理</button>
              <button class="btn primary" type="button" @click="handoffFocusToAgent">交给 Agent</button>
            </div>
          </section>
          <button class="btn primary focus-close" type="button" @click="closeFocus">关闭大屏</button>
        </aside>
      </div>
    </div>

    <div class="focus-modal" :style="{ display: monitorModalVisible ? 'flex' : 'none' }" :aria-hidden="monitorModalVisible ? 'false' : 'true'">
      <div class="monitor-shell">
        <header class="monitor-head">
          <div>
            <h4>全部监控点</h4>
            <p class="muted">点击点位会切换进当前选中的预览格，不会自动打开大屏</p>
          </div>
          <button class="btn" type="button" @click="closeMonitorModal">关闭</button>
        </header>
        <div class="monitor-list">
          <div
            v-for="item in monitors"
            :key="monitorKey(item)"
            class="monitor-row"
            :class="{ active: selectedMonitorName === item.name, previewing: isMonitorInPreview(item) }"
            @click="switchMonitorIntoPreview(item, true)"
          >
            <div>
              <div class="row-title">{{ item.name }}</div>
              <div class="row-sub">{{ item.department || '未标注区域' }}</div>
            </div>
            <div class="monitor-row-actions">
              <span class="status" :class="{ online: monitorIsOnline(item) }">
                {{ monitorIsOnline(item) ? '在线' : '离线' }}
              </span>
              <span class="preview-tag" :class="{ active: isMonitorInPreview(item) }">
                {{ isMonitorInPreview(item) ? '预览中' : '切换' }}
              </span>
            </div>
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
import AMapLinkage3D from '@/components/AMapLinkage3D.vue'
import VirtualAgentStage from '@/components/VirtualAgentStage.vue'
import ChatPanel from '@/components/chat_panel.vue'
import dialog1 from '@/components/dialog1.vue'
import axios from 'axios'
import flvjs from 'flv.js'
import { demoAlarmVideoMap, rtmpAddressList, simulateChannelName } from '@/config/config'
import { useAlarmStore } from '@/stores/alarm'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { AlarmSocketClient, type AlarmSocketMessage } from '@/utils/alarmSocket'

type ModuleTab = 'alarm' | 'analysis' | 'video' | 'env' | 'agent'
type AgentStageStatus = 'idle' | 'listening' | 'thinking' | 'speaking'
type VoiceInteractionState = 'idle' | 'listening' | 'speaking'

interface MonitorStreamItem {
  id?: number | string
  name: string
  department?: string
  status?: number | string | boolean
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

interface AnalysisHeatRow {
  area: string
  values: Record<string, number>
}

interface AnalysisHeatMatrix {
  defer?: number
  rangeLabel?: string
  total?: number
  byType?: Array<{ name: string; count: number }>
  byArea?: Array<{ name: string; count: number }>
  types: string[]
  rows: AnalysisHeatRow[]
  maxCount: number
}

const router = useRouter()
const alarmStore = useAlarmStore()
const appStore = useAppStore()
const userStore = useUserStore()

const tabs: Array<{ key: ModuleTab; label: string }> = [
  { key: 'alarm', label: '告警处置' },
  { key: 'analysis', label: '态势分析' },
  { key: 'video', label: '视频巡检' },
  { key: 'env', label: '环境车位' },
  { key: 'agent', label: '智能助手' },
]
const activeTab = ref<ModuleTab>('video')
const agentStageKey = ref(0)
const currentTabLabel = computed(() => tabs.find(item => item.key === activeTab.value)?.label || '导航')

const focusVisible = ref(false)
const alarmDialogVisible = ref(false)
const currentAlarmItem = ref<any>(null)
const selectedAlarmRow = ref<any>(null)
const processDialogVisible = ref(false)
const processingRow = ref<any>(null)
const processingContent = ref('')
const processingSubmitting = ref(false)
const alarmTableWrapRef = ref<HTMLDivElement | null>(null)

const openAlarmDetail = (row: any) => {
  currentAlarmItem.value = row
  alarmDialogVisible.value = true
}

const selectAlarmRow = (row: any) => {
  if (!row || row.eventName === '暂无报警') return
  selectedAlarmRow.value = row
}

const scrollSelectedAlarmIntoView = () => {
  nextTick(() => {
    const wrap = alarmTableWrapRef.value
    if (!wrap || !selectedAlarmRow.value) return
    const selectedIndex = filteredAlarmRows.value.findIndex(row => alarmRowKey(row) === alarmRowKey(selectedAlarmRow.value))
    if (selectedIndex < 0) return
    const rowEl = wrap.querySelectorAll('tbody tr')[selectedIndex] as HTMLElement | undefined
    rowEl?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  })
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
const selectedMonitorName = ref(cameraTiles.value[0]?.name || '')
const focusSelectedAlarmKey = ref('')

const mapPoints = ref<MapPointItem[]>([
  { title: '北门监测点', camera: '1号机位 - 北门实时画面', className: 'p1' },
  { title: '中庭监测点', camera: '3号机位 - 东侧步道实时画面', className: 'p2' },
  { title: '车库监测点', camera: '2号机位 - 车库入口实时画面', className: 'p3' },
])

const RECENT_EVENT_LIMIT = 6
const RECENT_EVENT_POLL_MS = 60000
const PREVIEW_TILE_LIMIT = 6
const recentEvents = ref<RecentEventItem[]>([])
const recentEventInitialized = ref(false)
let recentEventPollTimer: number | null = null

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
    const candidate = new Date(`${year}-${month}-${day}T${hour}:${minute}:00`)
    if (Number.isNaN(candidate.getTime())) return 0
    if (candidate.getTime() > Date.now()) {
      candidate.setFullYear(year - 1)
    }
    return candidate.getTime()
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

const toDateTimeParts = (timestamp: number) => {
  const d = new Date(timestamp)
  if (!timestamp || Number.isNaN(d.getTime())) return null
  return {
    year: d.getFullYear(),
    month: String(d.getMonth() + 1).padStart(2, '0'),
    day: String(d.getDate()).padStart(2, '0'),
    hour: String(d.getHours()).padStart(2, '0'),
    minute: String(d.getMinutes()).padStart(2, '0'),
  }
}

const formatAlarmFullTime = (item: any): string => {
  const timestamp = parseAlarmTimestamp(item)
  const parts = toDateTimeParts(timestamp)
  if (!parts) return item?.date || item?.time || item?.createTime || '--'
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`
}

const formatAlarmListTime = (item: any): string => {
  const timestamp = parseAlarmTimestamp(item)
  const parts = toDateTimeParts(timestamp)
  if (!parts) return item?.date || item?.time || item?.createTime || '--'
  return `${parts.year}-${parts.month}-${parts.day}`
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

  const normalized = rawList
    .filter(item => item && item.caseType !== 13 && isAlarmPending(item))
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

  recentEvents.value = normalized
    .map(item => ({
      id: item.__id,
      time: toTimeLabel(item.__ts),
      text: `${item.department || item.location || '未标注'} ${item.eventName || '事件'}`,
      severity: toSeverity(item.level),
      isPending: true,
      dealText: '未处理',
      timestamp: item.__ts,
    }))
    .slice(0, RECENT_EVENT_LIMIT)
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
    console.log('报警数据请求失败，启用备用数据', e)
    useMockData()
  }
}

let alarmSocketClient: AlarmSocketClient | null = null
let alarmSocketRefreshTimer: number | null = null

const resolveCurrentUserId = () => {
  if (userStore.userId) return userStore.userId
  const sessionUserId = Number(sessionStorage.getItem('userId') || 0)
  return Number.isFinite(sessionUserId) ? sessionUserId : 0
}

const refreshAlarmDataFromSocket = () => {
  if (alarmSocketRefreshTimer !== null) {
    window.clearTimeout(alarmSocketRefreshTimer)
  }
  alarmSocketRefreshTimer = window.setTimeout(async () => {
    alarmSocketRefreshTimer = null
    await Promise.all([
      fetchAlarmList(),
      fetchAnalysisHeatMatrix(),
    ])
    await fetchRecentEventStream()
    refreshSummaryNow()
  }, 300)
}

const startAlarmSocket = () => {
  const userId = resolveCurrentUserId()
  if (!userId || alarmSocketClient) return
  alarmSocketClient = new AlarmSocketClient({
    userId,
    onAlarm: async (message: AlarmSocketMessage) => {
      console.log('[AlarmSocket] 收到新报警:', message)
      refreshAlarmDataFromSocket()
      const { ElMessage } = await import('element-plus')
      ElMessage.warning(message.message || '收到新的报警信息')
    },
    onOpen: () => console.log('[AlarmSocket] 连接成功'),
    onClose: () => console.log('[AlarmSocket] 连接关闭'),
    onError: (event) => console.warn('[AlarmSocket] 连接异常:', event),
  })
  alarmSocketClient.connect()
}

const stopAlarmSocket = () => {
  if (alarmSocketRefreshTimer !== null) {
    window.clearTimeout(alarmSocketRefreshTimer)
    alarmSocketRefreshTimer = null
  }
  alarmSocketClient?.close()
  alarmSocketClient = null
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
      video: demoAlarmVideoMap.bike
    },
    {
      eventName: '烟雾火灾告警',
      department: '车库入口',
      date: new Date().toLocaleString(),
      level: '3',
      deal: '未处理',
      location: '车库',
      createTime: new Date().toISOString(),
      video: demoAlarmVideoMap.fire
    },
    {
      eventName: '垃圾桶溢出告警',
      department: '东侧步道',
      date: new Date().toLocaleString(),
      level: '1',
      deal: '未处理',
      location: '东侧',
      createTime: new Date().toISOString(),
      video: demoAlarmVideoMap.garbage
    }
  ]
  alarmStore.setAlarmList(mockAlarms)
  alarmStore.updateStatisticsFromAlarms()
  console.log('已启用备用报警数据')
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
    if (Array.isArray(list)) {
      syncRecentEvents(list)
      recentEventInitialized.value = true
    }
  } catch (e) {
    if (!recentEventInitialized.value) {
      const fallbackList = alarmStore.getAlarmList || []
      if (Array.isArray(fallbackList)) {
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
}

// 联动控制通道
let simChannel: BroadcastChannel | null = null;
onMounted(() => {
  if (window.BroadcastChannel) {
    simChannel = new BroadcastChannel(simulateChannelName);
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
      video: demoAlarmVideoMap.bike,
      id: Date.now(), name: '联动事件', deal: '未处理', content: '平台联动触发', phone: '13800000000'
    };
  } else if (type === 'fire') {
    newAlarm = {
      eventName: '明火',
      department: '车库入口',
      date: now.toLocaleString(),
      level: 3,
      location: '车库',
      createTime: iso,
      video: demoAlarmVideoMap.fire,
      id: Date.now(), name: '联动事件', deal: '未处理', content: '平台联动触发', phone: '13800000000'
    };
  } else if (type === 'garbage') {
    newAlarm = {
      eventName: '垃圾',
      department: '东侧步道',
      date: now.toLocaleString(),
      level: 1,
      location: '东侧',
      createTime: iso,
      video: demoAlarmVideoMap.garbage,
      id: Date.now(), name: '联动事件', deal: '未处理', content: '平台联动触发', phone: '13800000000'
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
      ElMessage({ message: '收到联动告警指令：' + newAlarm.eventName, type: 'warning' });
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
const alarmDealFilter = ref<'all' | 'pending' | 'done'>('pending')
const analysisRange = ref<'day' | 'week' | 'month'>('week')
const analysisHeatMatrix = ref<AnalysisHeatMatrix | null>(null)
const analysisHeatLoading = ref(false)
const showAlarmTypeOther = ref(false)
const activeAnalysisTypeIndex = ref<number | null>(null)
const analysisRangeOptions: Array<{ value: 'day' | 'week' | 'month'; label: string }> = [
  { value: 'day', label: '今日' },
  { value: 'week', label: '近7天' },
  { value: 'month', label: '近30天' },
]
const analysisPalette = ['#7ee8ff', '#6ce2b2', '#f8cb71', '#ff8d8d', '#9ca7ff', '#52b7ff', '#ffb86b', '#d6f1ff']

const analysisRangeLabel = computed(() => analysisRangeOptions.find(item => item.value === analysisRange.value)?.label || '近7天')
const analysisRangeDefer = computed(() => {
  if (analysisRange.value === 'day') return 1
  if (analysisRange.value === 'month') return 30
  return 7
})

const normalizeHeatMatrix = (raw: any): AnalysisHeatMatrix | null => {
  if (!raw) return null
  const typeSet = new Set<string>()
  if (Array.isArray(raw.types)) {
    raw.types.map((item: any) => String(item || '').trim()).filter(Boolean).forEach((item: string) => typeSet.add(item))
  }
  if (Array.isArray(raw.byType)) {
    raw.byType.map((item: any) => String(item?.name || '').trim()).filter(Boolean).forEach((item: string) => typeSet.add(item))
  }
  if (Array.isArray(raw.rows)) {
    raw.rows.forEach((row: any) => {
      const sourceValues = row?.values && typeof row.values === 'object' ? row.values : {}
      Object.keys(sourceValues).map(item => item.trim()).filter(Boolean).forEach(item => typeSet.add(item))
    })
  }
  const types = Array.from(typeSet).slice(0, 4)
  const rows = Array.isArray(raw.rows)
    ? raw.rows.map((row: any) => {
        const values: Record<string, number> = {}
        const sourceValues = row?.values && typeof row.values === 'object' ? row.values : {}
        types.forEach((type) => {
          values[type] = Number(sourceValues[type] || 0)
        })
        return {
          area: String(row?.area || '未标注区域'),
          values,
        }
      }).filter((row: AnalysisHeatRow) => row.area)
    : []
  return {
    defer: raw.defer,
    rangeLabel: raw.rangeLabel,
    total: Number(raw.total || 0),
    byType: Array.isArray(raw.byType) ? raw.byType : [],
    byArea: Array.isArray(raw.byArea) ? raw.byArea : [],
    types,
    rows,
    maxCount: Number(raw.maxCount || 0),
  }
}

const fetchAnalysisHeatMatrix = async () => {
  analysisHeatLoading.value = true
  try {
    const { data } = await axios.get('/alarm/query/cnt/type-area', {
      params: {
        defer: analysisRangeDefer.value,
      },
    })
    if (data?.code === '00000') {
      analysisHeatMatrix.value = normalizeHeatMatrix(data.data)
      return
    }
    analysisHeatMatrix.value = null
  } catch (error) {
    void error
    analysisHeatMatrix.value = null
  } finally {
    analysisHeatLoading.value = false
  }
}


const filteredAlarmRows = computed(() => {
  const keyword = alarmKeyword.value.toLowerCase()
  return alarmTableRows.value
    .filter((row) => {
      const eventName = String(row.eventName || '').toLowerCase()
      const department = String(row.department || '').toLowerCase()
      const matchKeyword =
        !keyword ||
        eventName.includes(keyword) ||
        department.includes(keyword)
      if (!matchKeyword) return false

      if (alarmDealFilter.value === 'done') return row.deal.includes('已')
      return true
    })
    .sort((a, b) => {
      if (alarmDealFilter.value === 'pending') {
        const pendingDiff = Number(!b.deal.includes('已')) - Number(!a.deal.includes('已'))
        if (pendingDiff !== 0) return pendingDiff
      }
      const levelDiff = Number(b.level || 0) - Number(a.level || 0)
      if (levelDiff !== 0) return levelDiff
      return parseAlarmTimestamp(b) - parseAlarmTimestamp(a)
    })
})

const alarmChartItemsFromEntries = (entries: Array<[string, number]>) => (
  entries.map(([eventType, eventCount]) => ({ eventType, eventCount }))
)

const analysisRangeStart = computed(() => {
  const now = new Date()
  const start = new Date(now)
  if (analysisRange.value === 'day') {
    start.setHours(0, 0, 0, 0)
    return start.getTime()
  }
  const days = analysisRange.value === 'week' ? 6 : 29
  start.setDate(start.getDate() - days)
  start.setHours(0, 0, 0, 0)
  return start.getTime()
})

const analysisRangeEnd = computed(() => Date.now())

const analysisRangeDuration = computed(() => (
  Math.max(analysisRangeEnd.value - analysisRangeStart.value, 1)
))

const analysisAlarmRows = computed(() => (
  alarmTableRows.value.filter((row) => {
    if (row.eventName === '暂无报警') return false
    const timestamp = parseAlarmTimestamp(row)
    return timestamp >= analysisRangeStart.value
  })
))

const analysisPreviousRows = computed(() => {
  const currentStart = analysisRangeStart.value
  const previousStart = currentStart - analysisRangeDuration.value
  return alarmTableRows.value.filter((row) => {
    if (row.eventName === '暂无报警') return false
    const timestamp = parseAlarmTimestamp(row)
    return timestamp >= previousStart && timestamp < currentStart
  })
})

const analysisTypeChartData = computed(() => {
  const counts: Record<string, number> = {}
  analysisAlarmRows.value.forEach((row) => {
    const name = row.eventName || '未知事件'
    counts[name] = (counts[name] || 0) + 1
  })
  return alarmChartItemsFromEntries(Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8))
})

const analysisTypeDistribution = computed(() => {
  const map: Record<string, { eventCount: number; highCount: number; areas: Set<string> }> = {}
  analysisAlarmRows.value.forEach((row) => {
    const type = row.eventName || '未知事件'
    const area = row.department || row.location || '未标注区域'
    if (!map[type]) map[type] = { eventCount: 0, highCount: 0, areas: new Set<string>() }
    map[type].eventCount += 1
    if (Number(row.level || 1) >= 3) map[type].highCount += 1
    map[type].areas.add(area)
  })
  const total = Math.max(analysisAlarmRows.value.length, 1)
  return Object.entries(map)
    .sort((a, b) => b[1].eventCount - a[1].eventCount)
    .map(([eventType, item], index) => ({
      eventType,
      eventCount: item.eventCount,
      highCount: item.highCount,
      areaCount: item.areas.size,
      percent: Math.round((item.eventCount / total) * 100),
      color: analysisPalette[index % analysisPalette.length],
    }))
})

const analysisTypeSegments = computed(() => {
  const radius = 42
  const circumference = 2 * Math.PI * radius
  const total = analysisTypeDistribution.value.reduce((sum, item) => sum + item.eventCount, 0) || 1
  let cursor = 0
  return analysisTypeDistribution.value.map((item) => {
    const rawLength = (item.eventCount / total) * circumference
    const gapSize = analysisTypeDistribution.value.length > 1 ? 1.6 : 0
    const length = Math.max(rawLength - gapSize, 0)
    const segment = {
      ...item,
      length: Number(length.toFixed(2)),
      gap: Number((circumference - length).toFixed(2)),
      offset: Number((-cursor + circumference * 0.25).toFixed(2)),
    }
    cursor += rawLength
    return segment
  })
})
const activeAnalysisTypeInfo = computed(() => {
  const list = analysisTypeDistribution.value
  if (!list.length) {
    return { eventType: '暂无', eventCount: 0, percent: 0, highCount: 0, areaCount: 0, color: '#7ee8ff' }
  }
  const index = activeAnalysisTypeIndex.value ?? 0
  return list[index] || list[0]
})
const analysisAreaChartData = computed(() => {
  const counts: Record<string, number> = {}
  analysisAlarmRows.value.forEach((row) => {
    const area = row.department || row.location || '未标注区域'
    counts[area] = (counts[area] || 0) + 1
  })
  return alarmChartItemsFromEntries(Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6))
})

const analysisTrendPoints = computed(() => {
  const now = new Date()
  if (analysisRange.value === 'day') {
    return Array.from({ length: 8 }, (_, index) => {
      const startHour = index * 3
      const endHour = startHour + 3
      const count = analysisAlarmRows.value.filter((row) => {
        const timestamp = parseAlarmTimestamp(row)
        if (!timestamp) return false
        const d = new Date(timestamp)
        return d.getHours() >= startHour && d.getHours() < endHour
      }).length
      return { label: `${String(startHour).padStart(2, '0')}:00`, value: count }
    })
  }

  const days = analysisRange.value === 'week' ? 7 : 30
  return Array.from({ length: days }, (_, index) => {
    const d = new Date(now)
    d.setDate(now.getDate() - (days - index - 1))
    d.setHours(0, 0, 0, 0)
    const next = new Date(d)
    next.setDate(d.getDate() + 1)
    const count = analysisAlarmRows.value.filter((row) => {
      const timestamp = parseAlarmTimestamp(row)
      return timestamp >= d.getTime() && timestamp < next.getTime()
    }).length
    const label = analysisRange.value === 'week'
      ? `${d.getMonth() + 1}/${d.getDate()}`
      : index % 5 === 0 || index === days - 1 ? `${d.getMonth() + 1}/${d.getDate()}` : ''
    return { label, value: count }
  })
})

const analysisTrendMax = computed(() => Math.max(...analysisTrendPoints.value.map(item => item.value), 0))

const analysisTrendSvgPoints = computed(() => {
  const points = analysisTrendPoints.value
  if (!points.length) return []
  const max = Math.max(analysisTrendMax.value, 1)
  const count = Math.max(points.length - 1, 1)
  return points.map((item, index) => ({
    x: Number(((index / count) * 100).toFixed(2)),
    y: Number((44 - (item.value / max) * 34).toFixed(2)),
    value: item.value,
    label: item.label,
  }))
})

const buildSmoothPath = (points: Array<{ x: number; y: number }>) => {
  if (!points.length) return ''
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`
  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x} ${point.y}`
    const prev = points[index - 1]
    const controlX = Number(((prev.x + point.x) / 2).toFixed(2))
    return `${path} C ${controlX} ${prev.y}, ${controlX} ${point.y}, ${point.x} ${point.y}`
  }, '')
}

const analysisTrendLinePath = computed(() => buildSmoothPath(analysisTrendSvgPoints.value))

const analysisTrendAreaPath = computed(() => {
  const points = analysisTrendSvgPoints.value
  if (!points.length) return ''
  return `M ${points[0].x} 46 ${analysisTrendLinePath.value.replace(/^M/, 'L')} L ${points[points.length - 1].x} 46 Z`
})

const analysisPeakPoint = computed(() => (
  analysisTrendPoints.value.reduce(
    (max, item) => (item.value > max.value ? item : max),
    { label: '--', value: 0 },
  )
))

const analysisDeltaValue = computed(() => analysisAlarmRows.value.length - analysisPreviousRows.value.length)
const analysisDeltaText = computed(() => {
  const delta = analysisDeltaValue.value
  if (delta > 0) return `+${delta}`
  if (delta < 0) return String(delta)
  return '持平'
})
const analysisDeltaTone = computed(() => {
  if (analysisDeltaValue.value > 0) return 'up'
  if (analysisDeltaValue.value < 0) return 'down'
  return 'flat'
})

const analysisPendingCount = computed(() => analysisAlarmRows.value.filter(row => isAlarmPending(row)).length)
const analysisHighCount = computed(() => analysisAlarmRows.value.filter(row => Number(row.level || 1) >= 3).length)
const analysisDoneCount = computed(() => Math.max(analysisAlarmRows.value.length - analysisPendingCount.value, 0))
const analysisCompletionRate = computed(() => {
  const total = analysisAlarmRows.value.length
  return total ? Math.round((analysisDoneCount.value / total) * 100) : 100
})

const topAnalysisType = computed(() => analysisTypeChartData.value[0]?.eventType || '暂无')
const topAnalysisArea = computed(() => analysisAreaChartData.value[0]?.eventType || '暂无')
const analysisTypeMax = computed(() => Math.max(...analysisTypeChartData.value.map(item => item.eventCount), 0))
const analysisAreaMax = computed(() => Math.max(...analysisAreaChartData.value.map(item => item.eventCount), 0))
const analysisHighRatio = computed(() => (
  analysisAlarmRows.value.length ? Math.round((analysisHighCount.value / analysisAlarmRows.value.length) * 100) : 0
))
const analysisAreaCoverage = computed(() => (
  new Set(analysisAlarmRows.value.map(row => row.department || row.location || '未标注区域')).size
))

const analysisRepeatPointData = computed(() => {
  const areaMap: Record<string, { count: number; typeCounts: Record<string, number> }> = {}
  analysisAlarmRows.value.forEach((row) => {
    const area = row.department || row.location || '未标注区域'
    const type = row.eventName || '未知事件'
    if (!areaMap[area]) areaMap[area] = { count: 0, typeCounts: {} }
    areaMap[area].count += 1
    areaMap[area].typeCounts[type] = (areaMap[area].typeCounts[type] || 0) + 1
  })
  return Object.entries(areaMap)
    .filter(([, value]) => value.count > 1)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 4)
    .map(([area, value]) => ({
      area,
      count: value.count,
      topType: Object.entries(value.typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '未知事件',
    }))
})

const analysisRepeatPointVisible = computed(() => analysisRepeatPointData.value.slice(0, 2))

const fallbackAnalysisCrossTypes = computed(() => analysisTypeChartData.value.slice(0, 4).map(item => item.eventType))

const fallbackAnalysisCrossRows = computed(() => {
  const topAreas = analysisAreaChartData.value.slice(0, 4).map(item => item.eventType)
  return topAreas.map((area) => {
    const values: Record<string, number> = {}
    fallbackAnalysisCrossTypes.value.forEach((type) => {
      values[type] = analysisAlarmRows.value.filter((row) => {
        const rowArea = row.department || row.location || '未标注区域'
        const rowType = row.eventName || '未知事件'
        return rowArea === area && rowType === type
      }).length
    })
    return { area, values }
  })
})

const uniqueTopItems = (items: string[], limit = 4) => (
  Array.from(new Set(items.map(item => item.trim()).filter(Boolean))).slice(0, limit)
)

const analysisCrossTypes = computed(() => uniqueTopItems([
  ...(analysisHeatMatrix.value?.types || []),
  ...fallbackAnalysisCrossTypes.value,
]))

const analysisCrossRows = computed(() => {
  const types = analysisCrossTypes.value
  const rowMap = new Map<string, AnalysisHeatRow>()

  const addRow = (row: AnalysisHeatRow) => {
    const area = String(row.area || '').trim()
    if (!area) return
    const current = rowMap.get(area) || { area, values: {} }
    types.forEach((type) => {
      const nextValue = Number(row.values?.[type] || 0)
      current.values[type] = Math.max(Number(current.values[type] || 0), nextValue)
    })
    rowMap.set(area, current)
  }

  ;(analysisHeatMatrix.value?.rows || []).forEach(addRow)
  fallbackAnalysisCrossRows.value.forEach(addRow)

  return Array.from(rowMap.values()).slice(0, 4).map(row => ({
    area: row.area,
    values: types.reduce<Record<string, number>>((values, type) => {
      values[type] = Number(row.values[type] || 0)
      return values
    }, {}),
  }))
})

const analysisCrossMax = computed(() => {
  if (analysisHeatMatrix.value?.maxCount) return analysisHeatMatrix.value.maxCount
  return Math.max(
    ...analysisCrossRows.value.flatMap(row => Object.values(row.values)),
    0,
  )
})

const getCrossHeat = (value: number, max: number) => {
  if (!value || !max) return 'rgba(126, 197, 255, 0.08)'
  const ratio = Math.min(value / max, 1)
  const alpha = 0.16 + ratio * 0.5
  if (ratio > 0.66) return `linear-gradient(135deg, rgba(255, 141, 141, ${alpha}), rgba(248, 203, 113, ${alpha - 0.08}))`
  if (ratio > 0.33) return `linear-gradient(135deg, rgba(248, 203, 113, ${alpha}), rgba(126, 232, 255, ${alpha - 0.08}))`
  return `linear-gradient(135deg, rgba(126, 232, 255, ${alpha}), rgba(108, 226, 178, ${alpha - 0.06}))`
}

const analysisTimeBuckets = computed(() => {
  const buckets = [
    { label: '凌晨', range: '00:00-06:00', start: 0, end: 6 },
    { label: '上午', range: '06:00-12:00', start: 6, end: 12 },
    { label: '下午', range: '12:00-18:00', start: 12, end: 18 },
    { label: '夜间', range: '18:00-24:00', start: 18, end: 24 },
  ]
  const counts = buckets.map((bucket) => {
    const count = analysisAlarmRows.value.filter((row) => {
      const timestamp = parseAlarmTimestamp(row)
      if (!timestamp) return false
      const hour = new Date(timestamp).getHours()
      return hour >= bucket.start && hour < bucket.end
    }).length
    return { ...bucket, count }
  })
  const max = Math.max(...counts.map(item => item.count), 1)
  const peak = Math.max(...counts.map(item => item.count), 0)
  return counts.map(item => ({
    ...item,
    percent: Math.max(Math.round((item.count / max) * 100), item.count > 0 ? 12 : 0),
    isPeak: item.count > 0 && item.count === peak,
  }))
})

const analysisPeakBucket = computed(() => {
  const peak = analysisTimeBuckets.value.reduce(
    (max, item) => (item.count > max.count ? item : max),
    analysisTimeBuckets.value[0] || { label: '暂无', range: '', start: 0, end: 0, count: 0, percent: 0, isPeak: false },
  )
  return peak.count > 0 ? peak : null
})

const analysisTimeConicStyle = computed(() => {
  const colors = ['#5ed7ff', '#6ce2b2', '#f8cb71', '#ff8d8d']
  const buckets = analysisTimeBuckets.value
  const total = buckets.reduce((sum, item) => sum + item.count, 0)
  if (!total) return 'conic-gradient(rgba(126, 197, 255, 0.12) 0deg 360deg)'
  let cursor = 0
  const stops = buckets.map((item, index) => {
    const start = cursor
    const end = cursor + (item.count / total) * 360
    cursor = end
    return `${colors[index % colors.length]} ${start.toFixed(1)}deg ${end.toFixed(1)}deg`
  })
  return `conic-gradient(${stops.join(', ')})`
})

const analysisKpis = computed(() => [
  { name: '样本总量', value: analysisAlarmRows.value.length, desc: analysisRangeLabel.value, tone: 'info' },
  { name: '环比变化', value: analysisDeltaText.value, desc: '较上一周期', tone: analysisDeltaTone.value },
  { name: '高等级占比', value: `${analysisHighRatio.value}%`, desc: `${analysisHighCount.value} 条高等级`, tone: analysisHighRatio.value >= 50 ? 'warn' : 'ok' },
  { name: '覆盖区域', value: analysisAreaCoverage.value, desc: '涉及报警区域', tone: 'area' },
  { name: '重复点位', value: analysisRepeatPointData.value.length, desc: '多次触发区域', tone: analysisRepeatPointData.value.length ? 'danger' : 'ok' },
])

const analysisSummary = computed(() => {
  if (!analysisAlarmRows.value.length) return `${analysisRangeLabel.value}暂无报警记录，社区整体运行平稳。`
  const peakBucket = analysisTimeBuckets.value.find(item => item.isPeak)
  if (analysisRepeatPointData.value.length > 0) {
    return `${analysisRangeLabel.value}报警主要集中在 ${topAnalysisArea.value}，重复触发点位 ${analysisRepeatPointData.value.length} 个，高频类型为 ${topAnalysisType.value}，高发时段为 ${peakBucket?.label || '暂无'}。`
  }
  if (analysisHighRatio.value >= 40) {
    return `${analysisRangeLabel.value}高等级报警占比 ${analysisHighRatio.value}%，建议复盘 ${topAnalysisType.value} 的触发条件和现场处置流程。`
  }
  return `${analysisRangeLabel.value}报警分布相对分散，可重点观察 ${topAnalysisArea.value} 与 ${topAnalysisType.value} 是否继续上升。`
})

const alarmCompletionRate = computed(() => {
  const validRows = alarmTableRows.value.filter(row => row.eventName !== '暂无报警')
  const total = validRows.length
  if (!total) return 100
  const done = validRows.filter(item => !isAlarmPending(item)).length
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

const alarmRowKey = (row: any, idx = 0): string => (
  String(row?.id ?? `${row?.eventName || 'alarm'}-${row?.department || 'area'}-${row?.date || idx}`)
)

const actionableAlarmRows = computed(() => (
  filteredAlarmRows.value.filter(row => row.eventName !== '暂无报警')
))

const activeAlarmRow = computed(() => {
  if (!actionableAlarmRows.value.length) return null
  const selectedKey = alarmRowKey(selectedAlarmRow.value)
  return actionableAlarmRows.value.find(row => alarmRowKey(row) === selectedKey) || actionableAlarmRows.value[0]
})

const selectedAlarmView = computed(() => activeAlarmRow.value || {
  eventName: '暂无报警',
  department: '--',
  date: '--',
  level: 1,
  deal: '已处理',
  phone: '--',
})

const isSelectedAlarm = (row: any): boolean => (
  Boolean(row && activeAlarmRow.value && alarmRowKey(row) === alarmRowKey(activeAlarmRow.value))
)

const selectedAlarmIsPending = computed(() => !String(selectedAlarmView.value.deal || '').includes('已'))

const selectedAlarmTone = computed(() => {
  if (!selectedAlarmIsPending.value) return 'resolved'
  return severityClass(Number(selectedAlarmView.value.level || 1))
})

const selectedAlarmHint = computed(() => {
  const alarm = selectedAlarmView.value
  if (alarm.eventName === '暂无报警') return '当前无可处置报警，系统处于观察状态。'
  if (!selectedAlarmIsPending.value) return '该报警已完成处理，可继续复核其他未处理事项。'
  if (Number(alarm.level || 1) >= 3) return '高等级未处理报警，建议立即查看报警视频片段并形成处置闭环。'
  return '建议先查看报警视频片段，再根据现场情况完成处理记录。'
})

const selectedAlarmAiAdvice = computed(() => {
  const alarm = selectedAlarmView.value
  if (alarm.eventName === '暂无报警') return '当前暂无报警任务，可保持巡检与视频轮询。'
  if (!selectedAlarmIsPending.value) return `该 ${alarm.eventName} 报警已处理，建议抽查 ${alarm.department} 的视频回放，确认处置记录完整。`
  const levelText = severityText(Number(alarm.level || 1))
  const urgentPrefix = Number(alarm.level || 1) >= 3 ? '优先级较高，建议立即' : '建议'
  return `${urgentPrefix}查看 ${alarm.department} 的报警视频片段，复核 ${alarm.eventName} 发生时的现场情况；确认异常后通知值班员现场核验，并在处理完成后补充处置说明。当前等级：${levelText}。`
})

const pendingAlarmCount = computed(() => (
  alarmTableRows.value.filter(row => row.eventName !== '暂无报警' && isAlarmPending(row)).length
))

const highPendingAlarmCount = computed(() => (
  alarmTableRows.value.filter(row => row.eventName !== '暂无报警' && isAlarmPending(row) && Number(row.level || 1) >= 3).length
))

const todayAlarmCount = computed(() => {
  const now = new Date()
  return alarmTableRows.value.filter((row) => {
    if (row.eventName === '暂无报警') return false
    const timestamp = parseAlarmTimestamp(row)
    if (!timestamp) return false
    const d = new Date(timestamp)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  }).length
})

const topAlarmArea = computed(() => {
  const counts: Record<string, number> = {}
  alarmTableRows.value.forEach((row) => {
    if (row.eventName === '暂无报警') return
    const area = row.department || '未标注'
    counts[area] = (counts[area] || 0) + 1
  })
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || '暂无'
})

const alarmCommandKpis = computed(() => [
  { name: '未处理', value: pendingAlarmCount.value, tone: 'danger' },
  { name: '高等级', value: highPendingAlarmCount.value, tone: 'warn' },
  { name: '今日新增', value: todayAlarmCount.value, tone: 'info' },
  { name: '处理率', value: `${alarmCompletionRate.value}%`, tone: 'ok' },
  { name: '重点区域', value: topAlarmArea.value, tone: 'area' },
])

interface AlarmTypeStat {
  name: string
  count: number
  percent: number
  isOther?: boolean
}

const alarmTypeSortedEntries = computed(() => {
  const counts: Record<string, number> = {}
  alarmTableRows.value.forEach((row) => {
    if (row.eventName === '暂无报警') return
    const eventName = row.eventName || '未知事件'
    counts[eventName] = (counts[eventName] || 0) + 1
  })
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
})

const alarmTypeOtherItems = computed<AlarmTypeStat[]>(() => {
  const rest = alarmTypeSortedEntries.value.slice(3)
  return rest.map(([name, count]) => ({
    name,
    count,
    percent: 0,
  }))
})

const alarmTypeOtherCount = computed(() => (
  alarmTypeOtherItems.value.reduce((sum, item) => sum + item.count, 0)
))

const alarmTypeStats = computed<AlarmTypeStat[]>(() => {
  const entries = alarmTypeSortedEntries.value
  const topList = entries.length > 4 ? entries.slice(0, 3) : entries.slice(0, 4)
  const otherCount = entries.length > 4 ? alarmTypeOtherCount.value : 0
  const list = otherCount > 0
    ? [...topList, ['其他', otherCount] as [string, number]]
    : topList
  if (!list.length) {
    return [{ name: '暂无报警', count: 0, percent: 0 }]
  }
  const max = Math.max(...list.map(([, count]) => count), 1)
  return list.map(([name, count]) => ({
    name,
    count,
    percent: Math.max(Math.round((count / max) * 100), count > 0 ? 16 : 0),
    isOther: name === '其他',
  }))
})

const toggleAlarmTypeOther = (item: AlarmTypeStat) => {
  if (!item.isOther) {
    showAlarmTypeOther.value = false
    return
  }
  showAlarmTypeOther.value = !showAlarmTypeOther.value
}

const activeAlarmAreaCount = computed(() => {
  const areas = new Set<string>()
  alarmTableRows.value.forEach((row) => {
    if (row.eventName === '暂无报警') return
    areas.add(row.department || '未标注')
  })
  return areas.size
})

const alarmSituationTone = computed(() => {
  if (highPendingAlarmCount.value > 0) return 'high'
  if (pendingAlarmCount.value > 0) return 'pending'
  return 'calm'
})

const alarmSituationStatus = computed(() => {
  if (highPendingAlarmCount.value > 0) return '高风险待处置'
  if (pendingAlarmCount.value > 0) return '有报警待处理'
  return '运行平稳'
})

const alarmSituationTitle = computed(() => {
  if (highPendingAlarmCount.value > 0) return `${highPendingAlarmCount.value} 条高等级未处理报警`
  if (pendingAlarmCount.value > 0) return `${pendingAlarmCount.value} 条未处理报警`
  if (todayAlarmCount.value > 0) return `今日新增 ${todayAlarmCount.value} 条报警`
  return '当前暂无未处理报警'
})

const alarmSituationDesc = computed(() => {
  const topType = alarmTypeStats.value[0]?.name || '暂无报警'
  if (pendingAlarmCount.value > 0) {
    return `主要集中在 ${topAlarmArea.value}，高频类型为 ${topType}，建议先处理未闭环事件。`
  }
  if (todayAlarmCount.value > 0) {
    return `今日报警已纳入处置闭环，重点复盘 ${topAlarmArea.value} 和 ${topType}。`
  }
  return '系统当前未发现待处置报警，可继续保持巡检和视频轮询。'
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

const ENV_PARKING_DATA_MODE: 'mock' | 'api' = 'api'
const ENV_PARKING_REFRESH_MS = 6000
const envParkingRefreshSeconds = Math.round(ENV_PARKING_REFRESH_MS / 1000)
const envParkingDataModeLabel = computed(() => (ENV_PARKING_DATA_MODE === 'mock' ? '备用数据' : '实时接口'))

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))
const randDelta = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min
const pad2 = (n: number) => String(n).padStart(2, '0')
const toHmLabel = (date: Date) => `${pad2(date.getHours())}:${pad2(date.getMinutes())}`

const ensureMonitorId = async (): Promise<number> => {
  if (appStore.getMonitorId && appStore.getMonitorId !== 0) return appStore.getMonitorId
  const { data } = await axios.get('/monitor')
  const list = data?.data || []
  const monitorId = Number(list[0]?.id || 0)
  if (monitorId) appStore.setMonitorId(monitorId)
  return monitorId
}

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
const envRangeOptions: Array<{ value: 'day' | 'week' | 'month'; label: string }> = [
  { value: 'day', label: '今日' },
  { value: 'week', label: '近7天' },
  { value: 'month', label: '近30天' },
]
const envRangeLabel = computed(() => envRangeOptions.find(item => item.value === envTrendRange.value)?.label || '近7天')

const envTrendMetrics = [
  { key: 'aqi', label: 'AQI', desc: '空气质量指数', unit: '指数', color: '#63b8ff', areaColor: 'rgba(99,184,255,0.22)' },
  { key: 'humidity', label: '湿度', desc: '空气湿度变化', unit: '%', color: '#53d5a5', areaColor: 'rgba(83,213,165,0.20)' },
  { key: 'pm25', label: 'PM2.5', desc: '细颗粒物变化', unit: 'ug/m3', color: '#f8cb71', areaColor: 'rgba(248,203,113,0.18)' },
  { key: 'combustibleGas', label: '可燃气体', desc: '可燃气体浓度', unit: 'ppm', color: '#ff8d8d', areaColor: 'rgba(255,141,141,0.18)' },
] as const

type EnvMetricKey = typeof envTrendMetrics[number]['key']
const envTrendMetricKey = ref<EnvMetricKey>('aqi')

interface EnvPoint {
  label: string
  aqi: number
  humidity: number
  pm25: number
  combustibleGas: number
}

interface EnvRealtimeApi {
  aqi: number
  humidity: number
  pm25: number
  combustibleGas: number
  createTime?: string
}

interface ParkingRealtimeApi {
  zones?: Array<{
    areaName: string
    totalSpaces: number
    occupiedSpaces: number
  }>
}

interface ParkingTrendApiPoint {
  label: string
  occupancy: number
  used: number
}

const envTrendDataState = ref<Record<'day' | 'week' | 'month', EnvPoint[]>>({
  day: [
    { label: '00:00', aqi: 72, humidity: 63, pm25: 42, combustibleGas: 11 },
    { label: '04:00', aqi: 76, humidity: 64, pm25: 46, combustibleGas: 10 },
    { label: '08:00', aqi: 79, humidity: 58, pm25: 48, combustibleGas: 14 },
    { label: '12:00', aqi: 84, humidity: 54, pm25: 55, combustibleGas: 16 },
    { label: '16:00', aqi: 87, humidity: 52, pm25: 59, combustibleGas: 13 },
    { label: '20:00', aqi: 80, humidity: 57, pm25: 50, combustibleGas: 12 },
    { label: '24:00', aqi: 75, humidity: 61, pm25: 45, combustibleGas: 9 },
  ],
  week: [
    { label: '周一', aqi: 76, humidity: 62, pm25: 47, combustibleGas: 12 },
    { label: '周二', aqi: 82, humidity: 59, pm25: 52, combustibleGas: 14 },
    { label: '周三', aqi: 78, humidity: 57, pm25: 49, combustibleGas: 13 },
    { label: '周四', aqi: 86, humidity: 55, pm25: 56, combustibleGas: 17 },
    { label: '周五', aqi: 81, humidity: 58, pm25: 51, combustibleGas: 15 },
    { label: '周六', aqi: 74, humidity: 63, pm25: 45, combustibleGas: 11 },
    { label: '周日', aqi: 72, humidity: 64, pm25: 43, combustibleGas: 10 },
  ],
  month: [
    { label: '4/01', aqi: 79, humidity: 60, pm25: 51, combustibleGas: 14 },
    { label: '4/05', aqi: 75, humidity: 62, pm25: 47, combustibleGas: 12 },
    { label: '4/10', aqi: 83, humidity: 58, pm25: 55, combustibleGas: 16 },
    { label: '4/15', aqi: 88, humidity: 54, pm25: 60, combustibleGas: 18 },
    { label: '4/20', aqi: 80, humidity: 57, pm25: 52, combustibleGas: 15 },
    { label: '4/25', aqi: 73, humidity: 63, pm25: 44, combustibleGas: 11 },
    { label: '4/30', aqi: 77, humidity: 61, pm25: 48, combustibleGas: 13 },
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

const envTrendMetricConfig = computed(() => (
  envTrendMetrics.find(item => item.key === envTrendMetricKey.value) || envTrendMetrics[0]
))

const buildTrendRender = (metric: EnvMetricKey): TrendRenderData => {
  const series = envTrendSeries.value
  const left = 40
  const right = 344
  const top = metric === 'aqi' || metric === 'pm25' ? 10 : 16
  const bottom = metric === 'aqi' || metric === 'pm25' ? 136 : 128
  const width = right - left
  const height = bottom - top
  const values = series.map(item => item[metric])
  const min = Math.min(...values)
  const max = Math.max(...values)
  const diff = Math.max(max - min, 1)
  const focusMetric = metric === 'aqi' || metric === 'pm25'
  const padRatio = focusMetric ? 0.04 : 0.2
  const minPad = focusMetric ? 0.5 : 2
  const rawMin = Math.max(min - Math.max(diff * padRatio, minPad), 0)
  const rawMax = max + Math.max(diff * padRatio, minPad)
  const tickStep = Math.max(Math.ceil((rawMax - rawMin) / 4), 1)
  const yMin = Math.max(Math.floor(rawMin / tickStep) * tickStep, 0)
  const yMax = Math.ceil(rawMax / tickStep) * tickStep
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
  const xTicks = series.length > 5
    ? series.filter((_, idx) => idx === 0 || idx === Math.floor((series.length - 1) / 2) || idx === series.length - 1)
        .map(item => ({ label: item.label, x: left + series.findIndex(source => source.label === item.label) * stepX }))
    : series.map((item, idx) => ({ label: item.label, x: left + idx * stepX }))

  return { points, areaPath: `M ${areaPath} Z`, dots, yTicks, xTicks }
}

const envTrendCharts = computed<Record<EnvMetricKey, TrendRenderData>>(() => ({
  aqi: buildTrendRender('aqi'),
  humidity: buildTrendRender('humidity'),
  pm25: buildTrendRender('pm25'),
  combustibleGas: buildTrendRender('combustibleGas'),
}))

const envTrendSelectedRender = computed(() => envTrendCharts.value[envTrendMetricKey.value])

const envTrendSelectedSeries = computed(() => envTrendSeries.value.map(item => item[envTrendMetricKey.value]))
const envTrendSelectedValue = computed(() => envTrendSelectedSeries.value.at(-1) ?? 0)
const envTrendSelectedPeak = computed(() => Math.max(...envTrendSelectedSeries.value, 0))
const envTrendSelectedDelta = computed(() => {
  const values = envTrendSelectedSeries.value
  if (values.length < 2) return 0
  return values[values.length - 1] - values[values.length - 2]
})
const envTrendSelectedDeltaText = computed(() => {
  const delta = envTrendSelectedDelta.value
  if (delta > 0) return `+${delta}`
  if (delta < 0) return String(delta)
  return '持平'
})
const envTrendSelectedDeltaTone = computed(() => {
  if (envTrendSelectedDelta.value > 0) return 'up'
  if (envTrendSelectedDelta.value < 0) return 'down'
  return 'flat'
})
const envTrendSelectedDeltaDesc = computed(() => {
  const delta = envTrendSelectedDelta.value
  if (delta > 0) return '较上一时刻上升'
  if (delta < 0) return '较上一时刻下降'
  return '较上一时刻持平'
})

const parkingZoneState = ref<ParkingZone[]>([
  { name: '地库A区', capacity: 62, used: 38 },
  { name: '地库B区', capacity: 44, used: 23 },
  { name: '地面东侧', capacity: 30, used: 16 },
  { name: '地面西侧', capacity: 24, used: 11 },
])

const parkingDayTrend = ref<ParkingDayPoint[]>([
  { label: '00:00', occupancy: 41, used: 66 },
  { label: '04:00', occupancy: 37, used: 59 },
  { label: '08:00', occupancy: 55, used: 88 },
  { label: '12:00', occupancy: 67, used: 107 },
  { label: '16:00', occupancy: 73, used: 117 },
  { label: '20:00', occupancy: 61, used: 98 },
  { label: '24:00', occupancy: 48, used: 77 },
])
const syncEnvParkingFromApi = async (): Promise<boolean> => {
  if (ENV_PARKING_DATA_MODE !== 'api') return false
  try {
    // 预留后端接口位：接入后将返回值写入 envTrendDataState / parkingZoneState / parkingDayTrend
    const monitorId = await ensureMonitorId()
    if (!monitorId) return false

    const envRealtimeRes = await axios.get('/env/realtime', { params: { monitorId } })
    const envDayRes = await axios.get('/env/trend', { params: { monitorId, range: 'day' } })
    const parkingRealtimeRes = await axios.get('/parking/realtime', { params: { monitorId } })
    const parkingTrendRes = await axios.get('/parking/trend', { params: { monitorId, range: 'day' } })
    const envScopedRes = envTrendRange.value === 'day'
      ? envDayRes
      : await axios.get('/env/trend', { params: { monitorId, range: envTrendRange.value } })

    const envRealtime = envRealtimeRes?.data?.data as EnvRealtimeApi | null
    const envDay = Array.isArray(envDayRes?.data?.data) ? envDayRes.data.data as EnvPoint[] : []
    const envScoped = Array.isArray(envScopedRes?.data?.data) ? envScopedRes.data.data as EnvPoint[] : []
    const parkingRealtime = parkingRealtimeRes?.data?.data as ParkingRealtimeApi | null
    const parkingTrend = Array.isArray(parkingTrendRes?.data?.data) ? parkingTrendRes.data.data as ParkingTrendApiPoint[] : []

    if (!envRealtime || !envDay.length || !parkingRealtime?.zones?.length || !parkingTrend.length) return false

    envTrendDataState.value.day = envDay.map(item => ({
      label: item.label,
      aqi: Number(item.aqi || 0),
      humidity: Number(item.humidity || 0),
      pm25: Number(item.pm25 || 0),
      combustibleGas: Number(item.combustibleGas || 0),
    }))
    envTrendDataState.value[envTrendRange.value] = envScoped.map(item => ({
      label: item.label,
      aqi: Number(item.aqi || 0),
      humidity: Number(item.humidity || 0),
      pm25: Number(item.pm25 || 0),
      combustibleGas: Number(item.combustibleGas || 0),
    }))
    parkingZoneState.value = parkingRealtime.zones.map(zone => ({
      name: zone.areaName,
      capacity: Number(zone.totalSpaces || 0),
      used: Number(zone.occupiedSpaces || 0),
    }))
    parkingDayTrend.value = parkingTrend.map(item => ({
      label: item.label,
      occupancy: Number(item.occupancy || 0),
      used: Number(item.used || 0),
    }))
    return true
  } catch (error) {
    void error
    return false
  }
}

const stepMockEnvParking = () => {
  const now = new Date()
  const daySeries = envTrendDataState.value.day
  const last = daySeries[daySeries.length - 1] || { label: '00:00', aqi: 72, humidity: 62, pm25: 44, combustibleGas: 10 }
  const nextPoint: EnvPoint = {
    label: toHmLabel(now),
    aqi: clamp(last.aqi + randDelta(-4, 5), 45, 135),
    humidity: clamp(last.humidity + randDelta(-3, 3), 35, 82),
    pm25: clamp(last.pm25 + randDelta(-4, 4), 18, 96),
    combustibleGas: clamp(last.combustibleGas + randDelta(-2, 3), 4, 40),
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
      combustibleGas: clamp(Math.round((prev.combustibleGas * 4 + nextPoint.combustibleGas) / 5 + randDelta(-1, 1)), 4, 40),
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

const monitorIsOnline = (monitor?: MonitorStreamItem): boolean => {
  if (!monitor) return false
  const status = monitor.status as unknown
  return status === 1 || status === 'online' || status === true || status === undefined
}

const monitorKey = (monitor?: MonitorStreamItem | null): string => (
  String(monitor?.id ?? monitor?.name ?? '')
)

const normalizeMonitorId = (value: unknown): string => {
  if (value === undefined || value === null || value === '') return ''
  return String(value)
}

const onlineCount = computed(() => monitors.value.filter(item => monitorIsOnline(item)).length)
const offlineCount = computed(() => Math.max(monitors.value.length - onlineCount.value, 0))
const pendingAlertCount = computed(() => (alarmStore.getAlarmList || []).filter((item: any) => isAlarmPending(item)).length)

const alarmMatchesMonitor = (item: any, monitorName: string, department = '', monitorId?: number | string): boolean => {
  const targetMonitorId = normalizeMonitorId(monitorId)
  const alarmMonitorId = normalizeMonitorId(item?.monitorId ?? item?.monitor_id ?? item?.monitorID)
  if (targetMonitorId && alarmMonitorId) return targetMonitorId === alarmMonitorId

  const name = normalizeName(monitorName)
  const dept = normalizeName(department)
  const alarmName = normalizeName(item?.cameraName || item?.monitorName || item?.monitor || item?.camera || item?.name || item?.eventName)
  const alarmDept = normalizeName(item?.department || item?.location || item?.area)

  if (alarmName && (name.includes(alarmName) || alarmName.includes(name))) return true
  if (dept && alarmDept && (dept.includes(alarmDept) || alarmDept.includes(dept))) return true
  if (alarmDept && name.includes(alarmDept.slice(0, 2))) return true
  return false
}

const getMonitorAlertList = (monitorName: string, department = '', monitorId?: number | string) => {
  const list = alarmStore.getAlarmList || []
  return list
    .filter((item: any) => alarmMatchesMonitor(item, monitorName, department, monitorId))
    .sort((a: any, b: any) => parseAlarmTimestamp(b) - parseAlarmTimestamp(a))
}

const tilePendingCount = (tile: MonitorStreamItem): number => (
  getMonitorAlertList(tile.name, tile.department, tile.id).filter((item: any) => isAlarmPending(item)).length
)

const monitorPriorityStats = (monitor: MonitorStreamItem) => {
  const pendingAlarms = getMonitorAlertList(monitor.name, monitor.department, monitor.id)
    .filter((item: any) => isAlarmPending(item))
  const latestAlarm = pendingAlarms[0]
  const maxLevel = pendingAlarms.reduce((max, item: any) => Math.max(max, Number(item?.level || item?.warningLevel || 0)), 0)
  return {
    pendingCount: pendingAlarms.length,
    latestTimestamp: latestAlarm ? parseAlarmTimestamp(latestAlarm) : 0,
    maxLevel,
  }
}

const sortMonitorsForPriority = (items: MonitorStreamItem[]): MonitorStreamItem[] => {
  const originalOrder = new Map(monitors.value.map((item, index) => [monitorKey(item), index]))
  const orderOf = (item: MonitorStreamItem) => originalOrder.get(monitorKey(item)) ?? Number.MAX_SAFE_INTEGER

  return [...items].sort((a, b) => {
    const aStats = monitorPriorityStats(a)
    const bStats = monitorPriorityStats(b)
    if (bStats.pendingCount !== aStats.pendingCount) return bStats.pendingCount - aStats.pendingCount
    if (bStats.latestTimestamp !== aStats.latestTimestamp) return bStats.latestTimestamp - aStats.latestTimestamp
    if (bStats.maxLevel !== aStats.maxLevel) return bStats.maxLevel - aStats.maxLevel
    const onlineDiff = Number(monitorIsOnline(b)) - Number(monitorIsOnline(a))
    if (onlineDiff !== 0) return onlineDiff
    return orderOf(a) - orderOf(b)
  })
}

const previewSignature = (tile: MonitorStreamItem): string => (
  [
    monitorKey(tile),
    tile.name,
    tile.department || '',
    String(tile.status ?? ''),
    tile.streamUrl || '',
  ].join('|')
)

const syncPriorityPreviewTiles = (): void => {
  const sourceList = monitors.value.length ? monitors.value : cameraTiles.value
  if (!sourceList.length) return

  const hasMonitorSource = monitors.value.length > 0
  const sourceByKey = new Map(sourceList.map(item => [monitorKey(item), item]))
  const currentPreview = cameraTiles.value
    .map(tile => sourceByKey.get(monitorKey(tile)) || (hasMonitorSource ? null : tile))
    .filter((tile): tile is MonitorStreamItem => Boolean(tile))
  const selectedMonitor =
    sourceList.find(item => item.name === selectedMonitorName.value) ||
    currentPreview.find(item => item.name === selectedMonitorName.value)
  const nextTiles: MonitorStreamItem[] = []
  const seenKeys = new Set<string>()
  const addTile = (tile?: MonitorStreamItem | null) => {
    if (!tile || nextTiles.length >= PREVIEW_TILE_LIMIT) return
    const key = monitorKey(tile)
    if (!key || seenKeys.has(key)) return
    seenKeys.add(key)
    nextTiles.push(tile)
  }
  const prioritizedSource = sortMonitorsForPriority(sourceList)
  const alertMonitors = prioritizedSource.filter(item => monitorPriorityStats(item).pendingCount > 0)

  alertMonitors.forEach(addTile)

  addTile(selectedMonitor)

  if (alertMonitors.length > 0) {
    currentPreview
      .filter(item => monitorPriorityStats(item).pendingCount === 0)
      .forEach(addTile)
  }

  prioritizedSource.forEach(addTile)

  const hasChanged =
    cameraTiles.value.length !== nextTiles.length ||
    cameraTiles.value.some((tile, index) => previewSignature(tile) !== previewSignature(nextTiles[index]))

  if (hasChanged) {
    cameraTiles.value = nextTiles
  }

  if (!selectedMonitorName.value && nextTiles[0]) {
    selectedMonitorName.value = nextTiles[0].name
  } else if (selectedMonitorName.value && !nextTiles.some(item => item.name === selectedMonitorName.value) && nextTiles[0]) {
    selectedMonitorName.value = nextTiles[0].name
  }
}

const tileIsOffline = (tile: MonitorStreamItem): boolean => (
  !monitorIsOnline(tile) || !tile.streamUrl
)

const tileStatus = (tile: MonitorStreamItem) => {
  if (tileIsOffline(tile)) return { label: '离线', tone: 'offline' }
  if (tilePendingCount(tile) > 0) return { label: '报警中', tone: 'alert' }
  return { label: '在线', tone: 'online' }
}

const inferMonitorAreaName = (name = ''): string => {
  const raw = String(name).trim()
  if (!raw) return ''
  const parts = raw.split(/\s*[-－—]\s*/).filter(Boolean)
  const source = parts.length > 1 ? parts[parts.length - 1] : raw
  const cleaned = source
    .replace(/^\d+号机位\s*/, '')
    .replace(/(?:实时)?(?:画面|视频|摄像头)$/g, '')
    .trim()

  if (!cleaned) return raw
  if (cleaned.length <= 4 && /(门|入口|车库|中庭|楼道|步道|电梯|停车)/.test(cleaned)) {
    return `${cleaned}监测点`
  }
  return cleaned
}

const tileDisplayName = (tile: MonitorStreamItem): string => (
  String(tile.department || '').trim() || inferMonitorAreaName(tile.name) || tile.name
)

const tileSubtitle = (tile: MonitorStreamItem): string => {
  const name = String(tile.name || '').trim()
  const displayName = tileDisplayName(tile)
  if (name && name !== displayName) return name
  return tile.streamUrl ? '视频流已接入' : '未配置视频流'
}

const normalizeName = (value: unknown): string => String(value || '').replace(/\s+/g, '').toLowerCase()

const selectedMonitorItem = computed(() => (
  monitors.value.find(item => item.name === selectedMonitorName.value) ||
  cameraTiles.value.find(item => item.name === selectedMonitorName.value) ||
  cameraTiles.value[0]
))

const selectedMonitorAlarms = computed(() => {
  const monitor = selectedMonitorItem.value
  if (!monitor) return []
  return getMonitorAlertList(monitor.name, monitor.department, monitor.id)
})

const selectedMonitorAlertStats = computed(() => {
  const alarms = selectedMonitorAlarms.value
  const pending = alarms.filter((item: any) => isAlarmPending(item)).length
  const last = alarms[0]
  return {
    total: alarms.length,
    pending,
    lastTime: last ? toTimeLabel(parseAlarmTimestamp(last)) : '无',
  }
})

const selectedMonitorOverview = computed(() => {
  const monitor = selectedMonitorItem.value
  const online = monitorIsOnline(monitor)
  return {
    name: monitor?.name || '暂无选中点位',
    department: monitor?.department || '未标注区域',
    online,
  }
})

const selectedMonitorRisk = computed(() => {
  const pending = selectedMonitorAlertStats.value.pending
  if (!selectedMonitorOverview.value.online) return { label: '离线风险', tone: 'offline', percent: 68 }
  if (pending > 1) return { label: '高风险', tone: 'danger', percent: 88 }
  if (pending === 1) return { label: '中风险', tone: 'alert', percent: 58 }
  return { label: '运行正常', tone: 'normal', percent: 22 }
})

const focusAlarmKey = (alarm: any): string => {
  if (!alarm) return ''
  const id = normalizeMonitorId(alarm?.id)
  if (id) return id
  return [
    alarm?.eventName || alarm?.name || 'alarm',
    alarm?.department || alarm?.location || '',
    alarm?.level || alarm?.warningLevel || '',
    parseAlarmTimestamp(alarm),
  ].join('|')
}

const focusPendingAlarms = computed(() => (
  selectedMonitorAlarms.value.filter((item: any) => isAlarmPending(item))
))

const focusActivePendingAlarm = computed(() => {
  if (!focusPendingAlarms.value.length) return null
  return (
    focusPendingAlarms.value.find((item: any) => focusAlarmKey(item) === focusSelectedAlarmKey.value) ||
    focusPendingAlarms.value[0]
  )
})

const focusActiveAlarmKey = computed(() => focusAlarmKey(focusActivePendingAlarm.value))
const focusVisibleAlarms = computed(() => focusPendingAlarms.value.slice(0, 5))
const focusHiddenAlarmCount = computed(() => Math.max(focusPendingAlarms.value.length - focusVisibleAlarms.value.length, 0))

const focusPanelState = computed(() => {
  const monitor = selectedMonitorItem.value
  if (!monitorIsOnline(monitor)) return { label: '离线', tone: 'offline' }
  if (focusActivePendingAlarm.value) return { label: '报警中', tone: 'alert' }
  return { label: '在线', tone: 'online' }
})

const focusPanelInfo = computed(() => {
  const monitor = selectedMonitorItem.value
  const alarm = focusActivePendingAlarm.value
  return {
    pointName: monitor ? tileDisplayName(monitor) : '暂无点位',
    statusLabel: focusPanelState.value.label,
    eventName: alarm?.eventName || alarm?.name || '暂无未处理事件',
    timeLabel: alarm ? toTimeLabel(parseAlarmTimestamp(alarm)) : '--',
    dealText: alarm ? '未处理' : '无',
  }
})

const mapAlarmCounts = computed(() => {
  const list = alarmStore.getAlarmList || []
  const monitorList = monitors.value || []
  const countsByCamera: Record<string, number> = {}
  const countsByArea: Record<string, number> = {}

  list.forEach((item: any) => {
    const pending = !(item?.status === 1 || item?.status === true || String(item?.deal || '').includes('已'))
    if (!pending) return

    const cameraName = String(item?.cameraName || item?.monitorName || item?.monitor || item?.camera || '').trim()
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

const ALARM_REFRESH_INTERVAL_MS = 60000
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
    combustibleGas: last?.combustibleGas ?? 0,
  }
})

const parkingZoneCards = computed(() => parkingZoneState.value.map((zone) => {
  const percent = Math.round((zone.used / Math.max(zone.capacity, 1)) * 100)
  return {
    ...zone,
    free: Math.max(zone.capacity - zone.used, 0),
    percent,
    tone: percent >= 85 ? 'danger' : percent >= 65 ? 'warn' : 'ok',
  }
}))

const envStatusCards = computed(() => {
  const values = envCurrentValues.value
  const rows = [
    { key: 'aqi', label: '空气质量', value: values.aqi, unit: 'AQI', limit: 100, color: '#63b8ff', good: values.aqi <= 80, warnLabel: '偏高' },
    { key: 'humidity', label: '湿度', value: values.humidity, unit: '%', limit: 100, color: '#53d5a5', good: values.humidity >= 40 && values.humidity <= 70, warnLabel: '需复核' },
    { key: 'pm25', label: 'PM2.5', value: values.pm25, unit: 'μg/m³', limit: 100, color: '#f8cb71', good: values.pm25 <= 55, warnLabel: '偏高' },
    { key: 'combustibleGas', label: '可燃气体', value: values.combustibleGas, unit: 'ppm', limit: 40, color: '#ff8d8d', good: values.combustibleGas <= 20, warnLabel: '需复核' },
  ]
  return rows.map(item => ({
    ...item,
    percent: clamp(Math.round((item.value / item.limit) * 100), 4, 100),
    status: item.good ? '正常' : item.warnLabel,
    tone: item.good ? 'ok' : 'warn',
  }))
})

const envWarningCount = computed(() => envStatusCards.value.filter(item => item.tone !== 'ok').length)
const parkingTenseZones = computed(() => parkingZoneCards.value.filter(item => item.percent >= 85).length)
const parkingTopZone = computed(() => [...parkingZoneCards.value].sort((a, b) => b.percent - a.percent)[0])
const parkingPressureTone = computed(() => {
  if (parkingOccupancy.value >= 85) return 'danger'
  if (parkingOccupancy.value >= 65) return 'warn'
  return 'ok'
})
const parkingPressureLabel = computed(() => {
  if (parkingOccupancy.value >= 85) return '车位紧张'
  if (parkingOccupancy.value >= 65) return '车位繁忙'
  return '车位充足'
})
const parkingPressureDesc = computed(() => {
  const zone = parkingTopZone.value
  if (!zone) return '暂无高压区域'
  return `${zone.name} · ${zone.percent}%占用`
})

const envPriorityState = computed(() => {
  if (envWarningCount.value > 0 && parkingOccupancy.value >= 85) {
    return {
      title: '环境与车位双重关注',
      desc: `${envWarningCount.value} 项环境指标异常，车位占用率 ${parkingOccupancy.value}%`,
      tone: 'danger',
    }
  }
  if (envWarningCount.value > 0) {
    return {
      title: '环境指标需复核',
      desc: `当前有 ${envWarningCount.value} 项环境指标异常，优先复核空气质量与设备点位。`,
      tone: 'warn',
    }
  }
  if (parkingOccupancy.value >= 85) {
    return {
      title: '车位压力偏高',
      desc: `当前占用率 ${parkingOccupancy.value}%，${parkingTopZone.value?.name || '高占用区域'} 需要加强引导。`,
      tone: 'warn',
    }
  }
  return {
    title: '当前运行平稳',
    desc: '环境指标正常，车位余量充足，可保持常规巡检。',
    tone: 'ok',
  }
})

const envOverviewKpis = computed(() => [
  { name: '舒适度', value: comfortScore.value, desc: comfortLabel.value, tone: comfortScore.value >= 80 ? 'ok' : comfortScore.value >= 60 ? 'warn' : 'danger' },
  { name: '异常指标', value: envWarningCount.value, desc: envWarningCount.value ? '需要关注' : '全部正常', tone: envWarningCount.value ? 'warn' : 'ok' },
  { name: '空闲车位', value: parkingFree.value, desc: `总车位 ${parkingTotal.value}`, tone: parkingFree.value < 20 ? 'danger' : 'ok' },
  { name: '占用率', value: `${parkingOccupancy.value}%`, desc: parkingOccupancy.value >= 85 ? '车位紧张' : '余量可用', tone: parkingOccupancy.value >= 85 ? 'danger' : parkingOccupancy.value >= 65 ? 'warn' : 'ok' },
])

const envParkingSummary = computed(() => {
  if (envWarningCount.value > 0 && parkingOccupancy.value >= 85) return `当前有 ${envWarningCount.value} 项环境指标需要关注，车位占用率 ${parkingOccupancy.value}%，建议同步安排巡检和停车引导。`
  if (envWarningCount.value > 0) return `当前有 ${envWarningCount.value} 项环境指标需要关注，优先复核空气质量与设备点位。`
  if (parkingOccupancy.value >= 85) return `环境整体平稳，但车位占用率已达 ${parkingOccupancy.value}%，${parkingTopZone.value?.name || '重点区域'} 需要加强引导。`
  return `环境指标整体稳定，车位占用率 ${parkingOccupancy.value}%，当前运行状态良好。`
})

const envParkingAdviceList = computed(() => {
  const list: string[] = []
  if (envWarningCount.value > 0) list.push('复核关注指标对应点位，确认是否存在短时波动或设备异常。')
  if (parkingOccupancy.value >= 85) list.push(`优先引导车辆前往空闲区域，缓解 ${parkingTopZone.value?.name || '高占用区域'} 压力。`)
  if (!list.length) list.push('保持常规巡检，重点观察晚高峰车位占用变化。')
  return list
})

// 预留给后续车流量检测接口：接入算法后替换这里的数据来源即可。
const trafficFlowReserve = computed(() => ({
  status: '未启用',
  today: '--',
  inCount: '--',
  outCount: '--',
  peak: '--',
}))

// ====== 车位仪表盘 ======
const parkingTotal = computed(() => parkingZoneState.value.reduce((sum, item) => sum + item.capacity, 0))
const parkingUsed = computed(() => parkingZoneState.value.reduce((sum, item) => sum + item.used, 0))
const parkingFree = computed(() => Math.max(parkingTotal.value - parkingUsed.value, 0))
const parkingOccupancy = computed(() => {
  if (!parkingTotal.value) return 0
  return Math.round((parkingUsed.value / parkingTotal.value) * 100)
})
// ====== 环境舒适度评分 ======
const comfortScore = computed(() => {
  const { aqi, humidity, pm25, combustibleGas } = envCurrentValues.value
  const aqiScore = Math.max(0, 100 - aqi)
  const humScore = humidity >= 40 && humidity <= 70 ? 100 : Math.max(0, 100 - Math.abs(humidity - 55) * 2)
  const pmScore = Math.max(0, 100 - pm25)
  const gasScore = Math.max(0, 100 - combustibleGas * 2.5)
  return Math.round(aqiScore * 0.3 + humScore * 0.25 + pmScore * 0.25 + gasScore * 0.2)
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

  const scoped = list.filter((item: any) => {
    const t = parseAlarmTimestamp(item)
    return t > 0 && t >= threshold && t <= now
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
    const t = parseAlarmTimestamp(item)
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
  const rows = alarmTableRows.value
    .filter(item => item.eventName !== '暂无报警' && !item.deal.includes('已'))
    .sort((a, b) => {
      const levelDiff = Number(b.level || 0) - Number(a.level || 0)
      if (levelDiff !== 0) return levelDiff
      return parseAlarmTimestamp(b) - parseAlarmTimestamp(a)
    })
    .slice(0, 4)
  if (!rows.length) {
    return [{
      key: 'empty',
      text: '当前无待处理报警，建议继续关注实时对话与巡检联动。',
      alarm: null,
    }]
  }
  return rows.map((item, idx) => ({
    key: alarmRowKey(item, idx),
    text: `${item.department} 存在 ${item.eventName} 报警，请尽快复核。`,
    alarm: item,
  }))
})

const goPendingTask = (task: { alarm: any | null }) => {
  if (!task.alarm) return
  alarmKeyword.value = ''
  alarmDealFilter.value = 'pending'
  selectedAlarmRow.value = task.alarm
  activeTab.value = 'alarm'
  stopAlarmAutoScroll()
  alarmAutoScrollPaused.value = true
  scrollSelectedAlarmIntoView()
}

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
        status: item.status ?? item.running,
        streamUrl: item.streamUrl || item.streamLink || item.video || rtmpAddressList[item.id],
      }))
      monitors.value = monitorList
      if (monitorList.length) {
        syncPriorityPreviewTiles()
        if (!monitorList.some(item => item.name === selectedMonitorName.value)) {
          selectedMonitorName.value = monitorList[0].name
        }
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

const selectPreviewTile = (camera: MonitorStreamItem) => {
  selectedMonitorName.value = camera.name
}

const isMonitorInPreview = (monitor: MonitorStreamItem) => (
  cameraTiles.value.some(tile => tile.name === monitor.name)
)

const findMonitorByName = (name?: string) => {
  if (!name) return null
  return (
    monitors.value.find(item => item.name === name) ||
    monitors.value.find(item => item.name.includes(name) || name.includes(item.name)) ||
    cameraTiles.value.find(item => item.name === name) ||
    cameraTiles.value.find(item => item.name.includes(name) || name.includes(item.name)) ||
    null
  )
}

const switchMonitorIntoPreview = (monitor: MonitorStreamItem, closeModal = false) => {
  activeTab.value = 'video'

  const existingIndex = cameraTiles.value.findIndex(tile => tile.name === monitor.name)
  if (existingIndex >= 0) {
    selectPreviewTile(cameraTiles.value[existingIndex])
    if (closeModal) closeMonitorModal()
    return
  }

  const nextTiles = [...cameraTiles.value]
  if (nextTiles.length < PREVIEW_TILE_LIMIT) {
    nextTiles.push(monitor)
  } else {
    const selectedIndex = nextTiles.findIndex(tile => tile.name === selectedMonitorName.value)
    const replaceIndex = selectedIndex >= 0 ? selectedIndex : 0
    nextTiles.splice(replaceIndex, 1, monitor)
  }

  cameraTiles.value = nextTiles.slice(0, PREVIEW_TILE_LIMIT)
  selectPreviewTile(monitor)
  if (closeModal) closeMonitorModal()
}

const processSelectedAlarm = () => {
  const alarm = activeAlarmRow.value
  if (!alarm || !selectedAlarmIsPending.value) return
  openProcessDialog(alarm)
}

const openSelectedAlarmVideo = () => {
  const alarm = activeAlarmRow.value
  if (!alarm) return
  openAlarmDetail(alarm)
}

const openFocus = (camera: MonitorStreamItem) => {
  selectPreviewTile(camera)
  focusSelectedAlarmKey.value = ''
  focusText.value = camera.name + '（大屏预览）'
  focusStreamUrl.value = camera.streamUrl || rtmpAddressList[0]
  focusVisible.value = true
  nextTick(() => {
    if (focusStreamUrl.value) {
      initFocusPlayer(focusStreamUrl.value)
    }
  })
}

const selectFocusAlarm = (alarm: any) => {
  focusSelectedAlarmKey.value = focusAlarmKey(alarm)
}

const viewFocusAlarm = () => {
  const alarm = focusActivePendingAlarm.value
  if (!alarm) return
  openAlarmDetail(alarm)
}

const processFocusAlarm = () => {
  const alarm = focusActivePendingAlarm.value
  if (!alarm) return
  openProcessDialog(alarm)
}

const handoffFocusToAgent = () => {
  const info = focusPanelInfo.value
  closeFocus()
  activeTab.value = 'agent'
  agentStatus.value = 'thinking'
  agentPreview.value = `已接收 ${info.pointName} 的${info.statusLabel}事件：${info.eventName}，时间 ${info.timeLabel}，处理状态 ${info.dealText}。`
}

const closeFocus = () => {
  focusVisible.value = false
  focusStreamUrl.value = ''
  destroyFocusPlayer()
}

const onMapPointClick = (point: MapPointItem) => {
  const target = findMonitorByName(point.camera)
  if (target) {
    switchMonitorIntoPreview(target)
    return
  }
  selectedMonitorName.value = point.camera
  activeTab.value = 'video'
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
    if (Array.isArray(list)) {
      syncRecentEvents(list)
      syncPriorityPreviewTiles()
      recentEventInitialized.value = true
    }
  },
  { deep: true },
)

onMounted(() => {
  fetchAlarmList()
  fetchAnalysisHeatMatrix()
  fetchMonitors()
  startAlarmSocket()
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
  stopAlarmSocket()
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

watch(analysisRange, () => {
  void fetchAnalysisHeatMatrix()
})

watch(envTrendRange, () => {
  if (ENV_PARKING_DATA_MODE === 'api') {
    void refreshEnvParkingData()
  }
})

watch(activeTab, (tab) => {
  if (tab === 'alarm' || tab === 'analysis') {
    void fetchAlarmList()
    if (tab === 'analysis') {
      void fetchAnalysisHeatMatrix()
    }
    window.dispatchEvent(new Event('resize'))
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
  overflow: hidden;
}

:deep(.grid > *) {
  min-width: 0;
  min-height: 0;
}

.page-shell {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-height: 0;
  height: 100%;
  overflow: hidden;
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
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
  font-size: 18px;
  font-weight: 600;
  color: #d9ecff;
  letter-spacing: 0.02em;
}

.video-current {
  flex: 1 1 auto;
  flex-wrap: nowrap;
  white-space: nowrap;
  overflow: hidden;
  font-size: 12px;
  font-weight: 500;
}

.nav-current-title {
  color: #eefaff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.nav-metric {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: rgba(217, 236, 255, 0.72);
  font-size: 12px;
}

.nav-metric b {
  color: #eefaff;
  font-size: 13px;
  font-weight: 700;
}

.nav-metric.ok b {
  color: #6ce2b2;
}

.nav-metric.warn b {
  color: #f8cb71;
}

.nav-metric.muted b {
  color: rgba(214, 230, 255, 0.68);
}

.nav-mini-action {
  flex: 0 0 auto;
  padding: 3px 9px;
}

.content-shell {
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.panel {
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.panel .card {
  background:
    radial-gradient(circle at 10% -10%, rgba(126, 197, 255, 0.08), transparent 38%),
    linear-gradient(180deg, rgba(17, 46, 75, 0.82), rgba(13, 33, 56, 0.82));
  box-shadow: inset 0 0 0 1px rgba(126, 197, 255, 0.08);
}

.alarm-panel {
  display: grid;
  grid-template-columns: minmax(360px, 0.42fr) minmax(0, 1fr);
  gap: 8px;
  min-height: 0;
}

.alarm-left,
.alarm-right,
.video-main,
.video-side,
.agent-main-card {
  min-height: 0;
  overflow: hidden;
}

.alarm-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alarm-right {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-height: 0;
}

.alarm-list-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.alarm-list-head h3 {
  margin: 0;
  color: #eef8ff;
  font-size: 15px;
  line-height: 1.3;
}

.alarm-list-head p {
  margin: 4px 0 0;
  color: rgba(214, 230, 255, 0.62);
  font-size: 11px;
}

.queue-count {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 999px;
  padding: 4px 9px;
  background: rgba(17, 47, 75, 0.58);
  color: #d9edff;
  font-size: 11px;
  white-space: nowrap;
}

.table-filters.alarm-table-filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(118px, 0.46fr);
  gap: 8px;
}

.table-filters.alarm-table-filters input {
  width: 100%;
}

.alarm-overview-card,
.selected-alarm-compact {
  min-height: 0;
  overflow: hidden;
}

.alarm-overview-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-color: rgba(126, 197, 255, 0.18);
  background:
    radial-gradient(circle at 8% 0, rgba(126, 232, 255, 0.12), transparent 34%),
    radial-gradient(circle at 100% 0, rgba(83, 213, 165, 0.08), transparent 30%),
    linear-gradient(180deg, rgba(15, 46, 78, 0.9), rgba(10, 30, 54, 0.86));
}

.alarm-overview-card.high {
  box-shadow:
    inset 0 0 0 1px rgba(255, 141, 141, 0.14),
    0 0 24px rgba(255, 78, 102, 0.08);
}

.alarm-overview-card.pending {
  box-shadow:
    inset 0 0 0 1px rgba(248, 203, 113, 0.12),
    0 0 20px rgba(248, 203, 113, 0.06);
}

.overview-head {
  align-items: flex-start;
  margin-bottom: 0;
}

.overview-head h3 {
  margin: 0;
  color: #eef8ff;
  font-size: 16px;
  line-height: 1.25;
}

.overview-head p {
  margin: 4px 0 0;
  color: rgba(214, 230, 255, 0.62);
  font-size: 11px;
  line-height: 1.4;
}

.alarm-situation-pill {
  flex: 0 0 auto;
  border: 1px solid rgba(126, 197, 255, 0.26);
  border-radius: 999px;
  background: rgba(17, 47, 75, 0.62);
  color: #d9edff;
  padding: 5px 10px;
  font-size: 11px;
  white-space: nowrap;
}

.alarm-overview-card.high .alarm-situation-pill {
  border-color: rgba(255, 141, 141, 0.46);
  background: rgba(90, 24, 38, 0.5);
  color: #ffb3bb;
}

.alarm-overview-card.pending .alarm-situation-pill {
  border-color: rgba(248, 203, 113, 0.44);
  background: rgba(86, 65, 24, 0.42);
  color: #ffe0a3;
}

.alarm-overview-layout {
  display: grid;
  grid-template-columns: minmax(220px, 0.82fr) minmax(0, 1.68fr);
  gap: 8px;
  min-height: 0;
}

.alarm-now-card {
  min-width: 0;
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 12px;
  background:
    radial-gradient(circle at 100% 0, rgba(126, 232, 255, 0.1), transparent 42%),
    rgba(8, 30, 54, 0.62);
  padding: 10px;
}

.alarm-now-card span {
  display: block;
  color: rgba(214, 230, 255, 0.6);
  font-size: 11px;
}

.alarm-now-card strong {
  display: block;
  margin-top: 5px;
  color: #eef8ff;
  font-size: 20px;
  line-height: 1.18;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-overview-card.high .alarm-now-card strong {
  color: #ff9aa3;
}

.alarm-overview-card.pending .alarm-now-card strong {
  color: #f8cb71;
}

.alarm-now-card p {
  margin: 7px 0 0;
  color: rgba(233, 246, 255, 0.72);
  font-size: 12px;
  line-height: 1.48;
}

.alarm-type-overview {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 12px;
  background: rgba(8, 30, 54, 0.46);
  padding: 8px;
  display: grid;
  grid-template-columns: 118px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  min-height: 0;
}

.alarm-type-title span {
  display: block;
  color: rgba(214, 230, 255, 0.62);
  font-size: 11px;
}

.alarm-type-title strong {
  display: block;
  margin-top: 4px;
  color: #eef8ff;
  font-size: 13px;
  line-height: 1.25;
}

.alarm-type-list {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 10px;
  min-width: 0;
}

.alarm-type-item {
  border: 0;
  background: transparent;
  padding: 0;
  display: grid;
  grid-template-columns: minmax(4.5rem, 0.78fr) minmax(0, 1fr) 1.7rem;
  gap: 7px;
  align-items: center;
  color: rgba(233, 246, 255, 0.78);
  font-size: 12px;
  min-width: 0;
  text-align: left;
}

.alarm-type-item span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-type-item.clickable {
  cursor: pointer;
}

.alarm-type-item.clickable span,
.alarm-type-item.clickable strong {
  color: #7ee8ff;
}

.alarm-type-item.clickable:hover span {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.alarm-type-item strong {
  color: #eef8ff;
  font-size: 12px;
  text-align: right;
}

.alarm-type-popover {
  position: absolute;
  right: 0;
  bottom: calc(100% + 8px);
  z-index: 5;
  width: min(260px, 100%);
  border: 1px solid rgba(126, 197, 255, 0.28);
  border-radius: 12px;
  background:
    radial-gradient(circle at 100% 0, rgba(126, 232, 255, 0.12), transparent 40%),
    rgba(6, 24, 43, 0.96);
  box-shadow: 0 18px 34px rgba(2, 12, 24, 0.42);
  padding: 9px;
}

.alarm-type-popover-head,
.alarm-type-popover-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.alarm-type-popover-head {
  padding-bottom: 7px;
  border-bottom: 1px solid rgba(126, 197, 255, 0.14);
  color: rgba(214, 230, 255, 0.66);
  font-size: 11px;
}

.alarm-type-popover-head strong {
  color: #eef8ff;
}

.alarm-type-popover-list {
  max-height: 11rem;
  overflow: auto;
  display: grid;
  gap: 5px;
  padding-top: 7px;
}

.alarm-type-popover-row {
  border-radius: 8px;
  background: rgba(17, 47, 75, 0.42);
  padding: 6px 8px;
  color: rgba(233, 246, 255, 0.8);
  font-size: 12px;
}

.alarm-type-popover-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-type-popover-row strong {
  flex: 0 0 auto;
  color: #7ee8ff;
}

.command-head {
  margin-bottom: 8px;
}

.selected-alarm-card {
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 12px;
  background:
    radial-gradient(circle at 100% 0, rgba(255, 141, 141, 0.09), transparent 36%),
    rgba(9, 32, 56, 0.58);
  padding: 10px;
  min-height: 0;
}

.selected-alarm-compact {
  display: flex;
  flex-direction: column;
}

.selected-alarm-compact.high {
  border-color: rgba(255, 141, 141, 0.42);
  box-shadow:
    inset 0 0 0 1px rgba(255, 141, 141, 0.12),
    0 0 24px rgba(255, 78, 102, 0.08);
}

.selected-alarm-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.alarm-eyebrow {
  grid-column: 1 / -1;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
}

.selected-alarm-main h4 {
  margin: 0;
  color: #eef8ff;
  font-size: 18px;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-alarm-grid {
  margin-top: 9px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 7px;
}

.selected-alarm-grid div {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 9px;
  background: rgba(17, 47, 75, 0.45);
  padding: 7px 8px;
  min-width: 0;
}

.selected-alarm-grid span {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 10px;
}

.selected-alarm-grid strong {
  display: block;
  margin-top: 3px;
  color: #eef8ff;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-alarm-note {
  margin: 8px 0 0;
  color: rgba(233, 246, 255, 0.72);
  font-size: 12px;
  line-height: 1.5;
}

.alarm-action-row {
  margin-top: 9px;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  gap: 7px;
}

.alarm-action-row .mini-action {
  justify-content: center;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  white-space: nowrap;
}

.mini-action.danger {
  border-color: rgba(255, 141, 141, 0.42);
  color: #ffb3bb;
  background: rgba(86, 26, 38, 0.48);
}

.mini-action.primary {
  border-color: rgba(126, 232, 255, 0.58);
  color: #ecfbff;
  background:
    radial-gradient(circle at 20% 0, rgba(126, 232, 255, 0.32), transparent 52%),
    linear-gradient(135deg, rgba(31, 135, 206, 0.76), rgba(20, 86, 152, 0.72));
  box-shadow: 0 8px 20px rgba(50, 154, 230, 0.18);
}

.mini-action[disabled] {
  opacity: 0.46;
  cursor: not-allowed;
}

.ai-advice-card {
  margin-top: 8px;
  width: 100%;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 10px;
  background: rgba(17, 47, 75, 0.38);
  color: #d9edff;
  padding: 7px 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ai-advice-card span {
  font-size: 12px;
  color: rgba(233, 246, 255, 0.78);
}

.ai-advice-card strong {
  flex: 0 0 auto;
  color: #7ee8ff;
  font-size: 11px;
}

.ai-advice-text {
  margin: 7px 0 0;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 10px;
  background: rgba(7, 24, 45, 0.5);
  color: rgba(233, 246, 255, 0.76);
  padding: 8px 9px;
  font-size: 12px;
  line-height: 1.55;
}

.alarm-kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) minmax(130px, 1.18fr);
  gap: 7px;
  min-height: 0;
}

.alarm-kpi {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 10px;
  background: rgba(17, 47, 75, 0.5);
  padding: 8px;
  min-width: 0;
}

.alarm-kpi span {
  display: block;
  color: rgba(214, 230, 255, 0.6);
  font-size: 10px;
}

.alarm-kpi strong {
  display: block;
  margin-top: 4px;
  color: #eef8ff;
  font-size: 17px;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-kpi.danger strong {
  color: #ff8d8d;
}

.alarm-kpi.warn strong {
  color: #f8cb71;
}

.alarm-kpi.ok strong {
  color: #6ce2b2;
}

.alarm-kpi.info strong {
  color: #7ee8ff;
}

.alarm-kpi.area strong {
  color: #eef8ff;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  white-space: normal;
  word-break: break-all;
  line-height: 1.18;
}

.alarm-bottom-row {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
  overflow: hidden;
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

.info-table tbody tr.high.pending {
  background: linear-gradient(90deg, rgba(255, 78, 102, 0.2), rgba(255, 141, 141, 0.08));
  box-shadow:
    inset 4px 0 0 rgba(255, 78, 102, 0.88),
    inset 0 0 0 1px rgba(255, 123, 136, 0.1);
}

.info-table tbody tr.mid.pending {
  background: linear-gradient(90deg, rgba(248, 203, 113, 0.16), rgba(248, 203, 113, 0.06));
  box-shadow: inset 4px 0 0 rgba(248, 203, 113, 0.76);
}

.info-table tbody tr.pending .state-chip.pending {
  font-weight: 700;
  box-shadow: 0 0 12px rgba(255, 78, 102, 0.18);
}

.info-table tbody tr.high.pending .level-chip.high {
  color: #ffd7dc;
  border-color: rgba(255, 123, 136, 0.74);
  background: rgba(255, 78, 102, 0.28);
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
  min-height: 0;
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

.analysis-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.42fr) minmax(320px, 0.78fr);
  grid-template-rows: minmax(82px, auto) minmax(268px, 1.05fr) minmax(188px, 0.74fr);
  gap: 10px;
  min-height: 0;
  overflow: hidden;
}

.analysis-hero-card {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(300px, 0.46fr) minmax(0, 1.54fr);
  gap: 10px;
  align-items: center;
  min-height: 0;
  padding: 10px 14px;
}

.analysis-headline {
  margin-bottom: 0;
  align-items: center;
}

.analysis-headline h3 {
  margin: 0;
  color: #eef8ff;
  font-size: 16px;
}

.analysis-headline p {
  margin: 4px 0 0;
  color: rgba(214, 230, 255, 0.62);
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.analysis-range-tabs {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 999px;
  background: rgba(8, 30, 54, 0.46);
  padding: 4px;
}

.analysis-range-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(214, 230, 255, 0.7);
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.analysis-range-btn.active {
  background: rgba(126, 197, 255, 0.18);
  color: #eef8ff;
}

.analysis-kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
}

.analysis-kpi {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 12px;
  background: rgba(17, 47, 75, 0.48);
  padding: 8px 10px;
  min-width: 0;
}

.analysis-kpi span,
.analysis-kpi em {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
}

.analysis-kpi strong {
  display: block;
  margin: 4px 0 3px;
  color: #eef8ff;
  font-size: 18px;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-kpi.danger strong,
.analysis-kpi.up strong {
  color: #ff8d8d;
}

.analysis-kpi.warn strong {
  color: #f8cb71;
}

.analysis-kpi.ok strong,
.analysis-kpi.down strong {
  color: #6ce2b2;
}

.analysis-kpi.info strong,
.analysis-kpi.flat strong,
.analysis-kpi.area strong {
  color: #7ee8ff;
}

.analysis-type-card,
.analysis-trend-card,
.analysis-cross-card,
.analysis-insight-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.analysis-type-card {
  grid-column: 1;
  grid-row: 2;
}

.analysis-trend-card {
  grid-column: 2;
  grid-row: 2;
}

.analysis-cross-card {
  grid-column: 1;
  grid-row: 3;
}

.analysis-insight-card {
  grid-column: 2;
  grid-row: 3;
}

.analysis-type-stage {
  position: relative;
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(150px, 0.44fr) minmax(0, 1fr);
  gap: 14px;
  align-items: center;
}

.analysis-donut-wrap {
  position: relative;
  width: min(210px, 100%);
  justify-self: center;
  display: grid;
  justify-items: center;
  gap: 9px;
  min-width: 0;
}

.analysis-donut-svg {
  width: min(190px, 100%);
  aspect-ratio: 1;
  overflow: visible;
  border-radius: 50%;
  box-shadow:
    0 0 28px rgba(126, 232, 255, 0.12),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  transform: rotate(-90deg);
}

.analysis-donut-track,
.analysis-donut-segment {
  fill: none;
  stroke-width: 15;
}

.analysis-donut-track {
  stroke: rgba(126, 197, 255, 0.1);
}

.analysis-donut-segment {
  cursor: pointer;
  transition:
    stroke-width 0.2s ease,
    opacity 0.2s ease,
    filter 0.2s ease;
}

.analysis-donut-segment:hover,
.analysis-donut-segment.active {
  stroke-width: 18;
  filter: drop-shadow(0 0 8px currentColor);
}

.analysis-donut-core {
  position: absolute;
  top: 95px;
  left: 50%;
  z-index: 1;
  width: 112px;
  height: 112px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 20%, rgba(126, 232, 255, 0.18), transparent 48%),
    rgba(8, 30, 54, 0.92);
  text-align: center;
  padding: 14px;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.analysis-donut-core strong,
.analysis-donut-core span {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-donut-core strong {
  color: #eef8ff;
  font-size: 18px;
}

.analysis-donut-core span {
  margin-top: 5px;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
}

.analysis-type-grid {
  min-height: 0;
  max-height: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-auto-rows: minmax(72px, auto);
  align-content: start;
  gap: 8px;
  overflow-y: auto;
  padding-right: 6px;
}

.analysis-type-grid::-webkit-scrollbar {
  width: 6px;
}

.analysis-type-grid::-webkit-scrollbar-track {
  background: rgba(126, 197, 255, 0.07);
  border-radius: 999px;
}

.analysis-type-grid::-webkit-scrollbar-thumb {
  background: rgba(126, 197, 255, 0.4);
  border-radius: 999px;
}

.analysis-type-cardlet {
  position: relative;
  min-width: 0;
  border: 1px solid rgba(126, 197, 255, 0.13);
  border-left: 3px solid var(--type-color);
  border-radius: 13px;
  background:
    linear-gradient(135deg, rgba(126, 232, 255, 0.08), transparent 62%),
    rgba(17, 47, 75, 0.36);
  padding: 9px 10px;
  cursor: pointer;
}

.analysis-type-cardlet.active,
.analysis-type-cardlet:hover {
  border-color: rgba(126, 232, 255, 0.34);
  box-shadow:
    inset 0 0 0 1px rgba(126, 232, 255, 0.08),
    0 0 14px rgba(126, 232, 255, 0.08);
}

.analysis-type-cardlet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.analysis-type-cardlet-head span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(233, 246, 255, 0.88);
  font-size: 13px;
  font-weight: 700;
}

.analysis-type-cardlet-head strong {
  flex: 0 0 auto;
  color: var(--type-color);
  font-size: 18px;
}

.analysis-type-cardlet-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 7px;
}

.analysis-type-cardlet-meta em {
  border-radius: 999px;
  background: rgba(8, 30, 54, 0.45);
  color: rgba(214, 230, 255, 0.62);
  font-size: 10px;
  font-style: normal;
  padding: 2px 6px;
}

.analysis-sparkline-card {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 10px;
}

.analysis-sparkline {
  width: 100%;
  height: 100%;
  min-height: 132px;
  border: 1px solid rgba(126, 197, 255, 0.13);
  border-radius: 14px;
  background:
    linear-gradient(rgba(126, 197, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(126, 197, 255, 0.08) 1px, transparent 1px),
    radial-gradient(circle at 20% 10%, rgba(126, 232, 255, 0.12), transparent 30%),
    rgba(8, 30, 54, 0.34);
  background-size: 100% 12px, 20px 100%, auto, auto;
  padding: 8px;
}

.analysis-spark-area {
  fill: rgba(126, 232, 255, 0.14);
}

.analysis-spark-line {
  fill: none;
  stroke: #7ee8ff;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 0 5px rgba(126, 232, 255, 0.35));
}

.analysis-spark-dot {
  fill: #d8fbff;
  stroke: rgba(8, 30, 54, 0.9);
  stroke-width: 0.6;
}

.analysis-trend-snapshot {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.analysis-trend-snapshot div {
  min-width: 0;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 12px;
  background: rgba(17, 47, 75, 0.36);
  padding: 8px 10px;
}

.analysis-trend-snapshot span,
.analysis-trend-snapshot em {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
}

.analysis-trend-snapshot strong {
  display: block;
  margin: 3px 0 1px;
  color: #eef8ff;
  font-size: 18px;
}

.analysis-trend-snapshot strong.up {
  color: #ff8d8d;
}

.analysis-trend-snapshot strong.down {
  color: #6ce2b2;
}

.analysis-trend-snapshot strong.flat {
  color: #7ee8ff;
}

.analysis-cross-table {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: auto;
  gap: 6px;
  overflow: auto;
  padding-right: 2px;
}

.analysis-cross-head,
.analysis-cross-row {
  display: grid;
  grid-template-columns: minmax(7.5rem, 1fr) repeat(4, minmax(4rem, 0.72fr));
  gap: 6px;
  align-items: center;
}

.analysis-cross-head {
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
}

.analysis-cross-row {
  border: 1px solid rgba(126, 197, 255, 0.13);
  border-radius: 11px;
  background: rgba(17, 47, 75, 0.34);
  padding: 7px 8px;
}

.analysis-cross-head span,
.analysis-cross-row span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-cross-row span {
  color: rgba(233, 246, 255, 0.82);
  font-size: 12px;
  font-weight: 700;
}

.analysis-cross-head strong,
.analysis-cross-row strong {
  min-width: 0;
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-cross-head strong {
  font-size: 11px;
  font-weight: 500;
}

.analysis-cross-row strong {
  border: 1px solid rgba(126, 197, 255, 0.1);
  border-radius: 9px;
  color: rgba(214, 230, 255, 0.58);
  font-size: 12px;
  padding: 5px 6px;
}

.analysis-cross-row strong.hot {
  color: #eef8ff;
  font-weight: 800;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.analysis-insight-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
  overflow: hidden;
}

.analysis-time-orbit {
  position: relative;
  width: 88px;
  aspect-ratio: 1;
  justify-self: center;
  border-radius: 50%;
  box-shadow: 0 0 26px rgba(126, 232, 255, 0.11);
}

.analysis-time-orbit::after {
  content: '';
  position: absolute;
  inset: 8px;
  border-radius: inherit;
  background: rgba(6, 23, 40, 0.84);
}

.analysis-time-orbit div {
  position: absolute;
  inset: 18px;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(17, 47, 75, 0.9);
  text-align: center;
}

.analysis-time-orbit strong {
  color: #eef8ff;
  font-size: 14px;
}

.analysis-time-orbit span {
  margin-top: 2px;
  color: rgba(214, 230, 255, 0.58);
  font-size: 10px;
}

.analysis-insight-copy {
  min-width: 0;
  min-height: 0;
  display: grid;
  align-content: start;
  gap: 6px;
  overflow: hidden;
}

.analysis-time-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.analysis-time-pills span {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 999px;
  background: rgba(17, 47, 75, 0.38);
  color: rgba(214, 230, 255, 0.66);
  font-size: 10px;
  padding: 2px 7px;
}

.analysis-time-pills span.active {
  border-color: rgba(248, 203, 113, 0.45);
  background: rgba(86, 65, 24, 0.28);
  color: #f8cb71;
}

.analysis-repeat-list {
  display: grid;
  gap: 6px;
  min-height: 0;
}

.analysis-repeat-list.compact {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  overflow: hidden;
}

.analysis-repeat-item {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 11px;
  background: rgba(17, 47, 75, 0.34);
  padding: 7px 9px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.analysis-repeat-list.compact .analysis-repeat-item {
  display: inline-flex;
  max-width: 100%;
  border-radius: 999px;
  padding: 5px 8px;
}

.analysis-repeat-list.compact .analysis-repeat-item div {
  min-width: 0;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.analysis-repeat-item span,
.analysis-repeat-item em {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-repeat-item span {
  color: rgba(233, 246, 255, 0.84);
  font-size: 12px;
  font-weight: 700;
}

.analysis-repeat-item em {
  color: rgba(214, 230, 255, 0.56);
  font-size: 11px;
  font-style: normal;
}

.analysis-repeat-item strong {
  color: #ffb3bb;
  font-size: 12px;
  white-space: nowrap;
}

.analysis-empty-state {
  flex: 1;
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(126, 197, 255, 0.16);
  border-radius: 12px;
  color: rgba(214, 230, 255, 0.56);
  font-size: 12px;
}

.analysis-sub-label {
  color: rgba(214, 230, 255, 0.62);
  font-size: 11px;
}

.analysis-mini-summary {
  margin: 0;
  border: 1px solid rgba(126, 197, 255, 0.13);
  border-radius: 10px;
  background: rgba(8, 30, 54, 0.36);
  color: rgba(233, 246, 255, 0.78);
  display: -webkit-box;
  font-size: 12px;
  line-height: 1.55;
  overflow: hidden;
  padding: 7px 9px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.video-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.62fr) minmax(360px, 0.98fr);
  grid-template-rows: minmax(0, 1fr);
  gap: 10px;
  min-height: 0;
}

.video-main {
  display: flex;
  flex-direction: column;
}

.video-headline {
  align-items: center;
  flex-wrap: nowrap;
  min-height: 28px;
  margin-bottom: 6px;
}

.video-title-row {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1 1 auto;
  white-space: nowrap;
}

.video-title-row h3 {
  flex: 0 0 auto;
  margin: 0;
  line-height: 1;
}

.video-subtitle {
  position: relative;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1;
}

.video-subtitle::before {
  content: '';
  display: inline-block;
  width: 1px;
  height: 12px;
  margin-right: 12px;
  vertical-align: -2px;
  background: rgba(168, 198, 232, 0.34);
}

.inline-status {
  flex: 0 0 auto;
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 999px;
  background: rgba(17, 47, 75, 0.58);
  padding: 4px 10px;
  color: #d9edff !important;
  line-height: 1.15;
}

.monitor-grid-large {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-auto-rows: minmax(0, 1fr);
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
  min-height: 0;
  height: 100%;
  border-radius: 8px;
  border: 1px dashed rgba(107, 176, 255, 0.55);
  background: rgba(7, 21, 38, 0.8);
  transition:
    border-color 0.24s ease,
    box-shadow 0.24s ease,
    filter 0.24s ease;
}

.tile-flow-move,
.tile-flow-enter-active,
.tile-flow-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.tile-flow-enter-from,
.tile-flow-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.985);
}

.tile-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition:
    filter 0.28s ease,
    opacity 0.28s ease;
}

.tile-overlay {
  position: absolute;
  inset: auto 0 0;
  z-index: 2;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
  background: linear-gradient(180deg, rgba(3, 10, 18, 0), rgba(3, 10, 18, 0.72));
  padding: 22px 12px 10px;
}

.tile-copy {
  min-width: 0;
}

.tile-title {
  font-weight: 600;
  text-align: left;
  color: #eaf6ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile-focus-btn {
  flex: 0 0 auto;
  border: 1px solid rgba(126, 197, 255, 0.32);
  border-radius: 999px;
  background: rgba(17, 47, 75, 0.68);
  color: #d9edff;
  padding: 4px 9px;
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease;
}

.tile-focus-btn:hover {
  border-color: rgba(126, 232, 255, 0.72);
  background: rgba(31, 77, 116, 0.84);
  transform: translateY(-1px);
}

.tile-sub {
  margin-top: 4px;
  color: var(--sub);
  font-size: 12px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-side {
  display: grid;
  grid-template-rows: minmax(0, 1fr) minmax(180px, 0.4fr);
  gap: 10px;
  min-height: 0;
  overflow: hidden;
}

.video-map-card,
.ai-alarm-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.map-headline {
  align-items: center;
}

.map-legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--sub);
  font-size: 11px;
}

.map-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.normal {
  background: #63b8ff;
  box-shadow: 0 0 8px rgba(99, 184, 255, 0.58);
}

.legend-dot.alert {
  background: #ff8d8d;
  box-shadow: 0 0 8px rgba(255, 141, 141, 0.58);
}

.map-square {
  border: 1px dashed rgba(107, 176, 255, 0.55);
  border-radius: 12px;
  padding: 0;
  background: linear-gradient(145deg, rgba(30, 67, 105, 0.86), rgba(22, 51, 83, 0.92));
  min-height: 0;
  flex: 1;
  overflow: hidden;
}

.mini-kpi {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 10px;
  background: rgba(17, 47, 75, 0.56);
  padding: 7px 8px 7px 14px;
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

.map-insight-strip {
  display: block;
  margin-top: 8px;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-radius: 10px;
  background:
    linear-gradient(90deg, rgba(10, 36, 61, 0.76), rgba(17, 47, 75, 0.42)),
    rgba(10, 30, 52, 0.58);
  padding: 7px 10px;
  flex: 0 0 auto;
}

.map-insight-main {
  min-width: 0;
}

.risk-pill {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 999px;
  padding: 3px 9px;
  background: rgba(17, 47, 75, 0.58);
  font-size: 11px !important;
}

.risk-pill.normal {
  color: #6ce2b2 !important;
  border-color: rgba(108, 226, 178, 0.34);
}

.risk-pill.alert {
  color: #f8cb71 !important;
  border-color: rgba(248, 203, 113, 0.45);
}

.risk-pill.danger,
.risk-pill.offline {
  color: #ff8d8d !important;
  border-color: rgba(255, 141, 141, 0.5);
}

.monitor-insight-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.monitor-insight-title strong {
  color: #eaf6ff;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.monitor-insight-title span,
.monitor-health-row {
  color: rgba(214, 230, 255, 0.68);
  font-size: 11px;
}

.monitor-health-row {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta-separator {
  color: rgba(214, 230, 255, 0.36);
}

.insight-pending-text.bad {
  color: #ff8d8d;
}

.insight-pending-text.ok {
  color: #6ce2b2;
}

.env-panel {
  display: grid;
  grid-template-columns: minmax(0, 0.55fr) minmax(0, 0.45fr);
  grid-template-rows: auto minmax(124px, 0.3fr) minmax(0, 1fr);
  grid-template-areas:
    "overview overview"
    "status trend"
    "parking trend";
  gap: 12px;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.env-overview-card {
  grid-area: overview;
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: minmax(0, 0.72fr) minmax(0, 1.28fr);
  gap: 12px;
  align-items: stretch;
  min-height: 0;
}

.env-overview-head {
  margin-bottom: 0;
  align-items: center;
}

.env-overview-head h3 {
  margin: 0;
  color: #eef8ff;
  font-size: 17px;
}

.env-overview-head p {
  margin: 5px 0 0;
  color: rgba(214, 230, 255, 0.62);
  font-size: 12px;
}

.env-overview-body {
  display: grid;
  grid-template-columns: minmax(220px, 0.68fr) minmax(0, 1.32fr);
  gap: 10px;
  min-height: 0;
}

.env-priority-card {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(17, 47, 75, 0.52), rgba(10, 30, 52, 0.66));
  padding: 12px 14px;
  min-height: 0;
}

.env-priority-card span,
.env-priority-card p {
  display: block;
}

.env-priority-card span {
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
}

.env-priority-card strong {
  display: block;
  margin-top: 6px;
  color: #eef8ff;
  font-size: 18px;
}

.env-priority-card p {
  margin: 8px 0 0;
  color: rgba(233, 246, 255, 0.78);
  font-size: 12px;
  line-height: 1.55;
}

.env-priority-card.ok strong {
  color: #6ce2b2;
}

.env-priority-card.warn strong {
  color: #f8cb71;
}

.env-priority-card.danger strong {
  color: #ff8d8d;
}

.env-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.env-kpi {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 12px;
  background: rgba(17, 47, 75, 0.48);
  padding: 10px;
  min-width: 0;
}

.env-kpi span,
.env-kpi em {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
}

.env-kpi strong {
  display: block;
  margin: 5px 0 4px;
  color: #eef8ff;
  font-size: 19px;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-kpi.ok strong {
  color: #6ce2b2;
}

.env-kpi.warn strong {
  color: #f8cb71;
}

.env-kpi.danger strong {
  color: #ff8d8d;
}

.env-status-card,
.env-trend-card,
.env-parking-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.env-status-card {
  grid-area: status;
  min-height: 0;
  overflow: visible;
}

.env-trend-card {
  grid-area: trend;
  min-height: 0;
}

.env-parking-card {
  grid-area: parking;
  min-height: 0;
}

.env-status-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 7px;
  align-items: stretch;
}

.env-status-item {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 10px;
  background: rgba(17, 47, 75, 0.42);
  padding: 7px 8px;
  min-width: 0;
  min-height: 64px;
  display: grid;
  grid-template-rows: auto auto auto;
  gap: 5px;
}

.env-status-item.warn {
  border-color: rgba(248, 203, 113, 0.3);
  background: rgba(80, 58, 24, 0.28);
}

.env-status-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.env-status-top span {
  min-width: 0;
  color: rgba(214, 230, 255, 0.66);
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-status-top em {
  flex: 0 0 auto;
  color: #6ce2b2;
  font-size: 10px;
  font-style: normal;
}

.env-status-item.warn .env-status-top em {
  color: #f8cb71;
}

.env-status-item strong {
  display: block;
  margin: 0;
  color: #eef8ff;
  font-size: 17px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.env-status-item small {
  margin-left: 4px;
  color: rgba(214, 230, 255, 0.5);
  font-size: 11px;
  font-weight: 500;
}

.env-status-bar {
  height: 3px;
  border-radius: 999px;
  background: rgba(126, 197, 255, 0.1);
  overflow: hidden;
}

.env-status-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.env-trend-head {
  margin-bottom: 7px;
}

.env-trend-head > div {
  min-width: 0;
}

.env-trend-head h3 {
  margin: 0;
  color: #eef8ff;
  font-size: 16px;
}

.env-trend-head span {
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
}

.env-trend-switch {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 999px;
  background: rgba(8, 30, 54, 0.46);
  padding: 4px;
  flex-wrap: wrap;
}

.env-trend-switch-btn {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(214, 230, 255, 0.7);
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}

.env-trend-switch-btn.active {
  background: rgba(126, 197, 255, 0.18);
  color: #eef8ff;
}

.env-inline-insight {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 12px;
  background: rgba(17, 47, 75, 0.34);
  padding: 7px 10px;
  margin-bottom: 8px;
  min-width: 0;
}

.env-inline-insight span {
  color: rgba(214, 230, 255, 0.6);
  font-size: 11px;
  white-space: nowrap;
}

.env-inline-insight strong {
  color: #6ce2b2;
  font-size: 14px;
  white-space: nowrap;
}

.env-inline-insight.warn strong {
  color: #f8cb71;
}

.env-inline-insight.danger strong {
  color: #ff8d8d;
}

.env-inline-insight p {
  margin: 0;
  min-width: 0;
  color: rgba(233, 246, 255, 0.74);
  font-size: 12px;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-trend-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 10px;
  overflow: hidden;
}

.env-trend-svg.single {
  width: 100%;
  height: 100%;
  min-height: 0;
  max-height: 100%;
}

.env-trend-footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.env-trend-mini {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 12px;
  background: rgba(17, 47, 75, 0.34);
  padding: 8px 10px;
  min-width: 0;
}

.env-trend-mini span,
.env-trend-mini em {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
}

.env-trend-mini strong {
  display: block;
  margin: 3px 0 1px;
  color: #eef8ff;
  font-size: 18px;
}

.env-trend-mini strong.up {
  color: #ff8d8d;
}

.env-trend-mini strong.down {
  color: #6ce2b2;
}

.env-trend-mini strong.flat {
  color: #7ee8ff;
}

.parking-head-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  min-width: 0;
}

.traffic-flow-inline {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  border: 1px dashed rgba(126, 232, 255, 0.3);
  border-radius: 999px;
  background: rgba(126, 232, 255, 0.08);
  padding: 4px 9px;
}

.traffic-flow-inline span {
  color: rgba(214, 230, 255, 0.78);
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}

.traffic-flow-inline em {
  color: #7ee8ff;
  font-size: 10px;
  font-style: normal;
  white-space: nowrap;
}

.traffic-flow-inline strong {
  color: rgba(233, 246, 255, 0.82);
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}

.parking-pressure-card {
  display: grid;
  grid-template-columns: minmax(150px, 0.28fr) minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
  min-height: 0;
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 14px;
  background:
    radial-gradient(circle at 8% 40%, rgba(126, 232, 255, 0.11), transparent 32%),
    rgba(17, 47, 75, 0.3);
  padding: 9px 12px;
}

.parking-pressure-main,
.parking-pressure-track,
.parking-pressure-stats {
  min-width: 0;
}

.parking-pressure-main {
  display: grid;
  grid-template-columns: auto auto;
  align-items: baseline;
  column-gap: 7px;
  row-gap: 2px;
}

.parking-pressure-main span {
  color: rgba(214, 230, 255, 0.66);
  font-size: 12px;
  white-space: nowrap;
}

.parking-pressure-main strong {
  color: #eef8ff;
  font-size: 34px;
  line-height: 0.9;
  font-variant-numeric: tabular-nums;
}

.parking-pressure-main small {
  margin-left: 2px;
  font-size: 17px;
}

.parking-pressure-main em {
  grid-column: 1 / -1;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.parking-pressure-card.ok .parking-pressure-main strong {
  color: #6ce2b2;
}

.parking-pressure-card.warn .parking-pressure-main strong {
  color: #f8cb71;
}

.parking-pressure-card.danger .parking-pressure-main strong {
  color: #ff8d8d;
}

.parking-pressure-track {
  display: grid;
  gap: 6px;
}

.parking-pressure-meter {
  position: relative;
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(83, 213, 165, 0.78), rgba(248, 203, 113, 0.82) 62%, rgba(255, 141, 141, 0.88));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.parking-pressure-meter::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: rgba(8, 25, 43, 0.48);
  clip-path: inset(0 0 0 var(--parking-percent));
}

.parking-pressure-meter i {
  position: absolute;
  left: var(--parking-percent);
  top: 50%;
  z-index: 1;
  width: 14px;
  height: 14px;
  border: 2px solid #eef8ff;
  border-radius: 50%;
  background: rgba(8, 25, 43, 0.92);
  box-shadow: 0 0 12px rgba(126, 232, 255, 0.32);
  transform: translate(-50%, -50%);
}

.parking-pressure-meter b {
  position: absolute;
  left: 65%;
  top: -4px;
  bottom: -4px;
  width: 1px;
  background: rgba(255, 255, 255, 0.18);
}

.parking-pressure-scale {
  display: flex;
  justify-content: space-between;
  color: rgba(214, 230, 255, 0.5);
  font-size: 10px;
}

.parking-pressure-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(64px, auto));
  gap: 8px;
}

.parking-pressure-stats div {
  border-left: 1px solid rgba(126, 197, 255, 0.14);
  padding-left: 10px;
}

.parking-pressure-stats span,
.parking-pressure-stats em {
  display: block;
  color: rgba(214, 230, 255, 0.58);
  font-size: 11px;
  font-style: normal;
  white-space: nowrap;
}

.parking-pressure-stats strong {
  display: block;
  margin-top: 3px;
  color: #eef8ff;
  font-size: 20px;
  line-height: 1;
  white-space: nowrap;
}

.parking-pressure-stats .hot strong {
  max-width: 92px;
  color: #f8cb71;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.parking-zone-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 2px;
}

.parking-zone-list.compact {
  flex: 1;
  gap: 6px;
}

.parking-zone-list::-webkit-scrollbar {
  width: 5px;
}

.parking-zone-list::-webkit-scrollbar-track {
  background: rgba(126, 197, 255, 0.06);
  border-radius: 999px;
}

.parking-zone-list::-webkit-scrollbar-thumb {
  background: rgba(126, 197, 255, 0.34);
  border-radius: 999px;
}

.parking-zone-row {
  border: 1px solid rgba(126, 197, 255, 0.14);
  border-radius: 10px;
  background: rgba(17, 47, 75, 0.34);
  padding: 7px 10px;
  min-height: 46px;
  display: grid;
  grid-template-columns: minmax(92px, 0.22fr) minmax(0, 1fr) minmax(44px, auto);
  align-items: center;
  gap: 10px;
}

.parking-zone-name {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.parking-zone-name span {
  min-width: 0;
  color: #d9edff;
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.parking-zone-name em {
  color: rgba(214, 230, 255, 0.52);
  font-size: 10px;
  font-style: normal;
  white-space: nowrap;
}

.parking-zone-bar {
  height: 7px;
  border-radius: 999px;
  background: rgba(126, 197, 255, 0.1);
  overflow: hidden;
}

.parking-zone-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.parking-zone-count {
  display: grid;
  justify-items: end;
  gap: 2px;
  min-width: 0;
}

.parking-zone-count strong {
  color: #d9edff;
  font-size: 14px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.parking-zone-count em {
  color: rgba(214, 230, 255, 0.52);
  font-size: 10px;
  font-style: normal;
  white-space: nowrap;
}

.parking-zone-row.ok .parking-zone-bar i {
  background: linear-gradient(90deg, rgba(83, 213, 165, 0.88), rgba(126, 232, 255, 0.62));
}

.parking-zone-row.warn .parking-zone-bar i {
  background: linear-gradient(90deg, rgba(248, 203, 113, 0.9), rgba(255, 190, 102, 0.68));
}

.parking-zone-row.danger .parking-zone-bar i {
  background: linear-gradient(90deg, rgba(255, 141, 141, 0.92), rgba(255, 78, 102, 0.68));
}

/* ====== 1. 视频卡片状态边框 ====== */
@keyframes tile-alert-pulse {
  0%, 100% { border-color: rgba(255, 120, 120, 0.5); box-shadow: 0 0 0 0 rgba(255, 100, 100, 0); }
  50% { border-color: rgba(255, 100, 100, 0.85); box-shadow: 0 0 18px 0 rgba(255, 80, 80, 0.25); }
}

.tile-online {
  animation: none;
  border-style: solid;
  border-color: rgba(108, 226, 178, 0.48);
  box-shadow: inset 0 0 0 1px rgba(108, 226, 178, 0.08);
}

.tile-alert {
  animation: tile-alert-pulse 1.8s ease-in-out infinite;
}

.tile-offline {
  animation: none;
  border-color: rgba(168, 198, 232, 0.18);
  background: rgba(6, 14, 24, 0.92);
}

.tile-offline .tile-video {
  filter: grayscale(1) brightness(0.38);
  opacity: 0.48;
}

.tile-offline .tile-overlay {
  background: linear-gradient(180deg, rgba(3, 10, 18, 0), rgba(3, 10, 18, 0.88));
}

.tile-selected {
  border-color: rgba(126, 232, 255, 0.92);
  box-shadow:
    inset 0 0 0 1px rgba(126, 232, 255, 0.22),
    0 0 24px rgba(126, 232, 255, 0.18);
}

.tile-offline.tile-selected {
  border-color: rgba(168, 198, 232, 0.24);
  box-shadow:
    inset 0 0 0 1px rgba(168, 198, 232, 0.08),
    0 0 18px rgba(18, 32, 48, 0.32);
}

.tile-offline-state {
  position: absolute;
  inset: 0;
  z-index: 1;
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

.tile-offline-state span {
  font-size: 12px;
  letter-spacing: 1px;
}

.tile-status-badge,
.tile-pending-badge {
  position: absolute;
  top: 10px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(126, 197, 255, 0.26);
  border-radius: 999px;
  background: rgba(5, 18, 32, 0.66);
  color: #d9edff;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.tile-status-badge {
  left: 10px;
  max-width: calc(100% - 110px);
}

.tile-pending-badge {
  right: 10px;
  color: #ff9fa9;
  border-color: rgba(255, 141, 141, 0.52);
  background: rgba(86, 26, 38, 0.72);
}

.tile-status-badge i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 10px currentColor;
  flex: 0 0 auto;
}

.tile-status-badge span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile-status-badge.online {
  color: #6ce2b2;
  border-color: rgba(108, 226, 178, 0.3);
}

.tile-status-badge.alert {
  color: #ff8d8d;
  border-color: rgba(255, 141, 141, 0.62);
  animation: event-breathe 1.4s ease-in-out infinite;
}

.tile-status-badge.offline {
  color: rgba(214, 230, 255, 0.62);
  border-color: rgba(168, 198, 232, 0.26);
  background: rgba(16, 27, 40, 0.76);
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
.kpi-alert::before { background: #f8cb71; }

/* ====== 4. AI 事件流 ====== */
.event-stream {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 12px;
  background: rgba(10, 30, 52, 0.6);
  padding: 8px 10px;
  min-height: 0;
  height: 100%;
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
  position: relative;
  min-height: 0;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-right: 2px;
}

.event-stream-list::before {
  content: '';
  position: absolute;
  left: 49px;
  top: 4px;
  bottom: 4px;
  width: 1px;
  background: linear-gradient(180deg, rgba(126, 197, 255, 0.08), rgba(126, 197, 255, 0.38), rgba(126, 197, 255, 0.08));
  pointer-events: none;
}

.event-stream-empty-list::before {
  display: none;
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
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 36px 12px minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 8px;
  background: rgba(17, 47, 75, 0.5);
  font-size: 11px;
  transition: background 0.2s;
}

.event-flow-move,
.event-flow-enter-active,
.event-flow-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease,
    max-height 0.28s ease,
    padding 0.28s ease,
    border-color 0.28s ease;
}

.event-flow-enter-active,
.event-flow-leave-active {
  overflow: hidden;
  max-height: 46px;
}

.event-flow-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.985);
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border-color: transparent;
}

.event-flow-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.985);
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border-color: transparent;
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
  justify-self: center;
  outline: 3px solid rgba(10, 30, 52, 0.86);
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
  grid-template-columns: 1fr;
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

.agent-panel {
  display: grid;
  grid-template-columns: minmax(0, 2.1fr) minmax(20rem, 0.78fr);
  gap: 8px;
  align-items: stretch;
  min-height: 0;
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
  grid-template-rows: minmax(0, 1fr);
  min-height: 0;
}

.side-col {
  display: grid;
  grid-template-rows: minmax(0, 0.34fr) minmax(0, 1fr);
  gap: 0.85rem;
}

.agent-main-card {
  display: flex;
  flex-direction: column;
}

.hero-card {
  display: flex;
  flex-direction: column;
  gap: 0.95rem;
  padding: 1rem;
  min-height: 0;
  overflow: hidden;
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
  min-height: 0;
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
  width: 100%;
  text-align: left;
  color: #eef8ff;
  border-left: 3px solid var(--warn);
  border-top: 0;
  border-right: 0;
  border-bottom: 0;
  border-radius: 8px;
  background: rgba(248, 203, 113, 0.12);
  padding: 8px 9px;
  font-size: 12px;
  line-height: 1.5;
  cursor: pointer;
}

.task-item:hover:not(:disabled) {
  background: rgba(248, 203, 113, 0.2);
  transform: translateX(2px);
}

.task-item:disabled {
  color: rgba(214, 230, 255, 0.62);
  cursor: default;
  opacity: 0.82;
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
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 12px;
}

.info-table th,
.info-table td {
  border-bottom: 1px solid rgba(126, 197, 255, 0.16);
  padding: 8px 6px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.info-table th:nth-child(1),
.info-table td:nth-child(1) {
  width: 20%;
}

.info-table th:nth-child(2),
.info-table td:nth-child(2) {
  width: 27%;
}

.info-table th:nth-child(3),
.info-table td:nth-child(3) {
  width: 23%;
}

.info-table th:nth-child(4),
.info-table td:nth-child(4) {
  width: 12%;
}

.info-table th:nth-child(5),
.info-table td:nth-child(5) {
  width: 18%;
}

.info-table tbody tr {
  cursor: pointer;
  transition:
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.info-table tbody tr.pending {
  box-shadow: inset 3px 0 0 rgba(255, 141, 141, 0.42);
}

.info-table tbody tr.selected {
  background: rgba(126, 197, 255, 0.16);
  box-shadow:
    inset 3px 0 0 rgba(126, 232, 255, 0.88),
    inset 0 0 0 1px rgba(126, 232, 255, 0.12);
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
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
}

.focus-title {
  margin: 0;
  font-size: 13px;
}

.ctrl-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.focus-state-card {
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 10px;
  background:
    radial-gradient(circle at 0 0, rgba(126, 197, 255, 0.12), transparent 42%),
    rgba(8, 29, 54, 0.7);
  padding: 10px;
  display: grid;
  gap: 9px;
}

.focus-state-card.alert {
  border-color: rgba(255, 141, 141, 0.46);
  box-shadow: inset 0 0 0 1px rgba(255, 141, 141, 0.08);
}

.focus-state-card.online {
  border-color: rgba(108, 226, 178, 0.32);
}

.focus-state-card.offline {
  border-color: rgba(168, 198, 232, 0.22);
  background: rgba(12, 24, 38, 0.72);
}

.focus-state-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.focus-state-head span,
.focus-state-row span {
  color: rgba(214, 230, 255, 0.66);
  font-size: 11px;
}

.focus-state-head strong {
  border: 1px solid rgba(126, 197, 255, 0.24);
  border-radius: 999px;
  padding: 3px 8px;
  color: #d9edff;
  font-size: 11px;
}

.focus-state-card.alert .focus-state-head strong {
  color: #ff9fa9;
  border-color: rgba(255, 141, 141, 0.5);
  background: rgba(86, 26, 38, 0.48);
}

.focus-state-card.online .focus-state-head strong {
  color: #6ce2b2;
  border-color: rgba(108, 226, 178, 0.38);
  background: rgba(21, 78, 61, 0.34);
}

.focus-state-list {
  display: grid;
  gap: 6px;
}

.focus-state-row {
  display: grid;
  grid-template-columns: 4rem minmax(0, 1fr);
  align-items: baseline;
  gap: 8px;
}

.focus-state-row strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #eef8ff;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}

.focus-alarm-switch {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 8px;
  background: rgba(7, 24, 45, 0.5);
  padding: 7px;
  display: grid;
  gap: 5px;
}

.focus-switch-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: rgba(214, 230, 255, 0.7);
  font-size: 11px;
}

.focus-switch-head strong {
  color: #ffb3bb;
  font-size: 11px;
}

.focus-alarm-option {
  border: 1px solid rgba(126, 197, 255, 0.16);
  border-radius: 7px;
  background: rgba(17, 47, 75, 0.46);
  color: #d9edff;
  padding: 5px 7px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px;
  align-items: center;
  cursor: pointer;
}

.focus-alarm-option.active {
  border-color: rgba(255, 141, 141, 0.58);
  background: rgba(86, 26, 38, 0.54);
}

.focus-alarm-option span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  text-align: left;
}

.focus-alarm-option em {
  color: rgba(214, 230, 255, 0.68);
  font-size: 10px;
  font-style: normal;
}

.focus-switch-more {
  margin: 0;
  color: rgba(214, 230, 255, 0.58);
  font-size: 10px;
  line-height: 1.4;
}

.focus-action-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.focus-action-row .btn {
  padding: 5px 6px;
  white-space: nowrap;
}

.focus-action-row .btn[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

.focus-close {
  margin-top: auto;
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

.monitor-row.active {
  border-color: rgba(126, 232, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(126, 232, 255, 0.12);
}

.monitor-row.previewing {
  background: rgba(16, 48, 78, 0.82);
}

.row-title {
  font-weight: 600;
}

.row-sub {
  color: var(--sub);
  font-size: 12px;
  margin-top: 2px;
}

.monitor-row-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
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

.preview-tag {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.24);
  background: rgba(17, 47, 75, 0.54);
  color: rgba(214, 230, 255, 0.76);
  font-size: 12px;
}

.preview-tag.active {
  color: #7ee8ff;
  border-color: rgba(126, 232, 255, 0.52);
  background: rgba(40, 94, 136, 0.42);
}

@media (max-width: 1400px) {
  .alarm-panel,
  .analysis-panel,
  .agent-panel {
    grid-template-columns: 1fr;
  }

  .alarm-panel {
    grid-template-rows: minmax(26rem, 0.95fr) minmax(34rem, 1.05fr);
  }

  .analysis-panel {
    grid-template-columns: 1fr;
    grid-template-rows: none;
    grid-auto-rows: minmax(16rem, auto);
  }

  .analysis-hero-card,
  .analysis-type-card,
  .analysis-trend-card,
  .analysis-cross-card,
  .analysis-insight-card {
    grid-column: auto;
    grid-row: auto;
  }

  .analysis-hero-card {
    grid-template-columns: 1fr;
  }

  .analysis-type-stage {
    grid-template-columns: minmax(160px, 0.36fr) minmax(0, 1fr);
  }

  .analysis-type-grid {
    max-height: 220px;
  }

  .analysis-insight-body {
    grid-template-columns: minmax(120px, 0.3fr) minmax(0, 1fr);
  }

  .alarm-kpi-strip {
    grid-template-columns: repeat(4, minmax(0, 1fr)) minmax(120px, 1.18fr);
  }

  .alarm-type-overview {
    grid-template-columns: minmax(0, 1fr);
  }

  .video-panel {
    grid-template-columns: 1fr;
    grid-template-rows: minmax(28rem, 1fr) minmax(36rem, auto);
    overflow: auto;
    padding-right: 2px;
  }

  .video-side {
    grid-template-rows: minmax(24rem, 1fr) minmax(14rem, auto);
  }

  .alarm-panel,
  .analysis-panel,
  .env-panel,
  .agent-panel {
    overflow: auto;
    padding-right: 2px;
  }

  .env-panel {
    grid-template-columns: minmax(0, 0.55fr) minmax(0, 0.45fr);
    grid-template-rows: auto minmax(124px, 0.3fr) minmax(0, 1fr);
    grid-template-areas:
      "overview overview"
      "status trend"
      "parking trend";
    gap: 10px;
  }

  .env-overview-card {
    grid-template-columns: 1fr;
  }

  .env-overview-body {
    grid-template-columns: minmax(0, 0.62fr) minmax(0, 1.38fr);
  }

  .env-status-card,
  .env-trend-card,
  .env-parking-card {
    min-height: 0;
  }

  .env-trend-svg.single {
    min-height: 0;
  }

  .main-col,
  .side-col {
    height: auto;
    min-height: 0;
    overflow: visible;
    grid-template-rows: auto;
  }

  .section-head,
  .hero-head,
  .card-title-row,
  .summary-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-shell {
    height: min(34rem, calc(100dvh - 16rem));
    min-height: 24rem;
  }
}

@media (max-width: 900px) {
  .video-headline {
    flex-wrap: wrap;
  }

  .video-title-row {
    flex-wrap: wrap;
    row-gap: 4px;
    white-space: normal;
  }

  .video-subtitle {
    white-space: normal;
  }

  .monitor-grid-large {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(11rem, auto);
  }

  .env-panel {
    grid-template-columns: 1fr;
    grid-template-rows: none;
    grid-template-areas: none;
    grid-auto-rows: auto;
    align-content: start;
  }

  .env-overview-card,
  .env-status-card,
  .env-parking-card {
    min-height: 220px;
  }

  .env-trend-card {
    min-height: 290px;
  }

  .env-overview-card {
    grid-template-columns: 1fr;
  }

  .env-overview-body,
  .env-kpi-grid,
  .env-trend-footer {
    grid-template-columns: 1fr;
  }

  .env-status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .parking-pressure-card {
    display: grid;
    grid-template-columns: 1fr;
  }

  .parking-head-right {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .parking-pressure-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .parking-pressure-stats div {
    border-left: 0;
    padding-left: 0;
  }

  .env-trend-head {
    gap: 8px;
  }

  .env-trend-switch {
    flex-wrap: wrap;
  }

  .env-inline-insight {
    grid-template-columns: auto auto;
  }

  .env-inline-insight p {
    grid-column: 1 / -1;
    white-space: normal;
  }

  .nav-current {
    font-size: 15px;
  }

  .video-current {
    justify-content: flex-start;
    flex-wrap: wrap;
    white-space: normal;
  }

  .alarm-kpi-strip,
  .alarm-type-list,
  .alarm-bottom-row,
  .analysis-kpi-grid,
  .analysis-type-grid,
  .analysis-trend-snapshot,
  .selected-alarm-grid,
  .alarm-action-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .summary-kpis,
  .focus-grid {
    grid-template-columns: 1fr;
  }

}

@media (max-width: 760px) {
  .page-shell {
    gap: 6px;
  }

  .nav-bar {
    align-items: flex-start;
    flex-direction: column;
  }

  .monitor-grid-large {
    grid-template-columns: 1fr;
    grid-auto-rows: minmax(10rem, auto);
  }

  .video-panel {
    grid-template-rows: minmax(22rem, 1fr) minmax(32rem, auto);
  }

  .alarm-kpi-strip,
  .alarm-type-list,
  .selected-alarm-grid,
  .analysis-kpi-grid,
  .analysis-type-grid,
  .analysis-trend-snapshot,
  .alarm-action-row,
  .table-filters.alarm-table-filters {
    grid-template-columns: 1fr;
  }

  .analysis-type-stage,
  .analysis-insight-body {
    grid-template-columns: 1fr;
  }

  .analysis-donut-svg,
  .analysis-time-orbit {
    width: 132px;
  }

  .analysis-donut-core {
    top: 66px;
    width: 78px;
    height: 78px;
    padding: 10px;
  }

  .selected-alarm-main {
    grid-template-columns: 1fr;
  }

  .hero-shell {
    height: min(30rem, calc(100dvh - 15rem));
    min-height: 20rem;
  }

  .hero-shell :deep(.chat-messages) {
    left: 1rem;
    right: 1rem;
    width: auto;
  }

  .hero-shell :deep(.chat-input),
  .hero-shell :deep(.realtime-banner) {
    right: 1rem;
    width: min(18rem, calc(100% - 2rem));
  }

  .focus-shell {
    grid-template-columns: 1fr;
  }

}
</style>
