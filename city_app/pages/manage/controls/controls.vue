<template>
  <view class="home-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="hero-card">
      <view class="hero-left">
        <view class="hero-title">智慧安防</view>
        <view class="hero-sub">管理端控制台</view>
      </view>
      <view class="hero-badge" @tap="jumpSetting">切换</view>
    </view>

    <view class="quick-grid">
      <view class="quick-item" @tap="goPage('/pages/manage/statistics/index')">
        <view class="quick-icon">警</view>
        <text>警情统计</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/ai/index')">
        <view class="quick-icon">A</view>
        <text>AI</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/property/parking/index')">
        <view class="quick-icon">位</view>
        <text>车位</text>
      </view>
      <view class="quick-item" @tap="goPage('/pages/manage/environment/index')">
        <view class="quick-icon">环</view>
        <text>环境</text>
      </view>
    </view>

    <view class="section-card map-card" @tap="goPage('/pages/manage/monitor/map')">
      <view class="section-head">
        <text class="section-title">监控地图</text>
        <text class="map-link">查看摄像头 ></text>
      </view>
      <view class="map-wrap">
        <MonitorMap :monitorList="monitorList" :compact="true" />
      </view>
    </view>

    <view class="section-card alert-card">
      <view class="section-head">
        <text class="section-title">待处理警情</text>
        <view class="all-link" @tap="goPage('/pages/manage/realtime/realtime')">全部警情 ></view>
      </view>

      <view class="level-overview">
        <view class="level-box urgent">
          <text class="level-name">紧急</text>
          <text class="level-count">{{ levelCount.urgent }}</text>
        </view>
        <view class="level-box serious">
          <text class="level-name">严重</text>
          <text class="level-count">{{ levelCount.serious }}</text>
        </view>
        <view class="level-box normal">
          <text class="level-name">一般</text>
          <text class="level-count">{{ levelCount.normal }}</text>
        </view>
      </view>

      <view class="alert-list">
        <view class="alert-item" v-for="item in displayAlerts" :key="item.id" @tap="goDetail(item.id)">
          <view class="dot" :class="levelClass(item)"></view>
          <view class="alert-main">
            <view class="alert-title-row">
              <text class="alert-title">{{ item.eventName || item.name || '未知警情' }}</text>
              <text class="level-tag" :class="levelClass(item)">{{ levelText(item) }}</text>
            </view>
            <view class="alert-meta">{{ item.department || '-' }} · {{ item.date || '-' }}</view>
          </view>
        </view>

        <view class="empty" v-if="!displayAlerts.length">暂无待处理警情</view>
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
    };
  },
  computed: {
    displayAlerts() {
      return this.alarms.slice(0, 10);
    },
    levelCount() {
      const data = { urgent: 0, serious: 0, normal: 0 };
      this.displayAlerts.forEach((item) => {
        const level = Number(item.level) || 3;
        if (level <= 1) data.urgent += 1;
        else if (level === 2) data.serious += 1;
        else data.normal += 1;
      });
      return data;
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
        pageSize: 10,
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
      uni.navigateTo({
        url: `/pages/manage/realtime/detail?id=${id}`,
      });
    },
    jumpSetting() {
      uni.navigateTo({
        url: "/pages/manage/personal/setting/setting",
      });
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
  background: linear-gradient(180deg, #eaf5ff 0%, #f7fbff 100%);
}

.hero-card {
  margin-top: 10rpx;
  border-radius: 28rpx;
  background: linear-gradient(120deg, #f9fcff 0%, #ddeeff 100%);
  padding: 26rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10rpx 28rpx rgba(64, 124, 192, 0.14);
}

.hero-title {
  color: #1470d8;
  font-size: 54rpx;
  font-weight: 900;
  line-height: 1.05;
}

.hero-sub {
  margin-top: 10rpx;
  color: #315c86;
  font-size: 26rpx;
  font-weight: 600;
}

.hero-badge {
  color: #1e81e9;
  font-size: 26rpx;
  font-weight: 700;
}

.quick-grid {
  margin-top: 20rpx;
  background: #ecf6ff;
  border-radius: 24rpx;
  padding: 18rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14rpx;
}

.quick-item {
  background: #f9fcff;
  border-radius: 18rpx;
  height: 142rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8rpx 20rpx rgba(52, 117, 185, 0.1);

  text {
    margin-top: 10rpx;
    color: #27486a;
    font-size: 26rpx;
    font-weight: 700;
  }
}

.quick-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  background: linear-gradient(140deg, #38b6ff 0%, #187cff 100%);
  color: #fff;
  font-size: 30rpx;
  font-weight: 800;
  display: flex;
  justify-content: center;
  align-items: center;
}

.section-card {
  margin-top: 18rpx;
  border-radius: 24rpx;
  background: #f8fbff;
  box-shadow: 0 10rpx 24rpx rgba(40, 91, 150, 0.1);
  padding: 20rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  color: #1e2d3d;
  font-size: 36rpx;
  font-weight: 800;
}

.map-wrap {
  margin-top: 12rpx;
  height: 330rpx;
  border-radius: 18rpx;
  overflow: hidden;
}

.map-link {
  color: #7f8da3;
  font-size: 24rpx;
  font-weight: 700;
}

.all-link {
  color: #7f8da3;
  font-size: 28rpx;
  font-weight: 700;
}

.level-overview {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
}

.level-box {
  border-radius: 16rpx;
  background: #f3f7fd;
  padding: 14rpx 10rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.level-name {
  font-size: 26rpx;
  color: #34485f;
  font-weight: 700;
}

.level-count {
  font-size: 30rpx;
  font-weight: 900;
}

.level-box.urgent .level-count { color: #ef4444; }
.level-box.serious .level-count { color: #f59e0b; }
.level-box.normal .level-count { color: #22c55e; }

.level-tag.urgent,
.dot.urgent { background-color: #ef4444; }

.level-tag.serious,
.dot.serious { background-color: #f59e0b; }

.level-tag.normal,
.dot.normal { background-color: #22c55e; }

.alert-list {
  margin-top: 12rpx;
}

.alert-item {
  border-top: 1px solid #e8edf5;
  padding: 14rpx 4rpx;
  display: flex;
  align-items: flex-start;
}

.dot {
  margin-top: 14rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 7rpx;
  margin-right: 12rpx;
}

.alert-main {
  flex: 1;
}

.alert-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-title {
  color: #1f2d3c;
  font-size: 29rpx;
  font-weight: 700;
  padding-right: 10rpx;
}

.level-tag {
  font-size: 22rpx;
  font-weight: 700;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  color: #fff;
}

.alert-meta {
  margin-top: 6rpx;
  color: #7f8da3;
  font-size: 23rpx;
}

.empty {
  text-align: center;
  color: #96a5b8;
  font-size: 24rpx;
  padding: 20rpx 0;
}
</style>
