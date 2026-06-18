<template>
  <view class="portal-page">
    <view class="portal-bg"></view>
    <view class="scan-line"></view>
    <view class="shape shape-a"></view>
    <view class="shape shape-b"></view>

    <view class="portal-hero">
      <image class="portal-logo" src="/static/logo.png" mode="aspectFit"></image>
      <view class="kicker">COMMUNITY COMMAND</view>
      <view class="title">社区智眼</view>
      <view class="subtitle">选择你的身份，进入对应的智慧社区工作台</view>
    </view>

    <view class="role-panel">
      <view class="role-card role-card--manage" @tap="goManage">
        <view class="role-icon">
          <u-icon name="server-man" color="#ffffff" size="44rpx"></u-icon>
        </view>
        <view class="role-copy">
          <view class="role-title">管理端</view>
          <view class="role-desc">告警处置、监控管理、物业事务</view>
        </view>
        <u-icon name="arrow-right" color="#7dd3fc" size="30rpx"></u-icon>
      </view>

      <view class="role-card role-card--owner" @tap="goOwner">
        <view class="role-icon">
          <u-icon name="home" color="#ffffff" size="44rpx"></u-icon>
        </view>
        <view class="role-copy">
          <view class="role-title">业主端</view>
          <view class="role-desc">社区提醒、报修访客、随手拍</view>
        </view>
        <u-icon name="arrow-right" color="#7dd3fc" size="30rpx"></u-icon>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    goManage() {
      uni.redirectTo({ url: '/pages/manage/login/index' });
    },
    goOwner() {
      uni.redirectTo({ url: '/pages/owner/login/index' });
    },
  },
};
</script>

<style lang="scss" scoped>
.portal-page {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 54rpx 32rpx calc(54rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  background-color: #071525;
}

.portal-bg {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 8%, rgba(32, 214, 210, 0.28), transparent 260rpx),
    radial-gradient(circle at 82% 12%, rgba(24, 168, 255, 0.32), transparent 320rpx),
    linear-gradient(180deg, #071525 0%, #0d2740 58%, #0b1e35 100%);
  pointer-events: none;
}

.scan-line {
  position: absolute;
  left: 40rpx;
  right: 40rpx;
  top: 18%;
  height: 1rpx;
  background: linear-gradient(90deg, transparent, rgba(32, 214, 210, 0.74), transparent);
  opacity: 0.7;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(60rpx);
  pointer-events: none;
}

.shape-a {
  width: 420rpx;
  height: 420rpx;
  left: -170rpx;
  top: -120rpx;
  background: rgba(32, 214, 210, 0.2);
}

.shape-b {
  width: 480rpx;
  height: 480rpx;
  right: -190rpx;
  bottom: -140rpx;
  background: rgba(24, 168, 255, 0.22);
}

.portal-hero,
.role-panel {
  position: relative;
  z-index: 1;
}

.portal-hero {
  color: #eaf7ff;
}

.portal-logo {
  width: 112rpx;
  height: 112rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18rpx 42rpx rgba(0, 0, 0, 0.24);
}

.kicker {
  margin-top: 32rpx;
  color: #7dd3fc;
  font-size: 22rpx;
  font-weight: 900;
}

.title {
  margin-top: 12rpx;
  color: #ffffff;
  font-size: 56rpx;
  font-weight: 900;
  line-height: 1.08;
}

.subtitle {
  margin-top: 14rpx;
  color: rgba(234, 247, 255, 0.72);
  font-size: 25rpx;
  line-height: 1.5;
  font-weight: 700;
}

.role-panel {
  width: 100%;
  margin-top: 56rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.role-card {
  min-height: 136rpx;
  border-radius: 28rpx;
  padding: 24rpx;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.10);
  border: 1rpx solid rgba(125, 211, 252, 0.24);
  display: flex;
  align-items: center;
  gap: 18rpx;
  box-shadow: 0 18rpx 42rpx rgba(0, 0, 0, 0.16);
}

.role-card:active {
  transform: scale(0.98);
}

.role-card--manage {
  background: linear-gradient(135deg, rgba(11, 111, 198, 0.92), rgba(24, 168, 255, 0.78));
}

.role-card--owner {
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.88), rgba(32, 214, 210, 0.64));
}

.role-icon {
  width: 78rpx;
  height: 78rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.role-copy {
  min-width: 0;
  flex: 1;
}

.role-title {
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 900;
}

.role-desc {
  margin-top: 8rpx;
  color: rgba(234, 247, 255, 0.78);
  font-size: 22rpx;
  font-weight: 700;
}
</style>
