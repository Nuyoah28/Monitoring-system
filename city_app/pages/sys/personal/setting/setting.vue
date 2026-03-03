<template>
  <view
    style="
      height: 100vh;
      width: 100vw;
      position: relative;
      background-color: transparent;
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
      content: "本项目旨在开发一个智能视频监控系统,能够对医院重点区域进行实时监控,使用计算机视觉技术智能分析监控画面,实现对病人跌倒、抽烟等危险情况的预警。一旦检测到危险情况,能够通过 App 推送和网页弹窗等方式向医务人员发出预警,以便采取及时干预措施,防止事态进一步恶化,保障医院安全。",
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
      uni.removeStorage({
        key: "token",
        success: () => {
          uni.reLaunch({
            url: "/pages/sys/login/index",
          });
        },
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
  background-color: transparent;
  
  .backImg {
    position: absolute;
    width: 100%;
    
    .title {
      position: absolute;
      top: 0;
      z-index: 999;
      color: #1A2A3A;
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
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 122, 255, 0.1);
        border-radius: 50%;
        box-shadow: 0 4rpx 12rpx rgba(100, 150, 200, 0.1);
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
    border-radius: 32rpx;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 1);
    box-shadow: 0 16rpx 48rpx rgba(26, 42, 58, 0.08);
    
    .items {
      background: rgba(255, 255, 255, 0.9);
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
      border: 1px solid rgba(255, 255, 255, 0.5);
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
