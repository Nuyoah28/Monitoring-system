<template>
  <view class="feature-page">
    <view class="bg-shape bg-1"></view>
    <view class="bg-shape bg-2"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">空闲车位引导</view>
      <view class="ghost-btn" @tap="loadSpaces">刷新</view>
    </view>

    <view class="panel form-panel">
      <view class="panel-title">新增车位区域</view>
      <view class="form-item">
        <view class="label">位置</view>
        <input v-model="form.location" class="ipt" placeholder="例如：地下A区" />
      </view>
      <view class="form-row">
        <view class="form-item half">
          <view class="label">总车位数</view>
          <input v-model="form.totalSpaces" type="number" class="ipt" placeholder="如：120" />
        </view>
        <view class="form-item half">
          <view class="label">占用车辆</view>
          <input v-model="form.occupiedVehicle" class="ipt" placeholder="选填车牌" />
        </view>
      </view>
      <view class="submit-btn" @tap="submitSpace">保存区域</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">车位状态</view>
      <view v-if="!spaces.length" class="empty">暂无车位数据。</view>
      <view v-for="item in spaces" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="name">{{ item.location || '未知区域' }}</view>
          <view class="delete" @tap="removeSpace(item.id)">删除</view>
        </view>
        <view class="meta">总车位：{{ item.totalSpaces || 0 }}</view>
        <view class="meta">占用车辆：{{ item.occupiedVehicle || '无' }}</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000';

export default {
  data() {
    return {
      form: {
        location: '',
        totalSpaces: '',
        occupiedVehicle: '',
      },
      spaces: [],
    };
  },
  onShow() {
    this.loadSpaces();
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    goBack() {
      const pages = getCurrentPages();
      if (pages.length > 1) {
        uni.navigateBack();
        return;
      }
      uni.reLaunch({ url: '/pages/owner/home/index' });
    },
    async loadSpaces() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/parking-space/list');
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载车位信息失败');
          return;
        }
        this.spaces = Array.isArray(res.data) ? res.data : [];
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async submitSpace() {
      if (!this.form.location.trim()) {
        uni.$showMsg('请填写位置');
        return;
      }
      const total = Number(this.form.totalSpaces);
      if (!total || total <= 0) {
        uni.$showMsg('请填写正确的总车位数');
        return;
      }
      const payload = {
        location: this.form.location.trim(),
        totalSpaces: total,
        occupiedVehicle: this.form.occupiedVehicle.trim(),
      };
      try {
        const { data: res } = await uni.$http.post('/api/v1/parking-space/create', payload);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '保存失败');
          return;
        }
        uni.showToast({ title: '保存成功', icon: 'success' });
        this.form.location = '';
        this.form.totalSpaces = '';
        this.form.occupiedVehicle = '';
        this.loadSpaces();
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async removeSpace(id) {
      try {
        const { data: res } = await uni.$http.delete(`/api/v1/parking-space/${id}`);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '删除失败');
          return;
        }
        uni.showToast({ title: '已删除', icon: 'success' });
        this.loadSpaces();
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.feature-page {
  min-height: 100vh;
  padding: 26rpx 24rpx 32rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef8ff 0%, #f8fbff 54%, #ffffff 100%);
  position: relative;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 999rpx;
  filter: blur(66rpx);
  z-index: 0;
}

.bg-1 {
  width: 380rpx;
  height: 380rpx;
  background: rgba(0, 184, 216, 0.2);
  right: -140rpx;
  top: -100rpx;
}

.bg-2 {
  width: 440rpx;
  height: 440rpx;
  background: rgba(72, 130, 255, 0.14);
  left: -160rpx;
  bottom: -180rpx;
}

.top-bar,
.panel {
  position: relative;
  z-index: 2;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.back-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(32, 74, 126, 0.1);
}

.top-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #18304b;
}

.ghost-btn {
  padding: 0 20rpx;
  height: 56rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.82);
  color: #2b5b99;
  font-size: 24rpx;
}

.panel {
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
  margin-bottom: 18rpx;
}

.panel-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 700;
  margin-bottom: 16rpx;
}

.form-item {
  margin-bottom: 14rpx;
}

.form-row {
  display: flex;
  justify-content: space-between;
}

.half {
  width: 48%;
}

.label {
  font-size: 23rpx;
  color: #4e647e;
  margin-bottom: 8rpx;
}

.ipt {
  width: 100%;
  height: 76rpx;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px solid #d9e9fb;
  padding: 0 18rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #1d2f44;
}

.submit-btn {
  margin-top: 10rpx;
  height: 82rpx;
  border-radius: 41rpx;
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty {
  border-radius: 16rpx;
  background: rgba(236, 246, 255, 0.8);
  color: #58708e;
  font-size: 24rpx;
  padding: 18rpx;
}

.record-card {
  padding: 18rpx;
  border-radius: 18rpx;
  background: #f7fbff;
  border: 1px solid #dceafa;
  margin-bottom: 12rpx;
}

.record-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
}

.name {
  font-size: 28rpx;
  color: #17314c;
  font-weight: 700;
}

.delete {
  font-size: 22rpx;
  color: #e45e5e;
}

.meta {
  font-size: 23rpx;
  color: #54708f;
  line-height: 1.5;
}
</style>
