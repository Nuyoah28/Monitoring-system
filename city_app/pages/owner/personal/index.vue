<template>
  <view class="owner-page" :style="{ paddingTop: pageTopPadding + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-bar">
      <view>
        <view class="top-title">个人中心</view>
        <view class="top-subtitle">账号资料与常用服务</view>
      </view>
      <view class="top-badge">业主端</view>
    </view>

    <view class="profile-card panel">
      <view class="profile-head">
        <view class="profile-avatar-wrap">
          <image v-if="avatarUrl" class="profile-avatar-img" :src="avatarUrl" mode="aspectFill"></image>
          <view v-else class="profile-avatar">{{ avatarLetter }}</view>
        </view>
        <view class="profile-main">
          <view class="profile-name">{{ username || '业主用户' }}</view>
          <view class="profile-desc">{{ homeArea ? `常驻区域：${homeArea}` : '请完善常驻区域，便于接收附近安全提醒' }}</view>
        </view>
        <view class="edit-chip" @tap="openEdit">编辑</view>
      </view>

      <view class="profile-meta">
        <view class="meta-item">
          <text class="meta-label">UID</text>
          <text class="meta-value">{{ userId || '--' }}</text>
        </view>
        <view class="meta-item">
          <text class="meta-label">推送提醒</text>
          <text class="meta-value">{{ notifyEnabled ? '已开启' : '已关闭' }}</text>
        </view>
      </view>
    </view>

    <view class="panel section-card">
      <view class="section-head">
        <view>
          <view class="section-title">快捷入口</view>
          <view class="section-sub">常用社区服务一键进入</view>
        </view>
      </view>
      <view class="shortcut-grid">
        <view class="shortcut-item shortcut-item--red" @tap="goFeature('/pages/owner/features/notice/index')">
          <view class="shortcut-icon">提</view>
          <text>社区提醒</text>
        </view>
        <view class="shortcut-item shortcut-item--green" @tap="goFeature('/pages/owner/features/parking/index')">
          <view class="shortcut-icon">停</view>
          <text>停车服务</text>
        </view>
        <view class="shortcut-item shortcut-item--blue" @tap="goFeature('/pages/owner/features/environment/index')">
          <view class="shortcut-icon">环</view>
          <text>社区环境</text>
        </view>
        <view class="shortcut-item shortcut-item--orange" @tap="goFeature('/pages/owner/features/repair/index')">
          <view class="shortcut-icon">修</view>
          <text>在线报修</text>
        </view>
        <view class="shortcut-item shortcut-item--cyan" @tap="goFeature('/pages/owner/features/visitor/index')">
          <view class="shortcut-icon">访</view>
          <text>访客登记</text>
        </view>
        <view class="shortcut-item shortcut-item--purple" @tap="goFeature('/pages/owner/ai/index')">
          <view class="shortcut-icon">助</view>
          <text>社区助手</text>
        </view>
      </view>
    </view>

    <view class="panel section-card">
      <view class="section-head">
        <view>
          <view class="section-title">安全提醒</view>
          <view class="section-sub">只推送与你所在区域相关的高风险事件</view>
        </view>
      </view>
      <view class="tip-list">
        <view class="tip-item">附近区域发生烟雾或明火时，会同步进入社区提醒。</view>
        <view class="tip-item">请保持常驻区域准确，其他普通告警不会频繁打扰业主端。</view>
      </view>
    </view>

    <view class="action" @tap="logout">退出登录</view>

    <view v-if="showEdit" class="edit-mask" @tap="closeEdit">
      <view class="edit-panel" @tap.stop>
        <view class="edit-head">
          <view>
            <view class="edit-title">编辑资料</view>
            <view class="edit-sub">UID 不可修改，区域默认保持当前值</view>
          </view>
          <view class="edit-close" @tap="closeEdit">×</view>
        </view>

        <view class="edit-avatar-block">
          <view class="edit-avatar">{{ editAvatarLetter }}</view>
          <view class="edit-avatar-text">
            <view class="edit-avatar-title">默认头像</view>
            <view class="edit-avatar-sub">当前先使用默认头像，后续可接入图片上传</view>
          </view>
        </view>

        <view class="form-item readonly">
          <view class="form-label">UID</view>
          <input class="form-input" :value="userId || '--'" disabled />
        </view>
        <view class="form-item">
          <view class="form-label">昵称</view>
          <input class="form-input" v-model="editForm.userName" placeholder="请输入昵称" />
        </view>
        <view class="form-item">
          <view class="form-label">所属区域</view>
          <input class="form-input" v-model="editForm.homeArea" placeholder="例如：小区东门街道" />
        </view>
        <view class="form-item form-row-item">
          <view>
            <view class="form-label">接收附近安全提醒</view>
            <view class="form-hint">仅烟雾、明火会推送到业主端</view>
          </view>
          <switch :checked="editForm.notifyEnabled" color="#1470d8" @change="onNotifyChange" />
        </view>

        <view class="edit-actions">
          <view class="cancel-btn" @tap="closeEdit">取消</view>
          <view class="save-btn" @tap="saveProfile">保存</view>
        </view>
      </view>
    </view>

    <owner-tabbar current="personal" />
  </view>
</template>

<script>
import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';

const SUCCESS_CODE = '00000';

export default {
  components: {
    OwnerTabbar,
  },
  data() {
    return {
      pageTopPadding: 30,
      username: '',
      userId: '',
      homeArea: '',
      avatarUrl: '',
      notifyEnabled: true,
      showEdit: false,
      editForm: {
        userName: '',
        homeArea: '',
        notifyEnabled: true,
      },
    };
  },
  onShow() {
    this.updatePagePadding();
    this.loadLocalProfile();
    this.fetchProfile();
  },
  computed: {
    avatarLetter() {
      const text = String(this.username || '业主用户').trim();
      return text ? text.slice(0, 1) : '业';
    },
    editAvatarLetter() {
      const text = String(this.editForm.userName || this.username || '业主用户').trim();
      return text ? text.slice(0, 1) : '业';
    },
  },
  methods: {
    isSuccess(res) {
      return String(res && res.code) === SUCCESS_CODE;
    },
    updatePagePadding() {
      const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
      this.pageTopPadding = (info && info.statusBarHeight) ? info.statusBarHeight + 18 : 30;
    },
    loadLocalProfile() {
      this.username = uni.getStorageSync('username') || '业主用户';
      this.userId = uni.getStorageSync('userId') || '';
      this.homeArea = uni.getStorageSync('homeArea') || '';
      this.avatarUrl = uni.getStorageSync('avatarUrl') || '';
      this.notifyEnabled = uni.getStorageSync('notifyEnabled') !== false;
    },
    cacheProfile(profile = {}) {
      const name = profile.name || profile.userName || this.username || '业主用户';
      this.username = name;
      this.userId = profile.id || this.userId || '';
      this.homeArea = profile.homeArea || '';
      this.avatarUrl = profile.avatarUrl || '';
      this.notifyEnabled = profile.notifyEnabled !== false;

      uni.setStorageSync('username', this.username);
      uni.setStorageSync('userId', this.userId);
      uni.setStorageSync('homeArea', this.homeArea);
      uni.setStorageSync('avatarUrl', this.avatarUrl);
      uni.setStorageSync('notifyEnabled', this.notifyEnabled);
    },
    async fetchProfile() {
      try {
        const { data: res } = await uni.$http.get('/api/v1/user/profile', {}, { silent: true });
        if (!this.isSuccess(res) || !res.data) return;
        this.cacheProfile(res.data);
      } catch (e) {
        // 保留本地缓存展示，不因为网络波动打断个人中心。
      }
    },
    openEdit() {
      this.editForm = {
        userName: this.username === '业主用户' ? '' : this.username,
        homeArea: this.homeArea || '',
        notifyEnabled: this.notifyEnabled,
      };
      this.showEdit = true;
    },
    closeEdit() {
      this.showEdit = false;
    },
    onNotifyChange(e) {
      this.editForm.notifyEnabled = Boolean(e.detail.value);
    },
    async saveProfile() {
      const userName = (this.editForm.userName || '').trim();
      const homeArea = (this.editForm.homeArea || '').trim();
      if (!userName) {
        uni.$showMsg('请填写昵称');
        return;
      }
      if (!homeArea) {
        uni.$showMsg('请填写所属区域');
        return;
      }
      const payload = {
        userName,
        homeArea,
        notifyEnabled: this.editForm.notifyEnabled,
      };
      try {
        const { data: res } = await uni.$http.post('/api/v1/user/profile', payload);
        if (!this.isSuccess(res)) {
          uni.$showMsg(res.message || '保存失败');
          return;
        }
        this.cacheProfile(res.data || payload);
        this.showEdit = false;
        uni.showToast({ title: '已保存', icon: 'success' });
      } catch (e) {
        uni.$showMsg('网络异常，请稍后重试');
      }
    },
    goFeature(url) {
      uni.navigateTo({ url });
    },
    logout() {
      uni.removeStorageSync('token');
      uni.removeStorageSync('userId');
      uni.removeStorageSync('appType');
      uni.removeStorageSync('homeArea');
      uni.removeStorageSync('avatarUrl');
      uni.removeStorageSync('notifyEnabled');
      uni.reLaunch({ url: '/pages/shared/select/index' });
    },
  },
};
</script>

<style lang="scss" scoped>
.owner-page {
  min-height: 100vh;
  padding: 34rpx 28rpx 150rpx;
  box-sizing: border-box;
  position: relative;
  overflow: visible;
  background:
    radial-gradient(circle at 10% 0%, rgba(56, 164, 255, 0.18) 0, rgba(56, 164, 255, 0) 240rpx),
    radial-gradient(circle at 90% 18%, rgba(20, 112, 216, 0.12) 0, rgba(20, 112, 216, 0) 280rpx),
    linear-gradient(180deg, #eaf6ff 0%, #f8fbff 52%, #ffffff 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.bg-orb--one {
  width: 220rpx;
  height: 220rpx;
  right: -80rpx;
  top: 140rpx;
  background: rgba(56, 164, 255, 0.1);
}

.bg-orb--two {
  width: 180rpx;
  height: 180rpx;
  left: -70rpx;
  top: 700rpx;
  background: rgba(22, 163, 74, 0.08);
}

.top-bar,
.panel {
  position: relative;
  z-index: 1;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.top-title {
  color: #102033;
  font-size: 34rpx;
  font-weight: 900;
}

.top-subtitle {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
}

.top-badge {
  height: 54rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(37, 99, 235, 0.12);
  color: #1470d8;
  font-size: 23rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
}

.panel {
  margin-top: 18rpx;
  padding: 24rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(37, 99, 235, 0.1);
  box-shadow: 0 10rpx 30rpx rgba(30, 88, 150, 0.1);
}

.profile-card {
  background: linear-gradient(135deg, rgba(20, 112, 216, 0.96) 0%, rgba(43, 142, 240, 0.96) 54%, rgba(54, 182, 255, 0.96) 100%);
  color: #fff;
  box-shadow: 0 18rpx 40rpx rgba(20, 112, 216, 0.22);
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.profile-avatar-wrap,
.profile-avatar,
.profile-avatar-img {
  width: 104rpx;
  height: 104rpx;
  border-radius: 32rpx;
  flex-shrink: 0;
}

.profile-avatar-wrap {
  overflow: hidden;
  background: rgba(255, 255, 255, 0.18);
  border: 1rpx solid rgba(255, 255, 255, 0.24);
}

.profile-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  font-weight: 900;
}

.profile-avatar-img {
  display: block;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-desc {
  margin-top: 12rpx;
  color: rgba(255, 255, 255, 0.88);
  font-size: 23rpx;
  line-height: 1.45;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-chip {
  height: 58rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  border: 1rpx solid rgba(255, 255, 255, 0.26);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 23rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.profile-meta {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14rpx;
}

.meta-item {
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.14);
  border: 1rpx solid rgba(255, 255, 255, 0.18);
  min-width: 0;
}

.meta-label {
  color: rgba(255, 255, 255, 0.78);
  font-size: 21rpx;
  font-weight: 700;
}

.meta-value {
  margin-top: 8rpx;
  color: #fff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-title {
  color: #102033;
  font-size: 31rpx;
  font-weight: 900;
}

.section-sub {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
}

.shortcut-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
}

.shortcut-item {
  min-height: 132rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid #dcebfa;
  box-shadow: 0 8rpx 22rpx rgba(37, 99, 235, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.shortcut-item:active {
  transform: scale(0.98);
}

.shortcut-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  color: #fff;
}

.shortcut-item text {
  margin-top: 12rpx;
  color: #1e3a5f;
  font-size: 22rpx;
  font-weight: 900;
}

.shortcut-item--red .shortcut-icon { background: linear-gradient(135deg, #ff7a7a 0%, #f05252 100%); }
.shortcut-item--green .shortcut-icon { background: linear-gradient(135deg, #34d399 0%, #16a34a 100%); }
.shortcut-item--blue .shortcut-icon { background: linear-gradient(135deg, #5bb4ff 0%, #2f73ff 100%); }
.shortcut-item--orange .shortcut-icon { background: linear-gradient(135deg, #fdba74 0%, #f97316 100%); }
.shortcut-item--cyan .shortcut-icon { background: linear-gradient(135deg, #67e8f9 0%, #06b6d4 100%); }
.shortcut-item--purple .shortcut-icon { background: linear-gradient(135deg, #c4b5fd 0%, #8b5cf6 100%); }

.tip-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.tip-item {
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #45607f;
  font-size: 24rpx;
  line-height: 1.6;
}

.action {
  margin-top: 22rpx;
  height: 90rpx;
  border-radius: 20rpx;
  background: #fff;
  color: #ef5350;
  font-size: 30rpx;
  font-weight: 800;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  z-index: 1;
}

.edit-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 99;
  background: rgba(12, 27, 46, 0.42);
  display: flex;
  align-items: flex-end;
  padding: 28rpx;
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.edit-panel {
  width: 100%;
  max-height: calc(100vh - 240rpx);
  overflow-y: auto;
  border-radius: 34rpx;
  background: #ffffff;
  padding: 30rpx;
  box-sizing: border-box;
  box-shadow: 0 -18rpx 46rpx rgba(15, 35, 66, 0.18);
}

.edit-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.edit-title {
  color: #102033;
  font-size: 32rpx;
  font-weight: 900;
}

.edit-sub {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
}

.edit-close {
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  background: #f1f5f9;
  color: #64748b;
  font-size: 38rpx;
  line-height: 50rpx;
  text-align: center;
  flex-shrink: 0;
}

.edit-avatar-block {
  margin-top: 24rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #eef7ff 0%, #f8fbff 100%);
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.edit-avatar {
  width: 82rpx;
  height: 82rpx;
  border-radius: 26rpx;
  background: linear-gradient(135deg, #1470d8 0%, #35b8ff 100%);
  color: #fff;
  font-size: 32rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.edit-avatar-text {
  min-width: 0;
}

.edit-avatar-title {
  color: #18304b;
  font-size: 26rpx;
  font-weight: 900;
}

.edit-avatar-sub {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.45;
}

.form-item {
  margin-top: 20rpx;
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
}

.form-item.readonly {
  opacity: 0.78;
}

.form-row-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.form-label {
  color: #31445c;
  font-size: 23rpx;
  font-weight: 900;
}

.form-hint {
  margin-top: 6rpx;
  color: #7a8aa0;
  font-size: 21rpx;
}

.form-input {
  margin-top: 12rpx;
  height: 50rpx;
  color: #102033;
  font-size: 27rpx;
  font-weight: 800;
}

.edit-actions {
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.cancel-btn,
.save-btn {
  height: 84rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
}

.cancel-btn {
  background: #f1f5f9;
  color: #64748b;
}

.save-btn {
  background: linear-gradient(135deg, #1470d8 0%, #35b8ff 100%);
  color: #fff;
  box-shadow: 0 12rpx 24rpx rgba(20, 112, 216, 0.22);
}
</style>
