<template>
  <view class="feature-page">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">物业通知管理</view>
      <view class="ghost-btn" @tap="loadNotices">刷新</view>
    </view>

    <view class="panel form-panel">
      <view class="panel-title">发布通知</view>
      <view class="form-item">
        <view class="label">通知内容</view>
        <textarea
          v-model="form.message"
          class="textarea"
          maxlength="300"
          placeholder="请输入物业通知内容"
        />
      </view>
      <view class="submit-btn" @tap="saveNotice">发布通知</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">通知记录</view>
      <view v-if="!list.length" class="empty">当前暂无通知。</view>
      <view v-for="item in list" :key="item.id" class="record-card">
        <view class="name">{{ item.message || '未命名通知' }}</view>
        <view class="meta">发布时间：{{ formatTime(item.timestamp) }}</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000'

export default {
  data() {
    return {
      form: {
        message: '',
      },
      list: [],
    }
  },
  onShow() {
    this.loadNotices()
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
    async loadNotices() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/system/message/getMessage')
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载通知失败')
          return
        }
        const arr = Array.isArray(res.data) ? res.data : []
        this.list = arr.sort((a, b) => {
          const ta = new Date(a.timestamp || 0).getTime()
          const tb = new Date(b.timestamp || 0).getTime()
          return tb - ta
        })
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      }
    },
    async saveNotice() {
      const message = this.form.message.trim()
      if (!message) {
        uni.$showMsg('请填写通知内容')
        return
      }
      try {
        const { data: res } = await uni.$http.post('/api/v1/system/message/addMessage', { message })
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '发布通知失败')
          return
        }
        uni.showToast({ title: '发布成功', icon: 'success' })
        this.form.message = ''
        this.loadNotices()
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

.label {
  font-size: 23rpx;
  color: #4e647e;
  margin-bottom: 8rpx;
}

.textarea {
  width: 100%;
  min-height: 160rpx;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px solid #d9e9fb;
  padding: 14rpx 18rpx;
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

.name {
  font-size: 28rpx;
  color: #17314c;
  font-weight: 700;
  line-height: 1.5;
}

.meta {
  margin-top: 8rpx;
  font-size: 23rpx;
  color: #54708f;
  line-height: 1.5;
}
</style>
