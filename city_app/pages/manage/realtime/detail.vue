<template>
  <view class="detail-page">
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">报警详情</view>
      <view class="ghost-btn" @tap="loadDetail">刷新</view>
    </view>

    <view class="panel" v-if="loaded">
      <view class="video-wrap">
        <video
          v-if="detail.video"
          :src="detail.video"
          controls
          muted
          class="video"
        ></video>
        <view v-else class="video-empty">暂无视频</view>
      </view>

      <view class="table">
        <view class="row">
          <view class="cell left">事件ID</view>
          <view class="cell right">{{ detail.id || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">摄像头</view>
          <view class="cell right">{{ detail.name || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">区域</view>
          <view class="cell right">{{ detail.department || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">类别</view>
          <view class="cell right">{{ detail.eventName || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">等级</view>
          <view class="cell right">{{ detail.level ? `${detail.level}级` : '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">时间</view>
          <view class="cell right">{{ detail.date || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">状态</view>
          <view class="cell right" :class="detail.deal === '已处理' ? 'dealt' : 'un-dealt'">
            {{ detail.deal || '--' }}
          </view>
        </view>
        <view class="row">
          <view class="cell left">处理内容</view>
          <view class="cell right">{{ detail.content || '--' }}</view>
        </view>
        <view class="row">
          <view class="cell left">联系电话</view>
          <view class="cell right">{{ detail.phone || '--' }}</view>
        </view>
      </view>
    </view>

    <view v-else class="loading-wrap">加载中...</view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000'

export default {
  data() {
    return {
      statusBarHeight: 0,
      alarmId: null,
      loaded: false,
      detail: {},
    }
  },
  onLoad(options) {
    const info = uni.getWindowInfo()
    this.statusBarHeight = info.statusBarHeight || 20
    this.alarmId = options && options.id ? Number(options.id) : null
    this.loadDetail()
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE
    },
    goBack() {
      uni.navigateBack()
    },
    async loadDetail() {
      // --- 模拟数据特殊逻辑 ---
      if (this.alarmId >= 999001 && this.alarmId <= 999003) {
        const mockMap = {
          999001: { id: 999001, name: '北门摄像头(模拟)', eventName: '电动车进楼', department: '北门入口', level: 2, deal: '未处理', video: 'http://localhost:8848/video/电动车进楼.mp4', date: '今日最新', phone: '13800138000', content: '演示模拟推送' },
          999002: { id: 999002, name: '车库摄像头(模拟)', eventName: '明火', department: '车库入口', level: 3, deal: '未处理', video: 'http://localhost:8848/video/火灾烟雾.mp4', date: '今日最新', phone: '13800138000', content: '演示模拟推送' },
          999003: { id: 999003, name: '东侧摄像头(模拟)', eventName: '垃圾', department: '东侧步道', level: 1, deal: '未处理', video: 'http://localhost:8848/video/垃圾桶溢出.mp4', date: '今日最新', phone: '13811112222', content: '演示模拟推送' }
        };
        this.detail = mockMap[this.alarmId];
        this.loaded = true;
        return;
      }

      if (!this.alarmId) {
        uni.$showMsg('报警ID无效')
        return
      }
      this.loaded = false
      try {
        const { data: res } = await uni.$http.get(`/api/v1/alarm/${this.alarmId}`)
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载报警详情失败')
          this.loaded = true
          return
        }
        this.detail = res.data || {}
        
        // --- 模拟演示视频重定向逻辑 ---
        const video = this.detail.video;
        if (video && typeof video === 'string') {
          if (video.includes('SIM_BIKE_DEMO')) {
            this.detail.video = 'http://localhost:8848/video/电动车进楼.mp4';
          } else if (video.includes('SIM_FIRE_DEMO')) {
            this.detail.video = 'http://localhost:8848/video/火灾烟雾.mp4';
          } else if (video.includes('SIM_GARBAGE_DEMO')) {
            this.detail.video = 'http://localhost:8848/video/垃圾桶溢出.mp4';
          }
        }
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试')
      } finally {
        this.loaded = true
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.detail-page {
  min-height: 100vh;
  padding: 0 24rpx 32rpx;
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
  padding: 20rpx;
}

.video-wrap {
  width: 100%;
  height: 360rpx;
  border-radius: 18rpx;
  overflow: hidden;
  background: #dfeffc;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video {
  width: 100%;
  height: 100%;
}

.video-empty {
  color: #5b7492;
  font-size: 24rpx;
}

.table {
  border-radius: 16rpx;
  overflow: hidden;
  border: 1px solid #dceafa;
}

.row {
  display: flex;
}

.row + .row {
  border-top: 1px solid #dceafa;
}

.cell {
  min-height: 72rpx;
  padding: 0 16rpx;
  display: flex;
  align-items: center;
  font-size: 24rpx;
  color: #2a4058;
}

.left {
  width: 32%;
  background: #f1f7ff;
  color: #49637e;
}

.right {
  width: 68%;
  background: #fff;
  word-break: break-all;
}

.dealt {
  color: #06bfa1;
  font-weight: 700;
}

.un-dealt {
  color: #ff5d5d;
  font-weight: 700;
}

.loading-wrap {
  margin-top: 120rpx;
  text-align: center;
  color: #6a7990;
  font-size: 26rpx;
}
</style>
