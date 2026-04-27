<template>
  <scroll-view scroll-y class="feature-page">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">车位引导</view>
      <view class="ghost-btn" @tap="loadSpaces">刷新</view>
    </view>

    <view class="overview panel">
      <view class="overview-head">
        <view>
          <view class="panel-title">车位总览</view>
          <view class="sub-text">实时占用与空位推荐</view>
        </view>
        <view class="rate-pill" :class="parkingRate >= 85 ? 'danger' : parkingRate >= 70 ? 'warn' : ''">
          {{ parkingRate }}%
        </view>
      </view>
      <view class="stats-grid">
        <view class="stat-cell">
          <text class="stat-label">总车位</text>
          <text class="stat-value">{{ parkingSummary.total }}</text>
        </view>
        <view class="stat-cell">
          <text class="stat-label">已占用</text>
          <text class="stat-value occupied">{{ parkingSummary.occupied }}</text>
        </view>
        <view class="stat-cell">
          <text class="stat-label">空闲</text>
          <text class="stat-value free">{{ parkingSummary.free }}</text>
        </view>
      </view>
      <view class="recommend-card">
        <view>
          <view class="recommend-label">推荐前往</view>
          <view class="recommend-title">{{ recommendedArea.location }}</view>
        </view>
        <view class="recommend-count">空 {{ recommendedArea.free }} 位</view>
      </view>
    </view>

    <view class="panel map-panel">
      <view class="panel-title">车位地图</view>
      <view class="legend-row">
        <view class="legend"><text class="dot free-dot"></text>空闲</view>
        <view class="legend"><text class="dot occupied-dot"></text>占用</view>
        <view class="legend"><text class="dot abnormal-dot"></text>紧张</view>
      </view>
      <view v-if="!parkingAreas.length" class="empty">暂无车位数据。</view>
      <view v-else class="parking-map">
        <view v-for="area in parkingAreas" :key="area.id || area.location" class="area-block">
          <view class="area-head">
            <view>
              <view class="area-name">{{ area.location }}</view>
              <view class="area-meta">{{ area.occupied }}/{{ area.total }} 已用</view>
            </view>
            <view class="area-rate" :class="area.rate >= 85 ? 'danger' : area.rate >= 70 ? 'warn' : ''">
              {{ area.rate }}%
            </view>
          </view>
          <view class="slot-grid">
            <view
              v-for="slot in area.slots"
              :key="slot.no"
              class="slot"
              :class="{ busy: slot.busy, tight: area.rate >= 85 && !slot.busy }"
            ></view>
          </view>
          <view class="progress">
            <view class="progress-inner" :style="{ width: area.rate + '%' }"></view>
          </view>
        </view>
      </view>
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
          <view class="label">占用车辆数</view>
          <input v-model="form.occupiedVehicle" type="number" class="ipt" placeholder="如：35" />
        </view>
      </view>
      <view class="submit-btn" @tap="submitSpace">保存区域</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">区域明细</view>
      <view v-if="!parkingAreas.length" class="empty">暂无车位数据。</view>
      <view v-for="item in parkingAreas" :key="'record-' + (item.id || item.location)" class="record-card">
        <view class="record-head">
          <view class="name">{{ item.location }}</view>
          <view class="delete" @tap="removeSpace(item.id)">删除</view>
        </view>
        <view class="record-row">
          <view class="meta">空闲 {{ item.free }} 位</view>
          <view class="meta">占用 {{ item.occupied }} 位</view>
          <view class="meta">总计 {{ item.total }} 位</view>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script>
const SUCCESS_CODE = '00000';

const FALLBACK_SPACES = [
  { id: 'mock-a', location: '地库A区', totalSpaces: 56, occupiedVehicle: '38' },
  { id: 'mock-b', location: '地库B区', totalSpaces: 48, occupiedVehicle: '29' },
  { id: 'mock-c', location: '地面东侧', totalSpaces: 32, occupiedVehicle: '18' },
  { id: 'mock-d', location: '地面西侧', totalSpaces: 28, occupiedVehicle: '23' },
];

export default {
  data() {
    return {
      form: {
        location: '',
        totalSpaces: '',
        occupiedVehicle: '',
      },
      spaces: [],
      usingMock: false,
    };
  },
  computed: {
    parkingAreas() {
      return this.spaces.map((item, index) => {
        const total = Math.max(0, Number(item.totalSpaces || item.total || 0));
        const occupied = Math.min(total, this.parseOccupiedCount(item.occupiedVehicle));
        const free = Math.max(0, total - occupied);
        const rate = total ? Math.round((occupied / total) * 100) : 0;
        return {
          id: item.id || `area-${index}`,
          location: item.location || item.area || `车位区域${index + 1}`,
          total,
          occupied,
          free,
          rate,
          slots: this.buildSlots(total, occupied),
        };
      });
    },
    parkingSummary() {
      return this.parkingAreas.reduce(
        (sum, item) => ({
          total: sum.total + item.total,
          occupied: sum.occupied + item.occupied,
          free: sum.free + item.free,
        }),
        { total: 0, occupied: 0, free: 0 }
      );
    },
    parkingRate() {
      const total = this.parkingSummary.total;
      if (!total) return 0;
      return Math.round((this.parkingSummary.occupied / total) * 100);
    },
    recommendedArea() {
      if (!this.parkingAreas.length) return { location: '暂无可推荐区域', free: 0 };
      return [...this.parkingAreas].sort((a, b) => b.free - a.free)[0];
    },
  },
  onShow() {
    this.loadSpaces();
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    parseOccupiedCount(value) {
      if (value === null || value === undefined) return 0;
      const text = `${value}`.trim();
      if (!text) return 0;
      if (/^\d+$/.test(text)) return Number(text);
      return text.split(/[,，\s]+/).filter(Boolean).length;
    },
    buildSlots(total, occupied) {
      const count = Math.min(24, Math.max(8, total || 8));
      const busyCount = total ? Math.round((occupied / total) * count) : 0;
      return Array.from({ length: count }, (_, index) => ({
        no: index + 1,
        busy: index < busyCount,
      }));
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
        return;
      }
      uni.switchTab({ url: '/pages/manage/controls/controls' });
    },
    async loadSpaces() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/parking-space/list');
        if (!this.isSuccess(res)) {
          this.spaces = FALLBACK_SPACES;
          this.usingMock = true;
          return;
        }
        const list = Array.isArray(res.data) ? res.data : [];
        this.spaces = list.length ? list : FALLBACK_SPACES;
        this.usingMock = !list.length;
      } catch (e) {
        this.spaces = FALLBACK_SPACES;
        this.usingMock = true;
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
      const occupiedCount = Number(this.form.occupiedVehicle);
      if (Number.isNaN(occupiedCount) || occupiedCount < 0 || occupiedCount > total) {
        uni.$showMsg('请填写正确的占用车辆数');
        return;
      }
      const payload = {
        location: this.form.location.trim(),
        totalSpaces: total,
        occupiedVehicle: String(occupiedCount),
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
      if (!id || `${id}`.startsWith('mock-')) {
        uni.$showMsg('模拟区域不可删除');
        return;
      }
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
  padding: 26rpx 24rpx 34rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #dceefa 0%, #f6fbff 58%, #ffffff 100%);
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
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
  margin-bottom: 18rpx;
  box-sizing: border-box;
}

.overview {
  background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(232,246,255,0.9));
}

.overview-head,
.area-head,
.record-head,
.recommend-card,
.record-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 30rpx;
  color: #1d2f44;
  font-weight: 800;
}

.sub-text,
.recommend-label,
.label,
.area-meta,
.meta {
  font-size: 23rpx;
  color: #58708e;
}

.rate-pill,
.area-rate {
  min-width: 92rpx;
  height: 54rpx;
  border-radius: 27rpx;
  background: rgba(56, 196, 139, 0.15);
  color: #1b9d67;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
}

.rate-pill.warn,
.area-rate.warn {
  background: rgba(255, 176, 58, 0.18);
  color: #d58a00;
}

.rate-pill.danger,
.area-rate.danger {
  background: rgba(255, 87, 104, 0.16);
  color: #e34a5d;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin-top: 20rpx;
}

.stat-cell {
  border-radius: 18rpx;
  background: #f6fbff;
  padding: 18rpx 12rpx;
}

.stat-label {
  display: block;
  color: #66809b;
  font-size: 22rpx;
}

.stat-value {
  display: block;
  margin-top: 8rpx;
  color: #19334f;
  font-size: 38rpx;
  font-weight: 900;
}

.stat-value.occupied {
  color: #ef5a66;
}

.stat-value.free {
  color: #15aa72;
}

.recommend-card {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: #edf7ff;
  border: 1px solid #d8ebff;
}

.recommend-title {
  margin-top: 4rpx;
  font-size: 30rpx;
  font-weight: 800;
  color: #17314c;
}

.recommend-count {
  color: #1377c8;
  font-size: 28rpx;
  font-weight: 800;
}

.legend-row {
  display: flex;
  gap: 18rpx;
  margin: 14rpx 0 16rpx;
}

.legend {
  display: flex;
  align-items: center;
  gap: 8rpx;
  color: #58708e;
  font-size: 22rpx;
}

.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
}

.free-dot {
  background: #5ed8a5;
}

.occupied-dot {
  background: #ff6672;
}

.abnormal-dot {
  background: #ffc857;
}

.area-block {
  margin-bottom: 16rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: #f8fcff;
  border: 1px solid #dceafa;
}

.area-name,
.name {
  font-size: 28rpx;
  color: #17314c;
  font-weight: 800;
}

.slot-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8rpx;
}

.slot {
  height: 34rpx;
  border-radius: 8rpx;
  background: linear-gradient(180deg, #75deb1, #46c993);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.52);
}

.slot.busy {
  background: linear-gradient(180deg, #ff8791, #ef5967);
}

.slot.tight {
  background: linear-gradient(180deg, #ffd56c, #f1ad2c);
}

.progress {
  margin-top: 14rpx;
  height: 10rpx;
  border-radius: 8rpx;
  background: #e2eef9;
  overflow: hidden;
}

.progress-inner {
  height: 100%;
  border-radius: 8rpx;
  background: linear-gradient(90deg, #65b8ff, #5ed8a5);
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
  font-weight: 800;
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

.delete {
  font-size: 22rpx;
  color: #e45e5e;
}
</style>
