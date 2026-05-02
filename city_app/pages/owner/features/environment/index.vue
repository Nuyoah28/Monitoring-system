<template>
  <view class="environment-page">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">社区环境</view>
      <view class="ghost-btn" @tap="refreshPage">刷新</view>
    </view>

    <view class="hero-card">
      <view>
        <view class="hero-kicker">社区环境</view>
        <view class="hero-title">实时数据总览</view>
        <view class="hero-sub">AQI {{ realtime.aqi }} · 温度 {{ formatNumber(realtime.temperature) }}°C · 湿度 {{ realtime.humidity }}% · PM2.5 {{ formatNumber(realtime.pm25) }}</view>
        <view class="detail-hint">{{ currentMonitorName }} · {{ updateTime }}</view>
      </view>
      <view class="score-ring">
        <text class="score-num">{{ realtime.aqi }}</text>
        <text class="score-unit">AQI</text>
      </view>
    </view>

    <view class="section-card picker-card">
      <view>
        <view class="section-title">关注区域</view>
        <view class="section-sub">选择你想查看的社区位置</view>
      </view>
      <picker :range="monitorNames" :value="currentIndex" @change="onMonitorChange">
        <view class="picker-value">{{ currentMonitorName }}</view>
      </picker>
    </view>

    <view class="metric-grid">
      <view class="metric-card metric-card--air">
        <view class="metric-top">
          <view class="metric-icon metric-icon--air">
            <view class="metric-symbol metric-symbol--air">
              <view class="air-line air-line--one"></view>
              <view class="air-line air-line--two"></view>
              <view class="air-dot"></view>
            </view>
          </view>
          <view class="metric-unit">AQI</view>
        </view>
        <view class="metric-name">空气指数</view>
        <view class="metric-value">{{ realtime.aqi || '--' }}</view>
        <view class="metric-desc">实时空气质量指数</view>
      </view>

      <view class="metric-card metric-card--temp">
        <view class="metric-top">
          <view class="metric-icon metric-icon--temp">
            <view class="metric-symbol metric-symbol--sun">
              <view class="sun-ray sun-ray--vertical"></view>
              <view class="sun-ray sun-ray--horizontal"></view>
              <view class="sun-ray sun-ray--slash"></view>
              <view class="sun-ray sun-ray--backslash"></view>
              <view class="sun-core"></view>
            </view>
          </view>
          <view class="metric-unit">°C</view>
        </view>
        <view class="metric-name">温度</view>
        <view class="metric-value">{{ formatNumber(realtime.temperature) }}°C</view>
        <view class="metric-desc">当前区域温度</view>
      </view>

      <view class="metric-card metric-card--humidity">
        <view class="metric-top">
          <view class="metric-icon metric-icon--humidity">
            <view class="metric-symbol metric-symbol--drop"></view>
          </view>
          <view class="metric-unit">%</view>
        </view>
        <view class="metric-name">湿度</view>
        <view class="metric-value">{{ formatNumber(realtime.humidity) }}%</view>
        <view class="metric-desc">当前空气湿度</view>
      </view>

      <view class="metric-card metric-card--pm">
        <view class="metric-top">
          <view class="metric-icon metric-icon--pm">
            <view class="metric-symbol metric-symbol--particles">
              <view class="particle particle--one"></view>
              <view class="particle particle--two"></view>
              <view class="particle particle--three"></view>
              <view class="particle particle--four"></view>
            </view>
          </view>
          <view class="metric-unit">ug/m3</view>
        </view>
        <view class="metric-name">PM2.5</view>
        <view class="metric-value">{{ formatNumber(realtime.pm25) }}</view>
        <view class="metric-desc">细颗粒物浓度</view>
      </view>
    </view>

    <view class="section-card trend-card">
      <view class="section-head">
        <view>
          <view class="section-title">今日变化</view>
          <view class="section-sub">空气质量趋势参考</view>
        </view>
        <view class="time-chip">{{ updateTime }}</view>
      </view>
      <view class="trend-box">
        <view class="trend-line">
          <view
            v-for="(point, index) in trendPoints"
            :key="'point-' + index"
            class="trend-point"
            :style="{ left: point.left + '%', bottom: point.bottom + '%' }"
          ></view>
        </view>
        <view class="trend-axis">
          <text v-for="item in trendData" :key="item.label">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="section-card detail-card">
      <view class="section-title">详细数据</view>
      <view class="detail-grid">
        <view class="detail-item">
          <text class="detail-label">可燃气体</text>
          <text class="detail-value">{{ gasDisplayText }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">监测位置</text>
          <text class="detail-value">{{ currentMonitorName }}</text>
        </view>
        <view class="detail-item detail-item--wide">
          <text class="detail-label">更新时间</text>
          <text class="detail-value">{{ updateTime }}</text>
        </view>
      </view>
    </view>

    <view class="empty-card" v-if="!hasRealtime">
      <u-icon name="info-circle" color="#8ca0b8" size="42rpx"></u-icon>
      <text>暂未获取到实时环境数据，当前展示社区参考数据。</text>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000';
const FALLBACK_MONITORS = [
  { id: 1, name: '社区公共区域' },
  { id: 2, name: '小区东门附近' },
  { id: 3, name: '地下停车区' },
];

export default {
  data() {
    return {
      monitors: [],
      currentIndex: 0,
      realtimeData: null,
      trendData: [],
      hasRealtime: false,
    };
  },
  computed: {
    monitorNames() {
      return this.monitors.map(item => item.name || item.department || `区域${item.id}`);
    },
    currentMonitor() {
      return this.monitors[this.currentIndex] || null;
    },
    currentMonitorName() {
      return this.currentMonitor ? (this.currentMonitor.name || this.currentMonitor.department || '社区公共区域') : '社区公共区域';
    },
    realtime() {
      const base = this.realtimeData || {};
      const seed = Number((this.currentMonitor && this.currentMonitor.id) || 1);
      const fallback = this.fallbackEnvironment(seed);
      const pm25 = this.pickNumber(base.pm25, fallback.pm25);
      return {
        temperature: this.pickNumber(base.temperature, fallback.temperature).toFixed(1),
        humidity: Math.round(this.pickNumber(base.humidity, fallback.humidity)),
        pm25: Math.round(pm25),
        combustibleGas: Math.round(this.pickNumber(base.combustibleGas, fallback.combustibleGas)),
        aqi: Math.round(this.pickNumber(base.aqi, Math.max(fallback.aqi, pm25 * 1.5))),
        createTime: base.createTime || fallback.createTime,
      };
    },
    updateTime() {
      return this.formatShortTime(this.realtime.createTime);
    },
    gasDisplayText() {
      return `${this.formatNumber(this.realtime.combustibleGas)} ppm`;
    },
    trendPoints() {
      if (!this.trendData.length) return [];
      const values = this.trendData.map(item => item.aqi || 0);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const span = Math.max(1, max - min);
      return this.trendData.map((item, index) => ({
        left: this.trendData.length === 1 ? 50 : Math.round((index / (this.trendData.length - 1)) * 100),
        bottom: Math.round(((item.aqi - min) / span) * 68) + 12,
      }));
    },
  },
  onShow() {
    this.initPage();
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/owner/home/index' });
    },
    async initPage() {
      await this.loadMonitors();
      await this.loadEnvironment();
    },
    async loadMonitors() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/monitor');
        const list = this.isSuccess(res) && Array.isArray(res.data) ? res.data : [];
        this.monitors = list.length ? list : FALLBACK_MONITORS;
      } catch (e) {
        this.monitors = FALLBACK_MONITORS;
      }
      this.currentIndex = Math.min(this.currentIndex, Math.max(this.monitors.length - 1, 0));
    },
    async loadEnvironment() {
      const monitor = this.currentMonitor || FALLBACK_MONITORS[0];
      try {
        const { data: realtimeRes } = await uni.$http.get(`/api/v1/env/realtime?monitorId=${monitor.id}`);
        if (this.isSuccess(realtimeRes) && realtimeRes.data) {
          this.realtimeData = realtimeRes.data;
          this.hasRealtime = true;
        } else {
          this.realtimeData = null;
          this.hasRealtime = false;
        }
      } catch (e) {
        this.realtimeData = null;
        this.hasRealtime = false;
      }
      await this.loadTrend(monitor.id);
    },
    async loadTrend(monitorId) {
      try {
        const { data: trendRes } = await uni.$http.get(`/api/v1/env/trend?monitorId=${monitorId}&range=day`);
        if (this.isSuccess(trendRes) && Array.isArray(trendRes.data) && trendRes.data.length) {
          this.trendData = trendRes.data.slice(-6);
          return;
        }
      } catch (e) {
        this.trendData = [];
      }
      this.trendData = this.createFallbackTrend();
    },
    createFallbackTrend() {
      const base = Number(this.realtime.aqi || 60);
      return ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00'].map((label, index) => ({
        label,
        aqi: Math.max(35, Math.round(base + Math.sin(index + 1) * 9 + index * 2)),
      }));
    },
    fallbackEnvironment(seed = 1) {
      const baseSeed = Number(seed) || 1;
      return {
        temperature: 22.6 + baseSeed * 0.6,
        humidity: 50 + baseSeed * 2,
        pm25: 26 + baseSeed * 4,
        combustibleGas: 6 + baseSeed,
        aqi: 46 + baseSeed * 4,
        createTime: null,
      };
    },
    pickNumber(value, fallback) {
      const num = Number(value);
      return Number.isFinite(num) ? num : fallback;
    },
    onMonitorChange(e) {
      this.currentIndex = Number(e.detail.value || 0);
      this.loadEnvironment();
    },
    refreshPage() {
      this.loadEnvironment();
      uni.showToast({ title: '已刷新', icon: 'success' });
    },
    formatNumber(value) {
      if (value === null || value === undefined || value === '') return '--';
      const num = Number(value);
      if (isNaN(num)) return '--';
      return Number.isInteger(num) ? `${num}` : num.toFixed(1);
    },
    formatShortTime(value) {
      if (!value) return '刚刚更新';
      const text = String(value).replace('T', ' ');
      return text.length >= 16 ? text.slice(5, 16) : text;
    },
  },
};
</script>

<style lang="scss" scoped>
.environment-page {
  min-height: 100vh;
  padding: 26rpx 24rpx 44rpx;
  box-sizing: border-box;
  position: relative;
  overflow: visible;
  background:
    radial-gradient(circle at 12% 2%, rgba(56, 164, 255, 0.20) 0, rgba(56, 164, 255, 0) 250rpx),
    radial-gradient(circle at 88% 18%, rgba(34, 197, 94, 0.12) 0, rgba(34, 197, 94, 0) 300rpx),
    linear-gradient(180deg, #eaf6ff 0%, #f7fbff 50%, #ffffff 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.bg-orb--one {
  width: 250rpx;
  height: 250rpx;
  right: -92rpx;
  top: 150rpx;
  background: rgba(56, 164, 255, 0.10);
}

.bg-orb--two {
  width: 200rpx;
  height: 200rpx;
  left: -80rpx;
  top: 760rpx;
  background: rgba(22, 163, 74, 0.08);
}

.top-bar,
.hero-card,
.section-card,
.metric-grid,
.empty-card {
  position: relative;
  z-index: 1;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.back-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(32, 74, 126, 0.1);
}

.top-title {
  color: #102033;
  font-size: 34rpx;
  font-weight: 900;
}

.ghost-btn {
  height: 56rpx;
  padding: 0 20rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.82);
  color: #1470d8;
  font-size: 24rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
}

.hero-card {
  border-radius: 34rpx;
  padding: 30rpx;
  color: #fff;
  background:
    radial-gradient(circle at 88% 0%, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 220rpx),
    linear-gradient(135deg, #1470d8 0%, #2b8ef0 50%, #36b6ff 100%);
  box-shadow: 0 18rpx 40rpx rgba(20, 112, 216, 0.22);
  display: flex;
  justify-content: space-between;
  gap: 22rpx;
}

.hero-kicker {
  font-size: 24rpx;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.82);
}

.hero-title {
  margin-top: 10rpx;
  font-size: 44rpx;
  line-height: 1.1;
  font-weight: 900;
}


.hero-sub {
  margin-top: 16rpx;
  color: rgba(255, 255, 255, 0.88);
  font-size: 24rpx;
  line-height: 1.45;
}
.detail-hint {
  margin-top: 14rpx;
  display: inline-flex;
  padding: 9rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 1rpx solid rgba(255, 255, 255, 0.24);
  color: rgba(255, 255, 255, 0.86);
  font-size: 21rpx;
  font-weight: 800;
}

.score-ring {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  border: 2rpx solid rgba(255, 255, 255, 0.38);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.score-num {
  font-size: 42rpx;
  line-height: 1;
  font-weight: 900;
}

.score-unit {
  margin-top: 4rpx;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.82);
}

.section-card {
  margin-top: 20rpx;
  padding: 24rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 30rpx rgba(30, 88, 150, 0.10);
}

.picker-card,
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-title {
  color: #102033;
  font-size: 31rpx;
  font-weight: 900;
}

.section-sub {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
}

.picker-value,
.time-chip {
  height: 54rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: #eaf4ff;
  color: #1470d8;
  font-size: 23rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.metric-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14rpx;
}

.metric-card {
  min-height: 210rpx;
  border-radius: 28rpx;
  padding: 20rpx;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid #dcebfa;
  box-shadow: 0 8rpx 22rpx rgba(37, 99, 235, 0.08);
}

.metric-card--air {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.metric-card--temp {
  background: #fff7ed;
  border-color: #fed7aa;
}

.metric-card--humidity {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.metric-card--pm {
  background: #fefce8;
  border-color: #fde68a;
}

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-icon--air { background: #dbeafe; color: #2563eb; }
.metric-icon--temp { background: #fee2e2; color: #dc2626; }
.metric-icon--humidity { background: #dcfce7; color: #16a34a; }
.metric-icon--pm { background: #fef3c7; color: #d97706; }

.metric-symbol {
  position: relative;
  width: 34rpx;
  height: 34rpx;
  color: currentColor;
}

.metric-symbol--sun {
  display: flex;
  align-items: center;
  justify-content: center;
}

.sun-core {
  width: 17rpx;
  height: 17rpx;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 4rpx rgba(220, 38, 38, 0.14);
}

.sun-ray {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 4rpx;
  height: 34rpx;
  margin-left: -2rpx;
  margin-top: -17rpx;
  border-radius: 999rpx;
  background: currentColor;
}

.sun-ray--horizontal { transform: rotate(90deg); }
.sun-ray--slash { transform: rotate(45deg); opacity: 0.72; }
.sun-ray--backslash { transform: rotate(-45deg); opacity: 0.72; }

.metric-symbol--drop {
  width: 22rpx;
  height: 30rpx;
  margin-top: 2rpx;
  border-radius: 50% 50% 50% 8rpx;
  background: currentColor;
  transform: rotate(45deg);
  box-shadow: -4rpx -4rpx 0 rgba(22, 163, 74, 0.12);
}

.metric-symbol--air {
  width: 36rpx;
  height: 30rpx;
}

.air-line {
  position: absolute;
  right: 0;
  height: 5rpx;
  border-radius: 999rpx;
  background: currentColor;
}

.air-line--one {
  top: 6rpx;
  width: 34rpx;
}

.air-line--two {
  top: 20rpx;
  width: 24rpx;
}

.air-dot {
  position: absolute;
  left: 2rpx;
  bottom: 5rpx;
  width: 7rpx;
  height: 7rpx;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.62;
}

.metric-symbol--particles {
  width: 34rpx;
  height: 34rpx;
}

.particle {
  position: absolute;
  border-radius: 50%;
  background: currentColor;
}

.particle--one {
  left: 3rpx;
  top: 7rpx;
  width: 9rpx;
  height: 9rpx;
}

.particle--two {
  right: 4rpx;
  top: 4rpx;
  width: 6rpx;
  height: 6rpx;
  opacity: 0.72;
}

.particle--three {
  left: 12rpx;
  bottom: 4rpx;
  width: 14rpx;
  height: 14rpx;
}

.particle--four {
  right: 2rpx;
  bottom: 10rpx;
  width: 7rpx;
  height: 7rpx;
  opacity: 0.82;
}

.metric-unit {
  color: #1470d8;
  font-size: 22rpx;
  font-weight: 900;
}

.metric-name {
  margin-top: 18rpx;
  color: #64748b;
  font-size: 23rpx;
  font-weight: 800;
}

.metric-value {
  margin-top: 8rpx;
  color: #102033;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 900;
}

.metric-desc {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 21rpx;
  line-height: 1.35;
}

.trend-box {
  margin-top: 22rpx;
  height: 210rpx;
  border-radius: 24rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  padding: 18rpx;
  box-sizing: border-box;
}

.trend-line {
  position: relative;
  height: 138rpx;
  border-bottom: 1rpx dashed #cbd5e1;
  background: linear-gradient(180deg, rgba(20, 112, 216, 0.06), rgba(20, 112, 216, 0));
}

.trend-point {
  position: absolute;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #1470d8;
  box-shadow: 0 0 0 8rpx rgba(20, 112, 216, 0.12);
  transform: translate(-50%, 50%);
}

.trend-axis {
  margin-top: 18rpx;
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 20rpx;
}

.detail-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12rpx;
}

.detail-item {
  padding: 14rpx 16rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
}

.detail-item--wide {
  grid-column: 1 / -1;
}

.detail-label {
  color: #64748b;
  font-size: 22rpx;
  font-weight: 800;
}

.detail-value {
  margin-top: 8rpx;
  color: #102033;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.3;
}

.empty-card {
  margin-top: 20rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #64748b;
  font-size: 23rpx;
  line-height: 1.45;
  display: flex;
  align-items: center;
  gap: 12rpx;
}
</style>
