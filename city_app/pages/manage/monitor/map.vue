<template>
  <view class="map-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="top-title">监控地图</text>
      <view class="top-placeholder"></view>
    </view>
    <view class="map-panel" :class="{ 'map-panel--with-detail': showDetail }">
      <MonitorMap
        :monitorList="filteredList"
        :alarmList="alarms"
        :pulseTick="mapPulseTick"
        :compact="true"
        @point-click="openPointDetail"
      />
    </view>

    <view class="detail-sheet" v-if="showDetail">
      <view class="detail-head">
        <text class="detail-title">监控详情</text>
        <view class="detail-close" @tap="closePointDetail">关闭</view>
      </view>

      <view class="detail-name">{{ activePoint.camera || activePoint.name || '未命名摄像头' }}</view>
      <view class="detail-area">{{ activePoint.department || activePoint.area || '未标注区域' }}</view>

      <view class="detail-grid">
        <view class="detail-item">
          <text class="detail-label">状态</text>
          <text class="detail-value" :class="activePoint.hasAlert ? 'is-alert' : 'is-safe'">
            {{ activePoint.hasAlert ? '有告警' : '正常' }}
          </text>
        </view>
        <view class="detail-item">
          <text class="detail-label">告警数</text>
          <text class="detail-value">{{ activePoint.alarmCount || 0 }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">经度</text>
          <text class="detail-value">{{ formatCoord(activePoint.longitude) }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">纬度</text>
          <text class="detail-value">{{ formatCoord(activePoint.latitude) }}</text>
        </view>
      </view>

      <view class="detail-alert" v-if="activePoint.hasAlert">
        <text class="detail-alert__label">最新告警</text>
        <text class="detail-alert__text">{{ activePoint.latestAlarm ? (activePoint.latestAlarm.eventName || activePoint.latestAlarm.caseTypeName || '警情告警') : '暂无最新告警' }}</text>
      </view>
    </view>

    <view class="list-panel">
      <view class="search-row">
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索摄像头名称/区域"
          @input="onSearch"
        />
      </view>

      <view class="camera-list">
        <view class="camera-item" v-for="item in pagedList" :key="item.id" @tap="openVideo(item)">
          <view class="name-row">
            <text class="name">{{ item.name || '未命名摄像头' }}</text>
            <text class="status" :class="item.running ? 'on' : 'off'">{{ item.running ? '在线' : '离线' }}</text>
          </view>
          <view class="meta">{{ item.department || item.area || '-' }}</view>
        </view>
        <view class="empty" v-if="!pagedList.length">当前页暂无摄像头</view>
      </view>

      <view class="pager">
        <view class="page-btn" @tap="prevPage">上一页</view>
        <text class="page-text">{{ pageNum }} / {{ totalPage }}</text>
        <view class="page-btn" @tap="nextPage">下一页</view>
      </view>
    </view>
  </view>
</template>

<script>
import MonitorMap from "../controls/components/monitorMap.vue";

export default {
  components: { MonitorMap },
  data() {
    return {
      statusBarHeight: 0,
      monitors: [],
      alarms: [],
      keyword: "",
      pageNum: 1,
      pageSize: 3,
      mapPulseTick: 0,
      alarmRefreshTimer: null,
      monitorRefreshTimer: null,
      mapPulseTimer: null,
      showDetail: false,
      activePoint: {},
    };
  },
  computed: {
    filteredList() {
      const k = this.keyword.trim().toLowerCase();
      if (!k) return this.monitors;
      return this.monitors.filter((item) => {
        const name = (item.name || "").toLowerCase();
        const area = (item.department || item.area || "").toLowerCase();
        return name.includes(k) || area.includes(k);
      });
    },
    totalPage() {
      return Math.max(1, Math.ceil(this.filteredList.length / this.pageSize));
    },
    pagedList() {
      const start = (this.pageNum - 1) * this.pageSize;
      return this.filteredList.slice(start, start + this.pageSize);
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.startRealtimeMap();
  },
  onHide() {
    this.stopRealtimeMap();
  },
  onUnload() {
    this.stopRealtimeMap();
  },
  methods: {
    startRealtimeMap() {
      this.stopRealtimeMap();
      this.getMonitors();
      this.getPendingAlerts();

      this.alarmRefreshTimer = setInterval(() => {
        this.getPendingAlerts();
      }, 10000);

      this.monitorRefreshTimer = setInterval(() => {
        this.getMonitors();
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
    },
    isVisibleAlarm(item) {
      return ![6, 9, 13].includes(Number(item && item.caseType));
    },
    isPendingAlarm(item) {
      if (!item) return false;
      const status = Number(item.status);
      return status === 0 || item.deal === '未处理';
    },
    isPendingAlarmVisible(item) {
      return this.isVisibleAlarm(item) && this.isPendingAlarm(item);
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
    async getMonitors() {
      try {
        const { data: monitorRes } = await uni.$http.get('/api/v1/monitor');
        const monitorList = (monitorRes && monitorRes.data) || [];

        let monitorPosList = [];
        try {
          const { data: mapRes } = await uni.$http.get('/api/v1/monitor/map');
          const mapData = (mapRes && mapRes.data) || {};
          monitorPosList = Array.isArray(mapData) ? mapData : mapData.monitorPosList || [];
        } catch (mapError) {
          console.warn("[monitor-map] 获取监控坐标失败：", mapError);
        }

        this.monitors = this.mergeMonitorPosition(monitorList, monitorPosList);
        this.pageNum = 1;
      } catch (error) {
        console.warn("[monitor-map] 获取监控地图信息失败：", error);
      }
    },
    async getPendingAlerts() {
      try {
        const query = {
          pageNum: 1,
          pageSize: 100,
          status: 0,
        };
        const { data } = await uni.$http.get("/api/v1/alarm/query", query);
        const list = (data && data.data && data.data.alarmList) || [];
        this.alarms = list.filter(this.isPendingAlarmVisible);
      } catch (error) {
        console.warn("[monitor-map] 获取实时警情失败：", error);
      }
    },
    onSearch() {
      this.pageNum = 1;
    },
    prevPage() {
      this.pageNum = Math.max(1, this.pageNum - 1);
    },
    nextPage() {
      this.pageNum = Math.min(this.totalPage, this.pageNum + 1);
    },
    openPointDetail(point) {
      if (!point) return;
      this.activePoint = point;
      this.showDetail = true;
    },
    closePointDetail() {
      this.showDetail = false;
    },
    formatCoord(value) {
      const num = Number(value);
      if (!Number.isFinite(num)) return '-';
      return num.toFixed(6);
    },
    openVideo(item) {
      const videoUrl = item.video || item.ip || '';
      if (!videoUrl) {
        uni.showToast({ title: '该设备暂无视频地址', icon: 'none' });
        return;
      }
      uni.navigateTo({
        url: `/pages/manage/monitor/video?id=${item.id || ''}&name=${encodeURIComponent(item.name || '')}&video=${encodeURIComponent(videoUrl)}`,
      });
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/manage/controls/controls' });
      }
    },
  },
};
</script>

<style scoped lang="scss">
.map-page {
  height: 100vh;
  background: linear-gradient(180deg, #eaf5ff 0%, #f7fbff 100%);
  padding: 0 20rpx 20rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.top-bar {
  flex-shrink: 0;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.back-btn {
  width: 64rpx;
  height: 64rpx;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 14rpx rgba(45, 98, 160, 0.16);
}

.top-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #1a2a3a;
}

.top-placeholder {
  width: 64rpx;
  height: 64rpx;
}

.map-panel {
  height: 48vh;
  border-radius: 18rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
  flex-shrink: 0;
}

.map-panel--with-detail {
  height: 36vh;
}

.detail-sheet {
  flex-shrink: 0;
  margin-top: 14rpx;
  padding: 18rpx 20rpx 20rpx;
  border-radius: 18rpx;
  background: #fff;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.detail-title {
  font-size: 28rpx;
  font-weight: 800;
  color: #1a2a3a;
}

.detail-close {
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: #edf6ff;
  color: #1470d8;
  font-size: 22rpx;
}

.detail-name {
  font-size: 28rpx;
  font-weight: 800;
  color: #1a2a3a;
  line-height: 1.35;
}

.detail-area {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #64748b;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10rpx;
  margin-top: 14rpx;
}

.detail-item {
  padding: 12rpx;
  background: #f8fbff;
  border-radius: 14rpx;
}

.detail-label {
  display: block;
  font-size: 19rpx;
  color: #94a3b8;
}

.detail-value {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: #1a2a3a;
}

.detail-value.is-alert {
  color: #dc2626;
}

.detail-value.is-safe {
  color: #16a34a;
}

.detail-alert {
  margin-top: 12rpx;
  padding: 14rpx;
  border-radius: 14rpx;
  background: #fff1f2;
  color: #b91c1c;
}

.detail-alert__label {
  display: block;
  font-size: 19rpx;
  font-weight: 700;
  opacity: 0.8;
}

.detail-alert__text {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.list-panel {
  flex: 1;
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.search-row {
  margin-bottom: 14rpx;
}

.search-input {
  width: 100%;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  background: #fff;
  border-radius: 18rpx;
  box-shadow: 0 4rpx 12rpx rgba(45, 98, 160, 0.08);
}

.camera-list {
  flex: 1;
  overflow: auto;
}

.camera-item {
  padding: 18rpx 20rpx;
  background: #fff;
  border-radius: 18rpx;
  margin-bottom: 14rpx;
  box-shadow: 0 4rpx 12rpx rgba(45, 98, 160, 0.08);
}

.name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.name {
  font-size: 28rpx;
  font-weight: 700;
  color: #1a2a3a;
}

.status {
  font-size: 20rpx;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.status.on {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
}

.status.off {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.1);
}

.meta {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #64748b;
}

.empty {
  text-align: center;
  padding: 40rpx 0;
  color: #94a3b8;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14rpx 0 0;
}

.page-btn {
  min-width: 120rpx;
  text-align: center;
  padding: 14rpx 20rpx;
  background: linear-gradient(135deg, #1470d8 0%, #38a4ff 100%);
  color: #fff;
  border-radius: 16rpx;
  font-size: 24rpx;
}

.page-text {
  font-size: 24rpx;
  color: #475569;
}
</style>
