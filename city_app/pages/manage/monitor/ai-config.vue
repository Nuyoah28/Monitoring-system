<template>
  <view class="rules-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="top-nav">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="top-title">识别规则管理</text>
      <view class="top-placeholder"></view>
    </view>

    <view class="header-card">
      <view class="header-main">
        <view class="eyebrow">当前摄像头</view>
        <view class="title">{{ cameraName || '请选择摄像头' }}</view>
        <view class="subtitle">{{ cameraArea || '未标注区域' }}</view>
      </view>
      <view class="status-pill" :class="isOnline ? 'is-online' : 'is-offline'">
        {{ isOnline ? '在线' : '离线' }}
      </view>
    </view>

    <view class="rule-summary">
      <view class="summary-item">
        <text class="summary-num">{{ enabledRuleCount }}</text>
        <text class="summary-label">已启用规则</text>
      </view>
      <view class="summary-item">
        <text class="summary-num warning">{{ disabledRuleCount }}</text>
        <text class="summary-label">未启用规则</text>
      </view>
      <view class="summary-item">
        <text class="summary-num success">{{ customRules.length }}</text>
        <text class="summary-label">新增关注</text>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">基础识别规则</text>
          <view class="section-subtitle">点击右侧开关，直接调整这个摄像头关注的内容</view>
        </view>
      </view>
      <view class="ability-list">
        <view class="ability-item" v-for="(item, index) in abilityList" :key="item.value">
          <view class="ability-copy">
            <view class="ability-name">{{ item.name }}</view>
            <view class="ability-desc">{{ item.desc }}</view>
          </view>
          <view class="ability-switch" :class="item.checked ? 'is-on' : 'is-off'" @tap="toggleRule(index)">
            {{ item.checked ? '启用' : '关闭' }}
          </view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">推荐场景</text>
          <view class="section-subtitle">一键套用常见社区巡查组合</view>
        </view>
      </view>
      <view class="template-grid">
        <view
          class="template-card"
          :class="activeTemplate === item.title ? 'is-active' : ''"
          v-for="item in templates"
          :key="item.title"
          @tap="applyTemplate(item)"
        >
          <view class="template-title">{{ item.title }}</view>
          <view class="template-desc">{{ item.desc }}</view>
          <view class="template-tags">
            <text v-for="tag in item.tags" :key="tag">{{ tag }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="section-card">
      <view class="section-head">
        <view>
          <text class="section-title">新增关注内容</text>
          <view class="section-subtitle">为当前摄像头补充更具体的现场关注点</view>
        </view>
      </view>
      <view class="form-group">
        <view class="field-label">事件名称</view>
        <input class="field-input" v-model="customName" placeholder="例如：人员长时间停留" />
      </view>
      <view class="form-group">
        <view class="field-label">关注内容</view>
        <textarea class="field-textarea" v-model="customPrompt" placeholder="例如：关注楼道内长时间徘徊的人员" />
      </view>
      <view class="form-group">
        <view class="field-label">风险等级</view>
        <view class="risk-row">
          <view class="risk-chip" :class="riskLevel === 1 ? 'is-active' : ''" @tap="riskLevel = 1">低</view>
          <view class="risk-chip" :class="riskLevel === 2 ? 'is-active' : ''" @tap="riskLevel = 2">中</view>
          <view class="risk-chip" :class="riskLevel === 3 ? 'is-active' : ''" @tap="riskLevel = 3">高</view>
        </view>
      </view>
      <view class="form-group">
        <view class="field-label">告警提示</view>
        <input class="field-input" v-model="alertHint" placeholder="例如：请及时查看现场情况" />
      </view>
      <view class="add-rule-btn" @tap="addCustomRule">添加到当前规则</view>

      <view class="custom-rule-list" v-if="customRules.length">
        <view class="custom-rule-item" v-for="(item, index) in customRules" :key="item.id || index">
          <view class="custom-rule-main">
            <view class="custom-rule-title">{{ item.name }}</view>
            <view class="custom-rule-desc">{{ item.prompt }}</view>
            <view class="custom-rule-meta">{{ riskText(item.riskLevel) }}风险 · {{ item.alertHint }}</view>
          </view>
          <view class="custom-rule-actions">
            <view class="rule-toggle" :class="item.enabled === false ? 'is-off' : 'is-on'" @tap="toggleCustomRule(index)">
              {{ item.enabled === false ? '关闭' : '启用' }}
            </view>
            <view class="delete-rule" @tap="removeCustomRule(index)">删除</view>
          </view>
        </view>
      </view>
    </view>

    <view class="footer-actions">
      <view class="secondary-btn" @tap="goSelectMonitor">选择摄像头</view>
      <view class="primary-btn" :class="saving ? 'is-disabled' : ''" @tap="saveConfig">
        {{ saving ? '保存中...' : '保存规则' }}
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarHeight: 0,
      cameraId: '',
      cameraName: '',
      cameraArea: '',
      isOnline: false,
      currentMonitor: {},
      customName: '',
      customPrompt: '',
      riskLevel: 2,
      alertHint: '请及时查看现场情况',
      customRules: [],
      activeTemplate: '',
      saving: false,
      abilityList: [
        { name: '危险区域', value: 1, checked: false, desc: '识别禁入或危险区域' },
        { name: '挥手', value: 2, checked: false, desc: '识别求助或招手动作' },
        { name: '摔倒', value: 3, checked: false, desc: '识别人员跌倒状态' },
        { name: '明火', value: 4, checked: false, desc: '识别火焰与明火风险' },
        { name: '吸烟', value: 5, checked: false, desc: '识别吸烟行为' },
        { name: '打拳', value: 6, checked: false, desc: '识别肢体冲突动作' },
        { name: '垃圾检测', value: 8, checked: false, desc: '识别垃圾堆放或乱放' },
        { name: '积冰检测', value: 9, checked: false, desc: '识别地面结冰风险' },
        { name: '电瓶车', value: 10, checked: false, desc: '识别电动车进入楼道' },
        { name: '载具占道', value: 11, checked: false, desc: '识别车辆占用通道' },
      ],
      templates: [
        { title: '消防安全', desc: '适合厨房、地下车库、楼道等重点区域', values: [4, 5, 10], tags: ['明火', '吸烟', '电瓶车'] },
        { title: '老人关怀', desc: '适合楼道、电梯口、老人活动区域', values: [2, 3], tags: ['挥手', '摔倒'] },
        { title: '楼道巡查', desc: '适合单元门、消防通道、楼梯间', values: [1, 8, 10, 11], tags: ['危险区域', '垃圾', '占道'] },
        { title: '冬季安全', desc: '适合室外道路、坡道和单元出入口', values: [9, 11], tags: ['积冰', '载具占道'] },
      ],
    };
  },
  computed: {
    enabledRuleCount() {
      return this.abilityList.filter((item) => item && item.checked).length;
    },
    disabledRuleCount() {
      return Math.max(0, this.abilityList.length - this.enabledRuleCount);
    },
  },
  onLoad(options) {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    this.cameraId = options.id || '';
    this.cameraName = options.name ? decodeURIComponent(options.name) : '';
    this.cameraArea = options.area ? decodeURIComponent(options.area) : '';
    if (!this.cameraId) {
      uni.showToast({ title: '请先选择摄像头', icon: 'none' });
      return;
    }
    this.getMonitorDetail();
    this.getCustomRules();
  },
  methods: {
    async getMonitorDetail() {
      try {
        const { data } = await uni.$http.get('/api/v1/monitor');
        const list = (data && data.data) || [];
        const current = list.find((item) => String(item.id) === String(this.cameraId));
        if (!current) return;
        this.currentMonitor = current;
        this.cameraName = current.name || this.cameraName;
        this.cameraArea = current.department || current.area || this.cameraArea;
        this.isOnline = !!current.running;
        const ability = Array.isArray(current.ability) ? current.ability : [];
        this.abilityList = this.abilityList.map((item) => {
          const match = ability.find((abilityItem) => Number(abilityItem.value) === Number(item.value));
          return match ? { ...item, checked: !!match.checked } : item;
        });
      } catch (error) {
        console.warn('[rules] 获取摄像头信息失败：', error);
      }
    },
    async getCustomRules() {
      try {
        const { data } = await uni.$http.get(`/api/v1/monitor/rules/${this.cameraId}`);
        this.customRules = ((data && data.data) || []).map((item) => ({
          id: item.id,
          name: item.name || '',
          prompt: item.prompt || '',
          translatedPrompt: item.translatedPrompt || '',
          riskLevel: item.riskLevel || 2,
          alertHint: item.alertHint || '请及时查看现场情况',
          enabled: item.enabled !== false,
        }));
      } catch (error) {
        console.warn('[rules] 获取自定义关注内容失败：', error);
      }
    },
    toggleRule(index) {
      const item = this.abilityList[index];
      if (!item) return;
      this.$set(this.abilityList, index, { ...item, checked: !item.checked });
    },
    applyTemplate(template) {
      const values = template.values || [];
      this.activeTemplate = template.title;
      this.abilityList = this.abilityList.map((item) => ({
        ...item,
        checked: values.includes(Number(item.value)),
      }));
      uni.showToast({ title: '已套用推荐场景', icon: 'none' });
    },
    addCustomRule() {
      const name = this.customName.trim();
      const prompt = this.customPrompt.trim();
      if (!name || !prompt) {
        uni.showToast({ title: '请填写事件名称和关注内容', icon: 'none' });
        return;
      }
      this.customRules.push({
        name,
        prompt,
        riskLevel: this.riskLevel,
        alertHint: this.alertHint || '请及时查看现场情况',
        enabled: true,
      });
      this.customName = '';
      this.customPrompt = '';
      this.riskLevel = 2;
      this.alertHint = '请及时查看现场情况';
    },
    toggleCustomRule(index) {
      const item = this.customRules[index];
      if (!item) return;
      this.$set(this.customRules, index, { ...item, enabled: item.enabled === false });
    },
    removeCustomRule(index) {
      this.customRules.splice(index, 1);
    },
    riskText(level) {
      const num = Number(level);
      if (num >= 3) return '高';
      if (num === 2) return '中';
      return '低';
    },
    abilityChecked(value) {
      const target = this.abilityList.find((x) => Number(x.value) === Number(value));
      return !!(target && target.checked);
    },
    buildMonitorUpdatePayload() {
      const current = this.currentMonitor || {};
      return {
        id: this.cameraId || current.id,
        name: current.name || this.cameraName,
        area: current.department || current.area || this.cameraArea,
        leader: current.leader || '',
        ip: current.video || current.ip || '',
        longitude: current.longitude,
        latitude: current.latitude,
        fall: this.abilityChecked(3),
        flame: this.abilityChecked(4),
        smoke: this.abilityChecked(5),
        wave: this.abilityChecked(2),
        punch: this.abilityChecked(6),
        rubbish: this.abilityChecked(8),
        ice: this.abilityChecked(9),
        ebike: this.abilityChecked(10),
        vehicle: this.abilityChecked(11),
        dangerArea: this.abilityChecked(1),
      };
    },
    buildCustomRulesPayload() {
      return this.customRules
        .filter((item) => item && String(item.name || '').trim() && String(item.prompt || '').trim())
        .map((item) => ({
          id: item.id,
          name: String(item.name || '').trim(),
          prompt: String(item.prompt || '').trim(),
          translatedPrompt: item.translatedPrompt || '',
          riskLevel: item.riskLevel || 2,
          alertHint: item.alertHint || '请及时查看现场情况',
          enabled: item.enabled !== false,
        }));
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.reLaunch({ url: '/pages/manage/monitor/index' });
      }
    },
    goSelectMonitor() {
      uni.reLaunch({ url: '/pages/manage/monitor/index' });
    },
    async saveConfig() {
      if (!this.cameraId) {
        uni.showToast({ title: '请先选择摄像头', icon: 'none' });
        return;
      }
      if (this.saving) return;
      this.saving = true;
      try {
        await uni.$http.post('/api/v1/monitor/update', this.buildMonitorUpdatePayload());
        const { data } = await uni.$http.post(`/api/v1/monitor/rules/${this.cameraId}`, {
          rules: this.buildCustomRulesPayload(),
        });
        this.customRules = ((data && data.data) || this.customRules).map((item) => ({
          id: item.id,
          name: item.name || '',
          prompt: item.prompt || '',
          translatedPrompt: item.translatedPrompt || '',
          riskLevel: item.riskLevel || 2,
          alertHint: item.alertHint || '请及时查看现场情况',
          enabled: item.enabled !== false,
        }));
        await this.getMonitorDetail();
        await this.getCustomRules();
        uni.showToast({ title: '规则已保存', icon: 'success' });
      } catch (error) {
        console.warn('[rules] 保存规则失败：', error);
        uni.showToast({ title: '保存失败，请稍后重试', icon: 'none' });
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.rules-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 24rpx 150rpx;
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 6%, rgba(56, 164, 255, 0.16) 0, rgba(56, 164, 255, 0) 260rpx),
    radial-gradient(circle at 88% 14%, rgba(20, 112, 216, 0.14) 0, rgba(20, 112, 216, 0) 280rpx),
    linear-gradient(180deg, #e6f2ff 0%, #f3f9ff 40%, #fbfdff 100%);
}

.top-nav {
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  margin-top: 12rpx;
  padding: 26rpx;
  border-radius: 32rpx;
  background: linear-gradient(135deg, #1470d8 0%, #2b8ef0 52%, #38a4ff 100%);
  box-shadow: 0 18rpx 40rpx rgba(20, 112, 216, 0.24);
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  align-items: flex-start;
}

.header-main {
  min-width: 0;
}

.eyebrow {
  font-size: 22rpx;
  font-weight: 800;
  opacity: 0.82;
}

.title {
  margin-top: 8rpx;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1.2;
}

.subtitle {
  margin-top: 10rpx;
  font-size: 24rpx;
  opacity: 0.82;
}

.status-pill {
  height: 56rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-pill.is-online {
  background: rgba(255, 255, 255, 0.96);
  color: #16a34a;
}

.status-pill.is-offline {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  border: 1rpx solid rgba(255, 255, 255, 0.28);
}

.rule-summary {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
}

.summary-item {
  min-height: 112rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 8rpx 24rpx rgba(30, 88, 150, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.summary-num {
  color: #1470d8;
  font-size: 34rpx;
  font-weight: 900;

  &.warning { color: #d97706; }
  &.success { color: #16a34a; }
}

.summary-label {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 20rpx;
  font-weight: 700;
}

.section-card {
  margin-top: 18rpx;
  padding: 22rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.10);
}

.section-head {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  margin-bottom: 16rpx;
}

.section-title {
  color: #102033;
  font-size: 31rpx;
  font-weight: 900;
}

.section-subtitle {
  color: #64748b;
  font-size: 22rpx;
}

.ability-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.ability-item {
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.ability-copy {
  flex: 1;
  min-width: 0;
}

.ability-name {
  color: #102033;
  font-size: 26rpx;
  font-weight: 900;
}

.ability-desc {
  margin-top: 6rpx;
  color: #64748b;
  font-size: 21rpx;
}

.ability-switch {
  min-width: 88rpx;
  height: 48rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ability-switch.is-on {
  background: rgba(22, 163, 74, 0.12);
  color: #16a34a;
}

.ability-switch.is-off {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12rpx;
}

.template-card {
  padding: 16rpx;
  border-radius: 20rpx;
  background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 100%);
  border: 1rpx solid #dcebfa;
}

.template-card.is-active {
  border-color: #1470d8;
  box-shadow: 0 8rpx 22rpx rgba(20, 112, 216, 0.14);
}

.template-title {
  color: #102033;
  font-size: 25rpx;
  font-weight: 900;
}

.template-desc {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 21rpx;
  line-height: 1.5;
}

.template-tags {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;

  text {
    padding: 5rpx 9rpx;
    border-radius: 999rpx;
    background: rgba(20, 112, 216, 0.10);
    color: #1470d8;
    font-size: 18rpx;
    font-weight: 800;
  }
}

.form-group {
  margin-top: 14rpx;
}

.field-label {
  margin-bottom: 10rpx;
  color: #475569;
  font-size: 23rpx;
  font-weight: 800;
}

.field-input,
.field-textarea,
.scope-card {
  width: 100%;
  box-sizing: border-box;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #102033;
  font-size: 24rpx;
}

.field-input {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 20rpx;
}

.field-textarea {
  min-height: 160rpx;
  padding: 18rpx 20rpx;
}

.risk-row {
  display: flex;
  gap: 12rpx;
}

.risk-chip {
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

.risk-chip.is-active {
  background: #1470d8;
  border-color: #1470d8;
  color: #fff;
}

.add-rule-btn {
  margin-top: 18rpx;
  height: 72rpx;
  border-radius: 20rpx;
  background: rgba(37, 99, 235, 0.10);
  color: #1470d8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
}

.custom-rule-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.custom-rule-item {
  padding: 16rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.custom-rule-main {
  flex: 1;
  min-width: 0;
}

.custom-rule-title {
  color: #102033;
  font-size: 25rpx;
  font-weight: 900;
}

.custom-rule-desc,
.custom-rule-meta {
  margin-top: 7rpx;
  color: #64748b;
  font-size: 21rpx;
  line-height: 1.45;
}

.custom-rule-actions {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  flex-shrink: 0;
}

.rule-toggle,
.delete-rule {
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 800;
  text-align: center;
}

.rule-toggle.is-on {
  background: rgba(22, 163, 74, 0.10);
  color: #16a34a;
}

.rule-toggle.is-off {
  background: rgba(148, 163, 184, 0.12);
  color: #64748b;
}

.delete-rule {
  background: rgba(220, 38, 38, 0.08);
  color: #dc2626;
}

.footer-actions {
  margin-top: 18rpx;
  display: flex;
  gap: 12rpx;
}

.secondary-btn,
.primary-btn {
  flex: 1;
  height: 74rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
}

.secondary-btn {
  background: rgba(37, 99, 235, 0.10);
  color: #1470d8;
}

.primary-btn {
  background: linear-gradient(135deg, #1470d8, #38a4ff);
  color: #fff;
}

.primary-btn.is-disabled {
  opacity: 0.7;
}
</style>
