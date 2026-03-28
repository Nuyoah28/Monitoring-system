<template>
  <view class="property-page">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view>
        <view class="title">物业管理</view>
        <view class="sub">点击板块进入具体功能页面</view>
      </view>
      <view class="setting-btn" @tap="jumpSetting">
        <u-icon name="setting" color="#666" size="44rpx"></u-icon>
      </view>
    </view>

    <view class="grid">
      <view class="feature-card" @tap="goFeature('/pages/manage/property/visitor/index')">
        <view class="feature-name">访客登记管理</view>
        <view class="feature-desc">新增、查看和删除访客登记</view>
      </view>

      <view class="feature-card" @tap="goFeature('/pages/manage/property/notice/index')">
        <view class="feature-name">物业通知管理</view>
        <view class="feature-desc">发布并查看面向业主的通知</view>
      </view>

      <view class="feature-card" @tap="goFeature('/pages/manage/property/repair/index')">
        <view class="feature-name">报修工单管理</view>
        <view class="feature-desc">仅查看和删除工单，不提供录入</view>
      </view>

      <view class="feature-card" @tap="goFeature('/pages/manage/property/parking/index')">
        <view class="feature-name">车位检测管理</view>
        <view class="feature-desc">新增、查看和删除车位检测记录</view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarHeight: 0,
    }
  },
  onLoad() {
    const info = uni.getWindowInfo()
    this.statusBarHeight = info.statusBarHeight || 20
  },
  methods: {
    jumpSetting() {
      uni.navigateTo({
        url: '/pages/manage/personal/setting/setting',
      })
    },
    goFeature(url) {
      uni.navigateTo({ url })
    },
  },
}
</script>

<style lang="scss" scoped>
.property-page {
  min-height: 100vh;
  padding: 0 24rpx 30rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22rpx;
}

.title {
  font-size: 40rpx;
  font-weight: 800;
  color: #1a2a3a;
}

.sub {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: rgba(26, 42, 58, 0.62);
}

.setting-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.88);
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8rpx 20rpx rgba(32, 74, 126, 0.1);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.feature-card {
  min-height: 196rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 8rpx 20rpx rgba(62, 95, 150, 0.08);
  padding: 24rpx 20rpx;
  box-sizing: border-box;

  &:active {
    transform: scale(0.98);
  }
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
