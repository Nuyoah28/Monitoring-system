<template>
  <view class="main">
    <view class="inner" v-if="isShow">
      <view class="header-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
        <view class="back-btn" @tap="goBackToAlarm">
          <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
        </view>
        <view class="top-tabs">
          <view
            class="tab-item"
            :class="{ active: choosen === 1 }"
            @click="chooseOne()"
          >
            <text class="tab-text">数据总览</text>
            <view class="indicator" v-if="choosen === 1"></view>
          </view>

          <view
            class="tab-item"
            :class="{ active: choosen === 2 }"
            @click="chooseTwo()"
          >
            <text class="tab-text">历史数据</text>
            <view class="indicator" v-if="choosen === 2"></view>
          </view>
        </view>

        <view class="setting-btn" @click="jump">
          <u-icon name="setting" color="#666" size="44rpx"></u-icon>
        </view>
      </view>

      <view class="content-scroll-area">
        <real-time v-if="!(choosen - 1)"></real-time>
        <history-data v-if="choosen - 1"></history-data>
      </view>
    </view>
  </view>
</template>

<script>
import realTime from '../dateWatcher/realTime.vue'
import historyData from '../dateWatcher/historyData.vue'

export default {
  components: { realTime, historyData },
  data() {
    return {
      statusBarHeight: 0,
      choosen: 1,
      isShow: true,
    }
  },
  onLoad() {
    const info = uni.getWindowInfo()
    this.statusBarHeight = info.statusBarHeight || 20
  },
  onShow() {
    this.isShow = true
  },
  onHide() {
    this.isShow = false
  },
  methods: {
    goBackToAlarm() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack()
        return
      }
      uni.navigateTo({
        url: '/pages/manage/realtime/realtime',
      })
    },
    chooseOne() {
      this.choosen = 1
      this.$forceUpdate()
    },
    chooseTwo() {
      this.choosen = 2
      this.$forceUpdate()
    },
    jump() {
      uni.navigateTo({
        url: '/pages/manage/personal/setting/setting',
      })
    },
  },
}
</script>

<style lang="scss" scoped>
.main {
  width: 100vw;
  background: transparent;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .inner {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .header-nav {
    width: 100%;
    min-height: 100rpx;
    background-color: transparent;
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 24rpx;
    padding: 0 40rpx;
    box-sizing: border-box;
    z-index: 10;
    margin-bottom: 20rpx;
    margin-top: 20rpx;
    flex-shrink: 0;

    .top-tabs {
      display: flex;
      gap: 50rpx;
      height: 80rpx;
      align-items: center;

      .tab-item {
        position: relative;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;

        .tab-text {
          font-size: 32rpx;
          color: rgba(26, 42, 58, 0.6);
          font-weight: 500;
          transition: all 0.3s;
        }

        &.active {
          .tab-text {
            color: #1a2a3a;
            font-size: 36rpx;
            font-weight: bold;
          }
        }

        .indicator {
          position: absolute;
          bottom: 0;
          width: 40rpx;
          height: 8rpx;
          background: linear-gradient(90deg, #00d2ff, #007aff);
          border-radius: 4rpx;
          animation: slideIn 0.3s ease;
        }
      }
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
      flex-shrink: 0;
    }

    .setting-btn {
      width: 60rpx;
      height: 60rpx;
      background: rgba(0, 0, 0, 0.05);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      transition: background 0.2s;
      margin-left: auto;

      &:active {
        background: rgba(0, 0, 0, 0.1);
      }
    }
  }

  .content-scroll-area {
    flex: 1;
    width: 100%;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scaleX(0.5);
  }
  to {
    opacity: 1;
    transform: scaleX(1);
  }
}
</style>
