<template>
  <view class="feature-page">
    <view class="bg-shape bg-1"></view>
    <view class="bg-shape bg-2"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">物业通知</view>
      <view class="ghost-btn" @tap="loadNotices">刷新</view>
    </view>

    <view class="panel">
      <view class="panel-title">最新公告</view>
      <view v-if="!list.length" class="empty">当前暂无公告。</view>
      <view v-for="item in list" :key="item.id" class="notice-card" @tap="openNotice(item)">
        <view class="notice-title">{{ item.message || '未命名公告' }}</view>
        <view class="notice-time">发布时间：{{ formatTime(item.timestamp) }}</view>
      </view>
    </view>

    <u-popup :show="showDetail" mode="bottom" @close="showDetail = false" round="20">
      <view class="detail-wrap">
        <view class="detail-head">通知详情</view>
        <view class="detail-content">{{ active.message || '--' }}</view>
        <view class="detail-time">发布时间：{{ formatTime(active.timestamp) }}</view>
        <view class="close-btn" @tap="showDetail = false">我知道了</view>
      </view>
    </u-popup>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000';

export default {
  data() {
    return {
      list: [],
      showDetail: false,
      active: {},
    };
  },
  onShow() {
    this.loadNotices();
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
    formatTime(value) {
      if (!value) return '--';
      if (typeof value === 'string') return value.replace('T', ' ').slice(0, 19);
      return `${value}`;
    },
    async loadNotices() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/system/message/getMessage');
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载通知失败');
          return;
        }
        const arr = Array.isArray(res.data) ? res.data : [];
        this.list = arr.sort((a, b) => {
          const ta = new Date(a.timestamp || 0).getTime();
          const tb = new Date(b.timestamp || 0).getTime();
          return tb - ta;
        });
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    openNotice(item) {
      this.active = item || {};
      this.showDetail = true;
    },
  },
};
</script>

<style lang="scss" scoped>
.feature-page {
  min-height: 100vh;
  padding: 26rpx 24rpx 32rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef7ff 0%, #f9fbff 54%, #ffffff 100%);
  position: relative;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 999rpx;
  filter: blur(66rpx);
  z-index: 0;
}

.bg-1 {
  width: 360rpx;
  height: 360rpx;
  background: rgba(0, 198, 255, 0.22);
  right: -140rpx;
  top: -110rpx;
}

.bg-2 {
  width: 420rpx;
  height: 420rpx;
  background: rgba(73, 121, 255, 0.14);
  left: -160rpx;
  bottom: -170rpx;
}

.top-bar,
.panel {
  position: relative;
  z-index: 2;
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
  font-size: 34rpx;
  font-weight: 800;
  color: #18304b;
}

.ghost-btn {
  padding: 0 20rpx;
  height: 56rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.82);
  color: #2b5b99;
  font-size: 24rpx;
}

.panel {
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
}

.panel-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 700;
  margin-bottom: 16rpx;
}

.empty {
  border-radius: 16rpx;
  background: rgba(236, 246, 255, 0.8);
  color: #58708e;
  font-size: 24rpx;
  padding: 18rpx;
}

.notice-card {
  padding: 18rpx;
  border-radius: 18rpx;
  background: #f7fbff;
  border: 1px solid #dceafa;
  margin-bottom: 12rpx;
}

.notice-title {
  font-size: 28rpx;
  color: #17314c;
  font-weight: 700;
  line-height: 1.5;
}

.notice-time {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #54708f;
}

.detail-wrap {
  padding: 28rpx 24rpx 36rpx;
}

.detail-head {
  font-size: 32rpx;
  color: #18304b;
  font-weight: 800;
}

.detail-content {
  margin-top: 16rpx;
  font-size: 28rpx;
  color: #2a4260;
  line-height: 1.7;
}

.detail-time {
  margin-top: 14rpx;
  font-size: 22rpx;
  color: #55708e;
}

.close-btn {
  margin-top: 24rpx;
  height: 82rpx;
  border-radius: 41rpx;
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
