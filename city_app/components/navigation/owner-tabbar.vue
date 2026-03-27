<template>
  <view class="owner-tabbar">
    <view
      class="tab-item"
      :class="{ active: current === 'home' }"
      @tap="go('/pages/owner/home/index')"
    >
      <image class="tab-icon" src="/static/tabBar/chart.png" mode="aspectFit" />
      <text class="tab-text">主页</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'ai' }"
      @tap="go('/pages/owner/ai/index')"
    >
      <image class="tab-icon" src="/static/tabBar/GPT.png" mode="aspectFit" />
      <text class="tab-text">Agent</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'personal' }"
      @tap="go('/pages/owner/personal/index')"
    >
      <image class="tab-icon" src="/static/tabBar/personal.png" mode="aspectFit" />
      <text class="tab-text">个人中心</text>
    </view>
  </view>
</template>

<script>
export default {
  props: {
    current: {
      type: String,
      default: 'home',
    },
  },
  methods: {
    go(url) {
      if ((this.current === 'home' && url.includes('/home/')) || (this.current === 'ai' && url.includes('/ai/')) || (this.current === 'personal' && url.includes('/personal/'))) {
        return;
      }
      uni.reLaunch({ url });
    },
  },
};
</script>

<style scoped lang="scss">
.owner-tabbar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(20rpx + env(safe-area-inset-bottom));
  height: 96rpx;
  border-radius: 48rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(0, 122, 255, 0.12);
  box-shadow: 0 10rpx 26rpx rgba(24, 72, 143, 0.16);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 1200;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 140rpx;
  height: 80rpx;
  border-radius: 40rpx;
}

.tab-icon {
  width: 32rpx;
  height: 32rpx;
  opacity: 0.58;
}

.tab-text {
  margin-top: 4rpx;
  font-size: 20rpx;
  color: #6a7990;
}

.tab-item.active {
  background: rgba(0, 122, 255, 0.12);
}

.tab-item.active .tab-icon {
  opacity: 1;
}

.tab-item.active .tab-text {
  color: #007aff;
  font-weight: 700;
}
</style>
