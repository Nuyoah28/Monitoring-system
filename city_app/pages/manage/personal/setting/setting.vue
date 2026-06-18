<template>
  <view
    class="setting-page"
    style="
      height: 100vh;
      width: 100vw;
      position: relative;
    "
  >
    <view class="setBox" :style="{ height: safeHeight + 'px' }">
      <view class="backImg">
        <view class="title">
          <view class="backing" @click="back">
            <u-icon name="arrow-left" color="#1A2A3A" size="44rpx"></u-icon>
          </view>
          <h3>设置</h3>
        </view>
      </view>
      
      <view class="content">
        <view class="items" @click="showAbout = true">
          <view class="text"> 关于 </view>
          <view class="img">
            <image
              src="../../../../static/warn-none.png"
              mode="aspectFit"
            ></image>
          </view>
        </view>
        <view class="items" @click="clear">
          <view class="text"> 清理缓存 </view>
          <view class="img">
            <image
              src="../../../../static/rubbish-none.png"
              mode="aspectFit"
            ></image>
          </view>
        </view>
        <view class="items" @click="exit">
          <view class="text"> 退出登录 </view>
          <view class="img">
            <image src="../../../../static/exit.png" mode="aspectFit"></image>
          </view>
        </view>
      </view>

      <u-modal
        :show="showAbout"
        :title="title"
        :content="content"
        :closeOnClickOverlay="true"
        @confirm="showAbout = false"
        @close="showAbout = false"
      ></u-modal>
      <u-modal
        :show="showClear"
        title="清理成功"
        :closeOnClickOverlay="true"
        @confirm="showClear = false"
        @close="showClear = false"
      ></u-modal>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      safeHeight: 0,
      showAbout: false,
      showClear: false,
      title: "关于",
      content: "本系统面向社区重点区域的智能化值守场景，支持视频监控、异常识别、报警推送、处置闭环与环境车位管理，帮助管理人员及时发现风险并完成联动处理。",
      timer: null,
    };
  },
  onLoad() {
    this.safeHeight = uni.getWindowInfo().safeArea.height;
  },
  methods: {
    back() {
      uni.navigateBack();
    },
    exit() {
      uni.removeStorageSync("token");
      uni.removeStorageSync("userId");
      uni.removeStorageSync("appType");
      uni.reLaunch({
        url: "/pages/shared/select/index",
      });
    },
    clear() {
      uni.showLoading({
      	title:'清理中',
      })
	  setTimeout(()=>{
		  uni.hideLoading();
		  uni.showToast({
		  	icon:'success',
			duration:1000,
			title:'清理完成'
		  })
	  },2000)
    },
  },
};
</script>

<style lang="scss" scoped>
.setBox {
  position: absolute;
  width: 100%;
  bottom: 0;
  background:
    linear-gradient(125deg, rgba(32, 214, 210, 0.14) 0%, rgba(32, 214, 210, 0) 34%),
    linear-gradient(180deg, #071525 0%, #0d2740 300rpx, #edf5ff 640rpx, #f8fbff 100%);
  
  .backImg {
    position: absolute;
    width: 100%;
    
    .title {
      position: absolute;
      top: 0;
      z-index: 999;
      color: #eaf7ff;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      width: 100%;
      padding: 26rpx 36rpx;
      box-sizing: border-box;
      
      .backing {
        width: 60rpx;
        height: 60rpx;
        margin-right: 12rpx;
        display: flex;
        justify-content: center;
        align-items: center;
        background: rgba(255, 255, 255, 0.94);
        border: 1rpx solid rgba(205, 225, 246, 0.9);
        border-radius: 50%;
        box-shadow: 0 10rpx 22rpx rgba(3, 20, 39, 0.16);
      }
      
      h3 {
        font-weight: bold;
        font-size: 36rpx;
      }
    }
  }
  
  .content {
    width: 90%;
    box-sizing: border-box;
    position: absolute;
    top: 25%;
    left: 50%;
    transform: translate(-50%);
    padding: 40rpx 30rpx;
    border-radius: 28rpx;
    background: rgba(255, 255, 255, 0.96);
    border: 1rpx solid rgba(205, 225, 246, 0.92);
    box-shadow: 0 14rpx 34rpx rgba(4, 29, 54, 0.14);
    
    .items {
      background: #f5faff;
      height: 110rpx;
      width: 100%;
      margin-bottom: 30rpx; /* Use margin-bottom for spacing */
      border-radius: 24rpx;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 30rpx;
      box-sizing: border-box;
      box-shadow: 0 4rpx 16rpx rgba(100, 150, 200, 0.05);
      border: 1rpx solid #d4e7fa;
      transition: transform 0.2s, box-shadow 0.2s;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      &:active {
        transform: scale(0.98);
        box-shadow: 0 2rpx 8rpx rgba(100, 150, 200, 0.05);
      }
      
      .text {
        margin-left: 10rpx;
        color: #1A2A3A;
        font-weight: 600;
        font-size: 32rpx;
      }
      
      .img {
        height: 40rpx;
        width: 40rpx;
        image {
          height: 100%;
          width: 100%;
          filter: brightness(0.6) sepia(1) hue-rotate(180deg) saturate(3); /* Darken icon slightly */
        }
      }
    }
  }
}
</style>
