<template>
  <scroll-view scroll-y class="feature-page" :style="{ paddingTop: pageTopPadding + 'px' }">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="title-box">
        <view class="top-title">车位检测管理</view>
        <view class="top-subtitle">实时掌握社区车位运行情况</view>
      </view>
    </view>

    <view class="status-strip panel">
      <view class="status-icon" :class="isLoading ? 'syncing' : ''">
        <view class="status-core"></view>
      </view>
      <view class="status-copy">
        <view class="status-title">{{ statusTitle }}</view>
        <view class="status-desc">最近更新：{{ formattedUpdateTime }}</view>
      </view>
    </view>

    <view class="overview panel">
      <view class="overview-head">
        <view>
          <view class="panel-title">车位检测总览</view>
          <view class="sub-text">根据各区域检测结果汇总当前占用情况</view>
        </view>
        <view class="rate-pill" :class="rateClass(parkingRate)">
          {{ parkingRate }}%
        </view>
      </view>
      <view class="stats-grid">
        <view class="stat-cell">
          <text class="stat-label">总车位</text>
          <text class="stat-value">{{ parkingSummary.total }}</text>
        </view>
        <view class="stat-cell">
          <text class="stat-label">已占用</text>
          <text class="stat-value occupied">{{ parkingSummary.occupied }}</text>
        </view>
        <view class="stat-cell">
          <text class="stat-label">空闲</text>
          <text class="stat-value free">{{ parkingSummary.free }}</text>
        </view>
      </view>
    </view>

    <view class="traffic-card panel">
      <view class="panel-head">
        <view>
          <view class="panel-title">车流量检测</view>
          <view class="sub-text">算法上报入口、出口与净流入</view>
        </view>
        <view class="traffic-badge">{{ trafficSourceLabel }}</view>
      </view>
      <view class="traffic-main">
        <view class="traffic-total">
          <text class="traffic-label">今日总车流</text>
          <text class="traffic-value">{{ trafficSummary.todayTotalFlow }}</text>
        </view>
        <view class="traffic-side">
          <view class="traffic-mini">
            <text>入口</text>
            <strong>{{ trafficSummary.todayInCount }}</strong>
          </view>
          <view class="traffic-mini">
            <text>出口</text>
            <strong>{{ trafficSummary.todayOutCount }}</strong>
          </view>
          <view class="traffic-mini">
            <text>净流入</text>
            <strong>{{ trafficSummary.todayNetFlow }}</strong>
          </view>
        </view>
      </view>
      <view class="traffic-footer">
        <text>最近一批</text>
        <text>入 {{ trafficSummary.latestInCount }} · 出 {{ trafficSummary.latestOutCount }}</text>
      </view>
    </view>

    <view class="focus-grid">
      <view class="focus-card panel">
        <view class="focus-label">重点关注区域</view>
        <view class="focus-title">{{ tightestArea.location }}</view>
        <view class="focus-meta">占用率 {{ tightestArea.rate }}% · {{ tightestArea.statusText }}</view>
      </view>
      <view class="focus-card panel soft">
        <view class="focus-label">空位最多区域</view>
        <view class="focus-title">{{ freestArea.location }}</view>
        <view class="focus-meta">剩余 {{ freestArea.free }} 位，可作为调度参考</view>
      </view>
    </view>

    <view class="panel map-panel">
      <view class="panel-head">
        <view>
          <view class="panel-title">区域检测状态</view>
          <view class="sub-text">按区域展示占用比例和紧张程度</view>
        </view>
        <view class="legend-row">
          <view class="legend"><text class="dot free-dot"></text>空闲</view>
          <view class="legend"><text class="dot occupied-dot"></text>占用</view>
          <view class="legend"><text class="dot tight-dot"></text>紧张</view>
        </view>
      </view>

      <view v-if="!parkingAreas.length" class="empty">暂无车位检测数据。</view>
      <view v-else class="parking-map">
        <view v-for="area in parkingAreas" :key="area.id" class="area-block" :class="rateClass(area.rate)">
          <view class="area-head">
            <view>
              <view class="area-name">{{ area.location }}</view>
              <view class="area-meta">
                已用 {{ area.occupied }}/{{ area.total }} · 空闲 {{ area.free }}
              </view>
            </view>
            <view class="area-rate" :class="rateClass(area.rate)">
              {{ area.rate }}%
            </view>
          </view>

          <view class="slot-grid">
            <view
              v-for="slot in area.slots"
              :key="slot.no"
              class="slot"
              :class="{ busy: slot.busy, tight: area.rate >= 85 && !slot.busy }"
            ></view>
          </view>

          <view class="area-footer">
            <view class="status-tag" :class="rateClass(area.rate)">{{ area.statusText }}</view>
            <view class="area-code">区域编码：{{ area.areaCode }}</view>
          </view>
          <view class="progress">
            <view class="progress-inner" :class="rateClass(area.rate)" :style="{ width: area.rate + '%' }"></view>
          </view>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script>
import { DEMO_FALLBACK_ENABLED, createDemoParkingRealtime, createDemoParkingTraffic } from '@/common/owner-demo-data.js';

const SUCCESS_CODE = '00000';
const PARKING_DATA_SOURCE = 'real';
const DEFAULT_MONITOR_ID = 1;
const AUTO_REFRESH_MS = 12000;

export default {
  data() {
    return {
      statusBarHeight: 0,
      monitorId: DEFAULT_MONITOR_ID,
      dataSource: PARKING_DATA_SOURCE,
      realtimeData: null,
      trafficData: null,
      updateTime: '',
      isLoading: false,
      refreshTimer: null,
      hasLoaded: false,
      requestLock: false,
      silentFailCount: 0,
    };
  },
  computed: {
    pageTopPadding() {
      return this.statusBarHeight + 14;
    },
    statusTitle() {
      if (this.isLoading && !this.hasLoaded) return '正在获取车位状态';
      if (this.dataSource === 'mock' || this.dataSource === 'local-demo') return '演示车位检测数据已更新';
      if (this.silentFailCount > 0) return '车位状态待更新';
      return '车位检测运行中';
    },
    formattedUpdateTime() {
      return this.updateTime || '--';
    },
    parkingAreas() {
      const zones = (this.realtimeData && Array.isArray(this.realtimeData.zones))
        ? this.realtimeData.zones
        : [];
      return zones.map((item, index) => {
        const total = Math.max(0, Number(item.totalSpaces || 0));
        const occupied = Math.min(total, Math.max(0, Number(item.occupiedSpaces || 0)));
        const free = Math.max(0, total - occupied);
        const rate = total ? Math.round((occupied / total) * 100) : 0;
        return {
          id: item.areaCode || `area-${index}`,
          areaCode: item.areaCode || `AREA-${index + 1}`,
          location: item.areaName || `车位区域${index + 1}`,
          total,
          occupied,
          free,
          rate,
          statusText: this.rateText(rate),
          slots: this.buildSlots(total, occupied),
        };
      });
    },
    parkingSummary() {
      if (this.realtimeData && Number(this.realtimeData.totalSpaces) > 0) {
        return {
          total: Number(this.realtimeData.totalSpaces || 0),
          occupied: Number(this.realtimeData.occupiedSpaces || 0),
          free: Number(this.realtimeData.freeSpaces || 0),
        };
      }
      return this.parkingAreas.reduce(
        (sum, item) => ({
          total: sum.total + item.total,
          occupied: sum.occupied + item.occupied,
          free: sum.free + item.free,
        }),
        { total: 0, occupied: 0, free: 0 }
      );
    },
    parkingRate() {
      if (this.realtimeData && this.realtimeData.occupancyRate !== undefined) {
        return Number(this.realtimeData.occupancyRate || 0);
      }
      const total = this.parkingSummary.total;
      if (!total) return 0;
      return Math.round((this.parkingSummary.occupied / total) * 100);
    },
    tightestArea() {
      if (!this.parkingAreas.length) return this.emptyArea('暂无重点区域');
      return [...this.parkingAreas].sort((a, b) => b.rate - a.rate)[0];
    },
    freestArea() {
      if (!this.parkingAreas.length) return this.emptyArea('暂无空闲区域');
      return [...this.parkingAreas].sort((a, b) => b.free - a.free)[0];
    },
    trafficSummary() {
      const data = this.trafficData || {};
      return {
        todayInCount: Number(data.todayInCount || 0),
        todayOutCount: Number(data.todayOutCount || 0),
        todayNetFlow: Number(data.todayNetFlow || 0),
        todayTotalFlow: Number(data.todayTotalFlow || 0),
        latestInCount: Number(data.latestInCount || 0),
        latestOutCount: Number(data.latestOutCount || 0),
      };
    },
    trafficSourceLabel() {
      const source = this.trafficData && this.trafficData.source;
      return source === 'mock' || source === 'local-demo' ? '演示' : '实时';
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.startAutoRefresh();
  },
  onHide() {
    this.stopAutoRefresh();
  },
  onUnload() {
    this.stopAutoRefresh();
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    startAutoRefresh() {
      this.stopAutoRefresh();
      this.loadRealtimeParking();
      this.refreshTimer = setInterval(() => {
        this.loadRealtimeParking(false);
      }, AUTO_REFRESH_MS);
    },
    stopAutoRefresh() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
    },
    emptyArea(location) {
      return {
        id: 'empty',
        areaCode: '--',
        location,
        total: 0,
        occupied: 0,
        free: 0,
        rate: 0,
        statusText: '暂无数据',
        slots: [],
      };
    },
    rateClass(rate) {
      if (rate >= 95) return 'full';
      if (rate >= 85) return 'danger';
      if (rate >= 70) return 'warn';
      return 'normal';
    },
    rateText(rate) {
      if (rate >= 95) return '接近满载';
      if (rate >= 85) return '车位紧张';
      if (rate >= 70) return '较为繁忙';
      return '运行正常';
    },
    buildSlots(total, occupied) {
      const count = Math.min(24, Math.max(8, total || 8));
      const busyCount = total ? Math.round((occupied / total) * count) : 0;
      return Array.from({ length: count }, (_, index) => ({
        no: index + 1,
        busy: index < busyCount,
      }));
    },
    normalizeUpdateTime(value) {
      if (!value) return this.formatDate(new Date());
      return String(value).replace('T', ' ').slice(0, 19);
    },
    formatDate(date) {
      const pad = (num) => String(num).padStart(2, '0');
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/manage/controls/controls' });
    },
    async loadRealtimeParking(showLoading = true) {
      if (this.requestLock) return;
      this.requestLock = true;
      if (showLoading && !this.hasLoaded) this.isLoading = true;
      try {
        const realtime = await this.fetchRealtimeParking({
          monitorId: this.monitorId,
        }, !showLoading || this.hasLoaded);

        if (this.hasParkingData(realtime)) {
          this.applyRealtimeParking(realtime);
          await this.loadTrafficSummary(true);
          return;
        }

        if (DEMO_FALLBACK_ENABLED) {
          const mockRealtime = await this.fetchRealtimeParking({
            monitorId: this.monitorId,
            source: 'mock',
          }, true);
          this.applyRealtimeParking(this.hasParkingData(mockRealtime) ? mockRealtime : createDemoParkingRealtime(this.monitorId));
          await this.loadTrafficSummary(true);
          return;
        }

        if (!this.hasLoaded) uni.$showMsg('加载车位检测数据失败');
        this.silentFailCount += 1;
      } catch (e) {
        if (DEMO_FALLBACK_ENABLED) {
          this.applyRealtimeParking(createDemoParkingRealtime(this.monitorId));
          this.applyTrafficSummary(createDemoParkingTraffic(this.monitorId));
          return;
        }
        if (!this.hasLoaded) uni.$showMsg('网络异常，车位检测数据加载失败');
        this.silentFailCount += 1;
      } finally {
        this.isLoading = false;
        this.requestLock = false;
      }
    },
    async fetchRealtimeParking(params, silent = false) {
      try {
        const { data: res } = await uni.$http.get('/api/v1/parking/realtime', params, { silent });
        if (!this.isSuccess(res)) return null;
        return res.data || null;
      } catch (e) {
        return null;
      }
    },
    hasParkingData(data) {
      return Boolean(data && (Number(data.totalSpaces) > 0 || (Array.isArray(data.zones) && data.zones.length)));
    },
    applyRealtimeParking(data) {
      this.realtimeData = data || null;
      this.dataSource = (this.realtimeData && this.realtimeData.source) || this.dataSource;
      this.updateTime = this.normalizeUpdateTime(this.realtimeData && this.realtimeData.updateTime);
      this.hasLoaded = true;
      this.silentFailCount = 0;
    },
    async loadTrafficSummary(silent = true) {
      const traffic = await this.fetchTrafficSummary({
        monitorId: this.monitorId,
      }, silent);
      if (traffic) {
        this.applyTrafficSummary(traffic);
        return;
      }
      if (DEMO_FALLBACK_ENABLED) {
        const mockTraffic = await this.fetchTrafficSummary({
          monitorId: this.monitorId,
          source: 'mock',
        }, true);
        this.applyTrafficSummary(mockTraffic || createDemoParkingTraffic(this.monitorId));
      }
    },
    async fetchTrafficSummary(params, silent = false) {
      try {
        const { data: res } = await uni.$http.get('/api/v1/parking/traffic/summary', params, { silent });
        if (!this.isSuccess(res)) return null;
        return res.data || null;
      } catch (e) {
        return null;
      }
    },
    applyTrafficSummary(data) {
      this.trafficData = data || null;
    },
  },
};
</script>

<style lang="scss" scoped>
.feature-page {
  min-height: 100vh;
  padding: 0 24rpx 34rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #dceefa 0%, #f6fbff 58%, #ffffff 100%);
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 82rpx;
  margin: 18rpx 0 26rpx;
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

.title-box {
  flex: 1;
  min-width: 0;
  margin: 0 16rpx;
}

.top-title {
  font-size: 34rpx;
  font-weight: 900;
  color: #18304b;
}

.top-subtitle {
  margin-top: 4rpx;
  color: #66809b;
  font-size: 22rpx;
}

.panel {
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
  margin-bottom: 18rpx;
  box-sizing: border-box;
}

.status-strip {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, rgba(239, 248, 255, 0.96), rgba(255, 255, 255, 0.94));
}

.status-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  background: rgba(70, 201, 147, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}

.status-icon::after {
  content: '';
  position: absolute;
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  background: rgba(70, 201, 147, 0.16);
  transform: scale(1);
  opacity: 0;
}

.status-icon.syncing::after {
  animation: soft-pulse 1.6s ease-out infinite;
}

.status-core {
  width: 22rpx;
  height: 22rpx;
  border-radius: 50%;
  background: #30bd80;
  box-shadow: 0 0 0 8rpx rgba(48, 189, 128, 0.12);
}

@keyframes soft-pulse {
  0% {
    transform: scale(0.82);
    opacity: 0.72;
  }

  100% {
    transform: scale(1.7);
    opacity: 0;
  }
}

.status-copy {
  margin-left: 18rpx;
  min-width: 0;
}

.status-title {
  color: #1d2f44;
  font-size: 28rpx;
  font-weight: 800;
}

.status-desc {
  margin-top: 4rpx;
  color: #66809b;
  font-size: 22rpx;
}

.overview {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(232, 246, 255, 0.92));
}

.overview-head,
.area-head,
.panel-head,
.area-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 900;
}

.sub-text,
.area-meta,
.focus-label,
.focus-meta,
.area-code {
  font-size: 23rpx;
  color: #58708e;
}

.rate-pill,
.area-rate {
  min-width: 92rpx;
  height: 54rpx;
  border-radius: 27rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 900;
}

.rate-pill.normal,
.area-rate.normal,
.status-tag.normal {
  background: rgba(56, 196, 139, 0.15);
  color: #1b9d67;
}

.rate-pill.warn,
.area-rate.warn,
.status-tag.warn {
  background: rgba(255, 176, 58, 0.18);
  color: #d58a00;
}

.rate-pill.danger,
.area-rate.danger,
.status-tag.danger,
.rate-pill.full,
.area-rate.full,
.status-tag.full {
  background: rgba(255, 87, 104, 0.16);
  color: #e34a5d;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin-top: 20rpx;
}

.stat-cell {
  border-radius: 18rpx;
  background: #f6fbff;
  padding: 18rpx 12rpx;
}

.stat-label {
  display: block;
  color: #66809b;
  font-size: 22rpx;
}

.stat-value {
  display: block;
  margin-top: 8rpx;
  color: #19334f;
  font-size: 38rpx;
  font-weight: 900;
  transition: color 0.25s ease, transform 0.25s ease;
}

.stat-value.occupied {
  color: #ef5a66;
}

.stat-value.free {
  color: #15aa72;
}

.traffic-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(238, 250, 255, 0.94));
}

.traffic-badge {
  height: 48rpx;
  min-width: 74rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  background: rgba(58, 132, 255, 0.12);
  color: #2f70d8;
  font-size: 22rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.traffic-main {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: 0.9fr 1.4fr;
  gap: 14rpx;
}

.traffic-total {
  border-radius: 18rpx;
  background: #f3f9ff;
  padding: 18rpx;
}

.traffic-label {
  display: block;
  color: #66809b;
  font-size: 22rpx;
}

.traffic-value {
  display: block;
  margin-top: 10rpx;
  color: #17314c;
  font-size: 42rpx;
  line-height: 1;
  font-weight: 900;
}

.traffic-side {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
}

.traffic-mini {
  min-width: 0;
  border-radius: 18rpx;
  background: #f8fcff;
  padding: 16rpx 10rpx;
}

.traffic-mini text,
.traffic-footer {
  color: #66809b;
  font-size: 22rpx;
}

.traffic-mini strong {
  display: block;
  margin-top: 8rpx;
  color: #17314c;
  font-size: 32rpx;
  line-height: 1;
}

.traffic-footer {
  margin-top: 16rpx;
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.focus-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14rpx;
}

.focus-card {
  min-height: 140rpx;
  background: linear-gradient(135deg, rgba(255, 248, 248, 0.96), rgba(255, 255, 255, 0.92));
}

.focus-card.soft {
  background: linear-gradient(135deg, rgba(238, 250, 255, 0.98), rgba(255, 255, 255, 0.94));
}

.focus-title {
  margin-top: 10rpx;
  color: #17314c;
  font-size: 32rpx;
  font-weight: 900;
}

.focus-meta {
  margin-top: 8rpx;
}

.panel-head {
  align-items: flex-start;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12rpx;
  max-width: 260rpx;
}

.legend {
  display: flex;
  align-items: center;
  gap: 8rpx;
  color: #58708e;
  font-size: 22rpx;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}

.free-dot {
  background: #5ed8a5;
}

.occupied-dot {
  background: #ff6672;
}

.tight-dot {
  background: #ffc857;
}

.parking-map {
  margin-top: 18rpx;
}

.area-block {
  margin-bottom: 16rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #f8fcff;
  border: 1px solid #dceafa;
  transition: background 0.3s ease, border-color 0.3s ease;
}

.area-block.danger,
.area-block.full {
  border-color: rgba(255, 87, 104, 0.24);
  background: #fff8f9;
}

.area-block.warn {
  border-color: rgba(255, 176, 58, 0.28);
  background: #fffaf0;
}

.area-name {
  font-size: 28rpx;
  color: #17314c;
  font-weight: 900;
}

.slot-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8rpx;
}

.slot {
  height: 34rpx;
  border-radius: 8rpx;
  background: linear-gradient(180deg, #75deb1, #46c993);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.52);
  transition: background 0.35s ease;
}

.slot.busy {
  background: linear-gradient(180deg, #ff8791, #ef5967);
}

.slot.tight {
  background: linear-gradient(180deg, #ffd56c, #f1ad2c);
}

.area-footer {
  margin-top: 14rpx;
}

.status-tag {
  padding: 5rpx 14rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 800;
}

.progress {
  margin-top: 14rpx;
  height: 10rpx;
  border-radius: 8rpx;
  background: #e2eef9;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  border-radius: 8rpx;
  background: linear-gradient(90deg, #65b8ff, #5ed8a5);
  transition: width 0.45s ease, background 0.3s ease;
}

.progress-inner.warn {
  background: linear-gradient(90deg, #ffcf6a, #ffad42);
}

.progress-inner.danger,
.progress-inner.full {
  background: linear-gradient(90deg, #ff8791, #ef5967);
}

.empty {
  margin-top: 18rpx;
  border-radius: 16rpx;
  background: rgba(236, 246, 255, 0.8);
  color: #58708e;
  font-size: 24rpx;
  padding: 18rpx;
}

</style>
