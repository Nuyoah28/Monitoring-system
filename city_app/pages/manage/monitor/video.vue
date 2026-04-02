<template>
  <view class="video-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="header">
      <view class="back" @tap="goBack"><u-icon name="arrow-left" size="34rpx" color="#2c3e50" /></view>
      <view class="title">{{ name || '监控视频' }}</view>
      <view class="placeholder"></view>
    </view>

    <view class="player-wrap">
      <video :src="video" :autoplay="true" :controls="true" :show-fullscreen-btn="true" class="player"></video>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarHeight: 0,
      name: '',
      video: '',
    };
  },
  onLoad(query) {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    this.name = decodeURIComponent(query.name || '');
    this.video = decodeURIComponent(query.video || '');
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
  },
};
</script>

<style scoped lang="scss">
.video-page {
  min-height: 100vh;
  background: #eef5fd;
  padding: 0 20rpx 30rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8rpx 0 16rpx;
}

.back, .placeholder {
  width: 52rpx;
  height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title {
  font-size: 32rpx;
  color: #213446;
  font-weight: 700;
}

.player-wrap {
  border-radius: 20rpx;
  overflow: hidden;
  background: #000;
}

.player {
  width: 100%;
  height: 480rpx;
}
</style>
