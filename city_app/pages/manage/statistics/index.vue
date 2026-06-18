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
            <text class="tab-text">趋势分析</text>
            <view class="indicator" v-if="choosen === 2"></view>
          </view>
        </view>

        <!-- 月份切换 -->
        <view class="month-picker-btn" @tap="showMonthPicker = true">
          <text class="month-btn-text">{{ selectedMonth }}月</text>
          <image class="month-arrow" src="/static/arrow-right.png" mode="aspectFit"></image>
        </view>
      </view>

      <!-- u-picker 隐藏容器 -->
      <view style="position: absolute; width: 0; height: 0; overflow: hidden;">
        <u-picker
          :show="showMonthPicker"
          :columns="monthColumns"
          keyName="label"
          title="选择年月"
          :showToolbar="true"
          @confirm="onMonthConfirm"
          @cancel="showMonthPicker = false"
        ></u-picker>
      </view>

      <view class="content-scroll-area">
        <real-time
          v-if="!(choosen - 1)"
          :year="selectedYear"
          :month="selectedMonth"
        ></real-time>
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
    const now = new Date();
    // 生成近 12 个月供选择
    const yearCols = [];
    const monthCols = [];
    for (let y = now.getFullYear() - 1; y <= now.getFullYear(); y++) {
      yearCols.push({ label: `${y}年`, value: y });
    }
    for (let m = 1; m <= 12; m++) {
      monthCols.push({ label: `${m}月`, value: m });
    }
    return {
      statusBarHeight: 0,
      choosen: 1,
      isShow: true,
      showMonthPicker: false,
      selectedYear: now.getFullYear(),
      selectedMonth: now.getMonth() + 1,
      monthColumns: [yearCols, monthCols],
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
    onMonthConfirm(e) {
      this.selectedYear  = e.value[0].value;
      this.selectedMonth = e.value[1].value;
      this.showMonthPicker = false;
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
    padding: 0 40rpx;
    box-sizing: border-box;
    z-index: 10;
    margin-bottom: 20rpx;
    margin-top: 20rpx;
    flex-shrink: 0;

    .top-tabs {
      display: flex;
      height: 72rpx;
      align-items: center;
      padding: 6rpx;
      border-radius: 999rpx;
      background: rgba(255, 255, 255, 0.94);
      border: 1rpx solid rgba(205, 225, 246, 0.9);
      box-shadow: 0 10rpx 22rpx rgba(3, 20, 39, 0.12);

      .tab-item + .tab-item {
        margin-left: 4rpx;
      }

      .tab-item {
        position: relative;
        min-width: 156rpx;
        height: 60rpx;
        border-radius: 999rpx;
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
        overflow: hidden;

        .tab-text {
          font-size: 25rpx;
          color: #61758e !important;
          font-weight: 800;
          transition: all 0.3s;
          text-shadow: none !important;
        }

        &.active {
          background: linear-gradient(135deg, #0b6fc6, #18a8ff) !important;

          .tab-text {
            color: #ffffff !important;
            font-size: 25rpx;
            font-weight: 900;
          }
        }

        .indicator {
          position: absolute;
          bottom: 7rpx;
          width: 32rpx;
          height: 4rpx;
          background: rgba(255, 255, 255, 0.82);
          border-radius: 999rpx;
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
      margin-right: 24rpx;
    }

    .month-picker-btn {
      margin-left: auto;
      display: flex;
      align-items: center;
      background: rgba(20, 112, 216, 0.08);
      border: 1.5rpx solid rgba(20, 112, 216, 0.2);
      border-radius: 999rpx;
      padding: 10rpx 20rpx;
      transition: all 0.15s;

      &:active {
        background: rgba(20, 112, 216, 0.15);
        transform: scale(0.97);
      }

      .month-arrow {
        width: 20rpx;
        height: 20rpx;
        margin-left: 8rpx;
        transform: rotate(90deg);
        opacity: 0.8;
      }
    }

    .month-btn-text {
      font-size: 28rpx;
      font-weight: 700;
      color: #0b6fc6;
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
