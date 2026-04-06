<template>
  <view class="env-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="title-row">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="title">环境质量检测</text>
    </view>

    <view class="picker-card">
      <text class="label">监测点</text>
      <picker :range="monitorNames" :value="currentIndex" @change="onMonitorChange">
        <view class="picker-value">{{ currentMonitor ? currentMonitor.name : '请选择监测点' }}</view>
      </picker>
    </view>

    <view class="grid" v-if="weather">
      <view class="metric-card">
        <text class="metric-name">温度</text>
        <text class="metric-value">{{ weather.temperature }}°C</text>
      </view>
      <view class="metric-card">
        <text class="metric-name">湿度</text>
        <text class="metric-value">{{ weather.humidity }}%</text>
      </view>
      <view class="metric-card full">
        <text class="metric-name">天气</text>
        <text class="metric-value">{{ weather.weather || '-' }}</text>
      </view>
      <view class="metric-card full">
        <text class="metric-name">更新时间</text>
        <text class="metric-value small">{{ weather.createTime || '-' }}</text>
      </view>
    </view>

    <view class="empty" v-else>暂无环境数据</view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarHeight: 0,
      monitors: [],
      currentIndex: 0,
      weather: null,
    };
  },
  computed: {
    monitorNames() {
      return this.monitors.map((item) => item.name || `监测点${item.id}`);
    },
    currentMonitor() {
      return this.monitors[this.currentIndex] || null;
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.initData();
  },
  methods: {
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/manage/controls/controls' });
      }
    },
    async initData() {
      const { data } = await uni.$http.get('/api/v1/monitor');
      this.monitors = (data && data.data) || [];
      if (this.monitors.length) {
        this.currentIndex = 0;
        this.getWeather(this.monitors[0].id);
      } else {
        this.weather = null;
      }
    },
    async getWeather(monitorId) {
      const { data } = await uni.$http.get(`/api/v1/weather/newest/${monitorId}`);
      this.weather = (data && data.data) || null;
    },
    onMonitorChange(e) {
      this.currentIndex = Number(e.detail.value || 0);
      const monitor = this.currentMonitor;
      if (monitor) {
        this.getWeather(monitor.id);
      }
    },
  },
};
</script>

<style scoped lang="scss">
.env-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eaf5ff 0%, #f7fbff 100%);
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
  color: #1f2d3c;
  font-size: 42rpx;
  font-weight: 800;
}

.picker-card {
  background: #f9fcff;
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
}

.label {
  font-size: 24rpx;
  color: #6f8093;
}

.picker-value {
  margin-top: 10rpx;
  padding: 14rpx 16rpx;
  border-radius: 12rpx;
  background: #edf6ff;
  color: #1f2d3c;
  font-size: 28rpx;
  font-weight: 600;
}

.grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
}

.metric-card {
  background: #f9fcff;
  border-radius: 18rpx;
  padding: 20rpx;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
}

.metric-card.full {
  grid-column: span 2;
}

.metric-name {
  font-size: 24rpx;
  color: #6f8093;
}

.metric-value {
  margin-top: 10rpx;
  color: #1f2d3c;
  font-size: 38rpx;
  font-weight: 800;
}

.metric-value.small {
  font-size: 26rpx;
  font-weight: 600;
}

.empty {
  margin-top: 40rpx;
  text-align: center;
  font-size: 26rpx;
  color: #8da0b5;
}
</style>
