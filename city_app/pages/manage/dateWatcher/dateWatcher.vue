<template>
  <view class="main">
    <view class="inner" v-if="isShow">
      
      <!-- 重新设计的顶部导航栏 -->
      <view class="header-nav" :style="{ paddingTop: statusBarHeight + 'px' }">
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
        
        <!-- 使用 u-icon 替换原本的本地设置按钮图片 -->
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
import realTime from "./realTime.vue";
import historyData from "./historyData.vue";
export default {
  components: { realTime, historyData },
  data() {
    return {
      statusBarHeight: 0, // 新增状态栏高度以防遮挡
      selected: false,
      choosen: 1,
	  isShow:true,
    };
  },
  onLoad() {
    const info = uni.getWindowInfo();
    // 只获取设备顶部状态栏高度，H5 和小程序下保证导航条不被刘海遮挡
    this.statusBarHeight = info.statusBarHeight || 20; 
  },
  onShow(){
	  this.isShow = true
  },
  onHide(){
	  this.isShow = false
  },
  methods: {
    chooseOne() {
      this.choosen = 1;
      this.$forceUpdate();
    },
    chooseTwo() {
      this.choosen = 2;
      this.$forceUpdate();
    },
    jump() {
      uni.navigateTo({
        url: "/pages/manage/personal/setting/setting",
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.main {
  width: 100vw;
  /* 承接全局赛博清晨背景 */
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
  
  /* 现代化的顶部透明导航条，融入深色背景 */
  .header-nav {
    width: 100%;
    /* 采用自适应高度以留足 padding 收容空间 */
    min-height: 100rpx;
    background-color: transparent; 
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 40rpx;
    box-sizing: border-box;
    z-index: 10;
    margin-bottom: 20rpx;
    margin-top: 20rpx; /* 在顶部额外预留空气间距防止设备贴边 */
    flex-shrink: 0; /* 绝对不要被压缩 */
    
    .top-tabs {
      display: flex;
      gap: 50rpx;
      height: 80rpx; /* 固定内部元素高度保证对齐 */
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
          color: rgba(26, 42, 58, 0.6); /* 浅色背景下改用深色文字 */
          font-weight: 500;
          transition: all 0.3s;
        }
        
        &.active {
          .tab-text {
            color: #1A2A3A; /* 高亮深海蓝 */
            font-size: 36rpx;
            font-weight: bold;
          }
        }
        
        .indicator {
          position: absolute;
          bottom: 0;
          width: 40rpx;
          height: 8rpx;
          /* 科技蓝高亮底线 */
          background: linear-gradient(90deg, #00d2ff, #007aff);
          border-radius: 4rpx;
          animation: slideIn 0.3s ease;
        }
      }
    }
    
    .setting-btn {
      width: 60rpx;
      height: 60rpx;
      background: rgba(0, 0, 0, 0.05); /* 浅色背景下的微暗玻璃感 */
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      transition: background 0.2s;
      
      &:active {
        background: rgba(0, 0, 0, 0.1);
      }
    }
  }

  .content-scroll-area {
    flex: 1;
    width: 100%;
    min-height: 0; /* 关键：允许 flex 子元素自由滚动而不撑破父容器 */
    overflow: hidden; 
    display: flex;
    flex-direction: column;
  }
}

@keyframes slideIn {
  from { opacity: 0; transform: scaleX(0.5); }
  to { opacity: 1; transform: scaleX(1); }
}
</style>
