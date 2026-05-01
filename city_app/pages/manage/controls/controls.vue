<template>
  <view class="home-page" :style="{ paddingTop: statusBarHeight + 'px' }">

    <view class="top-bar">
      <view>
        <view class="eyebrow">管理工作台</view>
        <view class="page-title">社区智眼</view>
        <view class="page-sub">{{ operationSummary }}</view>
      </view>
      <view class="identity-btn" @tap="jumpSetting">
        <image class="identity-icon" src="/static/settings.png" mode="aspectFit"></image>
        <text>身份</text>
      </view>
    </view>

    <view class="overview-card">
      <view class="overview-item overview-item--danger" :class="{ 'is-breathing': pendingTotal > 0 }" @tap="goPage('/pages/manage/realtime/realtime?scope=todayPending')">
        <view class="overview-num">{{ pendingTotal }}</view>
        <view class="overview-label">今日待处理</view>
      </view>
      <view class="overview-item overview-item--warning">
        <view class="overview-num">{{ levelCount.urgent + levelCount.serious }}</view>
        <view class="overview-label">重点警情</view>
      </view>
      <view class="overview-item overview-item--success" @tap="goPage('/pages/manage/monitor/index')">
        <view class="overview-num">{{ monitorList.length }}</view>
        <view class="overview-label">在线监控</view>
      </view>
    </view>

    <!-- ───── Quick Grid ───── -->
    <view class="section-card action-card">
      <view class="section-head">
        <view>
          <text class="section-title">常用操作</text>
          <view class="section-subtitle">快速进入高频处理流程</view>
        </view>
      </view>
      <view class="quick-grid">
      <view class="quick-item" @tap="goPage('/pages/manage/statistics/index')">
        <view class="quick-icon quick-icon--red">
          <image class="quick-icon-image" src="/static/chosenTabBar/realtime.png" mode="aspectFit"></image>
        </view>
        <text>警情统计</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/ai/index')">
        <view class="quick-icon quick-icon--purple">
          <image class="quick-icon-image" src="/static/chosenTabBar/GPT.png" mode="aspectFit"></image>
        </view>
        <text>AI 助手</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/property/parking/index')">
        <view class="quick-icon quick-icon--blue">
          <image class="quick-icon-image" src="/static/locate-blue.png" mode="aspectFit"></image>
        </view>
        <text>车位检测</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/environment/index')">
        <view class="quick-icon quick-icon--green">
          <image class="quick-icon-image" src="/static/chosenTabBar/chart.png" mode="aspectFit"></image>
        </view>
        <text>环境检测</text>
      </view>
      </view>
    </view>

    <!-- ───── Map Card ───── -->
    <view class="section-card map-card" @tap="goPage('/pages/manage/monitor/map')">
      <view class="section-head">
        <text class="section-title">监控地图</text>
        <view class="map-link-row">
          <view class="live-dot"></view>
          <text class="map-link">实时 · 查看摄像头 ›</text>
        </view>
      </view>
      <view class="map-wrap">
        <MonitorMap
          :monitorList="monitorList"
          :alarmList="alarms"
          :pulseTick="mapPulseTick"
          :compact="true"
        />
      </view>
    </view>

    <!-- ───── Alert Card ───── -->
    <view class="section-card alert-card">
      <view class="section-head">
        <view>
          <text class="section-title">待处理警情</text>
          <view class="section-subtitle">优先处理高等级和中等级事件</view>
        </view>
        <view class="all-link" @tap="goPage('/pages/manage/realtime/realtime')">查看全部 ›</view>
      </view>

      <!-- Level Tabs -->
      <view class="level-tabs">
        <view
          class="level-tab"
          :class="['level-tab--urgent', activeLevel === 'urgent' ? 'is-active' : '']"
          @tap="activeLevel = 'urgent'"
        >
          <view class="level-tab__inner">
            <text class="level-tab__label">高等级</text>
            <view class="level-tab__badge level-tab__badge--urgent" :class="levelCount.urgent > 0 ? 'is-pulse' : ''">
              {{ levelCount.urgent }}
            </view>
          </view>
          <view class="level-tab__bar level-tab__bar--urgent"></view>
        </view>
        <view
          class="level-tab"
          :class="['level-tab--serious', activeLevel === 'serious' ? 'is-active' : '']"
          @tap="activeLevel = 'serious'"
        >
          <view class="level-tab__inner">
            <text class="level-tab__label">中等级</text>
            <view class="level-tab__badge level-tab__badge--serious">{{ levelCount.serious }}</view>
          </view>
          <view class="level-tab__bar level-tab__bar--serious"></view>
        </view>
        <view
          class="level-tab"
          :class="['level-tab--normal', activeLevel === 'normal' ? 'is-active' : '']"
          @tap="activeLevel = 'normal'"
        >
          <view class="level-tab__inner">
            <text class="level-tab__label">低等级</text>
            <view class="level-tab__badge level-tab__badge--normal">{{ levelCount.normal }}</view>
          </view>
          <view class="level-tab__bar level-tab__bar--normal"></view>
        </view>
      </view>

      <!-- Alert List -->
      <view class="alert-list">
        <view
          class="alert-item"
          :class="'alert-item--' + levelClass(item)"
          v-for="item in displayAlerts"
          :key="item.id"
          @tap="goDetail(item.id)"
        >
          <view class="alert-stripe" :class="'alert-stripe--' + levelClass(item)"></view>
          <view class="alert-main">
            <view class="alert-title-row">
              <text class="alert-title">{{ item.eventName || item.name || '未知警情' }}</text>
              <view class="level-tag" :class="'level-tag--' + levelClass(item)">{{ levelText(item) }}</view>
            </view>
            <view class="alert-meta">
              <text>{{ item.department || '-' }}</text>
              <text class="meta-dot">·</text>
              <text>{{ item.date || '-' }}</text>
            </view>
          </view>
          <view class="alert-arrow">›</view>
        </view>

        <view class="empty" v-if="!displayAlerts.length">
          <image class="empty-icon" src="/static/warn-none.png" mode="aspectFit"></image>
          <text>暂无待处理警情</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import MonitorMap from "./components/monitorMap.vue";

export default {
  components: { MonitorMap },
  data() {
    return {
      statusBarHeight: 0,
      monitorList: [],
      alarms: [],
      todayPendingAlarms: [],
      activeLevel: 'urgent',
      mapPulseTick: 0,
      alarmRefreshTimer: null,
      monitorRefreshTimer: null,
      mapPulseTimer: null,
      pendingRefreshTimer: null,
    };
  },
  computed: {
    levelCount() {
      const data = { urgent: 0, serious: 0, normal: 0 };
      this.alarms.forEach((item) => {
        const level = Number(item.level) || 1;
        if (level >= 3) data.urgent += 1;
        else if (level === 2) data.serious += 1;
        else data.normal += 1;
      });
      return data;
    },
    pendingTotal() {
      return this.todayPendingAlarms.length;
    },
    operationSummary() {
      if (!this.pendingTotal) return '今日暂无待处理警情，社区运行平稳';
      return `今日有 ${this.pendingTotal} 条待处理警情，请及时跟进`;
    },
    displayAlerts() {
      return this.alarms
        .filter((item) => {
          const level = Number(item.level) || 1;
          if (this.activeLevel === 'urgent') return level >= 3;
          if (this.activeLevel === 'serious') return level === 2;
          return level <= 1;
        })
        .slice(0, 10);
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    uni.$on('newAlarm', this.handleNewAlarm);
  },
  onShow() {
    this.startRealtimeMap();
  },
  onHide() {
    this.stopRealtimeMap();
  },
  onUnload() {
    uni.$off('newAlarm', this.handleNewAlarm);
    this.stopRealtimeMap();
  },
  methods: {
    startRealtimeMap() {
      this.stopRealtimeMap();
      this.getMonitor();
      this.getPendingAlerts();

      this.alarmRefreshTimer = setInterval(() => {
        this.getPendingAlerts(true);
      }, 10000);

      this.monitorRefreshTimer = setInterval(() => {
        this.getMonitor(true);
      }, 30000);

      this.mapPulseTimer = setInterval(() => {
        this.mapPulseTick += 1;
      }, 900);
    },
    stopRealtimeMap() {
      if (this.alarmRefreshTimer) {
        clearInterval(this.alarmRefreshTimer);
        this.alarmRefreshTimer = null;
      }
      if (this.monitorRefreshTimer) {
        clearInterval(this.monitorRefreshTimer);
        this.monitorRefreshTimer = null;
      }
      if (this.mapPulseTimer) {
        clearInterval(this.mapPulseTimer);
        this.mapPulseTimer = null;
      }
      if (this.pendingRefreshTimer) {
        clearTimeout(this.pendingRefreshTimer);
        this.pendingRefreshTimer = null;
      }
    },
    isVisibleAlarm(item) {
      return ![6, 9, 13].includes(Number(item && item.caseType));
    },
    handleNewAlarm(payload) {
      const alarm = payload && payload.data ? payload.data : payload;
      if (alarm && this.isVisibleAlarm(alarm)) {
        this.prependRealtimeAlarm(alarm);
      }
      this.schedulePendingAlertRefresh(260);
    },
    schedulePendingAlertRefresh(delay = 0) {
      if (this.pendingRefreshTimer) {
        clearTimeout(this.pendingRefreshTimer);
      }
      this.pendingRefreshTimer = setTimeout(() => {
        this.pendingRefreshTimer = null;
        this.getPendingAlerts(true);
      }, delay);
    },
    prependRealtimeAlarm(alarm) {
      if (!alarm || typeof alarm !== 'object') return;
      const alarmId = alarm.id || alarm.alarmId || alarm.warningId || `${alarm.name || alarm.monitorName || 'alarm'}-${Date.now()}`;
      const exists = this.alarms.some((item) => String(item.id || item.alarmId || item.warningId) === String(alarmId));
      if (exists) return;
      const normalized = {
        ...alarm,
        id: alarmId,
        level: alarm.level || alarm.warningLevel || 1,
        eventName: alarm.eventName || alarm.caseTypeName || alarm.message || '新的警情',
        date: alarm.date || this.formatNowTime(),
        createTime: alarm.createTime || this.formatNowFullTime(),
        status: alarm.status === undefined ? 0 : alarm.status,
      };
      this.alarms = [normalized, ...this.alarms].filter(this.isPendingAlarmVisible).slice(0, 50);
      this.todayPendingAlarms = [normalized, ...this.todayPendingAlarms].filter(this.isTodayPendingAlarm).slice(0, 50);
    },
    formatNowTime() {
      const now = new Date();
      const pad = (num) => String(num).padStart(2, '0');
      return `${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
    },
    formatNowFullTime() {
      const now = new Date();
      const pad = (num) => String(num).padStart(2, '0');
      return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    },
    mergeMonitorPosition(monitorList, monitorPosList) {
      const monitors = Array.isArray(monitorList) ? monitorList : [];
      const posList = Array.isArray(monitorPosList) ? monitorPosList : [];
      if (!monitors.length) return [];
      if (!posList.length) return monitors;

      return monitors.map((monitor) => {
        const matched =
          posList.find((item) => Number(item.monitorId) === Number(monitor.id)) ||
          posList.find((item) => Number(item.id) === Number(monitor.id)) ||
          posList.find((item) => item.name && monitor.name && item.name === monitor.name) ||
          posList.find((item) => item.area && monitor.department && item.area === monitor.department);

        const lon = Number(matched && matched.longitude);
        const lat = Number(matched && matched.latitude);
        return {
          ...monitor,
          longitude: Number.isFinite(lon) ? lon : monitor.longitude,
          latitude: Number.isFinite(lat) ? lat : monitor.latitude,
        };
      });
    },
    buildTodayRange() {
      const now = new Date();
      const y = now.getFullYear();
      const m = String(now.getMonth() + 1).padStart(2, "0");
      const d = String(now.getDate()).padStart(2, "0");
      const date = `${y}-${m}-${d}`;
      return {
        date,
        time1: `${date} 00:00:00`,
        time2: `${date} 23:59:59`,
      };
    },
    getAlarmDateText(item) {
      const raw = item && (item.createTime || item.date || item.time);
      const text = raw ? String(raw) : '';
      if (/^\d{4}-\d{2}-\d{2}/.test(text)) return text.slice(0, 10);
      return '';
    },
    isPendingAlarm(item) {
      if (!item) return false;
      const status = Number(item.status);
      return status === 0 || item.deal === '未处理';
    },
    isTodayAlarm(item) {
      return this.getAlarmDateText(item) === this.buildTodayRange().date;
    },
    isPendingAlarmVisible(item) {
      return this.isVisibleAlarm(item) && this.isPendingAlarm(item);
    },
    isTodayPendingAlarm(item) {
      return this.isPendingAlarmVisible(item) && this.isTodayAlarm(item);
    },
    async getMonitor(silent = false) {
      try {
        const { data: monitorRes } = await uni.$http.get("/api/v1/monitor", {}, { silent });
        const monitorList = (monitorRes && monitorRes.data) || [];

        let monitorPosList = [];
        try {
          const { data: mapRes } = await uni.$http.get("/api/v1/monitor/map", {}, { silent });
          const mapData = (mapRes && mapRes.data) || {};
          monitorPosList = Array.isArray(mapData) ? mapData : mapData.monitorPosList || [];
        } catch (mapError) {
          console.warn("[controls] 获取监控坐标失败：", mapError);
        }

        this.monitorList = this.mergeMonitorPosition(monitorList, monitorPosList);
      } catch (error) {
        console.warn("[controls] 获取监控地图信息失败：", error);
      }
    },
    async getPendingAlerts(silent = false) {
      try {
        const range = this.buildTodayRange();
        const todayQuery = {
          pageNum: 1,
          pageSize: 100,
          status: 0,
          time1: range.time1,
          time2: range.time2,
        };
        const allQuery = {
          pageNum: 1,
          pageSize: 100,
          status: 0,
        };
        const [{ data: todayData }, { data: allData }] = await Promise.all([
          uni.$http.get("/api/v1/alarm/query", todayQuery, { silent }),
          uni.$http.get("/api/v1/alarm/query", allQuery, { silent }),
        ]);
        const todayList = (todayData && todayData.data && todayData.data.alarmList) || [];
        const allList = (allData && allData.data && allData.data.alarmList) || [];
        this.todayPendingAlarms = todayList.filter(this.isTodayPendingAlarm);
        this.alarms = allList.filter(this.isPendingAlarmVisible);
      } catch (error) {
        console.warn("[controls] 获取实时警情失败：", error);
      }
    },
    levelText(item) {
      const level = Number(item.level) || 1;
      if (level >= 3) return "高";
      if (level === 2) return "中";
      return "低";
    },
    levelClass(item) {
      const level = Number(item.level) || 1;
      if (level >= 3) return "urgent";
      if (level === 2) return "serious";
      return "normal";
    },
    goDetail(id) {
      if (!id) return;
      uni.navigateTo({ url: `/pages/manage/realtime/detail?id=${id}` });
    },
    jumpSetting() {
      uni.navigateTo({ url: "/pages/manage/personal/setting/setting" });
    },
    goPage(url) {
      if (url === "/pages/manage/monitor/index") {
        uni.switchTab({ url });
        return;
      }
      uni.navigateTo({ url });
    },
  },
};
</script>

<style lang="scss" scoped>
.home-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 24rpx 140rpx;
  background: #F5F7FB;
}

.top-bar {
  padding: 18rpx 2rpx 22rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.eyebrow {
  font-size: 23rpx;
  font-weight: 700;
  color: #2563EB;
}

.page-title {
  margin-top: 6rpx;
  font-size: 48rpx;
  line-height: 1.1;
  font-weight: 900;
  color: #0F172A;
}

.page-sub {
  margin-top: 10rpx;
  max-width: 520rpx;
  font-size: 24rpx;
  line-height: 1.45;
  color: #64748B;
}

.identity-btn {
  height: 64rpx;
  padding: 0 18rpx;
  border-radius: 32rpx;
  background: #FFFFFF;
  border: 1rpx solid #E2E8F0;
  box-shadow: 0 8rpx 22rpx rgba(15, 23, 42, 0.06);
  display: flex;
  align-items: center;
  color: #475569;
  font-size: 24rpx;
  font-weight: 700;
}

.identity-icon {
  width: 26rpx;
  height: 26rpx;
  margin-right: 8rpx;
}

.overview-card {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
  margin-bottom: 18rpx;
}

.overview-item {
  min-height: 146rpx;
  border-radius: 24rpx;
  padding: 22rpx 18rpx;
  background: #FFFFFF;
  border: 1rpx solid #E2E8F0;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.06);
}

.overview-num {
  font-size: 46rpx;
  line-height: 1;
  font-weight: 900;
  color: #0F172A;
}

.overview-label {
  margin-top: 14rpx;
  font-size: 23rpx;
  color: #64748B;
  font-weight: 700;
}

.overview-item--danger .overview-num { color: #DC2626; }
.overview-item--warning .overview-num { color: #F59E0B; }
.overview-item--success .overview-num { color: #16A34A; }

.overview-item.is-breathing {
  animation: card-breathe 1.25s ease-in-out infinite;
  position: relative;
  border-color: #FCA5A5;
}

.overview-item.is-breathing::after {
  content: '';
  position: absolute;
  inset: -10rpx;
  border-radius: 30rpx;
  border: 2rpx solid rgba(220, 38, 38, 0.28);
  box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.18);
  animation: card-halo 1.25s ease-in-out infinite;
  pointer-events: none;
}

@keyframes card-breathe {
  0%, 100% {
    box-shadow:
      0 10rpx 28rpx rgba(15, 23, 42, 0.06),
      0 0 0 0 rgba(220, 38, 38, 0.12);
    transform: translateY(0) scale(1);
  }
  50% {
    box-shadow:
      0 18rpx 38rpx rgba(220, 38, 38, 0.22),
      0 0 0 14rpx rgba(220, 38, 38, 0.08);
    transform: translateY(-4rpx) scale(1.03);
  }
}

@keyframes card-halo {
  0%, 100% {
    opacity: 0.18;
    transform: scale(0.98);
  }
  50% {
    opacity: 0.62;
    transform: scale(1.03);
  }
}


.section-card {
  margin-top: 18rpx;
  border-radius: 28rpx;
  background: #FFFFFF;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.06);
  padding: 24rpx;
  border: 1rpx solid #E2E8F0;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  color: #0F172A;
  font-size: 32rpx;
  font-weight: 800;
}

.section-subtitle {
  margin-top: 6rpx;
  color: #94A3B8;
  font-size: 22rpx;
}

.action-card {
  background: linear-gradient(180deg, #F8FBFF 0%, #EEF6FF 100%);
  border-color: #CFE0F6;
}

.quick-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14rpx;
}

.quick-item {
  min-height: 146rpx;
  border-radius: 22rpx;
  background: #FFFFFF;
  border: 1rpx solid #CFE0F6;
  box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;

  &:active {
    transform: scale(0.97);
  }

  text {
    margin-top: 12rpx;
    color: #1E3A5F;
    font-size: 23rpx;
    font-weight: 800;
    line-height: 1.2;
  }
}

.quick-icon {
  width: 66rpx;
  height: 66rpx;
  border-radius: 21rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.quick-icon--red { background: linear-gradient(135deg, #FEE2E2, #FECACA); }
.quick-icon--purple { background: linear-gradient(135deg, #EDE9FE, #DDD6FE); }
.quick-icon--blue { background: linear-gradient(135deg, #DBEAFE, #BFDBFE); }
.quick-icon--green { background: linear-gradient(135deg, #DCFCE7, #BBF7D0); }

.quick-icon-image {
  width: 38rpx;
  height: 38rpx;
  opacity: 1;
}

.map-wrap {
  margin-top: 18rpx;
  height: 330rpx;
  border-radius: 22rpx;
  overflow: hidden;
  background: #F8FAFC;
}

.map-link-row {
  display: flex;
  align-items: center;
}

.live-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #16A34A;
  box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.38);
  animation: live-pulse 1.8s ease-in-out infinite;
}

@keyframes live-pulse {
  0% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.38); }
  70% { box-shadow: 0 0 0 8rpx rgba(22, 163, 74, 0); }
  100% { box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
}

.map-link {
  color: #16A34A;
  font-size: 23rpx;
  font-weight: 700;
  margin-left: 8rpx;
}

.all-link {
  color: #2563EB;
  font-size: 25rpx;
  font-weight: 800;
}

.level-tabs {
  margin-top: 20rpx;
  display: flex;
  gap: 14rpx;
}

.level-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 8rpx 12rpx;
  border-radius: 20rpx;
  border: 1.5rpx solid #E2E8F0;
  background: #F8FAFC;

  &:active { transform: scale(0.97); }
}

.level-tab__inner {
  display: flex;
  align-items: center;
}

.level-tab__label {
  font-size: 25rpx;
  font-weight: 800;
  color: #64748B;
}

.level-tab__badge {
  min-width: 36rpx;
  height: 36rpx;
  border-radius: 999rpx;
  padding: 0 10rpx;
  margin-left: 8rpx;
  font-size: 21rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;

  &--urgent  { background: #DC2626; }
  &--serious { background: #F59E0B; }
  &--normal  { background: #16A34A; }

  &.is-pulse {
    animation: badge-pulse 1.5s ease-in-out infinite;
  }
}

@keyframes badge-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}

.level-tab__bar {
  margin-top: 10rpx;
  width: 52rpx;
  height: 5rpx;
  border-radius: 999rpx;
  opacity: 0;
  transition: opacity 0.2s;

  &--urgent  { background: #DC2626; }
  &--serious { background: #F59E0B; }
  &--normal  { background: #16A34A; }
}

.level-tab--urgent.is-active {
  border-color: rgba(220, 38, 38, 0.22);
  background: #FEF2F2;
  .level-tab__label { color: #DC2626; }
  .level-tab__bar--urgent { opacity: 1; }
}
.level-tab--serious.is-active {
  border-color: rgba(245, 158, 11, 0.24);
  background: #FFFBEB;
  .level-tab__label { color: #D97706; }
  .level-tab__bar--serious { opacity: 1; }
}
.level-tab--normal.is-active {
  border-color: rgba(22, 163, 74, 0.22);
  background: #F0FDF4;
  .level-tab__label { color: #16A34A; }
  .level-tab__bar--normal { opacity: 1; }
}

.alert-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
}

.alert-item + .alert-item {
  margin-top: 12rpx;
}

.alert-item {
  display: flex;
  align-items: stretch;
  border-radius: 20rpx;
  overflow: hidden;
  background: #F8FAFC;
  border: 1rpx solid #E2E8F0;

  &:active {
    transform: scale(0.99);
  }

  &--urgent  { background: #FEF2F2; border-color: rgba(220, 38, 38, 0.14); }
  &--serious { background: #FFFBEB; border-color: rgba(245, 158, 11, 0.16); }
  &--normal  { background: #F0FDF4; border-color: rgba(22, 163, 74, 0.14); }
}

.alert-stripe {
  width: 7rpx;
  flex-shrink: 0;
  &--urgent  { background: #DC2626; }
  &--serious { background: #F59E0B; }
  &--normal  { background: #16A34A; }
}

.alert-main {
  flex: 1;
  padding: 18rpx 16rpx;
}

.alert-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-title {
  color: #0F172A;
  font-size: 28rpx;
  font-weight: 800;
  flex: 1;
  padding-right: 10rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.level-tag {
  font-size: 20rpx;
  font-weight: 900;
  border-radius: 999rpx;
  padding: 5rpx 14rpx;
  flex-shrink: 0;

  &--urgent  { background: rgba(220, 38, 38, 0.1); color: #DC2626; }
  &--serious { background: rgba(245, 158, 11, 0.12); color: #D97706; }
  &--normal  { background: rgba(22, 163, 74, 0.1); color: #16A34A; }
}

.alert-meta {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  color: #64748B;
  font-size: 22rpx;
}

.meta-dot {
  color: #CBD5E1;
  margin: 0 8rpx;
}

.alert-arrow {
  display: flex;
  align-items: center;
  padding: 0 18rpx 0 4rpx;
  color: #94A3B8;
  font-size: 34rpx;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 42rpx 0;

  text {
    color: #94A3B8;
    font-size: 26rpx;
    margin-top: 14rpx;
  }
}

.empty-icon {
  width: 56rpx;
  height: 56rpx;
}
</style>
