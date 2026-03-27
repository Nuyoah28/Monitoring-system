<template>
  <view class="feature-page">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
    </view>
    <view class="title">空闲车位引导</view>
    <view class="card">这里可接入车位余量、推荐区域与一键导航。</view>
  </view>
</template>

<script>
export default {
  methods: {
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/owner/home/index' });
    },
  },
};
</script>

<style lang="scss" scoped>
.feature-page { min-height: 100vh; padding: 30rpx; box-sizing: border-box; }
.top-bar { margin-bottom: 16rpx; }
.back-btn { width: 64rpx; height: 64rpx; border-radius: 32rpx; background: rgba(255, 255, 255, 0.9); display: flex; align-items: center; justify-content: center; }
.title { font-size: 42rpx; font-weight: 800; color: #1a2a3a; margin-bottom: 20rpx; }
.card { border-radius: 22rpx; background: rgba(255,255,255,0.86); padding: 24rpx; color: #1a2a3a; line-height: 1.6; }
</style>
