<template>
  <view class="loginBox">
    <view class="bg-shape shape-1"></view>
    <view class="bg-shape shape-2"></view>

    <view class="login-shell" :style="{ paddingTop: pageTopPadding + 'px' }">
      <view class="top-nav">
        <view class="back-btn" @tap="goBack">
          <u-icon name="arrow-left" color="#17314c" size="34rpx"></u-icon>
        </view>
        <view class="top-nav-title">{{ isOwnerApp ? '业主端' : '管理端' }}</view>
        <view class="top-nav-placeholder"></view>
      </view>

      <view class="login-stage">
        <view class="login-container">
          <view class="header">
            <text class="title">社区智眼</text>
            <view class="mainTitle">{{ isOwnerApp ? '居民服务入口' : '智慧社区工作入口' }}</view>
          </view>

          <view class="glass-card logContent">
            <view class="mode-switch" v-if="canRegister">
              <view class="mode-item" :class="{ active: mode === 'login' }" @tap="setMode('login')">登录</view>
              <view class="mode-item" :class="{ active: mode === 'register' }" @tap="setMode('register')">注册</view>
            </view>
            <text class="card-title">{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</text>
            <text class="card-subtitle">{{ mode === 'login' ? '登录后查看社区提醒与服务' : '填写账号信息后即可进入业主端' }}</text>

            <view class="form-group">
              <view class="input-item">
                <view class="iconBox">
                  <u-icon name="account" color="#5672b9" size="34rpx"></u-icon>
                </view>
                <input
                  class="input custom-input"
                  type="text"
                  v-model="username"
                  placeholder="请输入用户名"
                  placeholder-style="color:#A0B2D4"
                />
              </view>

              <view class="input-item" v-if="mode === 'register'">
                <view class="iconBox">
                  <u-icon name="account-fill" color="#5672b9" size="34rpx"></u-icon>
                </view>
                <input
                  class="input custom-input"
                  type="text"
                  v-model="nickname"
                  placeholder="请输入昵称（可选）"
                  placeholder-style="color:#A0B2D4"
                />
              </view>

              <view class="input-item" v-if="mode === 'register'">
                <view class="iconBox">
                  <u-icon name="map" color="#5672b9" size="34rpx"></u-icon>
                </view>
                <input
                  class="input custom-input"
                  type="text"
                  v-model="homeArea"
                  placeholder="请输入所属区域，如小区东门街道"
                  placeholder-style="color:#A0B2D4"
                />
              </view>

              <view class="input-item">
                <view class="iconBox">
                  <u-icon name="lock" color="#5672b9" size="34rpx"></u-icon>
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

              <view class="input-item" v-if="mode === 'register'">
                <view class="iconBox">
                  <u-icon name="lock-fill" color="#5672b9" size="34rpx"></u-icon>
                </view>
                <input
                  class="input custom-input"
                  v-model="confirmPassword"
                  password
                  type="text"
                  placeholder="请再次输入密码"
                  placeholder-style="color:#A0B2D4"
                />
              </view>

              <view class="submit-wrap">
                <button class="btn modern-btn" @tap="submitAuth">{{ mode === 'login' ? '登录' : '注册并进入' }}</button>
              </view>

              <view class="wx-register" v-if="isOwnerApp && mode === 'register'" @tap="registerByWechat">
                微信注册
              </view>

              <view class="term-box">
                <checkbox-group @change="checked = !checked">
                  <label class="deal-wrapper">
                    <checkbox class="theme-checkbox" style="transform: scale(0.65);" value="true" :checked="checked" color="#007aff"/>
                    <text class="deal">
                      {{ mode === 'login' ? '登录' : '注册' }}即表示您已阅读并同意
                      <span class="link" @tap.stop="changeShow">《用户服务协议》</span>
                      与
                      <span class="link" @tap.stop="changeShow">《隐私政策》</span>
                    </text>
                  </label>
                </checkbox-group>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <u-modal
      :show="isShow"
      :closeOnClickOverlay="true"
      @close="isShow = false"
      @confirm="isShow = false"
      title="用户服务协议与隐私政策"
      confirmColor="#007aff"
    >
      <scroll-view scroll-y="true" style="height: 60vh;">
        <view class="modal-content">
          <p>
            欢迎您使用社区智眼服务。为保障您的合法权益，维护服务秩序，请您在注册、登录及使用本应用前，仔细阅读并充分理解本《用户服务协议》与《隐私政策》。当您点击同意或继续使用本服务，即视为您已阅读、理解并接受本协议全部条款。
          </p>
          <h4>1. 服务说明</h4>
          <p>1.1 本应用面向社区管理、物业服务与住户信息查询等场景提供相关功能与服务。</p>
          <p>1.2 我们将持续优化服务体验，但不承诺服务在所有设备、网络环境或系统版本下均保持完全一致。</p>
          <p>1.3 您应当按照本协议及相关法律法规使用本服务，不得利用本服务从事任何违法违规活动。</p>
          <h4>2. 账号使用规范</h4>
          <p>2.1 您应妥善保管账号、密码及相关验证信息，并对使用该账号产生的行为负责。</p>
          <p>2.2 如发现账号异常、被盗用或存在安全风险，您应及时采取必要措施并联系我们处理。</p>
          <p>2.3 您不得通过非法方式获取、转让、出租、借用或共享他人账号。</p>
          <h4>3. 个人信息保护</h4>
          <p>3.1 我们将按照相关法律法规及《隐私政策》的约定收集、使用、存储、传输和保护您的个人信息。</p>
          <p>3.2 为实现身份验证、消息通知、服务优化及安全保障等目的，我们可能会在必要范围内处理您的设备信息、账户信息及使用记录。</p>
          <p>3.3 我们将采取合理的技术和管理措施，防止信息泄露、损毁、丢失或被非法使用。</p>
          <h4>4. 知识产权</h4>
          <p>4.1 本应用内所含的文字、图像、界面设计、程序代码、标识、音视频及其他内容，其相关知识产权归本系统或合法权利人所有。</p>
          <p>4.2 未经授权，您不得以任何形式复制、传播、修改、反向工程、出售或用于其他商业用途。</p>
          <h4>5. 责任限制</h4>
          <p>5.1 因不可抗力、网络故障、设备异常、第三方服务中断等原因导致服务受限或中断的，我们在法律允许范围内不承担超出合理控制范围的责任。</p>
          <p>5.2 您理解并同意，本应用仅提供信息展示、辅助管理与智能分析服务，相关结果供参考使用，不构成任何法律、财务或安全承诺。</p>
          <h4>6. 协议变更与生效</h4>
          <p>6.1 我们有权根据法律法规变化、业务调整或产品升级对本协议进行修订，并在必要时以适当方式通知您。</p>
          <p>6.2 若您继续使用本服务，即视为接受修订后的协议内容。</p>
          <p>6.3 本协议的解释、效力及争议解决适用中华人民共和国法律。</p>
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
    registerApi: {
      type: String,
      default: '',
    },
    wxRegisterApi: {
      type: String,
      default: '',
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
      pageTopPadding: 30,
      mode: 'login',
      isShow: false,
      password: '',
      confirmPassword: '',
      username: '',
      nickname: '',
      homeArea: '',
      checked: false,
    };
  },
  computed: {
    isOwnerApp() {
      return this.appType === 'owner';
    },
    canRegister() {
      return this.isOwnerApp && Boolean(this.registerApi);
    },
  },
  mounted() {
    this.updateSafeAreaPadding();
  },
  methods: {
    updateSafeAreaPadding() {
      const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
      this.pageTopPadding = (info && info.statusBarHeight) ? info.statusBarHeight + 18 : 30;
    },
    setMode(mode) {
      this.mode = mode;
      this.password = '';
      this.confirmPassword = '';
      this.homeArea = '';
    },
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/shared/select/index' });
    },
    changeShow() {
      this.isShow = true;
    },
    submitAuth() {
      if (this.mode === 'register') {
        this.registerOwner();
        return;
      }
      this.jump();
    },
    ensureAgreed(actionText) {
      if (!this.checked) {
        uni.showToast({
          title: `请先阅读并勾选协议后再${actionText}`,
          duration: 2000,
          icon: 'none',
        });
        return false;
      }
      return true;
    },
    jump() {
      if (!this.ensureAgreed('登录')) return;
      if (!this.username || !this.password) {
        uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
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
          this.handleAuthSuccess(data.data || {}, '登录成功');
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
    registerOwner() {
      if (!this.ensureAgreed('注册')) return;
      if (!this.registerApi) {
        uni.showToast({ title: '注册暂未开放', icon: 'none' });
        return;
      }
      if (!this.username || !this.password) {
        uni.showToast({ title: '请输入用户名和密码', icon: 'none' });
        return;
      }
      if (this.password !== this.confirmPassword) {
        uni.showToast({ title: '两次密码不一致', icon: 'none' });
        return;
      }
      if (!this.homeArea.trim()) {
        uni.showToast({ title: '请填写所属区域', icon: 'none' });
        return;
      }

      const payload = {
        username: this.username,
        userName: this.username,
        password: this.password,
        name: this.nickname || this.username,
        homeArea: this.homeArea.trim(),
        role: 1,
      };

      uni.showLoading({ title: '注册中...' });
      uni.$http
        .post(this.registerApi, payload)
        .then(({ data }) => {
          if (data.code !== '00000') {
            uni.$showMsg(data.message || '注册失败');
            return;
          }
          const userData = data.data || {};
          if (userData.token) {
            this.handleAuthSuccess(userData, '注册成功');
            return;
          }
          this.autoLoginAfterRegister();
        })
        .catch(() => {
          uni.showToast({ title: '网络请求失败，请稍后重试', icon: 'none' });
        })
        .finally(() => {
          uni.hideLoading();
        });
    },
    autoLoginAfterRegister() {
      if (!this.username || !this.password) {
        uni.showToast({ title: '注册成功，请手动登录', icon: 'none' });
        this.setMode('login');
        return;
      }
      uni.showLoading({ title: '自动登录中...' });
      uni.$http
        .post(this.loginApi, {
          userName: this.username,
          password: this.password,
        })
        .then(({ data }) => {
          if (data.code !== '00000') {
            uni.$showMsg(data.message || '自动登录失败，请手动登录');
            this.setMode('login');
            return;
          }
          this.handleAuthSuccess(data.data || {}, '注册成功');
        })
        .catch(() => {
          uni.$showMsg('自动登录失败，请手动登录');
          this.setMode('login');
        })
        .finally(() => {
          uni.hideLoading();
        });
    },
    registerByWechat() {
      if (!this.ensureAgreed('注册')) return;
      if (!this.wxRegisterApi) {
        uni.showToast({ title: '微信注册即将开放', icon: 'none' });
        return;
      }
      if (typeof uni.login !== 'function') {
        uni.showToast({ title: '当前环境暂不支持微信注册', icon: 'none' });
        return;
      }
      uni.login({
        provider: 'weixin',
        success: (loginRes) => {
          uni.showLoading({ title: '注册中...' });
          uni.$http
            .post(this.wxRegisterApi, { code: loginRes.code })
            .then(({ data }) => {
              if (data.code !== '00000') {
                uni.$showMsg(data.message || '微信注册失败');
                return;
              }
              this.handleAuthSuccess(data.data || {}, '注册成功');
            })
            .catch(() => {
              uni.showToast({ title: '网络请求失败，请稍后重试', icon: 'none' });
            })
            .finally(() => {
              uni.hideLoading();
            });
        },
        fail: () => {
          uni.showToast({ title: '微信授权未完成', icon: 'none' });
        },
      });
    },
    handleAuthSuccess(userData, title) {
      const expectedRole = this.appType === 'owner' ? 1 : 0;
      if (userData && userData.role !== undefined && Number(userData.role) !== expectedRole) {
        uni.showToast({
          title: this.appType === 'owner' ? '请使用业主端账号登录' : '请使用管理端账号登录',
          icon: 'none',
        });
        return;
      }
      uni.setStorageSync('phone', this.username);
      uni.setStorageSync('username', userData.name || this.nickname || this.username);
      uni.setStorageSync('userId', userData.id || '');
      uni.setStorageSync('token', userData.token || '');
      uni.setStorageSync('appType', this.appType);
      uni.setStorageSync('homeArea', userData.homeArea || this.homeArea || '');
      uni.setStorageSync('avatarUrl', userData.avatarUrl || '');
      uni.setStorageSync('notifyEnabled', userData.notifyEnabled !== false);

      if (this.enableWebsocket && userData.id) {
        websocket.connect(userData.id);
      }

      uni.showToast({
        title,
        duration: 1200,
        icon: 'success',
        success: () => {
          setTimeout(() => {
              if (this.successUrl === '/pages/manage/controls/controls') {
                uni.reLaunch({ url: this.successUrl });
                return;
              }
              if (this.useSwitchTab) {
                uni.switchTab({ url: this.successUrl });
                return;
              }
              uni.reLaunch({ url: this.successUrl });
          }, 320);
        },
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.loginBox {
  min-height: 100vh;
  width: 100vw;
  background:
    radial-gradient(circle at 12% 2%, rgba(56, 164, 255, 0.2) 0, rgba(56, 164, 255, 0) 260rpx),
    radial-gradient(circle at 88% 18%, rgba(20, 112, 216, 0.14) 0, rgba(20, 112, 216, 0) 300rpx),
    linear-gradient(180deg, #eaf6ff 0%, #f8fbff 52%, #ffffff 100%);
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 0 28rpx 42rpx;
  display: flex;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  z-index: 0;
  pointer-events: none;
}

.shape-1 {
  width: 360rpx;
  height: 360rpx;
  background: rgba(0, 122, 255, 0.14);
  top: -120rpx;
  left: -130rpx;
}

.shape-2 {
  width: 420rpx;
  height: 420rpx;
  background: rgba(0, 210, 255, 0.1);
  right: -170rpx;
  bottom: -150rpx;
}

.top-nav,
.login-container {
  position: relative;
  z-index: 1;
}

.login-shell {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
  flex: 0 0 auto;
}

.back-btn,
.top-nav-placeholder {
  width: 66rpx;
  height: 66rpx;
}

.back-btn {
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(37, 99, 235, 0.1);
  box-shadow: 0 8rpx 20rpx rgba(32, 74, 126, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.top-nav-title {
  color: #17314c;
  font-size: 30rpx;
  font-weight: 900;
}

.login-container {
  width: 100%;
  max-width: 710rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.login-stage {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6rpx 0 12rpx;
  min-height: 0;
}

.mode-switch + .card-title {
  margin-top: 0;
}

.header {
  text-align: center;
  margin-bottom: 30rpx;
  width: 100%;
}

.title {
  color: #17314c;
  font-size: 62rpx;
  font-weight: 900;
  letter-spacing: 6rpx;
  display: block;
  line-height: 1.1;
}

.mainTitle {
  margin-top: 16rpx;
  color: #5a74ab;
  font-size: 24rpx;
  font-weight: 700;
}

.glass-card {
  width: 100%;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(255, 255, 255, 0.94);
  box-shadow: 0 16rpx 46rpx rgba(57, 96, 156, 0.12);
  border-radius: 34rpx;
  padding: 32rpx 30rpx 38rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mode-switch {
  width: 100%;
  padding: 6rpx;
  border-radius: 999rpx;
  background: #eaf4ff;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  box-sizing: border-box;
  margin-bottom: 24rpx;
}

.mode-item {
  height: 58rpx;
  border-radius: 999rpx;
  color: #64748b;
  font-size: 25rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-item.active {
  background: #fff;
  color: #1470d8;
  box-shadow: 0 6rpx 18rpx rgba(20, 112, 216, 0.12);
}

.card-title {
  color: #17314c;
  font-size: 36rpx;
  font-weight: 900;
  margin-bottom: 8rpx;
}

.card-subtitle {
  color: #64748b;
  font-size: 23rpx;
  margin-bottom: 28rpx;
}

.form-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 26rpx;
}

.mode-switch ~ .form-group {
  gap: 20rpx;
}

.input-item {
  display: flex;
  align-items: center;
  width: 100%;
  height: 90rpx;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 20rpx;
  overflow: hidden;
  border: 1rpx solid rgba(0, 122, 255, 0.11);
}

.input-item:focus-within {
  border-color: rgba(0, 122, 255, 0.42);
  box-shadow: 0 0 0 4rpx rgba(0, 122, 255, 0.06);
}

.iconBox {
  width: 86rpx;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.custom-input {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
  color: #17314c;
  border: none;
  outline: none;
  background: transparent;
  padding-right: 24rpx;
}

.submit-wrap {
  width: 100%;
  margin-top: 12rpx;
}

.modern-btn {
  width: 100%;
  height: 92rpx;
  background: linear-gradient(90deg, #1470d8 0%, #05b5ff 100%);
  color: #ffffff;
  font-size: 31rpx;
  font-weight: 900;
  letter-spacing: 2rpx;
  border-radius: 46rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 10rpx 26rpx rgba(20, 112, 216, 0.22);
}

.modern-btn:active {
  opacity: 0.92;
}

.modern-btn::after {
  border: none;
}

.wx-register {
  width: 100%;
  height: 84rpx;
  border-radius: 42rpx;
  background: #f0fdf4;
  border: 1rpx solid #bbf7d0;
  color: #16a34a;
  font-size: 28rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.term-box {
  display: flex;
  justify-content: center;
  margin-top: 10rpx;
}

.deal-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.deal {
  font-size: 22rpx;
  color: rgba(26, 42, 58, 0.72);
  margin-left: 6rpx;
  line-height: 1.5;
}

.link {
  color: #1470d8;
  font-weight: 800;
  margin: 0 4rpx;
}

.modal-content {
  padding: 30rpx 40rpx;
  color: #333333;
  line-height: 1.6;
  font-size: 28rpx;
}

.modal-content h4 {
  font-size: 32rpx;
  font-weight: bold;
  color: #007aff;
  margin: 30rpx 0 15rpx 0;
}

.modal-content p {
  margin-bottom: 16rpx;
  text-align: justify;
}
</style>
