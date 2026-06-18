<template>
  <view class="owner-tabbar">
    <view
      class="tab-item"
      :class="{ active: current === 'home' }"
      @tap.stop="go('/pages/owner/home/index')"
    >
      <image class="tab-icon" src="/static/tabBar/chart.png" mode="aspectFit" />
      <text class="tab-text">主页</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'ai' }"
      @tap.stop="go('/pages/owner/ai/index')"
    >
      <image class="tab-icon" src="/static/tabBar/GPT.png" mode="aspectFit" />
      <text class="tab-text">社区助手</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'personal' }"
      @tap.stop="go('/pages/owner/personal/index')"
    >
      <image class="tab-icon" src="/static/tabBar/personal.png" mode="aspectFit" />
      <text class="tab-text">个人中心</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      navLock: false,
    };
  },
  props: {
    current: {
      type: String,
      default: 'home',
    },
  },
  methods: {
    getCurrentRoutePath() {
      const pages = typeof getCurrentPages === 'function' ? getCurrentPages() : [];
      const currentPage = pages[pages.length - 1];
      const route = currentPage && currentPage.route ? `/${currentPage.route}` : '';
      return route.split('?')[0];
    },
    fallbackNavigate(path) {
      uni.redirectTo({
        url: path,
        fail: () => {
          uni.navigateTo({ url: path });
        },
      });
    },
    go(url) {
      const path = String(url || '');
      const currentMap = {
        home: '/pages/owner/home/index',
        ai: '/pages/owner/ai/index',
        personal: '/pages/owner/personal/index',
      };
      if (currentMap[this.current] === path || this.getCurrentRoutePath() === path) return;
      if (this.navLock) return;

      this.navLock = true;
      if (typeof uni.vibrateShort === 'function') {
        try { uni.vibrateShort(); } catch (e) {}
      }

      const releaseLock = () => {
        setTimeout(() => {
          this.navLock = false;
        }, 500);
      };

      uni.reLaunch({
        url: path,
        fail: (error) => {
          console.warn('[owner-tabbar] 页面跳转失败：', error);
          this.fallbackNavigate(path);
        },
        complete: releaseLock,
      });
    },
  },
};
</script>

<style scoped lang="scss">
.owner-tabbar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(18rpx + env(safe-area-inset-bottom));
  height: 100rpx;
  padding: 8rpx;
  box-sizing: border-box;
  border-radius: 50rpx;
  background: rgba(7, 21, 37, 0.92);
  border: 1rpx solid rgba(125, 211, 252, 0.22);
  box-shadow: 0 16rpx 36rpx rgba(2, 8, 23, 0.28);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 9999;
  pointer-events: auto;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 84rpx;
  border-radius: 42rpx;
  pointer-events: auto;
  position: relative;
}

.tab-icon {
  width: 34rpx;
  height: 34rpx;
  opacity: 0.58;
}

.tab-text {
  margin-top: 4rpx;
  font-size: 22rpx;
  line-height: 1.2;
  color: rgba(234, 247, 255, 0.62);
  white-space: nowrap;
  pointer-events: none;
}

.tab-item.active {
  background: rgba(24, 168, 255, 0.16);
}

.tab-item.active::before {
  content: "";
  position: absolute;
  top: 8rpx;
  left: 50%;
  width: 36rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #20d6d2;
  transform: translateX(-50%);
}

.tab-item.active .tab-icon {
  opacity: 1;
}

.tab-item.active .tab-text {
  color: #eaf7ff;
  font-weight: 900;
}
</style>
