<template>
  <view class="page-wrap" :style="{ paddingTop: (statusBarHeight + 18) + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-bar">
      <view>
        <view class="top-title">个人中心</view>
        <view class="top-subtitle">账号资料与常用服务</view>
      </view>
      <view class="top-badge">管理端</view>
    </view>

    <view class="panel profile-card">
      <view class="profile-head">
        <view class="profile-avatar-wrap">
          <image class="profile-avatar-img" src="../../../static/avatar.png" mode="aspectFit"></image>
        </view>
        <view class="profile-main">
          <view class="profile-name">{{ username || '管理员' }}</view>
          <view class="profile-desc">UID：{{ uid || '--' }}</view>
        </view>
      </view>
    </view>

    <view class="panel section-card">
      <view class="section-head">
        <view>
          <view class="section-title">快捷入口</view>
          <view class="section-sub">常用管理功能一键进入</view>
        </view>
      </view>
      <view class="menu-list">
        <view class="menu-row" @tap="jump('/pages/manage/personal/edit/edit')">
          <view class="menu-copy">
            <view class="menu-title">修改个人信息</view>
          </view>
          <view class="menu-arrow">
            <image src="../../../static/arrow-right.png" mode="aspectFit"></image>
          </view>
        </view>
        <view class="menu-row" @tap="showAbout">
          <view class="menu-copy">
            <view class="menu-title">关于</view>
          </view>
          <view class="menu-arrow">
            <image src="../../../static/arrow-right.png" mode="aspectFit"></image>
          </view>
        </view>
        <view class="menu-row" @tap="clearCache">
          <view class="menu-copy">
            <view class="menu-title">清理缓存</view>
          </view>
          <view class="menu-arrow">
            <image src="../../../static/arrow-right.png" mode="aspectFit"></image>
          </view>
        </view>
        <view class="menu-row menu-row--danger" @tap="logout">
          <view class="menu-copy">
            <view class="menu-title">退出登录</view>
          </view>
          <view class="menu-arrow">
            <image src="../../../static/arrow-right.png" mode="aspectFit"></image>
          </view>
        </view>
      </view>
    </view>

    <manage-tabbar current="personal" />
  </view>
</template>

<script>
import ManageTabbar from '@/components/navigation/manage-tabbar.vue';

export default {
  components: {
    ManageTabbar,
  },
  data() {
    return {
      safeHeight: 0,
      phone: "",
      uid: "",
      username: "",
      statusBarHeight: 0,
      aboutContent:
        "本系统面向社区重点区域的智能化值守场景，支持视频监控、异常识别、报警推送、处置闭环与环境车位管理，帮助管理人员及时发现风险并完成联动处理。",
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
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/manage/controls/controls' });
    },
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
          uni.removeStorageSync("appType");
          uni.reLaunch({
            url: "/pages/shared/select/index",
          });
        },
      });
    },
  },
};
</script>

<style lang="scss" scoped>
.page-wrap {
  min-height: 100vh;
  width: 100vw;
  position: relative;
  padding: 26rpx 24rpx 180rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef7ff 0%, #f9fbff 54%, #ffffff 100%);
  overflow-y: auto;
  overflow-x: hidden;
}

.bg-orb {
  position: absolute;
  border-radius: 999rpx;
  filter: blur(66rpx);
  z-index: 0;
  pointer-events: none;
}

.bg-orb--one {
  width: 360rpx;
  height: 360rpx;
  background: rgba(0, 198, 255, 0.20);
  right: -140rpx;
  top: -110rpx;
}

.bg-orb--two {
  width: 420rpx;
  height: 420rpx;
  background: rgba(73, 121, 255, 0.14);
  left: -160rpx;
  bottom: -170rpx;
}

.top-bar,
.panel {
  position: relative;
  z-index: 2;
}

.top-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.top-title {
  font-size: 38rpx;
  color: #18304b;
  font-weight: 800;
}

.top-subtitle {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(24, 48, 75, 0.62);
}

.top-badge {
  height: 54rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.88);
  color: #2b5b99;
  font-size: 22rpx;
  box-shadow: 0 8rpx 20rpx rgba(40, 92, 150, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.9);
}

.panel {
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
}

.profile-card {
  margin-bottom: 18rpx;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.profile-avatar-wrap {
  width: 112rpx;
  height: 112rpx;
  border-radius: 28rpx;
  overflow: hidden;
  background: linear-gradient(180deg, #edf5ff, #ffffff);
  box-shadow: 0 12rpx 26rpx rgba(40, 92, 150, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.88);
  flex-shrink: 0;
}

.profile-avatar-img {
  width: 100%;
  height: 100%;
}

.profile-main {
  min-width: 0;
}

.profile-name {
  font-size: 36rpx;
  font-weight: 800;
  color: #15283e;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-desc {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #5b7087;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 700;
}

.section-sub {
  margin-top: 6rpx;
  color: rgba(29, 47, 68, 0.55);
  font-size: 22rpx;
}

.menu-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.menu-row {
  min-height: 96rpx;
  border-radius: 22rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background:
    linear-gradient(90deg, rgba(20, 112, 216, 0.08), rgba(20, 112, 216, 0) 34%),
    rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(205, 223, 245, 0.92);
  box-shadow: 0 8rpx 18rpx rgba(40, 92, 150, 0.06);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.menu-row:active {
  transform: scale(0.985);
  box-shadow: 0 4rpx 12rpx rgba(40, 92, 150, 0.05);
}

.menu-row--danger {
  background:
    linear-gradient(90deg, rgba(244, 63, 94, 0.08), rgba(244, 63, 94, 0) 34%),
    rgba(255, 255, 255, 0.92);
}

.menu-copy {
  min-width: 0;
}

.menu-title {
  color: #1d2f44;
  font-size: 28rpx;
  font-weight: 800;
}

.menu-row--danger .menu-title {
  color: #be123c;
}

.menu-arrow {
  width: 34rpx;
  height: 34rpx;
  opacity: 0.58;
  flex-shrink: 0;
}

.menu-arrow image {
  width: 100%;
  height: 100%;
}
</style>
