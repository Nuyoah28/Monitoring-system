<template>
  <view class="env-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <!-- 顶部标题栏 -->
    <view class="title-row">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="title">环境质量检测</text>
    </view>

    <!-- 监测点选择 -->
    <view class="picker-card">
      <text class="label">监测点选择</text>
      <picker :range="monitorNames" :value="currentIndex" @change="onMonitorChange">
        <view class="picker-value">
          <u-icon name="map-pin" color="#409df8" size="28rpx"></u-icon>
          {{ currentMonitor ? currentMonitor.name : '请选择监测点' }}
        </view>
      </picker>
    </view>

    <!-- 空气质量等级卡片 -->
    <view class="quality-card" v-if="weather">
      <view class="quality-left">
        <text class="quality-tag" :class="aqiLevel.class">{{ aqiLevel.text }}</text>
        <text class="quality-desc">{{ aqiLevel.desc }}</text>
      </view>
      <view class="quality-right">
        <text class="aqi-value">{{ weather.aqi || '-' }}</text>
        <text class="aqi-label">AQI指数</text>
      </view>
    </view>

    <!-- 环境数据网格 -->
    <view class="grid" v-if="weather">
      <view class="metric-card">
        <view class="metric-icon">
          <u-icon name="sun" color="#ff9c28" size="36rpx"></u-icon>
        </view>
        <text class="metric-name">温度</text>
        <text class="metric-value">{{ weather.temperature }}°C</text>
      </view>

      <view class="metric-card">
        <view class="metric-icon">
          <u-icon name="water" color="#409df8" size="36rpx"></u-icon>
        </view>
        <text class="metric-name">湿度</text>
        <text class="metric-value">{{ weather.humidity }}%</text>
      </view>

      <view class="metric-card">
        <view class="metric-icon">
          <u-icon name="cloud" color="#6cc3fc" size="36rpx"></u-icon>
        </view>
        <text class="metric-name">天气</text>
        <text class="metric-value">{{ weather.weather || '-' }}</text>
      </view>

      <view class="metric-card">
        <view class="metric-icon">
          <u-icon name="wind" color="#56c999" size="36rpx"></u-icon>
        </view>
        <text class="metric-name">PM2.5</text>
        <text class="metric-value">{{ weather.pm25 || '-' }}μg/m³</text>
      </view>

      <view class="metric-card full">
        <view class="metric-icon">
          <u-icon name="clock" color="#8e9cad" size="32rpx"></u-icon>
        </view>
        <text class="metric-name">数据更新时间</text>
        <text class="metric-value small">{{ weather.createTime || '-' }}</text>
      </view>
    </view>

    <!-- 健康提示 -->
    <view class="tip-card" v-if="weather">
      <view class="tip-header">
        <u-icon name="info-circle" color="#409df8" size="28rpx"></u-icon>
        <text class="tip-title">健康出行提示</text>
      </view>
      <text class="tip-content">{{ healthTip }}</text>
    </view>

    <!-- 空状态 -->
    <view class="empty-box" v-else>
      <u-icon name="inbox" color="#c0c6d1" size="80rpx"></u-icon>
      <text class="empty-text">暂无环境监测数据</text>
      <text class="empty-desc">请选择其他监测点或稍后重试</text>
    </view>
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
    // 监测点名称数组
    monitorNames() {
      return this.monitors.map((item) => item.name || `监测点${item.id}`);
    },
    // 当前选中监测点
    currentMonitor() {
      return this.monitors[this.currentIndex] || null;
    },
    // AQI空气质量等级
    aqiLevel() {
      const aqi = Number(this.weather?.aqi) || 0;
      if (aqi <= 50) {
        return { class: 'level-excellent', text: '优', desc: '空气质量令人满意' };
      } else if (aqi <= 100) {
        return { class: 'level-good', text: '良', desc: '空气质量可接受' };
      } else if (aqi <= 150) {
        return { class: 'level-light', text: '轻度污染', desc: '敏感人群减少外出' };
      } else if (aqi <= 200) {
        return { class: 'level-moderate', text: '中度污染', desc: '一般人群减少外出' };
      } else {
        return { class: 'level-heavy', text: '重度污染', desc: '避免外出活动' };
      }
    },
    // 健康提示语
    healthTip() {
      const aqi = Number(this.weather?.aqi) || 0;
      const temp = Number(this.weather?.temperature) || 25;
      
      if (aqi <= 100) {
        return `当前空气质量良好，气温${temp}℃，适宜户外活动与开窗通风。`;
      } else if (aqi <= 150) {
        return `空气质量轻度污染，老人、儿童及敏感人群建议减少长时间户外逗留。`;
      } else if (aqi <= 200) {
        return `空气质量中度污染，建议关闭门窗，外出请佩戴口罩，减少户外活动。`;
      } else {
        return `空气质量重度污染，强烈建议避免外出，关闭门窗并开启空气净化设备。`;
      }
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
    // 返回上一页
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/manage/controls/controls' });
      }
    },
    // 初始化监测点数据
    async initData() {
      try {
        const { data } = await uni.$http.get('/api/v1/monitor');
        this.monitors = (data && data.data) || [];
        if (this.monitors.length) {
          this.currentIndex = 0;
          this.getWeather(this.monitors[0].id);
        } else {
          this.weather = null;
        }
      } catch (error) {
        this.weather = null;
        uni.showToast({ title: '数据加载失败', icon: 'none' });
      }
    },
    // 获取最新环境数据
    async getWeather(monitorId) {
      try {
        const { data } = await uni.$http.get(`/api/v1/weather/newest/${monitorId}`);
        this.weather = (data && data.data) || null;
      } catch (error) {
        this.weather = null;
        uni.showToast({ title: '环境数据获取失败', icon: 'none' });
      }
    },
    // 切换监测点
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
  padding: 0 24rpx 60rpx;
  box-sizing: border-box;
}

// 标题栏
.title-row {
  margin: 10rpx 0 24rpx;
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
  font-size: 44rpx;
  font-weight: 800;
}

// 选择器卡片
.picker-card {
  background: #f9fcff;
  border-radius: 20rpx;
  padding: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
  margin-bottom: 20rpx;
}

.label {
  font-size: 26rpx;
  color: #6f8093;
  font-weight: 500;
}

.picker-value {
  margin-top: 12rpx;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;
  background: #edf6ff;
  color: #1f2d3c;
  font-size: 28rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

// 空气质量等级卡片
.quality-card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 28rpx 24rpx;
  box-shadow: 0 8rpx 24rpx rgba(45, 98, 160, 0.12);
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.quality-left {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.quality-tag {
  font-size: 32rpx;
  font-weight: 700;
  padding: 6rpx 16rpx;
  border-radius: 30rpx;
  display: inline-block;
}

.level-excellent {
  background: #e6f7ef;
  color: #00b47d;
}
.level-good {
  background: #fff7e6;
  color: #ff8f23;
}
.level-light {
  background: #fff1f0;
  color: #ff6666;
}
.level-moderate {
  background: #fce6ef;
  color: #e63975;
}
.level-heavy {
  background: #f5e6f7;
  color: #b139c7;
}

.quality-desc {
  font-size: 24rpx;
  color: #6f8093;
}

.quality-right {
  text-align: right;
}

.aqi-value {
  font-size: 48rpx;
  font-weight: 800;
  color: #1f2d3c;
  line-height: 1;
}

.aqi-label {
  font-size: 22rpx;
  color: #8da0b5;
}

// 数据网格
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.metric-card {
  background: #ffffff;
  border-radius: 18rpx;
  padding: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.metric-card.full {
  grid-column: span 2;
}

.metric-icon {
  margin-bottom: 4rpx;
}

.metric-name {
  font-size: 24rpx;
  color: #6f8093;
  font-weight: 500;
}

.metric-value {
  color: #1f2d3c;
  font-size: 36rpx;
  font-weight: 800;
}

.metric-value.small {
  font-size: 26rpx;
  font-weight: 600;
}

// 健康提示卡片
.tip-card {
  background: linear-gradient(90deg, #edf6ff 0%, #f5f9ff 100%);
  border-radius: 20rpx;
  padding: 24rpx;
  border: 1rpx solid #d6e9ff;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 12rpx;
}

.tip-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #3a4a5e;
}

.tip-content {
  font-size: 25rpx;
  color: #5a6b80;
  line-height: 1.5;
}

// 空状态
.empty-box {
  margin-top: 80rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #8da0b5;
  font-weight: 500;
}

.empty-desc {
  font-size: 24rpx;
  color: #b0bfd1;
}
</style>