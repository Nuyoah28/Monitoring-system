<template>
  <view class="home-page" :style="{ paddingTop: statusBarHeight + 'px' }">

    <!-- ───── Hero ───── -->
    <view class="hero-card">
      <view class="hero-left">
        <view class="hero-title">社区智眼</view>
        <view class="hero-sub">管理端控制台</view>
        <view class="hero-switch" @tap="jumpSetting">
          <image class="hero-switch-icon" src="/static/settings.png" mode="aspectFit"></image>
          <text>切换身份</text>
        </view>
      </view>
      <view class="hero-deco">
        <image class="hero-deco-icon" src="/static/logo.png" mode="aspectFit"></image>
      </view>
    </view>

    <!-- ───── Quick Grid ───── -->
    <view class="quick-grid">
      <view class="quick-item" @tap="goPage('/pages/manage/statistics/index')">
        <view class="quick-icon quick-icon--red">
          <image class="quick-icon-image" src="/static/alarm.png" mode="aspectFit"></image>
        </view>
        <text>警情统计</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/ai/index')">
        <view class="quick-icon quick-icon--purple">
          <image class="quick-icon-image" src="/static/ai.png" mode="aspectFit"></image>
        </view>
        <text>AI 助手</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/property/parking/index')">
        <view class="quick-icon quick-icon--blue">
          <image class="quick-icon-image" src="/static/locate.png" mode="aspectFit"></image>
        </view>
        <text>车位引导</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/environment/index')">
        <view class="quick-icon quick-icon--green">
          <image class="quick-icon-image" src="/static/analysis.png" mode="aspectFit"></image>
        </view>
        <text>环境检测</text>
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
        <MonitorMap :monitorList="monitorList" :compact="true" />
      </view>
    </view>

    <!-- ───── Alert Card ───── -->
    <view class="section-card alert-card">
      <view class="section-head">
        <text class="section-title">待处理警情</text>
        <view class="all-link" @tap="goPage('/pages/manage/realtime/realtime')">全部警情 ›</view>
      </view>

      <!-- Level Tabs -->
      <view class="level-tabs">
        <view
          class="level-tab"
          :class="['level-tab--urgent', activeLevel === 'urgent' ? 'is-active' : '']"
          @tap="activeLevel = 'urgent'"
        >
          <view class="level-tab__inner">
            <text class="level-tab__label">紧急</text>
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
            <text class="level-tab__label">严重</text>
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
            <text class="level-tab__label">一般</text>
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
      activeLevel: 'urgent',
    };
  },
  computed: {
    levelCount() {
      const data = { urgent: 0, serious: 0, normal: 0 };
      this.alarms.forEach((item) => {
        const level = Number(item.level) || 3;
        if (level <= 1) data.urgent += 1;
        else if (level === 2) data.serious += 1;
        else data.normal += 1;
      });
      return data;
    },
    displayAlerts() {
      return this.alarms
        .filter((item) => {
          const level = Number(item.level) || 3;
          if (this.activeLevel === 'urgent') return level <= 1;
          if (this.activeLevel === 'serious') return level === 2;
          return level >= 3;
        })
        .slice(0, 10);
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.getMonitor();
    this.getPendingAlerts();
  },
  methods: {
    buildTodayRange() {
      const now = new Date();
      const y = now.getFullYear();
      const m = String(now.getMonth() + 1).padStart(2, "0");
      const d = String(now.getDate()).padStart(2, "0");
      return {
        startTime: `${y}-${m}-${d} 00:00:00`,
        endTime: `${y}-${m}-${d} 23:59:59`,
      };
    },
    async getMonitor() {
      const { data } = await uni.$http.get("/api/v1/monitor");
      this.monitorList = (data && data.data) || [];
    },
    async getPendingAlerts() {
      const range = this.buildTodayRange();
      const query = {
        pageNum: 1,
        pageSize: 50,
        status: 0,
        startTime: range.startTime,
        endTime: range.endTime,
      };
      const { data } = await uni.$http.get("/api/v1/alarm/query", query);
      const list = (data && data.data && data.data.alarmList) || [];
      this.alarms = list.filter((item) => item.caseType !== 13);
    },
    levelText(item) {
      const level = Number(item.level) || 3;
      if (level <= 1) return "紧急";
      if (level === 2) return "严重";
      return "一般";
    },
    levelClass(item) {
      const level = Number(item.level) || 3;
      if (level <= 1) return "urgent";
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
// ─── 全局背景 ───
.home-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 24rpx 140rpx;
  background: linear-gradient(170deg, #e8f4ff 0%, #f0f8ff 50%, #f7fbff 100%);
}

// ─── Hero Card ───
.hero-card {
  margin-top: 10rpx;
  border-radius: 28rpx;
  background: linear-gradient(130deg, #ffffff 0%, #d6ecff 60%, #c2dfff 100%);
  padding: 28rpx 28rpx 24rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 8rpx 32rpx rgba(20, 112, 216, 0.13), 0 2rpx 8rpx rgba(20, 112, 216, 0.06);
  border: 1rpx solid rgba(255, 255, 255, 0.8);
  overflow: hidden;
  position: relative;

  // 顶部装饰光晕
  &::before {
    content: '';
    position: absolute;
    top: -30rpx;
    right: 80rpx;
    width: 200rpx;
    height: 200rpx;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(20, 112, 216, 0.08) 0%, transparent 70%);
  }
}

.hero-left {
  flex: 1;
  z-index: 1;
}

.hero-title {
  font-size: 56rpx;
  font-weight: 900;
  line-height: 1.1;
  // 渐变文字
  background: linear-gradient(120deg, #0e5fc8 0%, #38a4ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  margin-top: 6rpx;
  color: #4a7da8;
  font-size: 25rpx;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.hero-switch {
  margin-top: 18rpx;
  display: flex;
  align-self: flex-start;
  align-items: center;
  background: rgba(20, 112, 216, 0.1);
  border: 1rpx solid rgba(20, 112, 216, 0.2);
  border-radius: 999rpx;
  padding: 8rpx 20rpx;
  color: #1470d8;

  text {
    font-size: 24rpx;
    font-weight: 700;
    color: #1470d8;
    margin-left: 8rpx;
  }
}

.hero-switch-icon {
  width: 24rpx;
  height: 24rpx;
}

.hero-deco {
  width: 90rpx;
  height: 90rpx;
  flex-shrink: 0;
  z-index: 1;
  border-radius: 22rpx;
  background: rgba(20, 112, 216, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-deco-icon {
  width: 56rpx;
  height: 56rpx;
}

// ─── Quick Grid ───
.quick-grid {
  margin-top: 20rpx;
  background: rgba(236, 246, 255, 0.7);
  border-radius: 24rpx;
  padding: 16rpx;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 4rpx 16rpx rgba(40, 91, 150, 0.07);
}

.quick-item {
  background: #ffffff;
  border-radius: 18rpx;
  height: 148rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(52, 117, 185, 0.08);
  border: 1rpx solid rgba(200, 225, 248, 0.6);
  transition: all 0.15s;
  width: calc(25% - 9rpx);

  &:active {
    transform: scale(0.96);
    box-shadow: 0 2rpx 8rpx rgba(52, 117, 185, 0.06);
  }

  text {
    margin-top: 12rpx;
    color: #2c4a68;
    font-size: 24rpx;
    font-weight: 700;
    line-height: 1.2;
  }
}

.quick-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.12);

  &--red    { background: linear-gradient(140deg, #ff6b6b 0%, #ef4444 100%); }
  &--purple { background: linear-gradient(140deg, #a78bfa 0%, #7c3aed 100%); }
  &--blue   { background: linear-gradient(140deg, #38b6ff 0%, #0e6ecf 100%); }
  &--green  { background: linear-gradient(140deg, #34d399 0%, #059669 100%); }
}

.quick-icon-image {
  width: 34rpx;
  height: 34rpx;
}

// ─── Section Card ───
.section-card {
  margin-top: 18rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 6rpx 24rpx rgba(40, 91, 150, 0.08);
  padding: 22rpx;
  border: 1rpx solid rgba(210, 230, 248, 0.5);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  color: #1a2d42;
  font-size: 34rpx;
  font-weight: 800;
}

// ─── Map Card ───
.map-wrap {
  margin-top: 14rpx;
  height: 330rpx;
  border-radius: 16rpx;
  overflow: hidden;
}

.map-link-row {
  display: flex;
  align-items: center;
}

.live-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4);
  animation: live-pulse 1.8s ease-in-out infinite;
}

@keyframes live-pulse {
  0%   { box-shadow: 0 0 0 0    rgba(34, 197, 94, 0.45); }
  70%  { box-shadow: 0 0 0 8rpx rgba(34, 197, 94, 0); }
  100% { box-shadow: 0 0 0 0    rgba(34, 197, 94, 0); }
}

.map-link {
  color: #22c55e;
  font-size: 24rpx;
  font-weight: 700;
  margin-left: 8rpx;
}

.all-link {
  color: #1470d8;
  font-size: 26rpx;
  font-weight: 700;
}

// ─── Level Tabs ───
.level-tabs {
  margin-top: 18rpx;
  display: flex;
}

.level-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 14rpx 8rpx 10rpx;
  border-radius: 16rpx;
  border: 1.5rpx solid transparent;
  background: #f4f8fd;
  transition: all 0.2s;
  margin-right: 14rpx;

  &:active { transform: scale(0.97); }

  &:last-child {
    margin-right: 0;
  }
}

.level-tab__inner text,
.level-tab__inner view {
  flex-shrink: 0;
}

.level-tab__inner {
  display: flex;
  align-items: center;
}

.level-tab__badge {
  margin-left: 8rpx;
}

.level-tab__label {
  font-size: 27rpx;
  font-weight: 700;
  color: #7a8da3;
}

.level-tab__badge {
  min-width: 36rpx;
  height: 36rpx;
  border-radius: 999rpx;
  padding: 0 10rpx;
  font-size: 22rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;

  &--urgent  { background: #ef4444; }
  &--serious { background: #f59e0b; }
  &--normal  { background: #22c55e; }

  // 有警情时的脉冲
  &.is-pulse {
    animation: badge-pulse 1.5s ease-in-out infinite;
  }
}

@keyframes badge-pulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.15); }
}

.level-tab__bar {
  width: 56rpx;
  height: 5rpx;
  border-radius: 999rpx;
  opacity: 0.3;
  transition: opacity 0.2s;
  &--urgent  { background: #ef4444; }
  &--serious { background: #f59e0b; }
  &--normal  { background: #22c55e; }
}

// Active state
.level-tab--urgent.is-active {
  border-color: rgba(239, 68, 68, 0.25);
  background: #fff5f5;
  .level-tab__label { color: #ef4444; }
  .level-tab__bar--urgent { opacity: 1; }
}
.level-tab--serious.is-active {
  border-color: rgba(245, 158, 11, 0.25);
  background: #fffbf0;
  .level-tab__label { color: #d97706; }
  .level-tab__bar--serious { opacity: 1; }
}
.level-tab--normal.is-active {
  border-color: rgba(34, 197, 94, 0.25);
  background: #f0fff4;
  .level-tab__label { color: #16a34a; }
  .level-tab__bar--normal { opacity: 1; }
}

// ─── Alert List ───
.alert-list {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
}

.alert-item + .alert-item {
  margin-top: 10rpx;
}

.alert-item {
  display: flex;
  align-items: stretch;
  border-radius: 14rpx;
  overflow: hidden;
  background: #f8fbff;
  border: 1rpx solid #e8edf8;
  box-shadow: 0 2rpx 8rpx rgba(40, 91, 150, 0.05);
  transition: all 0.15s;

  &:active {
    transform: scale(0.985);
    box-shadow: 0 1rpx 4rpx rgba(40, 91, 150, 0.04);
  }

  &--urgent  { background: #fff8f8; border-color: rgba(239, 68, 68, 0.12); }
  &--serious { background: #fffcf5; border-color: rgba(245, 158, 11, 0.12); }
  &--normal  { background: #f8fff9; border-color: rgba(34, 197, 94, 0.12); }
}

.alert-stripe {
  width: 6rpx;
  flex-shrink: 0;
  border-radius: 0;
  &--urgent  { background: #ef4444; }
  &--serious { background: #f59e0b; }
  &--normal  { background: #22c55e; }
}

.alert-main {
  flex: 1;
  padding: 16rpx 14rpx;
}

.alert-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-title {
  color: #1a2d42;
  font-size: 28rpx;
  font-weight: 700;
  flex: 1;
  padding-right: 10rpx;
}

.level-tag {
  font-size: 20rpx;
  font-weight: 800;
  border-radius: 999rpx;
  padding: 4rpx 14rpx;
  flex-shrink: 0;

  &--urgent  { background: rgba(239, 68, 68,  0.1); color: #ef4444; }
  &--serious { background: rgba(245, 158, 11, 0.1); color: #d97706; }
  &--normal  { background: rgba(34, 197, 94,  0.1); color: #16a34a; }
}

.alert-meta {
  margin-top: 6rpx;
  display: flex;
  align-items: center;
  color: #8a9db8;
  font-size: 22rpx;
}

.meta-dot {
  color: #b8c8d8;
  margin: 0 6rpx;
}

.alert-arrow {
  display: flex;
  align-items: center;
  padding: 0 16rpx 0 4rpx;
  color: #b8c8d8;
  font-size: 32rpx;
}

// ─── Empty ───
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;

  text {
    color: #a0b0c4;
    font-size: 26rpx;
    margin-top: 14rpx;
  }
}

.empty-icon {
  width: 56rpx;
  height: 56rpx;
}
</style>
