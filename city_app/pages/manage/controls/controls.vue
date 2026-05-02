<template>
  <view class="home-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="hero-card">
      <view class="hero-top">
        <view>
          <view class="eyebrow">管理工作台</view>
          <view class="page-title">社区智眼</view>
        </view>
        <view class="identity-btn" @tap="jumpSetting">
          <u-icon name="setting" color="#fff" size="28rpx"></u-icon>
          <text>身份</text>
        </view>
      </view>
      <view class="hero-summary">
        <view class="summary-dot" :class="pendingTotal > 0 ? 'is-alert' : ''"></view>
        <text>{{ operationSummary }}</text>
      </view>
      <view class="hero-metrics">
        <view class="hero-metric" @tap="goPage('/pages/manage/realtime/realtime')">
          <text class="metric-num">{{ pendingTotal }}</text>
          <text class="metric-label">今日待处理</text>
        </view>
        <view class="hero-metric" @tap="goPage('/pages/manage/realtime/realtime')">
          <text class="metric-num">{{ allPendingTotal }}</text>
          <text class="metric-label">待处理总数</text>
        </view>
        <view class="hero-metric" @tap="goPage('/pages/manage/monitor/index')">
          <text class="metric-num">{{ onlineMonitorCount }}/{{ monitorList.length }}</text>
          <text class="metric-label">在线摄像头</text>
        </view>
      </view>
    </view>

    <view class="section-card action-card">
      <view class="section-head">
        <view>
          <text class="section-title">常用入口</text>
          <view class="section-subtitle">值班常用功能集中在这里</view>
        </view>
      </view>
      <view class="quick-grid quick-grid--main">
        <view class="quick-item" @tap="goPage('/pages/manage/realtime/realtime')">
          <view class="quick-icon quick-icon--red">
            <image class="quick-icon-image" src="/static/chosenTabBar/realtime.png" mode="aspectFit"></image>
          </view>
          <text>告警处理</text>
        </view>
        <view class="quick-item" @tap="goPage('/pages/manage/monitor/index')">
          <view class="quick-icon quick-icon--blue">
            <image class="quick-icon-image" src="/static/chosenTabBar/control.png" mode="aspectFit"></image>
          </view>
          <text>摄像头管理</text>
        </view>
        <view class="quick-item" @tap="goPage('/pages/manage/monitor/ai-config')">
          <view class="quick-icon quick-icon--rule">
            <u-icon name="setting" color="#ffffff" size="38rpx"></u-icon>
          </view>
          <text>识别规则</text>
        </view>
        <view class="quick-item" @tap="goPage('/pages/manage/ai/index')">
          <view class="quick-icon quick-icon--purple">
            <image class="quick-icon-image" src="/static/chosenTabBar/GPT.png" mode="aspectFit"></image>
          </view>
          <text>AI助手</text>
        </view>
        <view class="quick-item" @tap="goPage('/pages/manage/environment/index')">
          <view class="quick-icon quick-icon--teal">
            <image class="quick-icon-image" src="/static/analysis.png" mode="aspectFit"></image>
          </view>
          <text>环境检测</text>
        </view>
        <view class="quick-item" @tap="goPage('/pages/manage/property/parking/index')">
          <view class="quick-icon quick-icon--parking">
            <u-icon name="car" color="#ffffff" size="38rpx"></u-icon>
          </view>
          <text>车位检测</text>
        </view>
      </view>
    </view>

    <view class="section-card map-card" @tap="goPage('/pages/manage/monitor/map')">
      <view class="section-head">
        <view>
          <text class="section-title">社区总览</text>
          <view class="section-subtitle">红点表示仍未处理的点位告警</view>
        </view>
        <view class="map-link-row">
          <view class="live-dot"></view>
          <text class="map-link">查看地图 ›</text>
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

    <view class="section-card task-card">
      <view class="section-head">
        <view>
          <text class="section-title">待办优先级</text>
          <view class="section-subtitle">按风险等级快速定位需要处理的警情</view>
        </view>
        <view class="all-link" @tap="goPage('/pages/manage/realtime/realtime')">进入告警 ›</view>
      </view>
      <view class="level-panel">
        <view class="level-card level-card--urgent" :class="activeLevel === 'urgent' ? 'is-active' : ''" @tap="activeLevel = 'urgent'">
          <view class="level-pulse"></view>
          <text class="level-num">{{ levelCount.urgent }}</text>
          <text class="level-name">高风险</text>
        </view>
        <view class="level-card level-card--serious" :class="activeLevel === 'serious' ? 'is-active' : ''" @tap="activeLevel = 'serious'">
          <view class="level-dot"></view>
          <text class="level-num">{{ levelCount.serious }}</text>
          <text class="level-name">中风险</text>
        </view>
        <view class="level-card level-card--normal" :class="activeLevel === 'normal' ? 'is-active' : ''" @tap="activeLevel = 'normal'">
          <view class="level-dot"></view>
          <text class="level-num">{{ levelCount.normal }}</text>
          <text class="level-name">低风险</text>
        </view>
      </view>
      <view class="priority-list">
        <view
          class="priority-item"
          :class="'priority-item--' + levelClass(item)"
          v-for="item in displayAlerts"
          :key="item.id"
          @tap="goDetail(item.id)"
        >
          <view class="priority-level" :class="'priority-level--' + levelClass(item)">{{ levelText(item) }}</view>
          <view class="priority-main">
            <view class="priority-title">{{ item.eventName || item.name || '未知警情' }}</view>
            <view class="priority-meta">{{ item.department || '-' }} · {{ item.date || item.createTime || '-' }}</view>
          </view>
          <view class="priority-arrow">›</view>
        </view>
        <view class="empty compact" v-if="!displayAlerts.length">
          <image class="empty-icon" src="/static/warn-none.png" mode="aspectFit"></image>
          <text>当前等级暂无待处理警情</text>
        </view>
      </view>
    </view>

    <manage-tabbar current="home" native-overlay />
  </view>
</template>

<script>
import MonitorMap from "./components/monitorMap.vue";
import ManageTabbar from '@/components/navigation/manage-tabbar.vue';

export default {
  components: { MonitorMap, ManageTabbar },
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
        const level = Number(item.level) || Number(item.warningLevel) || 1;
        if (level >= 3) data.urgent += 1;
        else if (level === 2) data.serious += 1;
        else data.normal += 1;
      });
      return data;
    },
    pendingTotal() {
      return this.todayPendingAlarms.length;
    },
    allPendingTotal() {
      return this.alarms.length;
    },
    onlineMonitorCount() {
      return this.monitorList.filter((item) => item.running).length;
    },
    offlineMonitorCount() {
      return Math.max(0, this.monitorList.length - this.onlineMonitorCount);
    },
    aiConfiguredCount() {
      return this.monitorList.filter(this.isAiConfigured).length;
    },
    aiUnconfiguredCount() {
      return Math.max(0, this.monitorList.length - this.aiConfiguredCount);
    },
    aiConfigPercent() {
      if (!this.monitorList.length) return 0;
      return Math.round((this.aiConfiguredCount / this.monitorList.length) * 100);
    },
    riskScore() {
      return Math.min(99, this.levelCount.urgent * 12 + this.levelCount.serious * 6 + this.levelCount.normal * 2);
    },
    riskStatusText() {
      if (this.levelCount.urgent > 0) return '高风险关注';
      if (this.levelCount.serious > 0) return '中风险关注';
      if (this.allPendingTotal > 0) return '有待处理事项';
      return '运行平稳';
    },
    riskPercent() {
      return Math.min(100, this.riskScore);
    },
    operationSummary() {
      if (!this.pendingTotal) return '今日暂无待处理警情，社区运行平稳';
      return `今日有 ${this.pendingTotal} 条待处理警情，请及时跟进`;
    },
    priorityAlerts() {
      return [...this.alarms]
        .sort((a, b) => {
          const levelDiff = (Number(b.level) || Number(b.warningLevel) || 1) - (Number(a.level) || Number(a.warningLevel) || 1);
          if (levelDiff) return levelDiff;
          return String(b.createTime || b.date || '').localeCompare(String(a.createTime || a.date || ''));
        })
        .slice(0, 5);
    },
    displayAlerts() {
      return this.alarms
        .filter((item) => {
          const level = Number(item.level) || Number(item.warningLevel) || 1;
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
    abilityList(item) {
      const ability = item && item.ability;
      if (Array.isArray(ability)) return ability;
      return [];
    },
    isAiConfigured(item) {
      if (item && typeof item.recognitionRuleConfigured === 'boolean') {
        return item.recognitionRuleConfigured;
      }
      return this.abilityList(item).some((ability) => ability && ability.checked);
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
      const level = Number(item.level) || Number(item.warningLevel) || 1;
      if (level >= 3) return "高";
      if (level === 2) return "中";
      return "低";
    },
    levelClass(item) {
      const level = Number(item.level) || Number(item.warningLevel) || 1;
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
      const path = String(url || '').split('?')[0];
      const tabPaths = [
        '/pages/manage/controls/controls',
        '/pages/manage/monitor/index',
        '/pages/manage/realtime/realtime',
        '/pages/manage/personal/personal',
      ];
      if (tabPaths.includes(path)) {
        uni.reLaunch({ url: path });
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
  padding: 0 24rpx calc(128rpx + env(safe-area-inset-bottom));
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 3%, rgba(56, 164, 255, 0.24) 0, rgba(56, 164, 255, 0) 260rpx),
    radial-gradient(circle at 88% 18%, rgba(20, 112, 216, 0.18) 0, rgba(20, 112, 216, 0) 300rpx),
    linear-gradient(180deg, #dcefff 0%, #eef7ff 38%, #f7fbff 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(4rpx);
  pointer-events: none;
}

.bg-orb--one {
  width: 220rpx;
  height: 220rpx;
  right: -80rpx;
  top: 160rpx;
  background: rgba(56, 164, 255, 0.16);
}

.bg-orb--two {
  width: 180rpx;
  height: 180rpx;
  left: -70rpx;
  top: 540rpx;
  background: rgba(22, 163, 74, 0.08);
}

.hero-card,
.section-card {
  position: relative;
  z-index: 1;
}

.hero-card {
  padding: 30rpx;
  border-radius: 34rpx;
  color: #fff;
  background:
    radial-gradient(circle at 88% 0%, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 230rpx),
    linear-gradient(135deg, #1470d8 0%, #2b8ef0 48%, #38a4ff 100%);
  box-shadow: 0 18rpx 40rpx rgba(20, 112, 216, 0.24);
}

.hero-top,
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20rpx;
}

.eyebrow {
  font-size: 24rpx;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.82);
}

.page-title {
  margin-top: 10rpx;
  font-size: 46rpx;
  line-height: 1.1;
  font-weight: 900;
}

.identity-btn {
  height: 56rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  border: 1rpx solid rgba(255, 255, 255, 0.28);
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 23rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.hero-summary {
  margin-top: 22rpx;
  padding: 16rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 1rpx solid rgba(255, 255, 255, 0.24);
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.summary-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #86efac;
  flex-shrink: 0;
}

.summary-dot.is-alert {
  background: #fef3c7;
  box-shadow: 0 0 0 0 rgba(254, 243, 199, 0.6);
  animation: home-alert-breathe 1.8s ease-in-out infinite;
}

.hero-metrics {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
}

.hero-metric {
  min-height: 80rpx;
  border-radius: 20rpx;
  background: rgba(255,255,255,0.18);
  border: 1rpx solid rgba(255,255,255,0.22);
  padding: 12rpx 14rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}

.metric-num {
  color: #fff;
  font-size: 28rpx;
  line-height: 1;
  font-weight: 900;
}

.metric-label {
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.82);
  font-size: 20rpx;
  font-weight: 700;
}

.section-card {
  margin-top: 20rpx;
  padding: 24rpx;
  border-radius: 30rpx;
  background: rgba(255,255,255,0.97);
  border: 1rpx solid rgba(37, 99, 235, 0.14);
  box-shadow: 0 14rpx 34rpx rgba(30, 88, 150, 0.12);
}

.map-card {
  overflow: hidden;
}

.action-card {
  background:
    radial-gradient(circle at 8% 0%, rgba(56, 164, 255, 0.08), transparent 28%),
    rgba(255, 255, 255, 0.98);
  border-color: rgba(37, 99, 235, 0.16);
}

.map-wrap {
  margin-top: 18rpx;
  height: 360rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(220, 235, 248, 0.9), rgba(243, 248, 252, 0.96));
}

.section-title {
  color: #0f172a;
  font-size: 32rpx;
  font-weight: 900;
}

.section-subtitle {
  margin-top: 6rpx;
  color: #475569;
  font-size: 22rpx;
}

.map-link-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.live-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #dc2626;
}

.map-link,
.all-link {
  color: #1470d8;
  font-size: 24rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.quick-grid--main {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
}

.quick-item {
  position: relative;
  min-height: 132rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 250, 255, 0.98));
  border: 1rpx solid #cddff5;
  box-shadow:
    0 10rpx 22rpx rgba(37, 99, 235, 0.10),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.quick-item:active {
  transform: scale(0.97);
}

.quick-item::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 24rpx;
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.20);
  pointer-events: none;
}

.quick-icon {
  width: 66rpx;
  height: 66rpx;
  border-radius: 22rpx;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid rgba(255, 255, 255, 0.42);
  box-sizing: border-box;
}

.quick-icon::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0) 55%);
  pointer-events: none;
}

.quick-icon-image {
  width: 38rpx;
  height: 38rpx;
  position: relative;
  z-index: 1;
  filter: brightness(1.12) contrast(1.08) saturate(1.08) drop-shadow(0 1rpx 1.5rpx rgba(15, 23, 42, 0.12));
}

.quick-icon--red {
  background: linear-gradient(180deg, #ff6b6b 0%, #f43f5e 100%);
  box-shadow: 0 10rpx 18rpx rgba(244, 63, 94, 0.22);
}
.quick-icon--blue {
  background: linear-gradient(180deg, #3b82f6 0%, #60a5fa 100%);
  box-shadow: 0 10rpx 18rpx rgba(59, 130, 246, 0.22);
}
.quick-icon--rule {
  background: linear-gradient(180deg, #334155 0%, #64748b 100%);
  box-shadow: 0 10rpx 18rpx rgba(100, 116, 139, 0.22);
}
.quick-icon--purple {
  background: linear-gradient(180deg, #7c3aed 0%, #c084fc 100%);
  box-shadow: 0 10rpx 18rpx rgba(124, 58, 237, 0.22);
}
.quick-icon--teal {
  background: linear-gradient(180deg, #0f766e 0%, #2dd4bf 100%);
  box-shadow: 0 10rpx 18rpx rgba(45, 212, 191, 0.22);
}
.quick-icon--parking {
  background: linear-gradient(180deg, #0369a1 0%, #38bdf8 100%);
  box-shadow: 0 10rpx 18rpx rgba(56, 189, 248, 0.22);
}

.quick-item text {
  margin-top: 12rpx;
  color: #0f172a;
  font-size: 22rpx;
  font-weight: 900;
}

.level-panel {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
}

.level-card {
  min-height: 118rpx;
  border-radius: 24rpx;
  padding: 18rpx 16rpx;
  box-sizing: border-box;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  position: relative;
  overflow: hidden;
}

.level-card.is-active {
  box-shadow: 0 10rpx 24rpx rgba(20, 112, 216, 0.12);
  transform: translateY(-2rpx);
}

.level-card--urgent {
  background: linear-gradient(180deg, rgba(255, 241, 242, 0.98), rgba(255, 248, 249, 0.98));
  border-color: rgba(239, 68, 68, 0.18);
}

.level-card--serious {
  background: linear-gradient(180deg, rgba(255, 250, 235, 0.98), rgba(255, 252, 247, 0.98));
  border-color: rgba(245, 158, 11, 0.18);
}

.level-card--normal {
  background: linear-gradient(180deg, rgba(240, 249, 255, 0.98), rgba(248, 252, 255, 0.98));
  border-color: rgba(59, 130, 246, 0.16);
}

.level-pulse {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: radial-gradient(circle, #ff6b6b 0%, #dc2626 70%);
  box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.34);
  margin-bottom: 6rpx;
  animation: home-alert-breathe 1.8s ease-in-out infinite;
}

.level-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  margin-bottom: 6rpx;
  background: #3b82f6;
  opacity: 0.9;
}

.level-card--serious .level-dot {
  background: #f59e0b;
}

.level-card--normal .level-dot {
  background: #22c55e;
}

.level-num {
  margin-top: 8rpx;
  color: #102033;
  font-size: 34rpx;
  line-height: 1;
  font-weight: 900;
}

.level-name {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 21rpx;
  font-weight: 700;
}

.priority-list {
  margin-top: 16rpx;
  padding-bottom: 6rpx;
}

.priority-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  margin-bottom: 12rpx;
}

.priority-item--urgent {
  border-color: rgba(239, 68, 68, 0.22);
  background: linear-gradient(180deg, rgba(255, 241, 242, 0.96), rgba(248, 251, 255, 0.98));
  box-shadow: 0 8rpx 20rpx rgba(239, 68, 68, 0.08);
  animation: home-alert-breathe 2.2s ease-in-out infinite;
}

.priority-item--serious {
  border-color: rgba(245, 158, 11, 0.16);
}

.priority-item--normal {
  border-color: rgba(59, 130, 246, 0.14);
}

.priority-level {
  width: 52rpx;
  height: 52rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.priority-level--urgent {
  background: linear-gradient(135deg, #ff6b6b, #dc2626);
  color: #fff;
  box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.28);
  animation: home-alert-breathe 1.8s ease-in-out infinite;
}

.priority-level--serious {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #fff;
}

.priority-level--normal {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  color: #fff;
}

.priority-main {
  flex: 1;
  min-width: 0;
}

.priority-title {
  color: #102033;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.priority-meta {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 21rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.priority-arrow {
  color: #94a3b8;
  font-size: 34rpx;
  font-weight: 700;
}

.empty {
  text-align: center;
  color: #94a3b8;
  font-size: 24rpx;
  padding: 60rpx 0;
}

@keyframes home-alert-breathe {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.22);
  }
  60% {
    transform: scale(1.03);
    box-shadow: 0 0 0 12rpx rgba(220, 38, 38, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(220, 38, 38, 0);
  }
}
</style>
