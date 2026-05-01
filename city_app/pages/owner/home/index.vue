<template>
  <view class="owner-page">
    <view class="hero">
      <view class="hero-main">
        <view class="hero-kicker">业主服务</view>
        <view class="hero-title">社区智眼</view>
        <view class="hero-sub">{{ homeSummary }}</view>
      </view>
      <view class="hero-status">
        <view class="status-dot"></view>
        <text>运行平稳</text>
      </view>
    </view>

    <view class="service-card">
      <view class="section-head">
        <view>
          <view class="section-title">常用服务</view>
          <view class="section-sub">访客、报修、公告和停车快速办理</view>
        </view>
      </view>
      <view class="grid">
        <view class="feature-card" @tap="goFeature('/pages/owner/features/visitor/index')">
          <view class="feature-icon feature-icon--blue">访</view>
          <view class="feature-name">访客登记</view>
          <view class="feature-desc">为亲友创建来访登记</view>
        </view>
        <view class="feature-card" @tap="goFeature('/pages/owner/features/notice/index')">
          <view class="feature-icon feature-icon--green">告</view>
          <view class="feature-name">物业通知</view>
          <view class="feature-desc">查看社区最新公告</view>
        </view>
        <view class="feature-card" @tap="goFeature('/pages/owner/features/repair/index')">
          <view class="feature-icon feature-icon--orange">修</view>
          <view class="feature-name">在线报修</view>
          <view class="feature-desc">提交问题并跟踪进度</view>
        </view>
        <view class="feature-card" @tap="goFeature('/pages/owner/features/parking/index')">
          <view class="feature-icon feature-icon--purple">停</view>
          <view class="feature-name">停车服务</view>
          <view class="feature-desc">查看当前可用车位</view>
        </view>
      </view>
    </view>

    <view class="dashboard-card">
      <view class="section-head">
        <view>
          <view class="section-title">今日社区状态</view>
          <view class="section-sub">常用事项一眼掌握</view>
        </view>
        <view class="refresh-chip" @tap="loadDashboard">刷新</view>
      </view>

      <view class="status-grid">
        <view class="status-item" @tap="goFeature('/pages/owner/features/notice/index')">
          <view class="status-num">{{ noticeCount }}</view>
          <view class="status-label">物业通知</view>
          <view class="status-note">{{ latestNoticeText }}</view>
        </view>
        <view class="status-item status-item--green" @tap="goFeature('/pages/owner/features/parking/index')">
          <view class="status-num">{{ freeParkingCount }}</view>
          <view class="status-label">空闲车位</view>
          <view class="status-note">{{ parkingSummary }}</view>
        </view>
        <view class="status-item status-item--orange" @tap="goFeature('/pages/owner/features/repair/index')">
          <view class="status-num">{{ repairCount }}</view>
          <view class="status-label">我的报修</view>
          <view class="status-note">{{ repairSummary }}</view>
        </view>
      </view>
    </view>

    <view class="todo-card">
      <view class="section-head">
        <view>
          <view class="section-title">我的事项</view>
          <view class="section-sub">近期记录与服务进度</view>
        </view>
      </view>

      <view class="todo-list">
        <view class="todo-item" @tap="goFeature('/pages/owner/features/visitor/index')">
          <view class="todo-icon todo-icon--blue">访</view>
          <view class="todo-main">
            <view class="todo-title">{{ visitorTitle }}</view>
            <view class="todo-desc">{{ visitorDesc }}</view>
          </view>
          <u-icon name="arrow-right" color="#8ca0b8" size="26rpx"></u-icon>
        </view>
        <view class="todo-item" @tap="goFeature('/pages/owner/features/repair/index')">
          <view class="todo-icon todo-icon--orange">修</view>
          <view class="todo-main">
            <view class="todo-title">{{ repairTodoTitle }}</view>
            <view class="todo-desc">{{ repairTodoDesc }}</view>
          </view>
          <u-icon name="arrow-right" color="#8ca0b8" size="26rpx"></u-icon>
        </view>
      </view>
    </view>

    <owner-tabbar current="home" />
  </view>
</template>

<script>
import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';

export default {
  components: {
    OwnerTabbar,
  },
  data() {
    return {
      notices: [],
      repairs: [],
      parkingSpaces: [],
      visitors: [],
    };
  },
  computed: {
    noticeCount() {
      return this.notices.length;
    },
    latestNoticeText() {
      const latest = this.notices[0];
      if (!latest) return '暂无新通知';
      const text = latest.message || '最新通知';
      return text.length > 8 ? `${text.slice(0, 8)}...` : text;
    },
    freeParkingCount() {
      return this.parkingSpaces.reduce((sum, item) => {
        const total = Number(item.totalSpaces || 0);
        const occupied = this.parseOccupiedCount(item.occupiedVehicle);
        return sum + Math.max(total - occupied, 0);
      }, 0);
    },
    parkingSummary() {
      if (!this.parkingSpaces.length) return '暂无车位数据';
      const best = this.parkingSpaces
        .map(item => {
          const total = Number(item.totalSpaces || 0);
          const occupied = this.parseOccupiedCount(item.occupiedVehicle);
          return {
            location: item.location || '车位区域',
            free: Math.max(total - occupied, 0),
          };
        })
        .sort((a, b) => b.free - a.free)[0];
      return best ? `${best.location}较充足` : '车位状态正常';
    },
    repairCount() {
      return this.repairs.length;
    },
    repairSummary() {
      return this.repairCount ? '查看处理进度' : '暂无报修记录';
    },
    visitorTitle() {
      const next = this.visitors[0];
      return next ? `${next.visitorName || '访客'}到访` : '暂无访客预约';
    },
    visitorDesc() {
      const next = this.visitors[0];
      return next ? `时间：${this.formatShortTime(next.visitTime)}` : '可快速登记亲友到访信息';
    },
    repairTodoTitle() {
      const latest = this.repairs[0];
      return latest ? latest.deviceName || '报修记录' : '暂无待跟进报修';
    },
    repairTodoDesc() {
      const latest = this.repairs[0];
      return latest ? `${latest.location || '未标注位置'} · ${this.formatShortTime(latest.reportTime)}` : '有故障可随时提交报修';
    },
    homeSummary() {
      if (this.noticeCount > 0) return `有 ${this.noticeCount} 条社区通知待查看`;
      if (this.repairCount > 0) return `有 ${this.repairCount} 条报修记录可跟进`;
      return '今日社区运行平稳，常用服务可快速办理';
    },
  },
  onShow() {
    this.loadDashboard();
  },
  methods: {
    goFeature(url) {
      uni.navigateTo({ url });
    },
    isSuccess(res) {
      return String(res && res.code) === '00000';
    },
    parseOccupiedCount(value) {
      if (value === null || value === undefined) return 0;
      const text = `${value}`.trim();
      if (!text) return 0;
      if (/^\d+$/.test(text)) return Number(text);
      return text.split(/[,，\s]+/).filter(Boolean).length;
    },
    formatShortTime(value) {
      if (!value) return '--';
      const text = String(value).replace('T', ' ');
      return text.slice(5, 16);
    },
    sortByTime(list, field) {
      return list.sort((a, b) => {
        const ta = new Date(a[field] || 0).getTime();
        const tb = new Date(b[field] || 0).getTime();
        return tb - ta;
      });
    },
    async safeGet(url) {
      try {
        const { data: res } = await uni.$http.get(url);
        if (!this.isSuccess(res)) return [];
        return Array.isArray(res.data) ? res.data : [];
      } catch (e) {
        return [];
      }
    },
    async loadDashboard() {
      const username = uni.getStorageSync('username') || '';
      const [notices, repairs, parkingSpaces, visitors] = await Promise.all([
        this.safeGet('/api/v1/system/message/getMessage'),
        this.safeGet('/api/v1/device-repair/list'),
        this.safeGet('/api/v1/parking-space/list'),
        this.safeGet('/api/v1/visitor/list'),
      ]);

      this.notices = this.sortByTime(notices, 'timestamp');
      const ownerRepairs = username ? repairs.filter(item => item.publisher === username) : repairs;
      this.repairs = this.sortByTime(ownerRepairs, 'reportTime');
      this.parkingSpaces = parkingSpaces;
      this.visitors = this.sortByTime(visitors, 'visitTime');
    },
  },
};
</script>

<style lang="scss" scoped>
.owner-page {
  min-height: 100vh;
  padding: 30rpx 24rpx 150rpx;
  box-sizing: border-box;
  background: #F5F7FB;
}

.hero {
  border-radius: 30rpx;
  padding: 34rpx 30rpx;
  background: linear-gradient(135deg, #FFFFFF 0%, #EEF6FF 100%);
  border: 1rpx solid #E2E8F0;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.06);
  margin-bottom: 22rpx;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.hero-main {
  flex: 1;
  min-width: 0;
}

.hero-kicker {
  font-size: 23rpx;
  color: #2563EB;
  font-weight: 800;
}

.hero-title {
  margin-top: 8rpx;
  font-size: 46rpx;
  font-weight: 900;
  color: #0F172A;
  letter-spacing: 1rpx;
}

.hero-sub {
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.45;
  color: #64748B;
}

.hero-status {
  height: 52rpx;
  padding: 0 16rpx;
  border-radius: 26rpx;
  background: #F0FDF4;
  color: #16A34A;
  font-size: 22rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-left: 16rpx;
}

.status-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #16A34A;
  margin-right: 8rpx;
}

.service-card,
.dashboard-card,
.todo-card {
  border-radius: 28rpx;
  background: #FFFFFF;
  border: 1rpx solid #E2E8F0;
  box-shadow: 0 10rpx 28rpx rgba(15, 23, 42, 0.06);
  padding: 24rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.feature-card {
  min-height: 184rpx;
  border-radius: 24rpx;
  background: #F8FAFC;
  border: 1rpx solid #E2E8F0;
  padding: 22rpx 20rpx;
  box-sizing: border-box;

  &:active {
    transform: scale(0.98);
  }
}

.feature-icon {
  width: 54rpx;
  height: 54rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  margin-bottom: 14rpx;
}

.feature-icon--blue { background: #DBEAFE; color: #2563EB; }
.feature-icon--green { background: #DCFCE7; color: #16A34A; }
.feature-icon--orange { background: #FEF3C7; color: #D97706; }
.feature-icon--purple { background: #EDE9FE; color: #7C3AED; }

.feature-name {
  font-size: 29rpx;
  color: #0F172A;
  font-weight: 800;
}

.feature-desc {
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.45;
  color: #64748B;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.section-title {
  font-size: 30rpx;
  color: #0F172A;
  font-weight: 900;
}

.section-sub {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #94A3B8;
}

.refresh-chip {
  height: 52rpx;
  padding: 0 20rpx;
  border-radius: 26rpx;
  background: #EAF2FF;
  color: #2563EB;
  font-size: 23rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
}

.status-item {
  min-height: 150rpx;
  border-radius: 22rpx;
  background: #F8FAFC;
  border: 1rpx solid #E2E8F0;
  padding: 18rpx 12rpx;
  box-sizing: border-box;
}

.status-item--green {
  background: #F0FDF4;
  border-color: #BBF7D0;
}

.status-item--orange {
  background: #FFFBEB;
  border-color: #FDE68A;
}

.status-num {
  font-size: 42rpx;
  line-height: 1;
  color: #2563EB;
  font-weight: 900;
}

.status-item--green .status-num { color: #16A34A; }
.status-item--orange .status-num { color: #D97706; }

.status-label {
  margin-top: 10rpx;
  font-size: 23rpx;
  color: #334155;
  font-weight: 800;
}

.status-note {
  margin-top: 8rpx;
  font-size: 20rpx;
  color: #64748B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.todo-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.todo-item {
  display: flex;
  align-items: center;
  min-height: 102rpx;
  border-radius: 22rpx;
  background: #F8FAFC;
  border: 1rpx solid #E2E8F0;
  padding: 16rpx;
  box-sizing: border-box;
}

.todo-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  margin-right: 16rpx;
}

.todo-icon--blue {
  background: #DBEAFE;
  color: #2563EB;
}

.todo-icon--orange {
  background: #FEF3C7;
  color: #D97706;
}

.todo-main {
  flex: 1;
  min-width: 0;
}

.todo-title {
  font-size: 27rpx;
  color: #0F172A;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.todo-desc {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: #64748B;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
