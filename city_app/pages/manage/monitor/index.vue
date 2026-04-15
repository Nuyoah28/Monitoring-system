<template>
  <view class="monitor-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="header-row">
      <view class="title">监控列表</view>
    </view>

    <scroll-view class="list" scroll-y>
      <view class="item" v-for="(item, index) in monitorList" :key="item.id">
        <view class="item-head">
          <text class="name">{{ item.name || '未命名监控' }}</text>
          <text class="status" :class="item.running ? 'on' : 'off'">{{ item.running ? '在线' : '离线' }}</text>
        </view>
        <view class="meta">区域：{{ item.department || item.area || '-' }}</view>
        <view class="meta">负责人：{{ item.leader || '-' }}</view>
        <view class="actions">
          <view class="btn" @tap="openEdit(index)">画范围/编辑</view>
          <view class="btn danger" :class="!item.running ? 'enable' : ''" @tap="editWorking(index)">{{ item.running ? '停用' : '启用' }}</view>
        </view>
      </view>
      <view class="empty" v-if="!monitorList.length">暂无监控设备</view>
    </scroll-view>

    <Edit
      v-if="showEdit"
      :showEdit="showEdit"
      :warnData="monitorList[currentIndex]"
      :monitorData="currentMonitorDetail"
      @change="changeShow"
    />
  </view>
</template>

<script>
import Edit from "../controls/components/edit.vue";

export default {
  components: { Edit },
  data() {
    return {
      statusBarHeight: 0,
      monitorList: [],
      markersDetail: [],
      markerDetailMap: {},
      showEdit: false,
      currentIndex: 0,
    };
  },
  computed: {
    currentMonitorDetail() {
      const current = this.monitorList[this.currentIndex] || {};
      return this.markerDetailMap[current.id] || {};
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.getMonitor();
    this.getMap();
  },
  methods: {
    async getMonitor() {
      const { data } = await uni.$http.get("/api/v1/monitor");
      this.monitorList = (data && data.data) || [];
    },
    async getMap() {
      const { data } = await uni.$http.get("/api/v1/monitor/map");
      const datas = (data && data.data) || {};
      this.markersDetail = datas.monitorPosList || [];
      const map = {};
      this.markersDetail.forEach((item) => {
        map[item.id] = item;
      });
      this.markerDetailMap = map;
    },
    openEdit(index) {
      this.currentIndex = index;
      this.showEdit = true;
    },
    async changeShow(bool) {
      if (bool) {
        await this.getMonitor();
        await this.getMap();
      }
      this.showEdit = false;
    },
    editWorking(index) {
      const id = this.monitorList[index].id;
      uni.showModal({
        showCancel: true,
        title: this.monitorList[index].running ? "是否关闭摄像头？" : "是否启用摄像头？",
        success: async (res) => {
          if (res.confirm) {
            const { data } = await uni.$http.post(`/api/v1/monitor/switch/${id}`);
            if (data && data.code === "00000") {
              this.getMonitor();
              this.getMap();
            }
          }
        },
      });
    },
  },
};
</script>

<style scoped lang="scss">
/* 统一物业管理页面 —— 蓝色渐变背景 */
.monitor-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eaf5ff 0%, #f7fbff 100%);
  padding: 0 24rpx 130rpx;
  box-sizing: border-box;
}

.header-row {
  margin-top: 8rpx;
  margin-bottom: 22rpx;
}

.title {
  font-size: 40rpx;
  font-weight: 800;
  color: #1a2a3a;
}

.list {
  height: calc(100vh - 220rpx);
}

/* 统一卡片样式 */
.item {
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 8rpx 20rpx rgba(62, 95, 150, 0.08);
  padding: 24rpx;
  margin-bottom: 16rpx;
}

.item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.name {
  font-size: 30rpx;
  font-weight: 700;
  color: #1a2a3a;
}

.status {
  font-size: 22rpx;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
  color: #fff;
}
.status.on {
  background: #22c55e;
}
.status.off {
  background: #94a3b8;
}

.meta {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: rgba(26, 42, 58, 0.62);
}

.actions {
  margin-top: 14rpx;
  display: flex;
  gap: 12rpx;
}

.btn {
  padding: 10rpx 20rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
  color: #fff;
  background: #3b82f6;
}

/* 启用 = 绿色 */
.btn.danger {
  background: #f43f5e;
}
/* 停用 = 红色 */
.btn.danger.enable {
  background: #22c55e;
}

.empty {
  text-align: center;
  color: rgba(26, 42, 58, 0.62);
  font-size: 24rpx;
  padding-top: 60rpx;
}
</style>