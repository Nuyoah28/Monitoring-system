<template>
  <view class="owner-page">
    <view class="owner-header">个人中心</view>
    <view class="profile-card">
      <view class="name">{{ username }}</view>
      <view class="uid">UID: {{ userId || '--' }}</view>
    </view>

    <view class="action" @tap="logout">退出登录</view>

    <owner-tabbar current="personal" />

  </view>
</template>

<script>
import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';

export default {
  components: {
    OwnerTabbar,
  },
  data() {
    return {
      username: '',
      userId: '',
    };
  },
  onShow() {
    this.username = uni.getStorageSync('username') || '业主用户';
    this.userId = uni.getStorageSync('userId') || '';
  },
  methods: {
    logout() {
      uni.removeStorageSync('token');
      uni.removeStorageSync('userId');
      uni.removeStorageSync('appType');
      uni.reLaunch({ url: '/pages/shared/select/index' });
    },
  },
};
</script>

<style lang="scss" scoped>
.owner-page {
  min-height: 100vh;
  padding: 34rpx 28rpx 150rpx;
  box-sizing: border-box;
}

.owner-header {
  font-size: 44rpx;
  font-weight: 800;
  color: #1a2a3a;
  margin-bottom: 28rpx;
}

.profile-card {
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 8rpx 30rpx rgba(60, 90, 140, 0.08);
  padding: 34rpx;
}

.name {
  font-size: 34rpx;
  color: #1a2a3a;
  font-weight: 700;
}

.uid {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: rgba(26, 42, 58, 0.62);
}

.action {
  margin-top: 22rpx;
  height: 90rpx;
  border-radius: 20rpx;
  background: #fff;
  color: #ef5350;
  font-size: 30rpx;
  font-weight: 700;
  display: flex;
  justify-content: center;
  align-items: center;
}

</style>
