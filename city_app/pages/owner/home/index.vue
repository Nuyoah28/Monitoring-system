<template>
  <view class="owner-page" :style="{ paddingTop: pageTopPadding + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="hero">
      <view class="hero-top">
        <view>
          <view class="hero-kicker">社区服务</view>
          <view class="hero-title">社区助手</view>
        </view>
        <view class="hero-status" :class="unreadNoticeCount ? 'is-warn' : ''">
          <view class="status-dot"></view>
          <text>{{ unreadNoticeCount ? '有新提醒' : '今日正常' }}</text>
        </view>
      </view>
      <view class="hero-sub">{{ homeSummary }}</view>
      <view class="hero-metrics">
        <view class="hero-chip" @tap="goFeature('/pages/owner/features/notice/index')">
          <text class="chip-num">{{ unreadNoticeCount }}</text>
          <text class="chip-label">条新提醒</text>
        </view>
        <view class="hero-chip" @tap="goFeature('/pages/owner/features/parking/index')">
          <text class="chip-num">{{ freeParkingCount }}</text>
          <text class="chip-label">个可用车位</text>
        </view>
        <view class="hero-chip" @tap="goFeature('/pages/owner/features/environment/index')">
          <text class="chip-num">{{ environmentText }}</text>
          <text class="chip-label">当前环境</text>
        </view>
      </view>
    </view>

    <view class="section-card reminder-card">
      <view class="section-head">
        <view>
          <view class="section-title">社区提醒</view>
          <view class="section-sub">与你所在区域相关的信息</view>
        </view>
        <view class="section-link" @tap="goFeature('/pages/owner/features/notice/index')">查看全部 ›</view>
      </view>
      <view class="reminder-list" v-if="topNotice">
        <view class="reminder-item" @tap="goFeature('/pages/owner/features/notice/index')">
          <view class="reminder-tag">提醒</view>
          <view class="reminder-main">
            <view class="reminder-title">{{ topNotice.message || '社区提醒' }}</view>
            <view class="reminder-time">提醒时间：{{ formatShortTime(topNotice.timestamp) }}</view>
          </view>
        </view>
      </view>
      <view class="empty-box" v-else>
        <text>{{ notices.length ? '当前暂无未读社区提醒' : '当前暂无社区提醒' }}</text>
      </view>
    </view>

    <view class="section-card status-card">
      <view class="section-head">
        <view>
          <view class="section-title">社区状态</view>
          <view class="section-sub">环境与车位一眼了解</view>
        </view>
      </view>
      <view class="status-grid">
        <view class="status-box status-box--blue" @tap="goFeature('/pages/owner/features/environment/index')">
          <view class="status-box-title">环境信息</view>
          <view class="status-box-main">{{ environmentText }}</view>
          <view class="status-box-sub">{{ environmentSubText }}</view>
        </view>
        <view class="status-box status-box--green" @tap="goFeature('/pages/owner/features/parking/index')">
          <view class="status-box-title">停车服务</view>
          <view class="status-box-main">{{ freeParkingCount }}</view>
          <view class="status-box-sub">{{ parkingSummaryText }} · {{ parkingSummaryBadge }}</view>
        </view>
      </view>
    </view>

    <view class="section-card service-card">
      <view class="section-head">
        <view>
          <view class="section-title">常用服务</view>
          <view class="section-sub">居民常用功能集中在这里</view>
        </view>
      </view>
      <view class="service-grid">
        <view class="service-item" @tap="goFeature('/pages/owner/features/notice/index')"><view class="service-icon service-icon--red">提</view><text>社区提醒</text></view>
        <view class="service-item" @tap="goFeature('/pages/owner/ai/index')"><view class="service-icon service-icon--purple">助</view><text>社区助手</text></view>
        <view class="service-item" @tap="goFeature('/pages/owner/features/repair/index')"><view class="service-icon service-icon--orange">修</view><text>在线报修</text></view>
        <view class="service-item" @tap="goFeature('/pages/owner/features/visitor/index')"><view class="service-icon service-icon--blue">访</view><text>访客登记</text></view>
        <view class="service-item" @tap="goFeature('/pages/owner/features/parking/index')"><view class="service-icon service-icon--green">停</view><text>停车服务</text></view>
        <view class="service-item" @tap="goFeature('/pages/owner/features/environment/index')"><view class="service-icon service-icon--cyan">环</view><text>环境信息</text></view>
      </view>
    </view>

    <view class="section-card todo-card">
      <view class="section-head"><view><view class="section-title">我的事项</view><view class="section-sub">近期记录与服务进度</view></view></view>
      <view class="todo-list">
        <view class="todo-item" @tap="goFeature('/pages/owner/features/repair/index')"><view class="todo-icon todo-icon--orange">修</view><view class="todo-main"><view class="todo-title">{{ repairTodoTitle }}</view><view class="todo-desc">{{ repairTodoDesc }}</view></view><u-icon name="arrow-right" color="#8ca0b8" size="26rpx"></u-icon></view>
        <view class="todo-item" @tap="goFeature('/pages/owner/features/visitor/index')"><view class="todo-icon todo-icon--blue">访</view><view class="todo-main"><view class="todo-title">{{ visitorTitle }}</view><view class="todo-desc">{{ visitorDesc }}</view></view><u-icon name="arrow-right" color="#8ca0b8" size="26rpx"></u-icon></view>
      </view>
    </view>

    <owner-tabbar current="home" />
  </view>
</template>

<script>
import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';
import {
  OWNER_DEMO_FALLBACK_ENABLED,
  createOwnerDemoEnvironment,
  createOwnerDemoNotices,
  createOwnerDemoParkingRealtime,
  createOwnerDemoRepairs,
  createOwnerDemoVisitors,
} from '@/common/owner-demo-data.js';
import { applyOwnerNoticeReadState } from '@/common/owner-notice-read.js';

export default {
  components: { OwnerTabbar },
  data() {
    return {
      pageTopPadding: 30,
      notices: [],
      lastAcknowledgedNoticeTimestamp: 0,
      repairs: [],
      parkingSpaces: [],
      parkingRealtime: null,
      visitors: [],
      environmentData: null,
    };
  },
  computed: {
    noticeCount() { return this.notices.length; },
    unreadNoticeCount() { return this.getUnreadNotices().length; },
    topNotice() { return this.getUnreadNotices()[0] || null; },
    parkingAreas() {
      const zones = (this.parkingRealtime && Array.isArray(this.parkingRealtime.zones)) ? this.parkingRealtime.zones : [];
      return zones.map((item, index) => {
        const total = Math.max(0, Number(item.totalSpaces || 0));
        const occupied = Math.min(total, Math.max(0, Number(item.occupiedSpaces || 0)));
        return { id: item.areaCode || `home-area-${index}`, location: item.areaName || `车位区域${index + 1}`, total, occupied, free: Math.max(0, total - occupied), rate: total ? Math.round((occupied / total) * 100) : 0 };
      });
    },
    parkingSummary() {
      if (this.parkingRealtime && Number(this.parkingRealtime.totalSpaces) > 0) return { total: Number(this.parkingRealtime.totalSpaces || 0), occupied: Number(this.parkingRealtime.occupiedSpaces || 0), free: Number(this.parkingRealtime.freeSpaces || 0) };
      return this.parkingAreas.reduce((sum, item) => ({ total: sum.total + item.total, occupied: sum.occupied + item.occupied, free: sum.free + item.free }), { total: 0, occupied: 0, free: 0 });
    },
    freeParkingCount() { return Math.max(this.parkingSummary.free, 0); },
    parkingRate() { return this.parkingSummary.total ? Math.round((this.parkingSummary.occupied / this.parkingSummary.total) * 100) : 0; },
    parkingSummaryText() { const topArea = this.parkingAreas.slice().sort((a, b) => b.free - a.free)[0]; return this.parkingSummary.total && topArea ? `优先看看 ${topArea.location}` : '暂无车库信息'; },
    parkingSummaryBadge() { if (!this.parkingSummary.total) return '等待更新'; if (this.parkingRate >= 85) return '车位偏紧'; if (this.parkingRate >= 70) return '可先查看空位'; return '空位较充足'; },
    environmentText() { return this.environmentData && this.environmentData.aqi ? `AQI ${this.environmentData.aqi}` : 'AQI --'; },
    environmentSubText() { if (!this.environmentData) return '温度 -- · 湿度 --'; return `温度 ${this.formatNumber(this.environmentData.temperature)}°C · 湿度 ${this.formatNumber(this.environmentData.humidity)}% · PM2.5 ${this.formatNumber(this.environmentData.pm25)}`; },
    repairTodoTitle() { const latest = this.repairs[0]; return latest ? latest.deviceName || '报修记录' : '暂无待跟进报修'; },
    repairTodoDesc() { const latest = this.repairs[0]; return latest ? `${latest.location || '未标注位置'} · ${this.formatShortTime(latest.reportTime)}` : '有故障可随时提交报修'; },
    visitorTitle() { const next = this.visitors[0]; return next ? `${next.visitorName || '访客'}到访` : '暂无访客预约'; },
    visitorDesc() { const next = this.visitors[0]; return next ? `时间：${this.formatShortTime(next.visitTime)}` : '可快速登记亲友到访信息'; },
    homeSummary() { if (this.unreadNoticeCount > 0) return `有 ${this.unreadNoticeCount} 条社区提醒待查看`; if (this.freeParkingCount > 0) return `当前还有 ${this.freeParkingCount} 个可用车位`; return '查看提醒、停车、环境和常用服务'; },
  },
  onShow() { this.updateSafeAreaPadding(); this.loadDashboard(); },
  methods: {
    updateSafeAreaPadding() { const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync(); this.pageTopPadding = (info && info.statusBarHeight) ? info.statusBarHeight + 18 : 30; },
    goFeature(url) { uni.navigateTo({ url }); },
    isSuccess(res) { return String(res && res.code) === '00000'; },
    formatShortTime(value) { if (!value) return '--'; return String(value).replace('T', ' ').slice(5, 16); },
    formatNumber(value) { if (value === null || value === undefined || value === '') return '--'; const num = Number(value); if (isNaN(num)) return '--'; return Number.isInteger(num) ? `${num}` : num.toFixed(1); },
    sortByTime(list, field) { return list.sort((a, b) => new Date(b[field] || 0).getTime() - new Date(a[field] || 0).getTime()); },
    getUnreadNotices() { return this.notices.filter(item => !item.isRead); },
    loadNoticeAckState() {
      try {
        const stored = uni.getStorageSync('ownerNoticeAck');
        const parsed = stored ? (typeof stored === 'string' ? JSON.parse(stored) : stored) : {};
        this.lastAcknowledgedNoticeTimestamp = Number(parsed.lastAcknowledgedNoticeTimestamp || 0);
      } catch (e) { this.lastAcknowledgedNoticeTimestamp = 0; }
    },
    async safeGet(url, params = {}) { try { const { data: res } = await uni.$http.get(url, params); if (!this.isSuccess(res)) return []; return Array.isArray(res.data) ? res.data : []; } catch (e) { return []; } },
    async safeGetObject(url, params = {}) { try { const { data: res } = await uni.$http.get(url, params); if (!this.isSuccess(res)) return null; return res.data || null; } catch (e) { return null; } },
    async getParkingRealtime() {
      const realtime = await this.safeGetObject('/api/v1/parking/realtime', { monitorId: 1 });
      if (this.hasParkingData(realtime)) return realtime;

      if (OWNER_DEMO_FALLBACK_ENABLED) {
        const mockRealtime = await this.safeGetObject('/api/v1/parking/realtime', { monitorId: 1, source: 'mock' });
        if (this.hasParkingData(mockRealtime)) return mockRealtime;
        return createOwnerDemoParkingRealtime(1);
      }
      return null;
    },
    hasParkingData(data) {
      return Boolean(data && (Number(data.totalSpaces) > 0 || (Array.isArray(data.zones) && data.zones.length)));
    },
    async loadDashboard() {
      this.loadNoticeAckState();
      const [notices, repairs, parkingSpaces, visitors, environment] = await Promise.all([this.safeGet('/api/v1/system/message/getMessage'), this.safeGet('/api/v1/device-repair/list'), this.getParkingRealtime(), this.safeGet('/api/v1/visitor/list'), this.safeGetObject('/api/v1/env/realtime', { monitorId: 1 })]);
      const displayNotices = notices.length || !OWNER_DEMO_FALLBACK_ENABLED ? notices : createOwnerDemoNotices();
      this.notices = applyOwnerNoticeReadState(this.sortByTime(displayNotices, 'timestamp'));
      this.repairs = this.sortByTime(repairs.length || !OWNER_DEMO_FALLBACK_ENABLED ? repairs : createOwnerDemoRepairs(), 'reportTime');
      this.parkingRealtime = parkingSpaces;
      this.visitors = this.sortByTime(visitors.length || !OWNER_DEMO_FALLBACK_ENABLED ? visitors : createOwnerDemoVisitors(), 'visitTime');
      this.environmentData = environment || (OWNER_DEMO_FALLBACK_ENABLED ? createOwnerDemoEnvironment(1) : null);
      if (this.parkingRealtime && !this.parkingRealtime.totalSpaces && !this.parkingAreas.length) this.parkingRealtime = null;
    },
  },
};
</script>

<style lang="scss" scoped>
.owner-page { min-height: 100vh; padding: 30rpx 24rpx 150rpx; box-sizing: border-box; position: relative; overflow: visible; background: radial-gradient(circle at 12% 2%, rgba(56, 164, 255, 0.22) 0, rgba(56, 164, 255, 0) 250rpx), radial-gradient(circle at 88% 18%, rgba(20, 112, 216, 0.14) 0, rgba(20, 112, 216, 0) 300rpx), linear-gradient(180deg, #eaf5ff 0%, #f5fbff 45%, #fbfdff 100%); }
.bg-orb { position: absolute; border-radius: 50%; pointer-events: none; }
.bg-orb--one { width: 220rpx; height: 220rpx; right: -82rpx; top: 160rpx; background: rgba(56, 164, 255, 0.12); }
.bg-orb--two { width: 180rpx; height: 180rpx; left: -70rpx; top: 720rpx; background: rgba(22, 163, 74, 0.08); }
.hero, .section-card { position: relative; z-index: 1; }
.hero { border-radius: 34rpx; padding: 30rpx; color: #fff; background: radial-gradient(circle at 88% 0%, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 230rpx), linear-gradient(135deg, #1470d8 0%, #2b8ef0 48%, #38a4ff 100%); box-shadow: 0 18rpx 40rpx rgba(20, 112, 216, 0.24); }
.hero-top, .section-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20rpx; }
.hero-kicker { font-size: 24rpx; font-weight: 800; color: rgba(255, 255, 255, 0.82); }
.hero-title { margin-top: 10rpx; font-size: 46rpx; line-height: 1.1; font-weight: 900; }
.hero-sub { margin-top: 22rpx; padding: 16rpx 18rpx; border-radius: 22rpx; background: rgba(255, 255, 255, 0.16); border: 1rpx solid rgba(255, 255, 255, 0.24); font-size: 25rpx; font-weight: 800; line-height: 1.4; }
.hero-status { height: 56rpx; padding: 0 18rpx; border-radius: 999rpx; background: rgba(255, 255, 255, 0.18); border: 1rpx solid rgba(255, 255, 255, 0.28); display: flex; align-items: center; gap: 8rpx; font-size: 23rpx; font-weight: 900; flex-shrink: 0; }
.status-dot { width: 12rpx; height: 12rpx; border-radius: 50%; background: #86efac; }
.hero-status.is-warn .status-dot { background: #fef3c7; }
.hero-metrics { margin-top: 20rpx; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12rpx; }
.hero-chip { min-height: 80rpx; border-radius: 20rpx; background: rgba(255,255,255,0.18); border: 1rpx solid rgba(255,255,255,0.22); padding: 12rpx 14rpx; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; }
.chip-num { color: #fff; font-size: 28rpx; line-height: 1; font-weight: 900; }
.chip-label { margin-top: 8rpx; color: rgba(255, 255, 255, 0.82); font-size: 20rpx; font-weight: 700; }
.section-card { margin-top: 20rpx; padding: 24rpx; border-radius: 30rpx; background: rgba(255,255,255,0.92); border: 1rpx solid rgba(37,99,235,0.10); box-shadow: 0 10rpx 30rpx rgba(30,88,150,0.10); }
.section-title { color: #102033; font-size: 32rpx; font-weight: 900; }
.section-sub { margin-top: 6rpx; color: #64748b; font-size: 22rpx; }
.section-link { color: #1470d8; font-size: 24rpx; font-weight: 900; flex-shrink: 0; }
.reminder-list, .service-grid, .todo-list, .status-grid { margin-top: 18rpx; }
.reminder-item, .todo-item { display: flex; gap: 14rpx; padding: 18rpx; border-radius: 22rpx; background: #f8fbff; border: 1rpx solid #dcebfa; }
.reminder-tag { height: 42rpx; padding: 0 14rpx; border-radius: 999rpx; background: rgba(245,158,11,0.12); color: #d97706; font-size: 21rpx; font-weight: 900; display: flex; align-items: center; flex-shrink: 0; }
.reminder-main, .todo-main { flex: 1; min-width: 0; }
.reminder-title, .todo-title { color: #102033; font-size: 27rpx; font-weight: 900; line-height: 1.35; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reminder-time, .todo-desc { margin-top: 8rpx; color: #64748b; font-size: 22rpx; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-box { margin-top: 18rpx; padding: 22rpx; border-radius: 20rpx; background: #f8fbff; color: #94a3b8; font-size: 24rpx; text-align: center; }
.status-card, .service-card { background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(240,248,255,0.94) 100%); }
.status-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12rpx; }
.status-box { min-height: 152rpx; border-radius: 24rpx; padding: 18rpx; box-sizing: border-box; border: 1rpx solid #dcebfa; background: #fff; }
.status-box--blue { background: #eff6ff; border-color: #bfdbfe; }
.status-box--green { background: #f0fdf4; border-color: #bbf7d0; }
.status-box-title { color: #64748b; font-size: 22rpx; font-weight: 800; }
.status-box-main { margin-top: 10rpx; color: #102033; font-size: 38rpx; line-height: 1; font-weight: 900; }
.status-box-sub { margin-top: 10rpx; color: #64748b; font-size: 21rpx; line-height: 1.35; }
.service-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14rpx; }
.service-item { min-height: 132rpx; border-radius: 24rpx; background: rgba(255,255,255,0.92); border: 1rpx solid #dcebfa; box-shadow: 0 8rpx 20rpx rgba(37,99,235,0.08); display: flex; flex-direction: column; justify-content: center; align-items: center; }
.service-item:active { transform: scale(0.97); }
.service-icon, .todo-icon { width: 62rpx; height: 62rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 900; }
.service-icon--red { background: #fee2e2; color: #dc2626; }
.service-icon--purple { background: #ede9fe; color: #7c3aed; }
.service-icon--orange, .todo-icon--orange { background: #fef3c7; color: #d97706; }
.service-icon--blue, .todo-icon--blue { background: #dbeafe; color: #2563eb; }
.service-icon--green { background: #dcfce7; color: #16a34a; }
.service-icon--cyan { background: #cffafe; color: #0891b2; }
.service-item text { margin-top: 12rpx; color: #1e3a5f; font-size: 22rpx; font-weight: 900; }
.todo-list { display: flex; flex-direction: column; gap: 12rpx; }
.todo-item { align-items: center; min-height: 102rpx; box-sizing: border-box; }
.todo-icon { margin-right: 16rpx; flex-shrink: 0; }
</style>
