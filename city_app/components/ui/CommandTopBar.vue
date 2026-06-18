<template>
  <view class="command-top-bar">
    <view class="command-top-bar__btn" @tap="$emit('back')">
      <u-icon name="arrow-left" color="#0f2238" size="34rpx"></u-icon>
    </view>
    <view class="command-top-bar__main">
      <view class="command-top-bar__title">{{ title }}</view>
      <view class="command-top-bar__subtitle" v-if="subtitle">{{ subtitle }}</view>
    </view>
    <view class="command-top-bar__btn" @tap="$emit('right')">
      <u-icon :name="rightIcon" color="#0f2238" size="32rpx"></u-icon>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CommandTopBar',
  props: {
    title: { type: String, default: '' },
    subtitle: { type: String, default: '' },
    rightIcon: { type: String, default: 'setting' },
  },
};
</script>

<style scoped lang="scss">
.command-top-bar {
  min-height: 78rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.command-top-bar__btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(205, 225, 246, 0.9);
  box-shadow: 0 10rpx 22rpx rgba(3, 20, 39, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.command-top-bar__main {
  min-width: 0;
  flex: 1;
  text-align: center;
}

.command-top-bar__title {
  color: #eaf7ff;
  font-size: 32rpx;
  font-weight: 900;
  line-height: 1.2;
}

.command-top-bar__subtitle {
  margin-top: 4rpx;
  color: rgba(234, 247, 255, 0.72);
  font-size: 20rpx;
  font-weight: 700;
}
</style>
