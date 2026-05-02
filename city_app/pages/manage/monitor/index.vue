<template>
  <view class="monitor-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-nav">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="top-title">摄像头管理</text>
      <view class="top-placeholder"></view>
    </view>

    <view class="header-card">
      <view class="header-copy">
        <view class="eyebrow">点位与识别规则</view>
        <view class="title">设备管控中心</view>
        <view class="subtitle">查看在线状态、点位区域和每台摄像头的识别规则</view>
      </view>
      <view class="header-actions">
        <view class="ghost-btn" @tap="goPage('/pages/manage/monitor/map')">地图</view>
        <view class="primary-btn" @tap="goAiConfig()">规则管理</view>
      </view>
    </view>

    <view class="stat-grid">
      <view class="stat-card stat-card--primary">
        <text class="stat-num">{{ monitorList.length }}</text>
        <text class="stat-label">总摄像头</text>
      </view>
      <view class="stat-card stat-card--success">
        <text class="stat-num">{{ onlineCount }}</text>
        <text class="stat-label">在线</text>
      </view>
      <view class="stat-card stat-card--muted">
        <text class="stat-num">{{ offlineCount }}</text>
        <text class="stat-label">离线</text>
      </view>
      <view class="stat-card stat-card--warning">
        <text class="stat-num">{{ unconfiguredCount }}</text>
        <text class="stat-label">未设规则</text>
      </view>
    </view>

    <view class="section-card health-card">
      <view class="health-head">
        <view>
          <view class="health-title">规则设置完成度</view>
          <view class="health-subtitle">优先处理离线和未设置识别规则的摄像头</view>
        </view>
        <view class="health-percent">{{ configuredPercent }}%</view>
      </view>
      <view class="health-track">
        <view class="health-fill" :style="{ width: configuredPercent + '%' }"></view>
      </view>
    </view>

    <view class="section-card filter-card">
      <view class="search-row">
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索摄像头名称/区域"
          @input="applyFilter"
        />
      </view>
      <view class="filter-tabs">
        <view class="filter-tab" :class="activeFilter === 'all' ? 'is-active' : ''" @tap="setFilter('all')">全部</view>
        <view class="filter-tab" :class="activeFilter === 'online' ? 'is-active' : ''" @tap="setFilter('online')">在线</view>
        <view class="filter-tab" :class="activeFilter === 'offline' ? 'is-active' : ''" @tap="setFilter('offline')">离线</view>
        <view class="filter-tab" :class="activeFilter === 'unconfigured' ? 'is-active' : ''" @tap="setFilter('unconfigured')">未设规则</view>
      </view>
    </view>

    <scroll-view class="list" scroll-y>
      <view class="item" v-for="(item, index) in filteredMonitorList" :key="item.id">
        <view class="item-top">
          <view>
            <text class="name">{{ item.name || '未命名摄像头' }}</text>
            <view class="meta">区域：{{ item.department || item.area || '-' }}</view>
          </view>
          <text class="status" :class="item.running ? 'on' : 'off'">{{ item.running ? '在线' : '离线' }}</text>
        </view>

        <view class="ability-row">
          <view class="ability-chip" :class="isAiConfigured(item) ? 'is-on' : 'is-off'">{{ isAiConfigured(item) ? '规则已设置' : '未设规则' }}</view>
          <view class="ability-chip">已启用 {{ enabledAbilityCount(item) }} 项</view>
          <view class="ability-chip">负责人 {{ item.leader || '-' }}</view>
        </view>

        <view class="actions">
          <view class="btn btn--secondary" @tap="openEdit(index)">编辑区域</view>
          <view class="btn btn--primary" @tap="goAiConfig(item)">规则</view>
          <view class="btn btn--ghost" :class="!item.running ? 'is-online' : ''" @tap="editWorking(index)">{{ item.running ? '停用' : '启用' }}</view>
        </view>
      </view>
      <view class="empty" v-if="!filteredMonitorList.length">暂无监控设备</view>
    </scroll-view>

    <Edit
      v-if="showEdit"
      :showEdit="showEdit"
      :warnData="monitorList[currentIndex]"
      :monitorData="currentMonitorDetail"
      @change="changeShow"
    />

    <manage-tabbar current="monitor" :hidden="showEdit" />
  </view>
</template>

<script>
import Edit from "../controls/components/edit.vue";
import ManageTabbar from '@/components/navigation/manage-tabbar.vue';

export default {
  components: { Edit, ManageTabbar },
  data() {
    return {
      statusBarHeight: 0,
      monitorList: [],
      markersDetail: [],
      markerDetailMap: {},
      showEdit: false,
      currentIndex: 0,
      keyword: "",
      activeFilter: "all",
      filteredMonitorList: [],
    };
  },
  computed: {
    currentMonitorDetail() {
      const current = this.monitorList[this.currentIndex] || {};
      return this.markerDetailMap[current.id] || {};
    },
    onlineCount() {
      return this.monitorList.filter((item) => item.running).length;
    },
    offlineCount() {
      return Math.max(0, this.monitorList.length - this.onlineCount);
    },
    unconfiguredCount() {
      return this.monitorList.filter((item) => !this.isAiConfigured(item)).length;
    },
    configuredPercent() {
      if (!this.monitorList.length) return 0;
      return Math.round(((this.monitorList.length - this.unconfiguredCount) / this.monitorList.length) * 100);
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
      this.applyFilter();
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
    getAbilityList(item) {
      const ability = item && item.ability;
      return Array.isArray(ability) ? ability : [];
    },
    isAiConfigured(item) {
      if (item && typeof item.recognitionRuleConfigured === 'boolean') {
        return item.recognitionRuleConfigured;
      }
      return this.getAbilityList(item).some((ability) => ability && ability.checked);
    },
    enabledAbilityCount(item) {
      return this.getAbilityList(item).filter((ability) => ability && ability.checked).length;
    },
    applyFilter() {
      const keyword = this.keyword.trim().toLowerCase();
      let list = [...this.monitorList];
      if (keyword) {
        list = list.filter((item) => {
          const name = String(item.name || '').toLowerCase();
          const area = String(item.department || item.area || '').toLowerCase();
          return name.includes(keyword) || area.includes(keyword);
        });
      }
      if (this.activeFilter === 'online') {
        list = list.filter((item) => item.running);
      } else if (this.activeFilter === 'offline') {
        list = list.filter((item) => !item.running);
      } else if (this.activeFilter === 'unconfigured') {
        list = list.filter((item) => !this.isAiConfigured(item));
      }
      this.filteredMonitorList = list;
    },
    setFilter(type) {
      this.activeFilter = type;
      this.applyFilter();
    },
    openEdit(index) {
      const current = this.filteredMonitorList[index];
      if (!current) return;
      this.currentIndex = this.monitorList.findIndex((item) => item.id === current.id);
      if (this.currentIndex < 0) this.currentIndex = 0;
      this.showEdit = true;
    },
    async changeShow(bool) {
      if (bool) {
        await this.getMonitor();
        await this.getMap();
      }
      this.showEdit = false;
    },
    goAiConfig(item) {
      const current = item || this.filteredMonitorList[0] || this.monitorList[0];
      if (!current) {
        uni.showToast({ title: '暂无摄像头可配置', icon: 'none' });
        return;
      }
      uni.navigateTo({
        url: `/pages/manage/monitor/ai-config?id=${current.id || ''}&name=${encodeURIComponent(current.name || '')}&area=${encodeURIComponent(current.department || current.area || '')}`,
      });
    },
    editWorking(index) {
      const current = this.filteredMonitorList[index];
      if (!current) return;
      const id = current.id;
      uni.showModal({
        showCancel: true,
        title: current.running ? "是否关闭摄像头？" : "是否启用摄像头？",
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
    goBack() {
      uni.reLaunch({ url: '/pages/manage/controls/controls' });
    },
    goPage(url) {
      uni.navigateTo({ url });
    },
  },
};
</script>

<style scoped lang="scss">
.monitor-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 12% 6%, rgba(56, 164, 255, 0.14) 0, rgba(56, 164, 255, 0) 250rpx),
    radial-gradient(circle at 88% 16%, rgba(14, 165, 233, 0.12) 0, rgba(14, 165, 233, 0) 280rpx),
    linear-gradient(180deg, #edf7ff 0%, #f5fbff 46%, #fbfdff 100%);
  padding: 0 24rpx calc(128rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
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

.back-btn {
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

.top-placeholder {
  width: 64rpx;
  height: 64rpx;
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
  gap: 16rpx;
  position: relative;
  z-index: 1;
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

.header-actions {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  flex-shrink: 0;
}

.primary-btn,
.ghost-btn {
  min-width: 140rpx;
  height: 56rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 800;
}

.primary-btn {
  background: linear-gradient(135deg, #1470d8, #38a4ff);
  color: #fff;
}

.ghost-btn {
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #1470d8;
}

.stat-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12rpx;
}

.stat-card {
  min-height: 126rpx;
  padding: 20rpx 16rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 30rpx rgba(30, 88, 150, 0.10);
}

.stat-card--primary { border-top: 4rpx solid #1470d8; }
.stat-card--success { border-top: 4rpx solid #16a34a; }
.stat-card--muted { border-top: 4rpx solid #94a3b8; }
.stat-card--warning { border-top: 4rpx solid #f59e0b; }

.stat-num {
  color: #102033;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1;
}

.stat-label {
  margin-top: 12rpx;
  color: #64748b;
  font-size: 21rpx;
  font-weight: 700;
}

.section-card {
  margin-top: 18rpx;
  padding: 22rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.93);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.10);
}

.health-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(239, 247, 255, 0.96));
}

.health-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.health-title {
  color: #102033;
  font-size: 28rpx;
  font-weight: 900;
}

.health-subtitle {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
}

.health-percent {
  color: #1470d8;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1;
}

.health-track {
  margin-top: 18rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(148, 163, 184, 0.16);
  overflow: hidden;
}

.health-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #38a4ff, #1470d8);
}

.search-row {
  margin-bottom: 14rpx;
}

.search-input {
  width: 100%;
  height: 70rpx;
  line-height: 70rpx;
  padding: 0 22rpx;
  box-sizing: border-box;
  background: #f8fbff;
  border-radius: 18rpx;
  border: 1rpx solid #dcebfa;
}

.filter-tabs {
  display: flex;
  gap: 10rpx;
}

.filter-tab {
  flex: 1;
  height: 64rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  font-size: 23rpx;
  font-weight: 800;
}

.filter-tab.is-active {
  background: #1470d8;
  border-color: #1470d8;
  color: #fff;
}

.list {
  flex: 1;
  min-height: 0;
  margin-top: 18rpx;
  padding-bottom: 8rpx;
  box-sizing: border-box;
}

.item {
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.95);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.08);
  padding: 22rpx;
  margin-bottom: 16rpx;
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12rpx;
}

.name {
  font-size: 30rpx;
  font-weight: 900;
  color: #102033;
}

.status {
  font-size: 21rpx;
  border-radius: 999rpx;
  padding: 6rpx 14rpx;
  color: #fff;
  flex-shrink: 0;
}

.status.on { background: #16a34a; }
.status.off { background: #94a3b8; }

.meta {
  margin-top: 8rpx;
  font-size: 23rpx;
  color: #64748b;
}

.ability-row {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.ability-chip {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #475569;
  font-size: 21rpx;
  font-weight: 700;
}

.ability-chip.is-on {
  background: rgba(22, 163, 74, 0.10);
  color: #16a34a;
  border-color: rgba(22, 163, 74, 0.18);
}

.ability-chip.is-off {
  background: rgba(245, 158, 11, 0.10);
  color: #d97706;
  border-color: rgba(245, 158, 11, 0.18);
}

.actions {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  align-items: center;
}

.btn {
  padding: 10rpx 16rpx;
  border-radius: 14rpx;
  font-size: 21rpx;
  font-weight: 800;
  text-align: center;
  min-height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  margin-right: 4rpx;
}

.btn--primary {
  background: linear-gradient(135deg, #1470d8, #38a4ff);
  color: #fff;
}

.btn--secondary {
  background: rgba(37, 99, 235, 0.10);
  color: #1470d8;
}

.btn--ghost {
  background: rgba(220, 38, 38, 0.08);
  color: #dc2626;
}

.btn--ghost.is-online {
  background: rgba(22, 163, 74, 0.10);
  color: #16a34a;
}

.empty {
  text-align: center;
  color: #94a3b8;
  font-size: 24rpx;
  padding: 60rpx 0;
}
</style>
