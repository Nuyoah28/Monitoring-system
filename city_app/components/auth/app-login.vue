<template>
  <view class="loginBox">
    <view class="bg-shape shape-1"></view>
    <view class="bg-shape shape-2"></view>
    <view class="bg-shape shape-3"></view>

    <view class="login-container">
      <view class="header">
        <text class="title">社区智眼</text>
        <view class="mainTitle">基于深度学习和边缘计算的智慧社区安防系统</view>
      </view>

      <view class="glass-card logContent">
        <text class="card-title">LOGIN</text>

        <view class="form-group">
          <view class="input-item">
            <view class="iconBox">
              <svg class="svg-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" stroke="#5672b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M20 21C20 18.2386 16.4183 16 12 16C7.58172 16 4 18.2386 4 21" stroke="#5672b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </view>
            <input
              class="input custom-input"
              type="text"
              v-model="username"
              placeholder="请输入用户名"
              placeholder-style="color:#A0B2D4"
            />
          </view>

          <view class="input-item">
            <view class="iconBox">
              <svg class="svg-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="5" y="11" width="14" height="10" rx="2" stroke="#5672b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 11V7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7V11" stroke="#5672b9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </view>
            <input
              class="input custom-input"
              v-model="password"
              password
              type="text"
              placeholder="请输入密码"
              placeholder-style="color:#A0B2D4"
            />
          </view>

          <view class="input-item" style="border: none; background: transparent; padding: 0;">
            <button class="btn modern-btn" @tap="jump">登录</button>
          </view>

          <view class="input-item term-box" style="border: none; background: transparent; justify-content: center;">
            <checkbox-group @change="checked = !checked">
              <label class="deal-wrapper">
                <checkbox class="theme-checkbox" style="transform: scale(0.65);" value="true" :checked="checked" color="#007aff"/>
                <text class="deal">
                  登录即代表您已阅读并同意
                  <span class="link" @tap.stop="changeShow">用户协议</span>
                  与
                  <span class="link" @tap.stop="changeShow">隐私政策</span>
                </text>
              </label>
            </checkbox-group>
          </view>
        </view>
      </view>

      <view class="footer-more">
        <view class="text-line">
          <view class="line"></view>
          <view class="word">DEVELOPED BY UNIAPP AND YOLOV8</view>
          <view class="line"></view>
        </view>
      </view>
    </view>

    <u-modal
      :show="isShow"
      :closeOnClickOverlay="true"
      @close="isShow = false"
      @confirm="isShow = false"
      title="用户协议与隐私政策"
      confirmColor="#007aff"
    >
      <scroll-view scroll-y="true" style="height: 60vh;">
        <view class="modal-content">
          <p>
            欢迎使用我们的服务！在使用本应用程序之前，请仔细阅读以下用户协议。<br />用户协议规定了您与我们之间的权利和责任。通过使用本应用程序，即表示您同意遵守以下条款和条件。
          </p>
          <h4>1. 服务接受与使用</h4>
          <p>1.1 您确认并同意，您仅在合法、合规的目的下使用本应用程序，并遵守适用的法律法规。</p>
          <p>1.2 您应确保所提供的个人信息和数据的准确性和完整性，并对您提供的信息和数据的安全负责。</p>
          <p>1.3 您不得使用本应用程序进行任何违法、欺诈、侵权、虚假、威胁、骚扰、诽谤、淫秽、攻击性或其他不当行为。</p>
          <h4>2. 知识产权</h4>
          <p>2.1 本应用程序及其相关内容（包括但不限于文字、图像、音频、视频、标识、商标、服务标识等）的知识产权归属于我们或相关权利人所有。</p>
          <p>2.2 未经我们或相关权利人明确授权，您不得复制、修改、传播、展示、使用或以其他方式侵犯知识产权的行为。</p>
          <h4>3. 隐私保护</h4>
          <p>3.1 我们将按照隐私政策的规定收集、使用、存储和保护您的个人信息。</p>
          <p>3.2 您理解并同意，为了提供更好的服务，我们可能会与第三方共享您的个人信息，但我们将采取合理的措施保护您的个人信息的安全和保密性。</p>
          <h4>4. 免责声明</h4>
          <p>4.1 您理解并同意，您使用本应用程序的风险由您自行承担。本应用程序提供的服务仅按照现有技术和条件提供，不对服务的及时性、安全性、准确性做出任何明示或暗示的保证。</p>
          <p>4.2 您理解并同意，我们不对由于以下原因导致的任何直接或间接损失承担责任：网络故障、计算机病毒、黑客攻击、系统不稳定、第三方服务故障等。</p>
          <h4>5. 终止与修改</h4>
          <p>5.1 我们有权根据实际情况，在任何时候终止或修改本应用程序的部分或全部功能。</p>
          <p>5.2 如您违反本用户协议的任何条款，我们有权立即终止您使用本应用程序的权利。</p>
          <h4>6. 其他条款</h4>
          <p>6.1 本用户协议适用中华人民共和国的法律。</p>
          <p>6.2 如本用户协议的任何条款被认定为无效或不可执行，不影响其他条款的有效性。</p>
          <p>6.3 本用户协议构成您与我们之间的完整协议，取代您与我们之间的任何其他口头或书面协议。</p>
          <p>请在使用本应用程序之前仔细阅读并理解以上用户协议。如您对协议内容有任何疑问，请与我们联系。感谢您的合作和支持！</p>
        </view>
      </scroll-view>
    </u-modal>
  </view>
</template>

<script>
import websocket from '@/common/websocket.js';

export default {
  props: {
    loginApi: {
      type: String,
      required: true,
    },
    successUrl: {
      type: String,
      required: true,
    },
    appType: {
      type: String,
      required: true,
    },
    enableWebsocket: {
      type: Boolean,
      default: false,
    },
    useSwitchTab: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      isShow: false,
      password: '',
      username: '',
      checked: false,
    };
  },
  methods: {
    changeShow() {
      this.isShow = true;
    },
    jump() {
      if (!this.checked) {
        uni.showToast({
          title: '请仔细阅读并勾选用户协议与隐私政策',
          duration: 2000,
          icon: 'none',
        });
        return;
      }

      const data = {
        userName: this.username,
        password: this.password,
      };

      uni.showLoading({ title: '登录中...' });
      uni.$http
        .post(this.loginApi, data)
        .then(({ data }) => {
          if (data.code === 'A1000') {
            uni.$showMsg(data.message);
            return;
          }
          if (data.code !== '00000') {
            uni.$showMsg(data.message || '登录失败');
            return;
          }

          const userData = data.data || {};
          uni.setStorageSync('phone', this.username);
          uni.setStorageSync('username', userData.name || this.username);
          uni.setStorageSync('userId', userData.id || '');
          uni.setStorageSync('token', userData.token || '');
          uni.setStorageSync('appType', this.appType);

          if (this.enableWebsocket && userData.id) {
            websocket.connect(userData.id);
          }

          uni.showToast({
            title: '登录成功',
            duration: 1200,
            icon: 'success',
            success: () => {
              if (this.useSwitchTab) {
                uni.switchTab({ url: this.successUrl });
                return;
              }
              uni.reLaunch({ url: this.successUrl });
            },
          });
        })
        .catch(() => {
          uni.showToast({
            title: '网络请求失败，请稍后重试',
            icon: 'none',
          });
        })
        .finally(() => {
          uni.hideLoading();
        });
    },
  },
};
</script>

<style lang="scss" scoped>
.loginBox {
  min-height: 100vh;
  width: 100vw;
  background: transparent;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
  padding: 56rpx 0;

  .bg-shape {
    position: absolute;
    border-radius: 50%;
    filter: blur(88px);
    z-index: 0;
    opacity: 0.28;
    animation: floating 11s infinite ease-in-out alternate;
  }
  .shape-1 {
    width: 620rpx;
    height: 620rpx;
    background: rgba(0, 122, 255, 0.26);
    top: -16%;
    left: -22%;
  }
  .shape-2 {
    width: 560rpx;
    height: 560rpx;
    background: rgba(0, 210, 255, 0.2);
    bottom: 4%;
    right: -18%;
    animation-delay: -3s;
  }
  .shape-3 {
    width: 430rpx;
    height: 430rpx;
    background: rgba(100, 150, 255, 0.16);
    top: 56%;
    left: 32%;
    animation-delay: -6s;
  }

  .login-container {
    width: 90%;
    max-width: 710rpx;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: auto;
    animation: fade-up 380ms ease;
    transform: translateY(25vh);
  }

  .header {
    text-align: center;
    margin-bottom: 54rpx;
    width: 100%;
    transform: translateY(-30rpx);

    .title {
      color: #1A2A3A;
      font-size: 74rpx;
      font-weight: 900;
      letter-spacing: 8rpx;
      text-shadow: 0 6rpx 20rpx rgba(0, 122, 255, 0.08);
      display: block;
      line-height: 1.1;
    }

    .mainTitle {
      margin-top: 20rpx;
      color: #5a74ab;
      font-size: 24rpx;
      letter-spacing: 1rpx;
      font-weight: 600;
      position: relative;
      display: inline-block;
      padding: 0 24rpx;

      &::before,
      &::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 34rpx;
        height: 1px;
        background: rgba(0, 122, 255, 0.2);
      }
      &::before {
        left: -16rpx;
      }
      &::after {
        right: -16rpx;
      }
    }
  }

  .glass-card {
    width: 100%;
    background: rgba(255, 255, 255, 0.58);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.86);
    box-shadow: 0 16rpx 60rpx rgba(57, 96, 156, 0.12);
    border-radius: 38rpx;
    padding: 54rpx 42rpx;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      width: 360rpx;
      height: 360rpx;
      right: -180rpx;
      top: -220rpx;
      background: radial-gradient(circle, rgba(86, 150, 255, 0.16) 0%, rgba(86, 150, 255, 0) 68%);
      pointer-events: none;
    }

    .card-title {
      color: #1A2A3A;
      font-size: 42rpx;
      font-weight: bold;
      letter-spacing: 5rpx;
      margin-bottom: 42rpx;
    }

    .form-group {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 28rpx;
    }

    .input-item {
      display: flex;
      align-items: center;
      width: 100%;
      height: 96rpx;
      background: rgba(255, 255, 255, 0.9);
      border-radius: 20rpx;
      transition: all 0.3s ease;
      overflow: hidden;
      border: 1px solid rgba(0, 122, 255, 0.11);

      &:focus-within {
        border-color: rgba(0, 122, 255, 0.56);
        box-shadow: 0 0 0 4rpx rgba(0, 122, 255, 0.07);
      }

      .iconBox {
        width: 90rpx;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
      }

      .custom-input {
        flex: 1;
        height: 100%;
        font-size: 29rpx;
        color: #1A2A3A;
        border: none;
        outline: none;
        background: transparent;
        padding-right: 30rpx;
      }

      .svg-icon {
        width: 34rpx;
        height: 34rpx;
      }
    }

    .modern-btn {
      width: 100%;
      height: 94rpx;
      background: linear-gradient(90deg, #007aff 0%, #00d2ff 100%);
      color: #ffffff;
      font-size: 32rpx;
      font-weight: bold;
      letter-spacing: 3rpx;
      border-radius: 47rpx;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 10rpx 30rpx rgba(0, 122, 255, 0.24);
      transition: transform 0.1s;

      &:active {
        transform: scale(0.98);
      }
      &::after {
        border: none;
      }
    }

    .term-box {
      margin-top: -6rpx;
    }
    .deal-wrapper {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .deal {
      font-size: 23rpx;
      color: #1A2A3A;
      margin-left: 8rpx;
      opacity: 0.74;

      .link {
        color: #007aff;
        font-weight: bold;
        text-decoration: underline;
        margin: 0 4rpx;
      }
    }
  }

  .footer-more {
    margin-top: 48rpx;
    width: 100%;

    .text-line {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 20rpx;

      .line {
        height: 1px;
        width: 60rpx;
        background-color: rgba(0, 122, 255, 0.1);
      }
      .word {
        font-size: 19rpx;
        color: rgba(26, 42, 58, 0.4);
        letter-spacing: 1.5rpx;
      }
    }
  }
}

.modal-content {
  padding: 30rpx 40rpx;
  color: #333333;
  line-height: 1.6;
  font-size: 28rpx;

  h4 {
    font-size: 32rpx;
    font-weight: bold;
    color: #007aff;
    margin: 30rpx 0 15rpx 0;
  }

  p {
    margin-bottom: 16rpx;
    text-align: justify;
  }
}

@keyframes floating {
  0% {
    transform: translate(0, 0) rotate(0deg);
  }
  100% {
    transform: translate(30rpx, 50rpx) rotate(15deg);
  }
}

@keyframes fade-up {
  0% {
    opacity: 0;
    transform: translateY(16rpx);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
