<template>
  <view class="launch-page">
    <view class="glow glow-a"></view>
    <view class="glow glow-b"></view>
    <view class="glow glow-c"></view>
    <view class="radar-ring radar-ring--one"></view>
    <view class="radar-ring radar-ring--two"></view>

    <view class="launch-center" :class="{ ready: centerReady }">
      <view class="logo-wrap" :class="{ pulse: logoPulse }">
        <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      </view>
      <text class="kicker">COMMUNITY COMMAND</text>
      <text class="title">社区智眼</text>
      <text class="subtitle">智慧安防 · 实时联动 · 可信守护</text>
    </view>

    <view class="launch-bottom" :class="{ show: footerShow }">
      <view class="bar">
        <view class="bar-inner" :style="{ width: progress + '%' }"></view>
      </view>
      <text class="tip">正在启动系统...</text>
    </view>
  </view>
</template>

<script>
const DEFAULT_TARGET = {
  navType: "reLaunch",
  url: "/pages/shared/select/index",
};

export default {
  data() {
    return {
      centerReady: false,
      logoPulse: false,
      footerShow: false,
      progress: 0,
      launchTimer: null,
      jumpTimer: null,
    };
  },
  onLoad() {
    this.startAnim();
  },
  onUnload() {
    if (this.launchTimer) clearInterval(this.launchTimer);
    if (this.jumpTimer) clearTimeout(this.jumpTimer);
  },
  methods: {
    startAnim() {
      this.centerReady = true;
      this.logoPulse = true;
      this.footerShow = true;

      this.launchTimer = setInterval(() => {
        if (this.progress >= 100) {
          clearInterval(this.launchTimer);
          this.launchTimer = null;
          return;
        }
        this.progress = Math.min(this.progress + 7, 100);
      }, 80);

      this.jumpTimer = setTimeout(() => {
        this.goNext();
      }, 1500);
    },
    goNext() {
      const target = uni.getStorageSync("__launch_target__") || DEFAULT_TARGET;
      uni.removeStorageSync("__launch_target__");

      if (!target || !target.url) {
        uni.reLaunch({ url: DEFAULT_TARGET.url, __skipSafeNavigation: true });
        return;
      }

      if (target.navType === "switchTab") {
        uni.switchTab({
          url: target.url,
          __skipSafeNavigation: true,
          fail: () => {
            uni.reLaunch({ url: target.url, __skipSafeNavigation: true });
          },
        });
        return;
      }

      if (target.navType === "redirectTo") {
        uni.redirectTo({
          url: target.url,
          __skipSafeNavigation: true,
          fail: () => {
            uni.reLaunch({ url: target.url, __skipSafeNavigation: true });
          },
        });
        return;
      }

      uni.reLaunch({ url: target.url, __skipSafeNavigation: true });
    },
  },
};
</script>

<style scoped lang="scss">
.launch-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 12%, rgba(32, 214, 210, 0.30), transparent 42%),
    radial-gradient(circle at 82% 72%, rgba(24, 168, 255, 0.30), transparent 44%),
    linear-gradient(160deg, #071525 0%, #0d2740 52%, #0b1e35 100%);
}

.launch-page::after {
  content: '';
  position: absolute;
  left: 36rpx;
  right: 36rpx;
  top: 24%;
  height: 1rpx;
  background: linear-gradient(90deg, transparent, rgba(32, 214, 210, 0.72), transparent);
  opacity: 0.68;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(56rpx);
  opacity: 0.55;
  animation: float 6s ease-in-out infinite;
}

.glow-a {
  width: 340rpx;
  height: 340rpx;
  left: -70rpx;
  top: -90rpx;
  background: rgba(32, 214, 210, 0.26);
}

.glow-b {
  width: 400rpx;
  height: 400rpx;
  right: -120rpx;
  top: 140rpx;
  background: rgba(24, 168, 255, 0.28);
  animation-delay: -2s;
}

.glow-c {
  width: 300rpx;
  height: 300rpx;
  left: 180rpx;
  bottom: -80rpx;
  background: rgba(34, 197, 94, 0.20);
  animation-delay: -3.5s;
}

.radar-ring {
  position: absolute;
  left: 50%;
  top: 42%;
  border-radius: 50%;
  border: 1rpx solid rgba(125, 211, 252, 0.22);
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.radar-ring--one {
  width: 420rpx;
  height: 420rpx;
}

.radar-ring--two {
  width: 620rpx;
  height: 620rpx;
  border-color: rgba(32, 214, 210, 0.12);
}

.launch-center {
  position: absolute;
  left: 50%;
  top: 44%;
  transform: translate(-50%, -50%) scale(0.86);
  opacity: 0;
  width: 80%;
  display: flex;
  align-items: center;
  flex-direction: column;
  transition: all 420ms ease;
}

.launch-center.ready {
  transform: translate(-50%, -50%) scale(1);
  opacity: 1;
}

.logo-wrap {
  width: 148rpx;
  height: 148rpx;
  border-radius: 36rpx;
  background: linear-gradient(145deg, rgba(245, 252, 255, 0.98), rgba(195, 235, 255, 0.94));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 40rpx rgba(11, 35, 62, 0.32);
}

.logo-wrap.pulse {
  animation: pulse 2s ease-in-out infinite;
}

.logo {
  width: 86rpx;
  height: 86rpx;
}

.kicker {
  margin-top: 34rpx;
  color: #7dd3fc;
  font-size: 20rpx;
  font-weight: 900;
  letter-spacing: 2rpx;
}

.title {
  margin-top: 12rpx;
  color: #ffffff;
  font-size: 56rpx;
  font-weight: 900;
  letter-spacing: 3rpx;
}

.subtitle {
  margin-top: 12rpx;
  color: rgba(215, 236, 255, 0.84);
  font-size: 24rpx;
  letter-spacing: 1rpx;
}

.launch-bottom {
  position: absolute;
  left: 50%;
  bottom: 118rpx;
  transform: translateX(-50%) translateY(12rpx);
  width: 76%;
  opacity: 0;
  transition: all 320ms ease;
}

.launch-bottom.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.bar {
  width: 100%;
  height: 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  overflow: hidden;
  box-shadow: inset 0 0 0 1rpx rgba(222, 244, 255, 0.18);
}

.bar-inner {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #18a8ff 0%, #20d6d2 50%, #22c55e 100%);
  box-shadow: 0 0 14rpx rgba(125, 211, 252, 0.55);
  transition: width 120ms linear;
}

.tip {
  margin-top: 18rpx;
  display: block;
  text-align: center;
  color: rgba(214, 236, 255, 0.82);
  font-size: 23rpx;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 16rpx 40rpx rgba(11, 35, 62, 0.32);
  }
  50% {
    transform: scale(1.045);
    box-shadow: 0 18rpx 48rpx rgba(62, 151, 245, 0.44);
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20rpx);
  }
}
</style>
