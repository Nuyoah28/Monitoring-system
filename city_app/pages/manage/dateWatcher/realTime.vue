<template>
  <scroll-view scroll-y="true" class="body">

    <!-- ───── 日期 Tab ───── -->
    <scroll-view scroll-x="true" class="date-scroll" :show-scrollbar="false">
      <view class="date-tabs">
        <!-- 月汇总 -->
        <view
          class="date-tab date-tab--month"
          :class="{ 'is-active': selectedDate === 'month' }"
          @tap="selectDate('month')"
        >
          <text class="dt-month">{{ currentMonth }}月</text>
          <text class="dt-label">汇总</text>
        </view>
        <view
          v-if="!dayTabs.length"
          class="date-tab date-tab--empty"
        >
          <text class="dt-day">暂无</text>
          <text class="dt-week">日期</text>
        </view>
        <!-- 每日 -->
        <view
          v-for="d in dayTabs"
          :key="d.date"
          class="date-tab"
          :class="{ 'is-active': selectedDate === d.date }"
          @tap="selectDate(d.date)"
        >
          <text class="dt-day">{{ d.label }}</text>
          <text class="dt-week">{{ d.week }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- ───── 报警次数 ───── -->
    <view class="stat-card">
      <view class="card-head">
        <view class="decorator"></view>
        <text class="card-title">报警次数</text>
      </view>
      <view class="count-row">
        <view class="count-item">
          <text class="count-num">{{ stats.total }}</text>
          <text class="count-label">总次数</text>
        </view>
        <view class="count-divider"></view>
        <view class="count-item">
          <view class="count-dot dot-urgent"></view>
          <text class="count-num count-num--urgent">{{ stats.urgent }}</text>
          <text class="count-label">高等级</text>
        </view>
        <view class="count-item">
          <view class="count-dot dot-serious"></view>
          <text class="count-num count-num--serious">{{ stats.serious }}</text>
          <text class="count-label">中等级</text>
        </view>
        <view class="count-item">
          <view class="count-dot dot-normal"></view>
          <text class="count-num count-num--normal">{{ stats.normal }}</text>
          <text class="count-label">低等级</text>
        </view>
      </view>
    </view>

    <!-- ───── 报警处理率 ───── -->
    <view class="stat-card">
      <view class="card-head">
        <view class="decorator"></view>
        <text class="card-title">报警处理率</text>
      </view>
      <view class="rate-row">
        <!-- 环形图 -->
        <view class="ring-wrap">
          <view class="ring-svg-box">
            <!-- SVG 环形进度 -->
            <svg viewBox="0 0 120 120" class="ring-svg">
              <!-- 背景圆 -->
              <circle cx="60" cy="60" r="48" fill="none" stroke="#E8F0FB" stroke-width="12"/>
              <!-- 进度圆（从顶部 -90° 起） -->
              <circle
                cx="60" cy="60" r="48"
                fill="none"
                stroke="url(#ringGrad)"
                stroke-width="12"
                stroke-linecap="round"
                :stroke-dasharray="ringDash"
                stroke-dashoffset="0"
                transform="rotate(-90 60 60)"
              />
              <defs>
                <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#38b6ff"/>
                  <stop offset="100%" stop-color="#0e6ecf"/>
                </linearGradient>
              </defs>
            </svg>
            <view class="ring-center">
              <text class="ring-pct">{{ rates.overall }}%</text>
              <text class="ring-sub">报警处理率</text>
            </view>
          </view>
        </view>
        <!-- 分级处理率 -->
        <view class="rate-detail">
          <view class="rate-line">
            <view class="rate-icon rate-icon--urgent">
              <!-- bell -->
              <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </view>
            <text class="rate-lbl">高等级</text>
            <text class="rate-val">{{ rates.urgent }}%</text>
          </view>
          <view class="rate-line">
            <view class="rate-icon rate-icon--serious">
              <!-- alert circle -->
              <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </view>
            <text class="rate-lbl">中等级</text>
            <text class="rate-val">{{ rates.serious }}%</text>
          </view>
          <view class="rate-line">
            <view class="rate-icon rate-icon--normal">
              <!-- check square -->
              <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
                <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
            </view>
            <text class="rate-lbl">低等级</text>
            <text class="rate-val">{{ rates.normal }}%</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ───── 报警类型分布（横向条形） ───── -->
    <view class="stat-card">
      <view class="card-head">
        <view class="decorator"></view>
        <text class="card-title">报警类型</text>
      </view>
      <view class="bar-list">
        <view class="bar-item" v-for="item in topTypes" :key="item.name">
          <text class="bar-label">{{ item.name }}</text>
          <view class="bar-track">
            <view
              class="bar-fill"
              :style="{ width: item.pct + '%' }"
            ></view>
          </view>
          <text class="bar-count">{{ item.count }}</text>
        </view>
        <view class="empty-tip" v-if="!topTypes.length">暂无数据</view>
      </view>
    </view>

    <!-- ───── 月度报警分布（折线图） ───── -->
    <view class="stat-card" style="margin-bottom: 40rpx;">
      <view class="card-head">
        <view class="decorator"></view>
        <text class="card-title">月度报警分布情况</text>
      </view>
      <view class="chart-box">
        <line-chart :range="30"></line-chart>
      </view>
    </view>

  </scroll-view>
</template>

<script>
import lineChart from "../../../components/lineChart.vue";

export default {
  components: { lineChart },
  props: {
    year:  { type: Number, default: () => new Date().getFullYear() },
    month: { type: Number, default: () => new Date().getMonth() + 1 },
  },
  data() {
    return {
      selectedDate: "month",
      currentMonth: this.month,
      monthTotal: { total: 0, todayNew: 0, dayChange: 0 },
      monthCaseList: [],
      monthAlarms: [],
      dayAlarms: [],
      allAlarms: [],
    };
  },
  watch: {
    year()  { this.onMonthChange(); },
    month() { this.onMonthChange(); },
  },
  computed: {
    // ── 生成当月每天 Tab ──
    dayTabs() {
      const year  = this.year;
      const month = this.month;
      const daysInMonth = new Date(year, month, 0).getDate();
      const now = new Date();
      const isCurrentMonth = year === now.getFullYear() && month === (now.getMonth() + 1);
      const isFutureMonth = year > now.getFullYear() || (year === now.getFullYear() && month > now.getMonth() + 1);
      const maxDay = isFutureMonth ? 0 : (isCurrentMonth ? now.getDate() : daysInMonth);
      const tabs = [];
      const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
      for (let d = 1; d <= maxDay; d++) {
        const date = new Date(year, month - 1, d);
        const mm = String(month).padStart(2, "0");
        const dd = String(d).padStart(2, "0");
        tabs.push({
          date: `${year}-${mm}-${dd}`,
          label: `${month}月${d}日`,
          mmdd: `${mm}.${dd}`,
          week: weeks[date.getDay()],
        });
      }
      return tabs.reverse();
    },

    // ── 统计数字 ──
    stats() {
      const source = this.selectedDate === "month" ? this.monthAlarms : this.dayAlarms;
      let urgent = 0, serious = 0, normal = 0;
      source.forEach(item => {
        const lv = Number(item.level || item.warningLevel) || 1;
        if (lv >= 3) urgent++;
        else if (lv === 2) serious++;
        else normal++;
      });
      return { total: source.length, urgent, serious, normal };
    },

    // ── 各等级处理率 ──
    rates() {
      if (this.selectedDate === "month") {
        const source = this.monthAlarms;
        const doneCount = source.filter(item => Number(item.status) === 1).length;
        const calc = (group) => {
          const list = source.filter(group);
          if (!list.length) return 0;
          const done = list.filter(item => Number(item.status) === 1).length;
          return Math.round((done / list.length) * 100);
        };
        return {
          overall: source.length ? Math.round((doneCount / source.length) * 100) : 0,
          urgent: calc(item => Number(item.level || item.warningLevel) >= 3),
          serious: calc(item => Number(item.level || item.warningLevel) === 2),
          normal: calc(item => Number(item.level || item.warningLevel) <= 1),
        };
      }

      const alarms = this.dayAlarms;
      const calc = (filterFn) => {
        const group = alarms.filter(filterFn);
        if (!group.length) return 0;
        const done = group.filter(i => Number(i.status) === 1).length;
        return Math.round((done / group.length) * 100);
      };
      return {
        overall: alarms.length ? Math.round((alarms.filter(i => Number(i.status) === 1).length / alarms.length) * 100) : 0,
        urgent: calc(i => Number(i.level || i.warningLevel) >= 3),
        serious: calc(i => Number(i.level || i.warningLevel) === 2),
        normal: calc(i => Number(i.level || i.warningLevel) <= 1),
      };
    },

    // ── 环形图 dasharray ──
    ringDash() {
      const circumference = 2 * Math.PI * 48; // r=48
      const filled = (this.rates.overall / 100) * circumference;
      return `${filled} ${circumference - filled}`;
    },

    // ── 报警类型 Top N ──
    topTypes() {
      let list = [];
      if (this.selectedDate === "month") {
        const map = {};
        this.monthAlarms.forEach(item => {
          const name = item.eventName || item.name || item.caseTypeName || "未知";
          map[name] = (map[name] || 0) + 1;
        });
        list = Object.entries(map).map(([name, count]) => ({ name, count }));
      } else {
        // 按日：从 dayAlarms 中聚合 eventName
        const map = {};
        this.dayAlarms.forEach(item => {
          const name = item.eventName || item.name || "未知";
          map[name] = (map[name] || 0) + 1;
        });
        list = Object.entries(map).map(([name, count]) => ({ name, count }));
      }
      list = list.filter(i => i.count > 0).sort((a, b) => b.count - a.count).slice(0, 6);
      const maxCount = list[0]?.count || 1;
      return list.map(i => ({ ...i, pct: Math.round((i.count / maxCount) * 100) }));
    },
  },
  methods: {
    async fetchAlarmList(time1 = null, time2 = null) {
      const { data } = await uni.$http.get("/api/v1/alarm/query", {
        pageNum: 1,
        pageSize: 5000,
        time1,
        time2,
      });
      if (data?.code === "D0400") {
        uni.showToast({ title: "登录失效，请重新登录！", icon: "none" });
        uni.removeStorageSync("token");
        uni.removeStorageSync("userId");
        uni.removeStorageSync("appType");
        uni.reLaunch({ url: "/pages/shared/select/index" });
        return [];
      }
      const list = (data?.data?.alarmList || []).filter(item => ![6, 9, 13].includes(Number(item.caseType)));
      if (!time1 || !time2) return list;
      const startDate = String(time1).slice(0, 10);
      const endDate = String(time2).slice(0, 10);
      return list.filter(item => {
        const raw = item.createTime || item.date || item.time;
        const day = raw ? String(raw).slice(0, 10) : '';
        return day >= startDate && day <= endDate;
      });
    },

    isSameMonth(item) {
      const raw = item.createTime || item.date || item.time;
      if (!raw) return false;
      const alarmDate = new Date(String(raw).replace(/-/g, "/"));
      return !Number.isNaN(alarmDate.getTime()) &&
        alarmDate.getFullYear() === this.year &&
        alarmDate.getMonth() + 1 === this.month;
    },

    isSameDay(item, dateStr) {
      const raw = item.createTime || item.date || item.time;
      return raw ? String(raw).slice(0, 10) === dateStr : false;
    },

    buildVisibleMonthRange() {
      const now = new Date();
      const isFutureMonth = this.year > now.getFullYear() || (this.year === now.getFullYear() && this.month > now.getMonth() + 1);
      if (isFutureMonth) return null;
      const monthEndDate = new Date(this.year, this.month, 0).getDate();
      const isCurrentMonth = this.year === now.getFullYear() && this.month === now.getMonth() + 1;
      const endDay = isCurrentMonth ? Math.min(now.getDate(), monthEndDate) : monthEndDate;
      const mm = String(this.month).padStart(2, "0");
      return {
        start: `${this.year}-${mm}-01 00:00:00`,
        end: `${this.year}-${mm}-${String(endDay).padStart(2, "0")} 23:59:59`,
      };
    },

    async refreshAlarms() {
      const visibleRange = this.buildVisibleMonthRange();
      if (!visibleRange) {
        this.allAlarms = [];
        this.monthAlarms = [];
        this.dayAlarms = [];
        return;
      }
      const list = await this.fetchAlarmList(visibleRange.start, visibleRange.end);
      this.allAlarms = list;
      this.monthAlarms = list.filter(item => this.isSameMonth(item));
      if (this.selectedDate !== "month") {
        this.dayAlarms = list.filter(item => this.isSameDay(item, this.selectedDate));
      }
    },

    // 月汇总接口
    async fetchMonthTotal() {
      try {
        const visibleRange = this.buildVisibleMonthRange();
        if (!visibleRange) {
          this.monthTotal = { total: 0, todayNew: 0, dayChange: 0 };
          this.monthCaseList = [];
          this.allAlarms = [];
          this.monthAlarms = [];
          this.dayAlarms = [];
          return;
        }
        const res = await uni.$http.get("/api/v1/alarm/realtime");
        if (res.data.code === "D0400") {
          uni.showToast({ title: "登录失效，请重新登录！", icon: "none" });
          uni.removeStorageSync("token");
          uni.removeStorageSync("userId");
          uni.removeStorageSync("appType");
          uni.reLaunch({ url: "/pages/shared/select/index" });
          return;
        }
        if (res.data.code === "00000") {
          this.monthTotal = res.data.data.alarmTotal || {};
          this.monthCaseList = res.data.data.alarmCaseTypeTotalList || [];
        }
        await this.refreshAlarms();
      } catch (e) { console.error(e); }
    },
    async fetchDayAlarms(dateStr) {
      try {
        const list = await this.fetchAlarmList(`${dateStr} 00:00:00`, `${dateStr} 23:59:59`);
        this.dayAlarms = list.filter(item => this.isSameDay(item, dateStr));
      } catch (e) { console.error(e); }
    },

    // 月份切换时重置
    onMonthChange() {
      this.selectedDate = "month";
      this.currentMonth = this.month;
      this.dayAlarms = [];
      this.fetchMonthTotal();
    },

    // Tab 切换
    selectDate(val) {
      this.selectedDate = val;
      if (val === "month") {
        this.fetchMonthTotal();
      } else {
        this.fetchDayAlarms(val);
      }
    },
  },
  mounted() { this.fetchMonthTotal(); },
  onShow()  { this.fetchMonthTotal(); },
};
</script>

<style lang="scss" scoped>
// ─── 滚动容器 ───
.body {
  height: 100%;
  background: transparent;
}

// ─── 日期 Tab ───
.date-scroll {
  width: 100%;
  flex-shrink: 0;
  padding: 4rpx 0 16rpx;
}

.date-tabs {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  gap: 12rpx;
  padding: 4rpx 24rpx 4rpx;
  white-space: nowrap;
}

.date-tab {
  flex-shrink: 0;
  min-width: 100rpx;
  padding: 16rpx 20rpx;
  border-radius: 16rpx;
  background: #fff;
  border: 1.5rpx solid #e5edf8;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  box-shadow: 0 2rpx 8rpx rgba(40, 91, 150, 0.06);
  transition: all 0.18s;

  &:active { transform: scale(0.95); }

  &.is-active {
    background: linear-gradient(135deg, #1470d8 0%, #38a4ff 100%);
    border-color: transparent;
    box-shadow: 0 4rpx 16rpx rgba(20, 112, 216, 0.3);
  }
}

.date-tab--month {
  min-width: 110rpx;
}

.date-tab--empty {
  opacity: 0.65;
}

.dt-month {
  font-size: 30rpx;
  font-weight: 900;
  color: #1470d8;
  .is-active & { color: #fff; }
}
.dt-label {
  font-size: 22rpx;
  color: #7a90aa;
  .is-active & { color: rgba(255,255,255,0.85); }
}
.dt-day {
  font-size: 26rpx;
  font-weight: 700;
  color: #2c4a68;
  .is-active & { color: #fff; }
}
.dt-week {
  font-size: 20rpx;
  color: #96a8b8;
  .is-active & { color: rgba(255,255,255,0.8); }
}

// ─── 通用卡片 ───
.stat-card {
  margin: 0 24rpx 20rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 26rpx 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(40, 91, 150, 0.07);
  border: 1rpx solid rgba(210, 228, 248, 0.5);
}

.card-head {
  display: flex;
  align-items: center;
  margin-bottom: 22rpx;
}

.decorator {
  width: 7rpx;
  height: 34rpx;
  border-radius: 4rpx;
  background: linear-gradient(180deg, #38b6ff, #0e6ecf);
  margin-right: 16rpx;
  flex-shrink: 0;
}

.card-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #1a2d42;
}

// ─── 报警次数 ───
.count-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.count-divider {
  width: 1rpx;
  height: 60rpx;
  background: #e8edf8;
  flex-shrink: 0;
}

.count-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  position: relative;
}

.count-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);

  &.dot-urgent  { background: #ef4444; }
  &.dot-serious { background: #f59e0b; }
  &.dot-normal  { background: #22c55e; }
}

.count-num {
  font-size: 52rpx;
  font-weight: 900;
  color: #1a2d42;
  margin-top: 4rpx;

  &--urgent  { color: #ef4444; }
  &--serious { color: #f59e0b; }
  &--normal  { color: #22c55e; }
}

.count-label {
  font-size: 22rpx;
  color: #8a9db8;
  font-weight: 600;
}

// ─── 处理率 ───
.rate-row {
  display: flex;
  align-items: center;
  gap: 30rpx;
}

.ring-wrap {
  flex-shrink: 0;
}

.ring-svg-box {
  position: relative;
  width: 180rpx;
  height: 180rpx;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ring-pct {
  font-size: 38rpx;
  font-weight: 900;
  color: #1a2d42;
}

.ring-sub {
  font-size: 18rpx;
  color: #8a9db8;
  margin-top: 4rpx;
}

.rate-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.rate-line {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.rate-icon {
  width: 44rpx;
  height: 44rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  svg { width: 24rpx; height: 24rpx; }

  &--urgent  { background: #ef4444; }
  &--serious { background: #f59e0b; }
  &--normal  { background: #22c55e; }
}

.rate-lbl {
  font-size: 27rpx;
  font-weight: 600;
  color: #3a5068;
  flex: 1;
}

.rate-val {
  font-size: 34rpx;
  font-weight: 900;
  color: #1a2d42;
}

// ─── 报警类型横向条形 ───
.bar-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.bar-label {
  width: 150rpx;
  flex-shrink: 0;
  font-size: 25rpx;
  color: #3a5068;
  font-weight: 600;
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 20rpx;
  background: #edf3fb;
  border-radius: 999rpx;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #38d9c0 0%, #38b6ff 60%, #1470d8 100%);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.bar-count {
  width: 40rpx;
  flex-shrink: 0;
  font-size: 26rpx;
  font-weight: 700;
  color: #2c4a68;
  text-align: left;
}

.empty-tip {
  text-align: center;
  color: #b0c0d4;
  font-size: 26rpx;
  padding: 20rpx 0;
}

// ─── 月度折线图 ───
.chart-box {
  width: 100%;
  height: 440rpx;
}
</style>
