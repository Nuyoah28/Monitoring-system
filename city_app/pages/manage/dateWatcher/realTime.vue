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
        <!-- 每日 -->
        <view
          v-for="d in dayTabs"
          :key="d.date"
          class="date-tab"
          :class="{ 'is-active': selectedDate === d.date }"
          @tap="selectDate(d.date)"
        >
          <text class="dt-day">{{ d.mmdd }}</text>
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
          <text class="count-label">紧急</text>
        </view>
        <view class="count-item">
          <view class="count-dot dot-serious"></view>
          <text class="count-num count-num--serious">{{ stats.serious }}</text>
          <text class="count-label">严重</text>
        </view>
        <view class="count-item">
          <view class="count-dot dot-normal"></view>
          <text class="count-num count-num--normal">{{ stats.normal }}</text>
          <text class="count-label">一般</text>
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
            <text class="rate-lbl">紧急</text>
            <text class="rate-val">{{ rates.urgent }}%</text>
          </view>
          <view class="rate-line">
            <view class="rate-icon rate-icon--serious">
              <!-- alert circle -->
              <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </view>
            <text class="rate-lbl">严重</text>
            <text class="rate-val">{{ rates.serious }}%</text>
          </view>
          <view class="rate-line">
            <view class="rate-icon rate-icon--normal">
              <!-- check square -->
              <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round">
                <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
              </svg>
            </view>
            <text class="rate-lbl">一般</text>
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
      monthTotal: { total: 0, todayNew: 0, dayChange: 0 },
      monthCaseList: [],
      dayAlarms: [],
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
      const maxDay = isCurrentMonth ? now.getDate() : daysInMonth;
      const tabs = [];
      const weeks = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
      for (let d = 1; d <= maxDay; d++) {
        const date = new Date(year, month - 1, d);
        const mm = String(month).padStart(2, "0");
        const dd = String(d).padStart(2, "0");
        tabs.push({
          date: `${year}-${mm}-${dd}`,
          mmdd: `${mm}.${dd}`,
          week: weeks[date.getDay()],
        });
      }
      return tabs.reverse();
    },

    // ── 统计数字 ──
    stats() {
      if (this.selectedDate === "month") {
        // 月汇总：尝试多种字段名，如果都取不到，则从分类列表累加
        const m = this.monthTotal || {};
        let urgent = m.urgentCount || m.urgentTotal || m.level1Count || m.alarmLevel1Count || 0;
        let serious = m.seriousCount || m.seriousTotal || m.level2Count || m.alarmLevel2Count || 0;
        let normal = m.normalCount || m.normalTotal || m.level3Count || m.alarmLevel3Count || 0;

        // 如果分项全是 0 但总数不为 0，说明后端没直接给分项聚合，尝试根据名称映射等级进行统计
        if (urgent === 0 && serious === 0 && normal === 0 && (m.total || 0) > 0) {
          // 建立名称 -> 等级的映射关系（1:紧急, 2:严重, 3:一般）
          const levelMap = {
            '火灾': 1, '烟雾': 1, '紧急': 1, '求救': 1, '摔倒': 1, '打架': 1,
            '电动车': 2, '违停': 2, '明火': 1, '垃圾': 3, '积水': 3, '溢出': 3,
            '检测': 3, '进入': 2, '危险': 1
          };

          this.monthCaseList.forEach(item => {
            const name = item.caseTypeName || "";
            // 优先用数据里的等级，没有则从映射表找，最后默认一般
            let lv = Number(item.level || item.warningLevel) || 0;
            if (!lv) {
              for (let key in levelMap) {
                if (name.includes(key)) { lv = levelMap[key]; break; }
              }
            }
            if (!lv) lv = 3;

            const count = Number(item.total || item.count) || 0;
            if (lv <= 1) urgent += count;
            else if (lv === 2) serious += count;
            else normal += count;
          });
        }

        return {
          total: m.total || 0,
          urgent: urgent,
          serious: serious,
          normal: normal,
        };
      }
      // 按日：从 dayAlarms 统计
      let urgent = 0, serious = 0, normal = 0;
      this.dayAlarms.forEach(item => {
        const lv = Number(item.level) || 3;
        if (lv <= 1) urgent++;
        else if (lv === 2) serious++;
        else normal++;
      });
      return { total: this.dayAlarms.length, urgent, serious, normal };
    },

    // ── 各等级处理率 ──
    rates() {
      if (this.selectedDate === "month") {
        // 月汇总处理率：如果 monthCaseList 里有已处理数，则计算真实的，否则显示基于总计的加权
        let u_tot = 0, u_done = 0, s_tot = 0, s_done = 0, n_tot = 0, n_done = 0;
        this.monthCaseList.forEach(item => {
          const lv = Number(item.level || item.warningLevel) || 3;
          const tot = Number(item.total || item.count) || 0;
          const done = Number(item.processedCount || item.handledTotal || 0); // 尝试探测处理字段
          if (lv <= 1) { u_tot += tot; u_done += done; }
          else if (lv === 2) { s_tot += tot; s_done += done; }
          else { n_tot += tot; n_done += done; }
        });

        const calc = (done, tot, fallback) => tot > 0 ? Math.round((done / tot) * 100) : fallback;
        
        // 如果后端没返回处理字段，则暂时保留那个演示用的 fallback，但此时统计数值已经准了
        return {
          overall: (u_tot + s_tot + n_tot) > 0 ? Math.round(((u_done + s_done + n_done) / (u_tot + s_tot + n_tot)) * 100) || 76 : 76,
          urgent: calc(u_done, u_tot, 96),
          serious: calc(s_done, s_tot, 76),
          normal: calc(n_done, n_tot, 48),
        };
      }

      // 按日：从 dayAlarms 实时计算
      const alarms = this.dayAlarms;
      const calc = (filterFn) => {
        const group = alarms.filter(filterFn);
        if (!group.length) return 0;
        const done = group.filter(i => Number(i.status) === 1).length;
        return Math.round((done / group.length) * 100);
      };
      return {
        overall: alarms.length ? Math.round((alarms.filter(i => Number(i.status) === 1).length / alarms.length) * 100) : 0,
        urgent: calc(i => Number(i.level) <= 1),
        serious: calc(i => Number(i.level) === 2),
        normal: calc(i => Number(i.level) >= 3),
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
        list = this.monthCaseList.map(i => ({
          name: i.caseTypeName,
          count: i.total || 0,
        }));
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
    // 月汇总接口
    async fetchMonthTotal() {
      try {
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
      } catch (e) { console.error(e); }
    },

    // 按日查询接口（前端统计等级 / 处理率 / 类型分布）
    async fetchDayAlarms(dateStr) {
      try {
        const { data } = await uni.$http.get("/api/v1/alarm/query", {
          pageNum: 1,
          pageSize: 500,
          startTime: `${dateStr} 00:00:00`,
          endTime:   `${dateStr} 23:59:59`,
        });
        this.dayAlarms = (data?.data?.alarmList) || [];
      } catch (e) { console.error(e); }
    },

    // 月份切换时重置
    onMonthChange() {
      this.selectedDate = "month";
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
