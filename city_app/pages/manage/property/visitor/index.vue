<template>
  <view class="feature-page">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">访客登记管理</view>
      <view class="ghost-btn" @tap="loadVisitors">刷新</view>
    </view>

    <view class="panel form-panel">
      <view class="panel-title">新增访客</view>
      <view class="form-item">
        <view class="label">访客姓名</view>
        <input v-model="form.visitorName" class="ipt" placeholder="请输入姓名" />
      </view>
      <view class="form-row">
        <view class="form-item half">
          <view class="label">到访日期</view>
          <picker mode="date" :value="visitDate" @change="onDateChange">
            <view class="picker">{{ visitDate || '请选择日期' }}</view>
          </picker>
        </view>
        <view class="form-item half">
          <view class="label">到访时间</view>
          <picker mode="time" :value="visitTime" @change="onTimeChange">
            <view class="picker">{{ visitTime || '请选择时间' }}</view>
          </picker>
        </view>
      </view>
      <view class="form-item">
        <view class="label">车牌号</view>
        <input v-model="form.plateNumber" class="ipt" placeholder="选填，如：鲁B12345" />
      </view>
      <view class="submit-btn" @tap="submitVisitor">提交登记</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">登记记录</view>
      <view v-if="!records.length" class="empty">暂无记录。</view>
      <view v-for="item in records" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="name">{{ item.visitorName || '未命名访客' }}</view>
          <view class="delete" @tap="removeVisitor(item.id)">删除</view>
        </view>
        <view class="meta">到访时间：{{ formatTime(item.visitTime) }}</view>
        <view class="meta">车牌号码：{{ item.plateNumber || '无' }}</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000'

export default {
  data() {
    const now = new Date()
    const yyyy = now.getFullYear()
    const mm = `${now.getMonth() + 1}`.padStart(2, '0')
    const dd = `${now.getDate()}`.padStart(2, '0')
    const hh = `${now.getHours()}`.padStart(2, '0')
    const mi = `${now.getMinutes()}`.padStart(2, '0')
    return {
      visitDate: `${yyyy}-${mm}-${dd}`,
      visitTime: `${hh}:${mi}`,
      form: {
        visitorName: '',
        plateNumber: '',
      },
      records: [],
    }
  },
  onShow() {
    this.loadVisitors()
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE
    },
    goBack() {
      uni.navigateBack()
    },
    onDateChange(e) {
      this.visitDate = e.detail.value
    },
    onTimeChange(e) {
      this.visitTime = e.detail.value
    },
    buildVisitTime() {
      return `${this.visitDate} ${this.visitTime}:00`
    },
    formatTime(value) {
      if (!value) return '--'
      if (typeof value === 'string') return value.replace('T', ' ').slice(0, 19)
      return `${value}`
    },
    async loadVisitors() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/visitor/list')
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载访客列表失败')
          return
        }
        this.records = Array.isArray(res.data) ? res.data : []
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      }
    },
    async submitVisitor() {
      if (!this.form.visitorName.trim()) {
        uni.$showMsg('请填写访客姓名')
        return
      }
      const payload = {
        visitorName: this.form.visitorName.trim(),
        visitTime: this.buildVisitTime(),
        plateNumber: this.form.plateNumber.trim(),
      }
      try {
        const { data: res } = await uni.$http.post('/api/v1/visitor/create', payload)
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '提交失败')
          return
        }
        uni.showToast({ title: '登记成功', icon: 'success' })
        this.form.visitorName = ''
        this.form.plateNumber = ''
        this.loadVisitors()
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      }
    },
    async removeVisitor(id) {
      try {
        const { data: res } = await uni.$http.delete(`/api/v1/visitor/${id}`)
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '删除失败')
          return
        }
        uni.showToast({ title: '已删除', icon: 'success' })
        this.loadVisitors()
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

.ipt,
.picker {
  width: 100%;
  height: 76rpx;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px solid #d9e9fb;
  padding: 0 18rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #1d2f44;
  display: flex;
  align-items: center;
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
