<template>
  <view class="feature-page">
    <view class="bg-shape bg-1"></view>
    <view class="bg-shape bg-2"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">报修入口</view>
      <view class="ghost-btn" @tap="loadRepairs">刷新</view>
    </view>

    <view class="panel form-panel">
      <view class="panel-title">发起报修</view>
      <view class="form-item">
        <view class="label">设备名称</view>
        <input v-model="form.deviceName" class="ipt" placeholder="例如：小区东门摄像头" />
      </view>
      <view class="form-item">
        <view class="label">故障位置</view>
        <input v-model="form.location" class="ipt" placeholder="例如：3号楼1单元" />
      </view>
      <view class="form-item">
        <view class="label">报修详情</view>
        <textarea v-model="form.repairDetail" class="textarea" placeholder="请描述故障现象、紧急程度等" maxlength="300" />
      </view>
      <view class="submit-btn" @tap="submitRepair">提交报修</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">我的报修记录</view>
      <view v-if="!records.length" class="empty">暂无报修记录。</view>
      <view v-for="item in records" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="name">{{ item.deviceName || '未命名设备' }}</view>
          <view class="delete" @tap="removeRepair(item.id)">删除</view>
        </view>
        <view class="meta">位置：{{ item.location || '--' }}</view>
        <view class="meta">时间：{{ formatTime(item.reportTime) }}</view>
        <view class="detail">{{ item.repairDetail || '暂无详情' }}</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000';

export default {
  data() {
    return {
      records: [],
      form: {
        deviceName: '',
        location: '',
        repairDetail: '',
      },
    };
  },
  onShow() {
    this.loadRepairs();
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
    formatTime(value) {
      if (!value) return '--';
      if (typeof value === 'string') return value.replace('T', ' ').slice(0, 19);
      return `${value}`;
    },
    nowTimeStr() {
      const now = new Date();
      const yyyy = now.getFullYear();
      const mm = `${now.getMonth() + 1}`.padStart(2, '0');
      const dd = `${now.getDate()}`.padStart(2, '0');
      const hh = `${now.getHours()}`.padStart(2, '0');
      const mi = `${now.getMinutes()}`.padStart(2, '0');
      const ss = `${now.getSeconds()}`.padStart(2, '0');
      return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`;
    },
    async loadRepairs() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/device-repair/list');
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载报修记录失败');
          return;
        }
        const username = uni.getStorageSync('username') || '';
        const all = Array.isArray(res.data) ? res.data : [];
        this.records = username ? all.filter((item) => item.publisher === username) : all;
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async submitRepair() {
      if (!this.form.deviceName.trim()) {
        uni.$showMsg('请填写设备名称');
        return;
      }
      if (!this.form.location.trim()) {
        uni.$showMsg('请填写故障位置');
        return;
      }
      if (!this.form.repairDetail.trim()) {
        uni.$showMsg('请填写报修详情');
        return;
      }
      const payload = {
        deviceName: this.form.deviceName.trim(),
        location: this.form.location.trim(),
        reportTime: this.nowTimeStr(),
        repairDetail: this.form.repairDetail.trim(),
        publisher: uni.getStorageSync('username') || '业主用户',
      };
      try {
        const { data: res } = await uni.$http.post('/api/v1/device-repair/create', payload);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '提交报修失败');
          return;
        }
        uni.showToast({ title: '提交成功', icon: 'success' });
        this.form.deviceName = '';
        this.form.location = '';
        this.form.repairDetail = '';
        this.loadRepairs();
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async removeRepair(id) {
      try {
        const { data: res } = await uni.$http.delete(`/api/v1/device-repair/${id}`);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '删除失败');
          return;
        }
        uni.showToast({ title: '已删除', icon: 'success' });
        this.loadRepairs();
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
  background: linear-gradient(180deg, #f2f9ff 0%, #fbfdfd 54%, #ffffff 100%);
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
  background: rgba(0, 180, 216, 0.2);
  right: -140rpx;
  top: -100rpx;
}

.bg-2 {
  width: 420rpx;
  height: 420rpx;
  background: rgba(66, 122, 255, 0.14);
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

.label {
  font-size: 23rpx;
  color: #4e647e;
  margin-bottom: 8rpx;
}

.ipt,
.textarea {
  width: 100%;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px solid #d9e9fb;
  padding: 14rpx 18rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #1d2f44;
}

.ipt {
  height: 76rpx;
}

.textarea {
  min-height: 160rpx;
  line-height: 1.5;
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

.detail {
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #395978;
  line-height: 1.6;
}
</style>
