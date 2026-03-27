<template>
  <view class="page-wrap">
    <view class="mainBox" :style="{ height: safeHeight + 'px' }">
      <view class="backImg">
        <view class="title" :style="{ paddingTop: statusBarHeight + 'px' }">
          <h2>个人中心</h2>
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
              uid: {{ uid || '--' }}
            </view>
          </view>
        </view>
        <view class="command">
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
          <view class="items" @tap="showAbout">
            <view class="left">
              <view class="img">
                <image
                  src="../../../static/warn-none.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="text"> 关于 </view>
            </view>
            <view class="img">
              <image
                src="../../../static/arrow-right.png"
                mode="aspectFit"
              ></image>
            </view>
          </view>
          <view class="items" @tap="clearCache">
            <view class="left">
              <view class="img">
                <image
                  src="../../../static/rubbish-none.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="text"> 清理缓存 </view>
            </view>
            <view class="img">
              <image
                src="../../../static/arrow-right.png"
                mode="aspectFit"
              ></image>
            </view>
          </view>
          <view class="items" @tap="logout">
            <view class="left">
              <view class="img">
                <image
                  src="../../../static/exit.png"
                  mode="aspectFit"
                ></image>
              </view>
              <view class="text"> 退出登录 </view>
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
      uid: "",
      username: "",
      statusBarHeight: 0,
      aboutContent:
        "本项目旨在开发一个智能视频监控系统,能够对重点区域进行实时监控,使用计算机视觉技术智能分析监控画面,实现对跌倒、抽烟等危险情况的预警,并通过 App 推送和网页弹窗提醒值守人员及时干预。",
    };
  },
  onShow() {
    const info = uni.getWindowInfo();
    this.safeHeight = info.safeArea.height;
    this.statusBarHeight = info.statusBarHeight || 20;
    this.phone = uni
      .getStorageSync("phone")
      .replace(/(\d{3})\d{4}(\d{4})/, "$1****$2");
    this.uid = uni.getStorageSync("userId") || "";
    this.username = uni.getStorageSync("username");
  },
  methods: {
    jump(url) {
      // console.log(url);
      uni.navigateTo({
        url: url,
      });
    },
    showAbout() {
      uni.showModal({
        title: "关于",
        content: this.aboutContent,
        showCancel: false,
      });
    },
    clearCache() {
      uni.showLoading({ title: "清理中" });
      setTimeout(() => {
        uni.hideLoading();
        uni.showToast({
          icon: "success",
          duration: 1000,
          title: "清理完成",
        });
      }, 1200);
    },
    logout() {
      uni.showModal({
        title: "退出登录",
        content: "确认退出当前账号吗？",
        success: (res) => {
          if (!res.confirm) return;
          uni.removeStorageSync("token");
          uni.removeStorageSync("userId");
          uni.reLaunch({
            url: "/pages/manage/login/index",
          });
        },
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.page-wrap {
  height: 100vh;
  width: 100vw;
  position: relative;
  background: radial-gradient(1200rpx 520rpx at 10% -10%, rgba(81, 150, 255, 0.16) 0%, rgba(81, 150, 255, 0) 62%),
    radial-gradient(1000rpx 500rpx at 100% 12%, rgba(91, 206, 255, 0.14) 0%, rgba(91, 206, 255, 0) 64%);
}

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
        justify-content: center;
        width: 100vw;
        padding: 0 40rpx;
        box-sizing: border-box;
        height: 100rpx;
        margin-top: 8rpx;

      h2 {
        font-weight: bold;
        font-size: 40rpx;
        letter-spacing: 2rpx;
      }
    }
  }
  
  .content {
    width: 90%;
    box-sizing: border-box;
    padding: 54rpx 40rpx;
    padding-bottom: 80rpx;
    border-radius: 32rpx;
    /* 核心毛玻璃效果 */
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 1);
    box-shadow: 0 16rpx 48rpx rgba(26, 42, 58, 0.08);
    position: absolute;
    top: 22%;
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
        flex-shrink: 0;
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
          font-size: 40rpx;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          max-width: 420rpx;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
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
        position: relative;

        &::after {
          content: "";
          position: absolute;
          left: 72rpx;
          right: 72rpx;
          bottom: 0;
          height: 1px;
          background: linear-gradient(90deg, rgba(40, 98, 182, 0), rgba(40, 98, 182, 0.12), rgba(40, 98, 182, 0));
          opacity: 0;
          transition: opacity 0.2s;
        }
        
        &:active {
          transform: scale(0.98);
          box-shadow: 0 2rpx 8rpx rgba(100, 150, 200, 0.05);

          &::after {
            opacity: 1;
          }
        }
        
        .left {
          display: flex;
          width: 80%;
          align-items: center;
          
          .text {
            margin-left: 20rpx;
            color: #1A2A3A;
            font-weight: 600;
            font-size: 30rpx;
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
