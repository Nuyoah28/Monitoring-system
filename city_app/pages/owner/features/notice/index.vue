<template>
  <view class="feature-page">
    <view class="bg-shape bg-1"></view>
    <view class="bg-shape bg-2"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">社区提醒</view>
      <view class="ghost-btn" @tap="loadNotices">刷新</view>
    </view>

    <view class="panel">
      <view class="panel-title">最新提醒</view>
      <view v-if="!list.length" class="empty">当前暂无社区提醒。</view>
      <view v-for="item in list" :key="noticeKey(item)" class="notice-card" :class="{ read: item.isRead }" @tap="openNotice(item)">
        <view class="notice-head">
          <view class="notice-title">{{ item.message || '未命名提醒' }}</view>
          <view class="read-pill" :class="{ read: item.isRead }">{{ item.isRead ? '已读' : '未读' }}</view>
        </view>
        <view class="notice-time">提醒时间：{{ formatTime(item.timestamp) }}</view>
      </view>
    </view>

    <u-popup :show="showDetail" mode="bottom" @close="showDetail = false" round="20">
      <view class="detail-wrap">
        <view class="detail-head">提醒详情</view>
        <view class="detail-content">{{ active.message || '--' }}</view>
        <view class="detail-time">提醒时间：{{ formatTime(active.timestamp || active.createTime) }}</view>
        <view class="close-btn" @tap="closeDetail">我知道了</view>
      </view>
    </u-popup>
  </view>
</template>

<script>
import { OWNER_DEMO_FALLBACK_ENABLED, createOwnerDemoNotices } from '@/common/owner-demo-data.js';
import { applyOwnerNoticeReadState, getOwnerNoticeKey, markOwnerNoticeRead } from '@/common/owner-notice-read.js';

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
      let shouldUseFallback = false;
      try {
        const { data: res } = await uni.$http.get('/api/v1/system/message/getMessage');
        if (!this.isSuccess(res)) {
          shouldUseFallback = true;
        } else {
          const arr = Array.isArray(res.data) ? res.data : [];
          shouldUseFallback = !arr.length && OWNER_DEMO_FALLBACK_ENABLED;
          this.list = this.normalizeNotices(shouldUseFallback ? createOwnerDemoNotices() : arr);
          return;
        }
      } catch (e) {
        shouldUseFallback = true;
      }

      if (shouldUseFallback && OWNER_DEMO_FALLBACK_ENABLED) {
        this.list = this.normalizeNotices(createOwnerDemoNotices());
        return;
      }

      uni.$showMsg('网络异常，请稍后重试');
    },
    normalizeNotices(list = []) {
      const sorted = [...list].sort((a, b) => {
        const ta = new Date(a.timestamp || a.createTime || 0).getTime();
        const tb = new Date(b.timestamp || b.createTime || 0).getTime();
        return tb - ta;
      });
      return applyOwnerNoticeReadState(sorted);
    },
    noticeKey(item) {
      return getOwnerNoticeKey(item);
    },
    openNotice(item) {
      this.active = item || {};
      this.showDetail = true;
      this.saveNoticeAck(this.active);
    },
    closeDetail() {
      this.saveNoticeAck(this.active);
      this.showDetail = false;
    },
    saveNoticeAck(item = null) {
      const target = item && (item.timestamp || item.createTime) ? item : this.list[0];
      if (!target) return;
      const targetKey = this.noticeKey(target);
      markOwnerNoticeRead(target);
      this.list = this.list.map(notice => ({
        ...notice,
        isRead: this.noticeKey(notice) === targetKey ? true : notice.isRead,
      }));
      if (this.active && this.noticeKey(this.active) === targetKey) {
        this.active = { ...this.active, isRead: true };
      }
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
  overflow: visible;
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

.notice-card.read {
  background: #fbfdff;
  border-color: #e8f0fa;
  opacity: 0.78;
}

.notice-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.notice-title {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  color: #17314c;
  font-weight: 700;
  line-height: 1.5;
}

.read-pill {
  flex-shrink: 0;
  height: 40rpx;
  padding: 0 14rpx;
  border-radius: 999rpx;
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
  font-size: 21rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.read-pill.read {
  background: rgba(100, 116, 139, 0.1);
  color: #64748b;
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
