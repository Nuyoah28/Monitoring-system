<template>
  <view class="map-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="back-btn" @tap="goBack">
      <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
    </view>
    <view class="map-panel">
      <MonitorMap :monitorList="filteredList" :compact="true" />
    </view>

    <view class="list-panel">
      <view class="search-row">
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索摄像头名称/区域"
          @input="onSearch"
        />
      </view>

      <view class="camera-list">
        <view class="camera-item" v-for="item in pagedList" :key="item.id" @tap="openVideo(item)">
          <view class="name-row">
            <text class="name">{{ item.name || '未命名摄像头' }}</text>
            <text class="status" :class="item.running ? 'on' : 'off'">{{ item.running ? '在线' : '离线' }}</text>
          </view>
          <view class="meta">{{ item.department || item.area || '-' }}</view>
        </view>
        <view class="empty" v-if="!pagedList.length">当前页暂无摄像头</view>
      </view>

      <view class="pager">
        <view class="page-btn" @tap="prevPage">上一页</view>
        <text class="page-text">{{ pageNum }} / {{ totalPage }}</text>
        <view class="page-btn" @tap="nextPage">下一页</view>
      </view>
    </view>
  </view>
</template>

<script>
import MonitorMap from "../controls/components/monitorMap.vue";

export default {
  components: { MonitorMap },
  data() {
    return {
      statusBarHeight: 0,
      monitors: [],
      keyword: "",
      pageNum: 1,
      pageSize: 3,
    };
  },
  computed: {
    filteredList() {
      const k = this.keyword.trim().toLowerCase();
      if (!k) return this.monitors;
      return this.monitors.filter((item) => {
        const name = (item.name || "").toLowerCase();
        const area = (item.department || item.area || "").toLowerCase();
        return name.includes(k) || area.includes(k);
      });
    },
    totalPage() {
      return Math.max(1, Math.ceil(this.filteredList.length / this.pageSize));
    },
    pagedList() {
      const start = (this.pageNum - 1) * this.pageSize;
      return this.filteredList.slice(start, start + this.pageSize);
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.getMonitors();
  },
  methods: {
    async getMonitors() {
      const { data } = await uni.$http.get('/api/v1/monitor');
      this.monitors = (data && data.data) || [];
      this.pageNum = 1;
    },
    onSearch() {
      this.pageNum = 1;
    },
    prevPage() {
      this.pageNum = Math.max(1, this.pageNum - 1);
    },
    nextPage() {
      this.pageNum = Math.min(this.totalPage, this.pageNum + 1);
    },
    openVideo(item) {
      const videoUrl = item.video || item.ip || '';
      if (!videoUrl) {
        uni.showToast({ title: '该设备暂无视频地址', icon: 'none' });
        return;
      }
      uni.navigateTo({
        url: `/pages/manage/monitor/video?id=${item.id || ''}&name=${encodeURIComponent(item.name || '')}&video=${encodeURIComponent(videoUrl)}`,
      });
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: '/pages/manage/controls/controls' });
      }
    },
  },
};
</script>

<style scoped lang="scss">
.map-page {
  height: 100vh;
  background: linear-gradient(180deg, #eaf5ff 0%, #f7fbff 100%);
  padding: 0 20rpx 20rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.back-btn {
  position: absolute;
  left: 20rpx;
  top: 10rpx;
  width: 60rpx;
  height: 60rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 14rpx rgba(45, 98, 160, 0.16);
  z-index: 20;
}

.map-panel {
  height: 60vh;
  border-radius: 18rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
}

.list-panel {
  margin-top: 14rpx;
  flex: 1;
  min-height: 0;
  background: #f9fcff;
  border-radius: 18rpx;
  padding: 14rpx;
  box-shadow: 0 8rpx 20rpx rgba(45, 98, 160, 0.1);
  display: flex;
  flex-direction: column;
}

.search-input {
  width: 100%;
  height: 72rpx;
  border-radius: 12rpx;
  background: #edf6ff;
  padding: 0 18rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #1f2d3c;
}

.camera-list {
  flex: 1;
  margin-top: 12rpx;
  overflow: hidden;
}

.camera-item {
  padding: 14rpx 10rpx;
  border-bottom: 1px solid #e8edf5;
}

.name-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.name {
  color: #1f2d3c;
  font-size: 30rpx;
  font-weight: 700;
}

.status {
  font-size: 22rpx;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  color: #fff;
}

.status.on { background: #22c55e; }
.status.off { background: #f97316; }

.meta {
  margin-top: 6rpx;
  color: #7b8ca0;
  font-size: 24rpx;
}

.pager {
  margin-top: 10rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-btn {
  padding: 8rpx 16rpx;
  border-radius: 10rpx;
  background: #2b8cff;
  color: #fff;
  font-size: 24rpx;
}

.page-text {
  color: #6f8093;
  font-size: 24rpx;
}

.empty {
  text-align: center;
  color: #8da0b5;
  font-size: 24rpx;
  padding: 30rpx 0;
}
</style>
