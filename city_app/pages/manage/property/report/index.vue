<template>
  <view class="feature-page" :style="{ paddingTop: pageTopPadding + 'px' }">
    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">社区上报管理</view>
      <view class="ghost-btn" @tap="loadList">刷新</view>
    </view>

    <view class="filter-row">
      <view
        v-for="opt in filterOptions"
        :key="opt.value"
        class="filter-chip"
        :class="filterStatus === opt.value ? 'is-active' : ''"
        @tap="filterStatus = opt.value"
      >{{ opt.label }}</view>
    </view>

    <view class="panel list-panel">
      <view v-if="!filteredRecords.length" class="empty">暂无居民上报。</view>
      <view v-for="item in filteredRecords" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="cate-tag">{{ item.category || '其他' }}</view>
          <view class="status-badge" :class="'status-' + statusClass(item.status)">{{ statusText(item.status) }}</view>
          <view class="delete" @tap="removeReport(item.id)">删除</view>
        </view>
        <view class="detail">{{ item.description || '暂无描述' }}</view>
        <view class="meta">上报人：{{ item.publisher || '--' }}</view>
        <view class="meta">位置：{{ item.location || '--' }}</view>
        <view class="meta">时间：{{ formatTime(item.reportTime) }}</view>
        <view class="img-grid" v-if="item.imageUrls && item.imageUrls.length">
          <image
            class="thumb"
            v-for="(url, i) in item.imageUrls"
            :key="i"
            :src="url"
            mode="aspectFill"
            @tap="previewRemote(item.imageUrls, url)"
          ></image>
        </view>
        <view class="reply" v-if="item.handleReply">回复：{{ item.handleReply }}（{{ item.handler || '物业' }}）</view>
        <view class="handle-btn" @tap="openHandle(item)">处理</view>
      </view>
    </view>

    <!-- 处理弹层 -->
    <view class="mask" v-if="showHandle" @tap="showHandle = false"></view>
    <view class="sheet" v-if="showHandle">
      <view class="sheet-title">处理上报</view>
      <view class="sheet-label">处理状态</view>
      <view class="status-row">
        <view
          v-for="opt in statusOptions"
          :key="opt.value"
          class="status-opt"
          :class="handleForm.status === opt.value ? 'is-active' : ''"
          @tap="handleForm.status = opt.value"
        >{{ opt.label }}</view>
      </view>
      <view class="sheet-label">处理回复</view>
      <textarea v-model="handleForm.handleReply" class="textarea" placeholder="填写处理说明，业主可见" maxlength="200" />
      <view class="sheet-actions">
        <view class="sheet-btn ghost" @tap="showHandle = false">取消</view>
        <view class="sheet-btn primary" @tap="submitHandle">提交</view>
      </view>
    </view>
  </view>
</template>

<script>
const SUCCESS_CODE = '00000';

export default {
  data() {
    return {
      statusBarHeight: 0,
      records: [],
      filterStatus: -1,
      filterOptions: [
        { label: '全部', value: -1 },
        { label: '待处理', value: 0 },
        { label: '处理中', value: 1 },
        { label: '已处理', value: 2 },
      ],
      statusOptions: [
        { label: '待处理', value: 0 },
        { label: '处理中', value: 1 },
        { label: '已处理', value: 2 },
      ],
      showHandle: false,
      handleForm: {
        id: null,
        status: 0,
        handleReply: '',
      },
    };
  },
  computed: {
    pageTopPadding() {
      return this.statusBarHeight + 14;
    },
    filteredRecords() {
      if (this.filterStatus === -1) return this.records;
      return this.records.filter((item) => Number(item.status) === this.filterStatus);
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    uni.$on('newReport', this.handleNewReport);
  },
  onShow() {
    this.loadList();
  },
  onUnload() {
    uni.$off('newReport', this.handleNewReport);
  },
  methods: {
    handleNewReport() {
      this.loadList();
    },
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    goBack() {
      uni.navigateBack();
    },
    formatTime(value) {
      if (!value) return '--';
      if (typeof value === 'string') return value.replace('T', ' ').slice(0, 19);
      return `${value}`;
    },
    statusText(status) {
      return ['待处理', '处理中', '已处理'][Number(status) || 0] || '待处理';
    },
    statusClass(status) {
      return ['pending', 'doing', 'done'][Number(status) || 0] || 'pending';
    },
    previewRemote(urls, current) {
      uni.previewImage({ urls, current });
    },
    async loadList() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/community-report/list');
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载上报列表失败');
          return;
        }
        this.records = Array.isArray(res.data) ? res.data : [];
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    openHandle(item) {
      this.handleForm = {
        id: item.id,
        status: Number(item.status) || 0,
        handleReply: item.handleReply || '',
      };
      this.showHandle = true;
    },
    async submitHandle() {
      if (!this.handleForm.id) return;
      try {
        const { data: res } = await uni.$http.put('/api/v1/community-report/handle', {
          id: this.handleForm.id,
          status: this.handleForm.status,
          handleReply: this.handleForm.handleReply.trim(),
        });
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '处理失败');
          return;
        }
        uni.showToast({ title: '已提交', icon: 'success' });
        this.showHandle = false;
        this.loadList();
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async removeReport(id) {
      const confirmed = await new Promise((resolve) => {
        uni.showModal({
          title: '提示',
          content: '确定要删除这条上报记录吗？',
          confirmText: '删除',
          confirmColor: '#e45e5e',
          success: (res) => resolve(!!res.confirm),
          fail: () => resolve(false),
        });
      });
      if (!confirmed) return;
      try {
        const { data: res } = await uni.$http.delete(`/api/v1/community-report/${id}`);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '删除失败');
          return;
        }
        uni.showToast({ title: '已删除', icon: 'success' });
        this.loadList();
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

.filter-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.filter-chip {
  padding: 0 22rpx;
  height: 58rpx;
  line-height: 58rpx;
  border-radius: 29rpx;
  background: rgba(255, 255, 255, 0.82);
  color: #46627f;
  font-size: 24rpx;
}

.filter-chip.is-active {
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  color: #fff;
  font-weight: 700;
}

.panel {
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 10rpx 28rpx rgba(40, 92, 150, 0.08);
  padding: 24rpx;
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
  align-items: center;
  gap: 12rpx;
  margin-bottom: 10rpx;
}

.cate-tag {
  height: 44rpx;
  line-height: 44rpx;
  padding: 0 16rpx;
  border-radius: 12rpx;
  background: rgba(0, 122, 255, 0.1);
  color: #1d6fd0;
  font-size: 22rpx;
  font-weight: 700;
}

.status-badge {
  height: 44rpx;
  line-height: 44rpx;
  padding: 0 16rpx;
  border-radius: 12rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.status-pending {
  background: rgba(245, 158, 11, 0.14);
  color: #d97706;
}

.status-doing {
  background: rgba(59, 130, 246, 0.14);
  color: #2563eb;
}

.status-done {
  background: rgba(22, 163, 74, 0.14);
  color: #16a34a;
}

.delete {
  margin-left: auto;
  font-size: 22rpx;
  color: #e45e5e;
}

.detail {
  margin-bottom: 6rpx;
  font-size: 25rpx;
  color: #28415e;
  line-height: 1.55;
  font-weight: 600;
}

.meta {
  font-size: 23rpx;
  color: #54708f;
  line-height: 1.5;
}

.img-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 12rpx;
}

.thumb {
  width: 150rpx;
  height: 150rpx;
  border-radius: 14rpx;
  background: #e8f0fb;
}

.reply {
  margin-top: 10rpx;
  padding: 12rpx 14rpx;
  border-radius: 12rpx;
  background: rgba(22, 163, 74, 0.08);
  color: #1f7a45;
  font-size: 23rpx;
  line-height: 1.5;
}

.handle-btn {
  margin-top: 14rpx;
  height: 64rpx;
  border-radius: 32rpx;
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 10;
}

.sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 11;
  background: #fff;
  border-radius: 28rpx 28rpx 0 0;
  padding: 28rpx 28rpx calc(34rpx + env(safe-area-inset-bottom));
}

.sheet-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #1d2f44;
  text-align: center;
  margin-bottom: 18rpx;
}

.sheet-label {
  font-size: 23rpx;
  color: #4e647e;
  margin: 14rpx 0 10rpx;
}

.status-row {
  display: flex;
  gap: 12rpx;
}

.status-opt {
  flex: 1;
  height: 70rpx;
  line-height: 70rpx;
  text-align: center;
  border-radius: 16rpx;
  background: #f1f7ff;
  border: 1px solid #d9e9fb;
  color: #46627f;
  font-size: 25rpx;
}

.status-opt.is-active {
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  border-color: transparent;
  color: #fff;
  font-weight: 700;
}

.textarea {
  width: 100%;
  min-height: 150rpx;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px solid #d9e9fb;
  padding: 14rpx 18rpx;
  box-sizing: border-box;
  font-size: 26rpx;
  color: #1d2f44;
  line-height: 1.5;
}

.sheet-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 22rpx;
}

.sheet-btn {
  flex: 1;
  height: 82rpx;
  border-radius: 41rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
}

.sheet-btn.ghost {
  background: #eef4fb;
  color: #5a7794;
}

.sheet-btn.primary {
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  color: #fff;
}
</style>
