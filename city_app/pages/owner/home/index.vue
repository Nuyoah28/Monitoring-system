<template>
  <view class="owner-page">
    <view class="hero">
      <view class="hero-title">主页功能</view>
      <view class="hero-sub">智慧社区业主端 · 便捷服务入口</view>
    </view>

    <view class="grid">
      <view class="feature-card" @tap="goFeature('/pages/owner/features/visitor/index')">
        <view class="feature-name">访客登记</view>
        <view class="feature-desc">快速登记访客并生成通行凭证</view>
      </view>
      <view class="feature-card" @tap="goFeature('/pages/owner/features/notice/index')">
        <view class="feature-name">物业通知</view>
        <view class="feature-desc">查看最新社区通知与公告</view>
      </view>
      <view class="feature-card" @tap="goFeature('/pages/owner/features/repair/index')">
        <view class="feature-name">报修入口</view>
        <view class="feature-desc">提交报修并跟踪处理进度</view>
      </view>
      <view class="feature-card" @tap="goFeature('/pages/owner/features/parking/index')">
        <view class="feature-name">空闲车位引导</view>
        <view class="feature-desc">引导前往当前可用车位区域</view>
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
  methods: {
    goFeature(url) {
      uni.navigateTo({ url });
    },
  },
};
</script>

<style lang="scss" scoped>
.owner-page {
  min-height: 100vh;
  padding: 30rpx 24rpx 150rpx;
  box-sizing: border-box;
}

.hero {
  border-radius: 30rpx;
  padding: 36rpx 30rpx;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.12), rgba(0, 184, 216, 0.14));
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 10rpx 30rpx rgba(65, 102, 161, 0.08);
  margin-bottom: 24rpx;
}

.hero-title {
  font-size: 46rpx;
  font-weight: 800;
  color: #1a2a3a;
  letter-spacing: 1rpx;
}

.hero-sub {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: rgba(26, 42, 58, 0.66);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.feature-card {
  min-height: 180rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 8rpx 20rpx rgba(62, 95, 150, 0.08);
  padding: 24rpx 20rpx;
  box-sizing: border-box;
}

.feature-name {
  font-size: 30rpx;
  color: #1a2a3a;
  font-weight: 700;
}

.feature-desc {
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.45;
  color: rgba(26, 42, 58, 0.62);
}

</style>
