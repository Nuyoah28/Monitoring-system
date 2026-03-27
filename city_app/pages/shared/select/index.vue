<template>
  <view class="portal-page">
    <view class="shape shape-a"></view>
    <view class="shape shape-b"></view>

    <view class="portal-card">
      <text class="title">选择登录端</text>
      <text class="subtitle">同一套系统，按身份进入对应应用</text>

      <view class="btn-group">
        <button class="role-btn manage" @tap="goManage">管理端登录</button>
        <button class="role-btn owner" @tap="goOwner">业主端登录</button>
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
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 40rpx;
  box-sizing: border-box;
}

.shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
}

.shape-a {
  width: 520rpx;
  height: 520rpx;
  left: -200rpx;
  top: -140rpx;
  background: rgba(0, 180, 216, 0.22);
}

.shape-b {
  width: 460rpx;
  height: 460rpx;
  right: -180rpx;
  bottom: -120rpx;
  background: rgba(0, 122, 255, 0.2);
}

.portal-card {
  width: 100%;
  max-width: 700rpx;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 32rpx;
  box-shadow: 0 16rpx 48rpx rgba(35, 68, 123, 0.1);
  padding: 60rpx 42rpx;
  box-sizing: border-box;
}

.title {
  display: block;
  color: #1a2a3a;
  font-size: 48rpx;
  font-weight: 800;
  text-align: center;
  letter-spacing: 2rpx;
}

.subtitle {
  display: block;
  margin-top: 12rpx;
  color: rgba(26, 42, 58, 0.68);
  font-size: 26rpx;
  text-align: center;
}

.btn-group {
  margin-top: 56rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.role-btn {
  height: 94rpx;
  border-radius: 47rpx;
  font-size: 32rpx;
  letter-spacing: 2rpx;
  font-weight: 700;
  border: none;

  &::after {
    border: none;
  }
}

.manage {
  color: #fff;
  background: linear-gradient(90deg, #007aff, #00b8d8);
}

.owner {
  color: #1a2a3a;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(0, 122, 255, 0.14);
}
</style>
