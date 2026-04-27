<template>
  <scroll-view scroll-y class="env-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="title-row">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="title">环境质量检测</text>
      <view class="refresh-btn" @tap="refreshAll">刷新</view>
    </view>

    <view class="picker-card">
      <view>
        <text class="label">监测点</text>
        <picker :range="monitorNames" :value="currentIndex" @change="onMonitorChange">
          <view class="picker-value">{{ currentMonitor ? currentMonitor.name : '请选择监测点' }}</view>
        </picker>
      </view>
      <view class="status-pill" :class="comfortLevel.type">{{ comfortLevel.text }}</view>
    </view>

    <view class="score-panel">
      <view>
        <view class="score-label">综合舒适度</view>
        <view class="score-main">{{ comfortScore }}<text>/100</text></view>
      </view>
      <view class="score-bars">
        <view class="score-row">
          <text>AQI</text>
          <view class="bar"><view class="bar-inner blue" :style="{ width: aqiScore + '%' }"></view></view>
        </view>
        <view class="score-row">
          <text>湿度</text>
          <view class="bar"><view class="bar-inner green" :style="{ width: humidityScore + '%' }"></view></view>
        </view>
        <view class="score-row">
          <text>PM2.5</text>
          <view class="bar"><view class="bar-inner amber" :style="{ width: pm25Score + '%' }"></view></view>
        </view>
      </view>
    </view>

    <view class="grid">
      <view class="metric-card">
        <text class="metric-name">温度</text>
        <text class="metric-value">{{ realtime.temperature }}°C</text>
        <text class="metric-desc">较昨日 {{ realtime.temperatureDelta >= 0 ? '+' : '' }}{{ realtime.temperatureDelta }}°C</text>
      </view>
      <view class="metric-card">
        <text class="metric-name">湿度</text>
        <text class="metric-value">{{ realtime.humidity }}%</text>
        <text class="metric-desc">动态区间 {{ humidityRange }}</text>
      </view>
      <view class="metric-card">
        <text class="metric-name">AQI</text>
        <text class="metric-value">{{ realtime.aqi }}</text>
        <text class="metric-desc">{{ aqiText }}</text>
      </view>
      <view class="metric-card">
        <text class="metric-name">PM2.5</text>
        <text class="metric-value">{{ realtime.pm25 }}</text>
        <text class="metric-desc">ug/m3</text>
      </view>
    </view>

    <view class="panel">
      <view class="panel-head">
        <view class="panel-title">今日动态趋势</view>
        <view class="panel-tag">{{ realtime.time }}</view>
      </view>
      <view class="trend-chart">
        <view class="chart-line">
          <view
            v-for="(point, index) in trendPoints"
            :key="'line-' + index"
            class="trend-point"
            :style="{ left: point.left + '%', bottom: point.bottom + '%' }"
          ></view>
        </view>
        <view class="trend-axis">
          <text v-for="item in trendData" :key="item.label">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="panel">
      <view class="panel-title">区域环境对比</view>
      <view v-for="item in areaStats" :key="item.name" class="area-row">
        <view class="area-name">{{ item.name }}</view>
        <view class="area-bar">
          <view class="area-bar-inner" :style="{ width: item.score + '%' }"></view>
        </view>
        <view class="area-score">{{ item.score }}</view>
      </view>
    </view>

    <view class="panel">
      <view class="panel-title">实时分析</view>
      <view v-for="item in analysisList" :key="item" class="analysis-item">{{ item }}</view>
    </view>

    <view class="panel">
      <view class="panel-title">异常记录</view>
      <view v-for="item in abnormalList" :key="item.time + item.text" class="event-card">
        <view class="event-time">{{ item.time }}</view>
        <view class="event-text">{{ item.text }}</view>
      </view>
    </view>
  </scroll-view>
</template>

<script>
const MOCK_MONITORS = [
  { id: 1, name: '小区东门街道', department: '小区东门街道' },
  { id: 2, name: '地库A区', department: '地库A区' },
  { id: 3, name: '4号楼楼道', department: '4号楼楼道' },
];

export default {
  data() {
    return {
      statusBarHeight: 0,
      monitors: [],
      currentIndex: 0,
      weather: null,
      trendData: [],
      areaStats: [],
      tickTimer: null,
    };
  },
  computed: {
    monitorNames() {
      return this.monitors.map((item) => item.name || item.department || `监测点${item.id}`);
    },
    currentMonitor() {
      return this.monitors[this.currentIndex] || null;
    },
    realtime() {
      const base = this.weather || {};
      const seed = Number((this.currentMonitor && this.currentMonitor.id) || 1);
      const nowMinute = new Date().getMinutes();
      const temperature = Number(base.temperature || (22 + seed + (nowMinute % 5) * 0.4)).toFixed(1);
      const humidity = Math.round(Number(base.humidity || (48 + seed * 3 + (nowMinute % 6))));
      const pm25 = Math.max(18, Math.round(42 + seed * 4 + (nowMinute % 7) * 2));
      const aqi = Math.max(45, Math.round(pm25 * 1.55));
      return {
        temperature,
        humidity,
        pm25,
        aqi,
        temperatureDelta: Number((Number(temperature) - 23.5).toFixed(1)),
        time: this.formatTime(base.createTime),
      };
    },
    humidityRange() {
      const values = this.trendData.map((item) => item.humidity);
      if (!values.length) return '--';
      return `${Math.min(...values)}-${Math.max(...values)}%`;
    },
    aqiText() {
      if (this.realtime.aqi >= 120) return '空气偏差';
      if (this.realtime.aqi >= 80) return '轻度波动';
      return '状态良好';
    },
    aqiScore() {
      return Math.max(12, Math.min(100, 100 - Math.max(0, this.realtime.aqi - 40) * 0.7));
    },
    humidityScore() {
      const diff = Math.abs(this.realtime.humidity - 55);
      return Math.max(18, Math.round(100 - diff * 2));
    },
    pm25Score() {
      return Math.max(12, Math.min(100, 100 - Math.max(0, this.realtime.pm25 - 18)));
    },
    comfortScore() {
      return Math.round((this.aqiScore * 0.38 + this.humidityScore * 0.32 + this.pm25Score * 0.3));
    },
    comfortLevel() {
      if (this.comfortScore >= 82) return { text: '良好', type: 'good' };
      if (this.comfortScore >= 65) return { text: '关注', type: 'warn' };
      return { text: '较差', type: 'bad' };
    },
    trendPoints() {
      if (!this.trendData.length) return [];
      const values = this.trendData.map((item) => item.aqi);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const span = Math.max(1, max - min);
      return this.trendData.map((item, index) => ({
        left: this.trendData.length === 1 ? 50 : Math.round((index / (this.trendData.length - 1)) * 100),
        bottom: Math.round(((item.aqi - min) / span) * 72) + 10,
      }));
    },
    analysisList() {
      const list = [];
      list.push(`当前${this.currentMonitor ? this.currentMonitor.name : '监测点'}舒适度为 ${this.comfortScore} 分。`);
      if (this.realtime.pm25 > 55) list.push('PM2.5 偏高，建议加强通风并关注烟雾类报警。');
      else list.push('PM2.5 处于可控范围，空气质量整体稳定。');
      if (this.realtime.humidity > 65) list.push('湿度偏高，地下或楼道区域建议开启除湿/排风。');
      else if (this.realtime.humidity < 40) list.push('湿度偏低，室外扬尘风险略有上升。');
      else list.push('湿度处于舒适区间，环境波动较小。');
      return list;
    },
    abnormalList() {
      const events = [];
      if (this.realtime.pm25 > 55) events.push({ time: '近10分钟', text: 'PM2.5 短时抬升' });
      if (this.realtime.aqi > 95) events.push({ time: '今日', text: 'AQI 达到关注阈值' });
      if (!events.length) events.push({ time: '今日', text: '暂无明显环境异常' });
      return events;
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.initData();
    this.tickTimer = setInterval(() => this.refreshMockRealtime(), 8000);
  },
  onHide() {
    this.clearTimer();
  },
  onUnload() {
    this.clearTimer();
  },
  methods: {
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/manage/controls/controls' });
      }
    },
    clearTimer() {
      if (this.tickTimer) {
        clearInterval(this.tickTimer);
        this.tickTimer = null;
      }
    },
    async initData() {
      try {
        const { data } = await uni.$http.get('/api/v1/monitor');
        const list = (data && data.data) || [];
        this.monitors = list.length ? list : MOCK_MONITORS;
      } catch (e) {
        this.monitors = MOCK_MONITORS;
      }
      if (this.monitors.length) {
        this.currentIndex = Math.min(this.currentIndex, this.monitors.length - 1);
        await this.getWeather(this.currentMonitor.id);
      }
      this.generateVisualData();
    },
    async getWeather(monitorId) {
      try {
        const { data } = await uni.$http.get(`/api/v1/weather/newest/${monitorId}`);
        this.weather = (data && data.data) || null;
      } catch (e) {
        this.weather = null;
      }
    },
    onMonitorChange(e) {
      this.currentIndex = Number(e.detail.value || 0);
      const monitor = this.currentMonitor;
      if (monitor) {
        this.getWeather(monitor.id).then(() => this.generateVisualData());
      }
    },
    refreshAll() {
      this.initData();
      uni.showToast({ title: '已刷新', icon: 'success' });
    },
    refreshMockRealtime() {
      this.generateVisualData();
    },
    generateVisualData() {
      const seed = Number((this.currentMonitor && this.currentMonitor.id) || 1);
      const labels = ['06:00', '09:00', '12:00', '15:00', '18:00', '21:00'];
      this.trendData = labels.map((label, index) => ({
        label,
        aqi: Math.round(58 + seed * 5 + Math.sin(index + seed) * 13 + index * 2),
        humidity: Math.round(48 + seed * 2 + Math.cos(index + seed) * 8),
      }));
      const names = this.monitors.slice(0, 4).map((item) => item.name || item.department || '监测区域');
      this.areaStats = (names.length ? names : MOCK_MONITORS.map((item) => item.name)).map((name, index) => ({
        name,
        score: Math.max(48, Math.min(94, Math.round(this.comfortScore - index * 5 + Math.sin(index + seed) * 8))),
      }));
    },
    formatTime(value) {
      if (!value) {
        const now = new Date();
        return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      }
      if (typeof value === 'string') return value.replace('T', ' ').slice(11, 16) || value.slice(0, 16);
      return `${value}`;
    },
  },
};
</script>

<style scoped lang="scss">
.env-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #dceefa 0%, #f7fbff 58%, #ffffff 100%);
  padding: 0 24rpx 40rpx;
  box-sizing: border-box;
}

.title-row {
  margin: 10rpx 0 18rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
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
  flex-shrink: 0;
}

.title {
  flex: 1;
  color: #1f2d3c;
  font-size: 38rpx;
  font-weight: 900;
}

.refresh-btn {
  height: 56rpx;
  padding: 0 20rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.82);
  color: #2b5b99;
  font-size: 24rpx;
  display: flex;
  align-items: center;
}

.picker-card,
.score-panel,
.panel,
.metric-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  border-radius: 26rpx;
  box-sizing: border-box;
}

.picker-card {
  padding: 22rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label,
.metric-name,
.score-label,
.panel-tag {
  font-size: 23rpx;
  color: #607893;
}

.picker-value {
  margin-top: 10rpx;
  padding: 14rpx 18rpx;
  border-radius: 14rpx;
  background: #edf6ff;
  color: #1f2d3c;
  font-size: 28rpx;
  font-weight: 700;
}

.status-pill {
  min-width: 96rpx;
  height: 56rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
}

.status-pill.good {
  background: rgba(62, 202, 143, 0.15);
  color: #16a36f;
}

.status-pill.warn {
  background: rgba(255, 184, 66, 0.2);
  color: #d48d08;
}

.status-pill.bad {
  background: rgba(255, 91, 105, 0.15);
  color: #e04d60;
}

.score-panel {
  margin-top: 18rpx;
  padding: 24rpx;
  display: flex;
  gap: 22rpx;
  align-items: center;
}

.score-main {
  margin-top: 8rpx;
  color: #1178cc;
  font-size: 64rpx;
  font-weight: 900;
  line-height: 1;
}

.score-main text {
  font-size: 24rpx;
  color: #7288a1;
  font-weight: 700;
}

.score-bars {
  flex: 1;
}

.score-row {
  display: grid;
  grid-template-columns: 84rpx 1fr;
  align-items: center;
  margin: 10rpx 0;
  font-size: 22rpx;
  color: #58708e;
}

.bar,
.area-bar {
  height: 12rpx;
  border-radius: 10rpx;
  background: #e3eef8;
  overflow: hidden;
}

.bar-inner,
.area-bar-inner {
  height: 100%;
  border-radius: 10rpx;
}

.bar-inner.blue {
  background: linear-gradient(90deg, #5bb3ff, #6cc7ff);
}

.bar-inner.green,
.area-bar-inner {
  background: linear-gradient(90deg, #55d69f, #72dfc7);
}

.bar-inner.amber {
  background: linear-gradient(90deg, #ffc45a, #ffdb82);
}

.grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
}

.metric-card {
  padding: 20rpx;
}

.metric-value {
  display: block;
  margin-top: 10rpx;
  color: #1f2d3c;
  font-size: 42rpx;
  font-weight: 900;
}

.metric-desc {
  display: block;
  margin-top: 8rpx;
  color: #71879f;
  font-size: 22rpx;
}

.panel {
  margin-top: 18rpx;
  padding: 24rpx;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  color: #1d2f44;
  font-size: 30rpx;
  font-weight: 900;
}

.trend-chart {
  margin-top: 20rpx;
  height: 250rpx;
  border-radius: 20rpx;
  background: #f6fbff;
  border: 1px solid #dceafa;
  position: relative;
  overflow: hidden;
}

.chart-line {
  position: absolute;
  left: 24rpx;
  right: 24rpx;
  top: 18rpx;
  bottom: 58rpx;
  background-image: linear-gradient(to bottom, rgba(59, 118, 176, 0.12) 1px, transparent 1px);
  background-size: 100% 44rpx;
}

.trend-point {
  position: absolute;
  width: 18rpx;
  height: 18rpx;
  margin-left: -9rpx;
  margin-bottom: -9rpx;
  border-radius: 50%;
  background: #3d9df4;
  box-shadow: 0 0 0 8rpx rgba(61, 157, 244, 0.13);
}

.trend-axis {
  position: absolute;
  left: 22rpx;
  right: 22rpx;
  bottom: 14rpx;
  display: flex;
  justify-content: space-between;
}

.trend-axis text {
  color: #71879f;
  font-size: 20rpx;
}

.area-row {
  display: grid;
  grid-template-columns: 170rpx 1fr 56rpx;
  gap: 14rpx;
  align-items: center;
  margin-top: 18rpx;
}

.area-name {
  color: #1d2f44;
  font-size: 24rpx;
  font-weight: 700;
}

.area-score {
  text-align: right;
  color: #1277c7;
  font-size: 24rpx;
  font-weight: 800;
}

.analysis-item,
.event-card {
  margin-top: 12rpx;
  padding: 16rpx;
  border-radius: 16rpx;
  background: #f7fbff;
  border: 1px solid #dceafa;
  color: #38506a;
  font-size: 24rpx;
  line-height: 1.5;
}

.event-card {
  display: flex;
  justify-content: space-between;
  gap: 14rpx;
}

.event-time {
  color: #1277c7;
  font-size: 23rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.event-text {
  flex: 1;
  text-align: right;
  color: #38506a;
}
</style>
