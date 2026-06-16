<template>
  <view class="property-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-nav">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="top-title">物业管理</text>
      <view class="icon-btn" @tap="jumpSetting">
        <u-icon name="setting" color="#1a2a3a" size="32rpx"></u-icon>
      </view>
    </view>

    <view class="header-card">
      <view class="header-copy">
        <view class="eyebrow">物业服务中台</view>
        <view class="title">社区事务管理</view>
        <view class="subtitle">访客、通知、报修、车位与居民随手拍集中处理</view>
      </view>
      <view class="summary-pill">
        <text class="summary-num">{{ featureList.length }}</text>
        <text class="summary-label">模块</text>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <view class="section-title">业务入口</view>
          <view class="section-subtitle">按物业日常处理场景进入对应功能</view>
        </view>
      </view>

      <view class="feature-list">
        <view
          v-for="item in featureList"
          :key="item.path"
          class="feature-card"
          @tap="goFeature(item.path)"
        >
          <view class="feature-left">
            <view class="feature-icon" :class="'feature-icon--' + item.tone">
              <u-icon :name="item.icon" color="#ffffff" size="38rpx"></u-icon>
            </view>
            <view class="feature-copy">
              <view class="feature-name">{{ item.name }}</view>
              <view class="feature-desc">{{ item.desc }}</view>
            </view>
          </view>
          <view class="feature-right">
            <view class="feature-tag">{{ item.tag }}</view>
            <u-icon name="arrow-right" color="#94a3b8" size="28rpx"></u-icon>
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
      statusBarHeight: 0,
      featureList: [
        {
          name: '访客登记',
          desc: '新增、查看和删除访客登记',
          tag: '通行',
          icon: 'account',
          tone: 'blue',
          path: '/pages/manage/property/visitor/index',
        },
        {
          name: '物业通知',
          desc: '发布并查看面向业主的通知',
          tag: '公告',
          icon: 'bell',
          tone: 'teal',
          path: '/pages/manage/property/notice/index',
        },
        {
          name: '报修工单',
          desc: '查看和删除居民报修工单',
          tag: '工单',
          icon: 'file-text',
          tone: 'amber',
          path: '/pages/manage/property/repair/index',
        },
        {
          name: '车位检测',
          desc: '新增、查看和删除车位检测记录',
          tag: '车位',
          icon: 'car',
          tone: 'cyan',
          path: '/pages/manage/property/parking/index',
        },
        {
          name: '社区上报',
          desc: '查看与处理居民随手拍上报',
          tag: '随手拍',
          icon: 'camera',
          tone: 'rose',
          path: '/pages/manage/property/report/index',
        },
      ],
    }
  },
  onLoad() {
    const info = uni.getWindowInfo()
    this.statusBarHeight = info.statusBarHeight || 20
  },
  methods: {
    goBack() {
      uni.reLaunch({ url: '/pages/manage/controls/controls' })
    },
    jumpSetting() {
      uni.navigateTo({
        url: '/pages/manage/personal/setting/setting',
      })
    },
    goFeature(url) {
      uni.navigateTo({ url })
    },
  },
}
</script>

<style lang="scss" scoped>
.property-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  padding: 0 24rpx 36rpx;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 12% 6%, rgba(56, 164, 255, 0.14) 0, rgba(56, 164, 255, 0) 250rpx),
    radial-gradient(circle at 88% 16%, rgba(14, 165, 233, 0.12) 0, rgba(14, 165, 233, 0) 280rpx),
    linear-gradient(180deg, #edf7ff 0%, #f5fbff 46%, #fbfdff 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.bg-orb--one {
  width: 210rpx;
  height: 210rpx;
  right: -75rpx;
  top: 180rpx;
  background: rgba(56, 164, 255, 0.12);
}

.bg-orb--two {
  width: 170rpx;
  height: 170rpx;
  left: -55rpx;
  top: 520rpx;
  background: rgba(22, 163, 74, 0.08);
}

.top-nav {
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.back-btn,
.icon-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 6rpx 16rpx rgba(30, 88, 150, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.top-title {
  color: #102033;
  font-size: 32rpx;
  font-weight: 900;
}

.header-card {
  margin-top: 8rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 12rpx 32rpx rgba(30, 88, 150, 0.12);
  color: #102033;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18rpx;
  position: relative;
  z-index: 1;
  overflow: hidden;
}

.header-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 24rpx;
  width: 8rpx;
  height: 88rpx;
  border-radius: 0 999rpx 999rpx 0;
  background: linear-gradient(180deg, #1470d8, #38a4ff);
}

.header-copy {
  min-width: 0;
}

.eyebrow {
  font-size: 22rpx;
  font-weight: 800;
  color: #1470d8;
}

.title {
  margin-top: 8rpx;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1.1;
  color: #102033;
}

.subtitle {
  margin-top: 10rpx;
  font-size: 23rpx;
  color: #64748b;
  line-height: 1.45;
}

.summary-pill {
  min-width: 112rpx;
  padding: 18rpx 16rpx;
  border-radius: 22rpx;
  background: linear-gradient(180deg, #f8fbff, #eef7ff);
  border: 1rpx solid #dcebfa;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.summary-num {
  color: #1470d8;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1;
}

.summary-label {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 21rpx;
  font-weight: 800;
}

.section-card {
  margin-top: 18rpx;
  padding: 22rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.93);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.10);
  position: relative;
  z-index: 1;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.section-title {
  color: #102033;
  font-size: 30rpx;
  font-weight: 900;
}

.section-subtitle {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
}

.feature-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.feature-card {
  min-height: 132rpx;
  border-radius: 24rpx;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 250, 255, 0.98));
  border: 1rpx solid #cddff5;
  box-shadow:
    0 10rpx 22rpx rgba(37, 99, 235, 0.08),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
  padding: 22rpx 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  box-sizing: border-box;
}

.feature-card:active {
  transform: scale(0.98);
}

.feature-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.feature-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx solid rgba(255, 255, 255, 0.42);
  box-shadow: 0 10rpx 18rpx rgba(37, 99, 235, 0.16);
  flex-shrink: 0;
}

.feature-icon--blue {
  background: linear-gradient(180deg, #3b82f6 0%, #60a5fa 100%);
}

.feature-icon--teal {
  background: linear-gradient(180deg, #0f766e 0%, #2dd4bf 100%);
}

.feature-icon--amber {
  background: linear-gradient(180deg, #d97706 0%, #fbbf24 100%);
}

.feature-icon--cyan {
  background: linear-gradient(180deg, #0369a1 0%, #38bdf8 100%);
}

.feature-icon--rose {
  background: linear-gradient(180deg, #db2777 0%, #fb7185 100%);
}

.feature-copy {
  min-width: 0;
}

.feature-name {
  font-size: 28rpx;
  color: #102033;
  font-weight: 900;
}

.feature-desc {
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.45;
  color: #64748b;
}

.feature-right {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
}

.feature-tag {
  height: 46rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #1470d8;
  font-size: 21rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
