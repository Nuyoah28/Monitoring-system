<template>
  <view
    style="
      height: 100vh;
      width: 100vw;
      position: relative;
      background-color: transparent;
    "
  >
    <view class="mainBox" :style="{ height: safeHeight + 'px' }">
      <view class="backImg">
        <view class="title" :style="{ paddingTop: statusBarHeight + 'px' }">
          <h2>个人中心</h2>
          <view class="setting-btn" @click="jump('/pages/sys/personal/setting/setting')">
            <u-icon name="setting" color="#1A2A3A" size="44rpx"></u-icon>
          </view>
        </view>
      </view>

      <view class="content">
        <view class="inform">
          <view class="avatar">
            <image
              src="../../../static/avatar.png"
              mode="aspectFit"
            ></image>
          </view>
          <view class="user">
            <view class="name">
              {{ username }}
            </view>
            <view class="phone">
              {{ phone }}
            </view>
          </view>
        </view>
        <view class="command">
          <view
            class="items"
            @tap="jump('/pages/sys/personal/setting/setting')"
          >
            <view class="left">
              <view class="img">
                <image
                  src="../../../static/431f6795-3757-42bc-bea2-6bf124b64131.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="text"> 前往设置 </view>
            </view>
            <view class="img">
              <image
                src="../../../static/arrow-right.png"
                mode="aspectFit"
              ></image>
            </view>
          </view>
          <view class="items" @tap="jump('/pages/sys/personal/edit/edit')">
            <view class="left">
              <view class="img">
                <image
                  src="../../../static/f810fcf9-a1b3-43f2-b2c4-55a7ce72c064.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="text"> 修改个人信息 </view>
            </view>
            <view class="img">
              <image
                src="../../../static/arrow-right.png"
                mode="aspectFit"
              ></image>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      safeHeight: 0,
      phone: "",
      username: "",
      statusBarHeight: 0,
    };
  },
  onShow() {
    const info = uni.getWindowInfo();
    this.safeHeight = info.safeArea.height;
    this.statusBarHeight = info.statusBarHeight || 20;
    this.phone = uni
      .getStorageSync("phone")
      .replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
    this.username = uni.getStorageSync("username");
  },
  methods: {
    jump(url) {
      // console.log(url);
      uni.navigateTo({
        url: url,
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.mainBox {
  position: absolute;
  width: 100%;
  bottom: 0;
  background-color: transparent; /* 透出全局背景 */
  
  .backImg {
    position: absolute;
    width: 100%;
    
    .title {
      position: absolute;
      top: 0;
      z-index: 999;
      color: #1A2A3A; /* 深色文字 */
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100vw;
      padding: 0 40rpx;
      box-sizing: border-box;
      height: 100rpx;
      margin-top: 20rpx;

      h2 {
        font-weight: bold;
      }

      .setting-btn {
        width: 60rpx;
        height: 60rpx;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 122, 255, 0.1);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4rpx 12rpx rgba(100, 150, 200, 0.1);
      }
    }
  }
  
  .content {
    width: 90%;
    box-sizing: border-box;
    padding: 50rpx 40rpx;
    padding-bottom: 80rpx;
    border-radius: 32rpx;
    /* 核心毛玻璃效果 */
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 1);
    box-shadow: 0 16rpx 48rpx rgba(26, 42, 58, 0.08);
    position: absolute;
    top: 25%;
    left: 50%;
    transform: translate(-50%);
    
    .inform {
      display: flex;
      justify-content: flex-start;
      align-items: flex-end;
      padding-bottom: 40rpx;
      margin-bottom: 60rpx;
      border-bottom: 1px solid rgba(26, 42, 58, 0.1);
      
      .avatar {
        background-color: #fff;
        width: 120rpx;
        height: 120rpx;
        border: 2px solid #FFFFFF;
        box-shadow: 0 8rpx 24rpx rgba(0, 122, 255, 0.15);
        border-radius: 20rpx;
        overflow: hidden;
        image {
          width: 100%;
          height: 100%;
        }
      }
      
      .user {
        margin-left: 30rpx;
        color: #1A2A3A;
        font-weight: bold;
        
        .name {
          margin-bottom: 12rpx;
          font-size: 42rpx;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        
        .phone {
          font-size: 24rpx;
          color: rgba(26, 42, 58, 0.6);
          font-weight: 500;
        }
      }
    }
    
    .command {
      width: 100%;
      
      .items {
        background: rgba(255, 255, 255, 0.9);
        height: 110rpx;
        width: 100%;
        margin-top: 30rpx;
        border-radius: 24rpx;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 30rpx;
        box-sizing: border-box;
        box-shadow: 0 4rpx 16rpx rgba(100, 150, 200, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: transform 0.2s, box-shadow 0.2s;
        
        &:active {
          transform: scale(0.98);
          box-shadow: 0 2rpx 8rpx rgba(100, 150, 200, 0.05);
        }
        
        .left {
          display: flex;
          width: 80%;
          align-items: center;
          
          .text {
            margin-left: 20rpx;
            color: #1A2A3A;
            font-weight: 600;
            font-size: 32rpx;
            display: flex;
            align-items: center;
          }
        }
        
        .img {
          height: 40rpx;
          width: 40rpx;
          image {
            height: 100%;
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
