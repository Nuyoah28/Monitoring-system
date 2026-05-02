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
  bottom: calc(20rpx + env(safe-area-inset-bottom));
  height: 96rpx;
  border-radius: 48rpx;
  background: #FFFFFF;
  border: 1rpx solid #E2E8F0;
  box-shadow: 0 12rpx 30rpx rgba(15, 23, 42, 0.12);
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
  height: 88rpx;
  border-radius: 40rpx;
  pointer-events: auto;
}

.tab-icon {
  width: 32rpx;
  height: 32rpx;
  opacity: 0.5;
}

.tab-text {
  margin-top: 4rpx;
  font-size: 22rpx;
  line-height: 1.2;
  color: #64748B;
  white-space: nowrap;
  pointer-events: none;
}

.tab-item.active {
  background: #EAF2FF;
}

.tab-item.active .tab-icon {
  opacity: 1;
}

.tab-item.active .tab-text {
  color: #2563EB;
  font-weight: 700;
}
</style>
