<template>
  <view class="feature-page">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">报修工单管理</view>
      <view class="ghost-btn" @tap="loadRepairs">刷新</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">工单记录（仅查看/删除）</view>
      <view v-if="!records.length" class="empty">暂无报修记录。</view>
      <view v-for="item in records" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="name">{{ item.deviceName || '未命名设备' }}</view>
          <view class="delete" @tap="removeRepair(item.id)">删除</view>
        </view>
        <view class="meta">位置：{{ item.location || '--' }}</view>
        <view class="meta">时间：{{ formatTime(item.reportTime) }}</view>
        <view class="meta">提交人：{{ item.publisher || '--' }}</view>
        <view class="detail">{{ item.repairDetail || '暂无详情' }}</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000'

export default {
  data() {
    return {
      records: [],
    }
  },
  onShow() {
    this.loadRepairs()
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE
    },
    goBack() {
      uni.navigateBack()
    },
    formatTime(value) {
      if (!value) return '--'
      if (typeof value === 'string') return value.replace('T', ' ').slice(0, 19)
      return `${value}`
    },
    async loadRepairs() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/device-repair/list')
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载报修记录失败')
          return
        }
        this.records = Array.isArray(res.data) ? res.data : []
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      }
    },
    async removeRepair(id) {
      try {
        const { data: res } = await uni.$http.delete(`/api/v1/device-repair/${id}`)
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '删除失败')
          return
        }
        uni.showToast({ title: '已删除', icon: 'success' })
        this.loadRepairs()
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.feature-page {
  min-height: 100vh;
  padding: 26rpx 24rpx 32rpx;
  box-sizing: border-box;
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
}

.panel-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 700;
  margin-bottom: 16rpx;
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
