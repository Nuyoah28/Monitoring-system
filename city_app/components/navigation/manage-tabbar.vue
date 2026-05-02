<template>
  <!-- #ifdef APP-PLUS -->
  <cover-view v-if="nativeOverlay && !hidden" class="manage-tabbar">
    <cover-view
      class="tab-item"
      :class="{ active: current === 'home' }"
      @tap.stop="go('/pages/manage/controls/controls')"
    >
      <cover-image class="tab-icon" src="/static/tabBar/realTime.png" mode="aspectFit" />
      <cover-view class="tab-text">首页</cover-view>
    </cover-view>
    <cover-view
      class="tab-item"
      :class="{ active: current === 'monitor' }"
      @tap.stop="go('/pages/manage/monitor/index')"
    >
      <cover-image class="tab-icon" src="/static/tabBar/contorl.png" mode="aspectFit" />
      <cover-view class="tab-text">监控</cover-view>
    </cover-view>
    <cover-view
      class="tab-item"
      :class="{ active: current === 'alarm' }"
      @tap.stop="go('/pages/manage/realtime/realtime')"
    >
      <cover-image class="tab-icon" src="/static/tabBar/chart.png" mode="aspectFit" />
      <cover-view class="tab-text">报警</cover-view>
    </cover-view>
    <cover-view
      class="tab-item"
      :class="{ active: current === 'personal' }"
      @tap.stop="go('/pages/manage/personal/personal')"
    >
      <cover-image class="tab-icon" src="/static/tabBar/personal.png" mode="aspectFit" />
      <cover-view class="tab-text">我的</cover-view>
    </cover-view>
  </cover-view>

  <view v-else-if="!hidden" class="manage-tabbar">
    <view
      class="tab-item"
      :class="{ active: current === 'home' }"
      @tap.stop="go('/pages/manage/controls/controls')"
    >
      <image class="tab-icon" src="/static/tabBar/realTime.png" mode="aspectFit" />
      <text class="tab-text">首页</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'monitor' }"
      @tap.stop="go('/pages/manage/monitor/index')"
    >
      <image class="tab-icon" src="/static/tabBar/contorl.png" mode="aspectFit" />
      <text class="tab-text">监控</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'alarm' }"
      @tap.stop="go('/pages/manage/realtime/realtime')"
    >
      <image class="tab-icon" src="/static/tabBar/chart.png" mode="aspectFit" />
      <text class="tab-text">报警</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'personal' }"
      @tap.stop="go('/pages/manage/personal/personal')"
    >
      <image class="tab-icon" src="/static/tabBar/personal.png" mode="aspectFit" />
      <text class="tab-text">我的</text>
    </view>
  </view>
  <!-- #endif -->

  <!-- #ifndef APP-PLUS -->
  <view v-if="!hidden" class="manage-tabbar">
    <view
      class="tab-item"
      :class="{ active: current === 'home' }"
      @tap.stop="go('/pages/manage/controls/controls')"
    >
      <image class="tab-icon" src="/static/tabBar/realTime.png" mode="aspectFit" />
      <text class="tab-text">首页</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'monitor' }"
      @tap.stop="go('/pages/manage/monitor/index')"
    >
      <image class="tab-icon" src="/static/tabBar/contorl.png" mode="aspectFit" />
      <text class="tab-text">监控</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'alarm' }"
      @tap.stop="go('/pages/manage/realtime/realtime')"
    >
      <image class="tab-icon" src="/static/tabBar/chart.png" mode="aspectFit" />
      <text class="tab-text">报警</text>
    </view>
    <view
      class="tab-item"
      :class="{ active: current === 'personal' }"
      @tap.stop="go('/pages/manage/personal/personal')"
    >
      <image class="tab-icon" src="/static/tabBar/personal.png" mode="aspectFit" />
      <text class="tab-text">我的</text>
    </view>
  </view>
  <!-- #endif -->
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
    nativeOverlay: {
      type: Boolean,
      default: false,
    },
    hidden: {
      type: Boolean,
      default: false,
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
        home: '/pages/manage/controls/controls',
        monitor: '/pages/manage/monitor/index',
        alarm: '/pages/manage/realtime/realtime',
        personal: '/pages/manage/personal/personal',
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
          console.warn('[manage-tabbar] 页面跳转失败：', error);
          this.fallbackNavigate(path);
        },
        complete: releaseLock,
      });
    },
  },
};
</script>

<style scoped lang="scss">
.manage-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  height: calc(104rpx + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid #E2E8F0;
  box-shadow: 0 -8rpx 24rpx rgba(15, 23, 42, 0.08);
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
  height: 104rpx;
  pointer-events: auto;
  position: relative;
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
  background: transparent;
}

.tab-item.active::before {
  content: "";
  position: absolute;
  top: 0;
  left: 50%;
  width: 44rpx;
  height: 6rpx;
  border-radius: 0 0 999rpx 999rpx;
  background: #2563EB;
  transform: translateX(-50%);
}

.tab-item.active .tab-icon {
  opacity: 1;
}

.tab-item.active .tab-text {
  color: #2563EB;
  font-weight: 700;
}
</style>
