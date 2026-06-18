<template>
  <view class="feature-page" :style="{ paddingTop: pageTopPadding + 'px' }">
    <view class="bg-shape bg-1"></view>
    <view class="bg-shape bg-2"></view>

    <view class="top-bar">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <view class="top-title">问题上报</view>
      <view class="ghost-btn" @tap="loadList">刷新</view>
    </view>

    <view class="panel form-panel">
      <view class="panel-title">随手拍上报</view>

      <view class="form-item">
        <view class="label">问题分类</view>
        <view class="cate-row">
          <view
            v-for="cate in categories"
            :key="cate"
            class="cate-chip"
            :class="form.category === cate ? 'is-active' : ''"
            @tap="form.category = cate"
          >{{ cate }}</view>
        </view>
      </view>

      <view class="form-item">
        <view class="label">问题位置</view>
        <input v-model="form.location" class="ipt" placeholder="例如：3号楼1单元前" />
      </view>

      <view class="form-item">
        <view class="label">问题描述</view>
        <textarea v-model="form.description" class="textarea" placeholder="请描述发现的问题，方便物业核实处理" maxlength="300" />
      </view>

      <view class="form-item">
        <view class="label">现场照片（选填，最多3张）</view>
        <view class="img-grid">
          <view class="img-cell" v-for="(img, idx) in images" :key="idx">
            <image class="thumb" :src="img" mode="aspectFill" @tap="previewLocal(idx)"></image>
            <view class="img-del" @tap.stop="removeImage(idx)">×</view>
          </view>
          <view class="img-add" v-if="images.length < 3" @tap="chooseImage">
            <u-icon name="camera-fill" color="#9bb4d0" size="44rpx"></u-icon>
            <text>拍照/相册</text>
          </view>
        </view>
      </view>

      <view class="submit-btn" @tap="submit">提交上报</view>
    </view>

    <view class="panel list-panel">
      <view class="panel-title">我的上报记录</view>
      <view v-if="!records.length" class="empty">暂无上报记录。</view>
      <view v-for="item in records" :key="item.id" class="record-card">
        <view class="record-head">
          <view class="cate-tag">{{ item.category || '其他' }}</view>
          <view class="status-badge" :class="'status-' + statusClass(item.status)">{{ statusText(item.status) }}</view>
          <view class="delete" @tap="removeReport(item.id)">删除</view>
        </view>
        <view class="detail">{{ item.description || '暂无描述' }}</view>
        <view class="meta">位置：{{ item.location || '--' }}</view>
        <view class="meta">时间：{{ formatTime(item.reportTime) }}</view>
        <view class="img-grid view-grid" v-if="item.imageUrls && item.imageUrls.length">
          <image
            class="thumb"
            v-for="(url, i) in item.imageUrls"
            :key="i"
            :src="url"
            mode="aspectFill"
            @tap="previewRemote(item.imageUrls, url)"
          ></image>
        </view>
        <view class="reply" v-if="item.handleReply">物业回复：{{ item.handleReply }}</view>
      </view>
    </view>
  </view>
</template>

<script>
import { API_BASE_URL } from '@/common/config.js';

const SUCCESS_CODE = '00000';

export default {
  data() {
    return {
      categories: ['环境卫生', '公共设施', '安全隐患', '违规停车', '其他'],
      records: [],
      images: [],
      form: {
        category: '',
        location: '',
        description: '',
      },
      statusBarHeight: 0,
    };
  },
  computed: {
    pageTopPadding() {
      return this.statusBarHeight + 14;
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
  },
  onShow() {
    this.loadList();
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
    statusText(status) {
      return ['待处理', '处理中', '已处理'][Number(status) || 0] || '待处理';
    },
    statusClass(status) {
      return ['pending', 'doing', 'done'][Number(status) || 0] || 'pending';
    },
    chooseImage() {
      const remain = 3 - this.images.length;
      if (remain <= 0) {
        uni.showToast({ title: '最多上传3张', icon: 'none' });
        return;
      }
      uni.chooseImage({
        count: remain,
        sizeType: ['compressed'],
        sourceType: ['camera', 'album'],
        success: (res) => {
          this.images = this.images.concat(res.tempFilePaths).slice(0, 3);
        },
      });
    },
    removeImage(idx) {
      this.images.splice(idx, 1);
    },
    previewLocal(idx) {
      uni.previewImage({ urls: this.images, current: this.images[idx] });
    },
    previewRemote(urls, current) {
      uni.previewImage({ urls, current });
    },
    uploadOne(filePath) {
      const token = uni.getStorageSync('token') || '';
      return new Promise((resolve) => {
        uni.uploadFile({
          url: API_BASE_URL + '/api/v1/community-report/upload',
          filePath,
          name: 'file',
          header: token ? { Authorization: token } : {},
          success: (res) => {
            try {
              const data = typeof res.data === 'string' ? JSON.parse(res.data || '{}') : res.data || {};
              if (String(data.code) === SUCCESS_CODE && data.data && data.data.key) {
                resolve(data.data.key);
              } else {
                resolve('');
              }
            } catch (e) {
              resolve('');
            }
          },
          fail: () => resolve(''),
        });
      });
    },
    async uploadImages() {
      const keys = [];
      for (let i = 0; i < this.images.length; i += 1) {
        // 逐张上传，保证顺序与失败可感知
        // eslint-disable-next-line no-await-in-loop
        const key = await this.uploadOne(this.images[i]);
        if (key) keys.push(key);
      }
      return keys;
    },
    async submit() {
      if (!this.form.category) {
        uni.$showMsg('请选择问题分类');
        return;
      }
      if (!this.form.description.trim()) {
        uni.$showMsg('请填写问题描述');
        return;
      }
      uni.showLoading({ title: '提交中', mask: true });
      try {
        let imageKeys = '';
        if (this.images.length) {
          const keys = await this.uploadImages();
          if (keys.length < this.images.length) {
            uni.hideLoading();
            uni.$showMsg('部分图片上传失败，请重试');
            return;
          }
          imageKeys = keys.join(',');
        }
        const payload = {
          category: this.form.category,
          location: this.form.location.trim(),
          description: this.form.description.trim(),
          imageKeys,
        };
        const { data: res } = await uni.$http.post('/api/v1/community-report/create', payload, { silent: true });
        uni.hideLoading();
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '提交失败');
          return;
        }
        uni.showToast({ title: '提交成功', icon: 'success' });
        this.form.category = '';
        this.form.location = '';
        this.form.description = '';
        this.images = [];
        this.loadList();
      } catch (e) {
        uni.hideLoading();
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    async loadList() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/community-report/list');
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '加载上报记录失败');
          return;
        }
        this.records = Array.isArray(res.data) ? res.data : [];
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
  padding: 26rpx 24rpx calc(32rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  background: linear-gradient(180deg, #f2f9ff 0%, #fbfdfd 54%, #ffffff 100%);
  position: relative;
  overflow: visible;
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
  margin-bottom: 16rpx;
}

.label {
  font-size: 23rpx;
  color: #4e647e;
  margin-bottom: 10rpx;
}

.cate-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.cate-chip {
  padding: 0 22rpx;
  height: 60rpx;
  line-height: 60rpx;
  border-radius: 30rpx;
  background: #f1f7ff;
  border: 1px solid #d9e9fb;
  color: #46627f;
  font-size: 24rpx;
}

.cate-chip.is-active {
  background: linear-gradient(90deg, #007aff 0%, #05b5ff 100%);
  border-color: transparent;
  color: #fff;
  font-weight: 700;
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

.img-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.img-cell {
  position: relative;
  width: 160rpx;
  height: 160rpx;
}

.thumb {
  width: 160rpx;
  height: 160rpx;
  border-radius: 16rpx;
  background: #e8f0fb;
}

.img-del {
  position: absolute;
  top: -12rpx;
  right: -12rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background: rgba(20, 30, 45, 0.78);
  color: #fff;
  font-size: 30rpx;
  line-height: 38rpx;
  text-align: center;
}

.img-add {
  width: 160rpx;
  height: 160rpx;
  border-radius: 16rpx;
  background: #f4f9ff;
  border: 1px dashed #b9d2ee;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  color: #9bb4d0;
  font-size: 22rpx;
}

.view-grid {
  margin-top: 12rpx;
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

.meta {
  font-size: 23rpx;
  color: #54708f;
  line-height: 1.5;
}

.detail {
  margin-bottom: 6rpx;
  font-size: 25rpx;
  color: #28415e;
  line-height: 1.55;
  font-weight: 600;
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
</style>
