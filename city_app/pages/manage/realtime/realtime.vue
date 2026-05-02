<template>
  <view class="alarm-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="bg-orb bg-orb--one"></view>
    <view class="bg-orb bg-orb--two"></view>

    <view class="top-nav">
      <view class="back-btn" @tap="goBack">
        <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
      </view>
      <text class="top-title">告警中心</text>
    </view>

    <view class="header-card">
      <view class="header-copy">
        <view class="eyebrow">社区安全事件</view>
        <view class="title">{{ choosen === 0 ? '待处理告警' : '已处理记录' }}</view>
        <view class="subtitle">
          {{ choosen === 0 ? '优先处理高风险和最新告警，处理后会自动归档' : '查看已经完成处理的历史事件' }}
        </view>
      </view>
      <view class="header-stat" :class="choosen === 0 ? 'is-danger' : 'is-success'">
        <text class="stat-num">{{ currentList.length }}</text>
        <text class="stat-label">{{ choosen === 0 ? '待处理' : '已处理' }}</text>
      </view>
    </view>

    <view class="section-card filter-card">
      <view class="tab-row">
        <view class="tab-item" :class="choosen === 0 ? 'is-active' : ''" @tap="switchTab(0)">待处理</view>
        <view class="tab-item" :class="choosen === 1 ? 'is-active' : ''" @tap="switchTab(1)">已处理</view>
      </view>
      <view class="filter-row">
        <view class="filter-chip" @tap="showFilter = true">
          <text>{{ filterIndex !== null ? filters[0][filterIndex] : '事件类型' }}</text>
          <u-icon name="arrow-down" color="#64748b" size="22rpx"></u-icon>
        </view>
        <view class="filter-chip" @tap="showStatus = true">
          <text>{{ statusIndex !== null ? status[0][statusIndex] : '告警等级' }}</text>
          <u-icon name="arrow-down" color="#64748b" size="22rpx"></u-icon>
        </view>
        <view class="refresh-btn" :class="{ 'is-refreshing': isRefreshing }" @tap="reset">
          <u-icon name="reload" color="#1470d8" size="32rpx"></u-icon>
        </view>
      </view>
    </view>

    <scroll-view
      class="alarm-list"
      scroll-y="true"
      :scroll-top="scrollTop"
      @scrolltolower="getMore"
      @scroll="getTop"
    >
      <view
        class="alarm-card"
        v-for="(item, index) in currentList"
        :key="item.id"
        @tap="openDetail(item)"
      >
        <view class="card-top">
          <view class="camera-info">
            <view class="camera-name">{{ item.name || '未命名摄像头' }}</view>
            <view class="camera-area">{{ item.department || '未标注区域' }}</view>
          </view>
          <view class="level-pill" :class="levelClass(item.level)">{{ levelText(item.level) }}</view>
        </view>

        <view class="event-row">
          <view class="event-dot" :class="levelClass(item.level)"></view>
          <view class="event-name">{{ item.eventName || '异常事件' }}</view>
          <view class="deal-pill" :class="item.deal === '已处理' ? 'is-done' : 'is-pending'">{{ item.deal }}</view>
        </view>

        <view class="meta-row">
          <text>{{ item.date || '--' }}</text>
          <text>ID {{ item.id }}</text>
        </view>

        <view class="content-note" v-if="item.content && item.deal === '已处理'">
          处理说明：{{ item.content }}
        </view>

        <view class="action-row" @tap.stop>
          <view class="action-btn action-btn--ghost" @tap="openDetail(item)">查看详情</view>
          <view class="action-btn action-btn--call" v-if="item.deal === '未处理'" @tap="alert(index)">联系</view>
          <view class="action-btn action-btn--primary" v-if="item.deal === '未处理'" @tap="deal(index)">处理告警</view>
          <view class="action-btn action-btn--ghost" v-else @tap="openDetail(item)">处理记录</view>
        </view>
      </view>

      <view class="empty-state" v-if="!currentList.length && statusList !== 'loading'">
        <view class="empty-title">{{ choosen === 0 ? '暂无待处理告警' : '暂无已处理记录' }}</view>
        <view class="empty-desc">{{ choosen === 0 ? '当前社区运行平稳' : '处理完成后会在这里归档' }}</view>
      </view>
      <u-loadmore :status="statusList"></u-loadmore>
    </scroll-view>

    <u-modal
      :show="showDeal"
      :closeOnClickOverlay="true"
      @close="closeDealModal"
      @confirm="sendDeal"
      showCancelButton
      @cancel="closeDealModal"
      confirmText="确认处理"
      cancelText="取消"
      width="650rpx"
    >
      <view class="deal-modal" v-if="showDeal">
        <view class="deal-title">处理告警</view>
        <view class="deal-subtitle">{{ activeDealItem.eventName || '异常事件' }} · {{ activeDealItem.department || '未标注区域' }}</view>
        <view class="quick-title">常用处理结果</view>
        <view class="quick-result-row">
          <view class="quick-result" v-for="text in quickDealTexts" :key="text" @tap="content = text">{{ text }}</view>
        </view>
        <textarea
          class="deal-textarea"
          v-model="content"
          placeholder="请填写现场核实结果或处理说明"
          :adjust-position="false"
        />
      </view>
    </u-modal>

    <u-picker
      :show="showFilter"
      :columns="filters"
      @confirm="setFilter"
      @cancel="showFilter = false"
    ></u-picker>
    <u-picker
      :show="showStatus"
      :columns="status"
      @confirm="setStatus"
      @cancel="showStatus = false"
    ></u-picker>

    <manage-tabbar current="alarm" :hidden="showDeal || showFilter || showStatus" />
  </view>
</template>

<script>
import ManageTabbar from '@/components/navigation/manage-tabbar.vue';

export default {
  components: {
    ManageTabbar,
  },
  data() {
    return {
      top: 0,
      scrollTop: 0,
      statusList: "nomore",
      moveX: 0,
      startX: 0,
      statusBarHeight: 0,
      safeAreaTop: 0,
      show: false,
      showFilter: false,
      showStatus: false,
      status: [["高", "中", "低"]],
      statusValue: [3, 2, 1],
      statusIndex: null,
      filters: [
        [
          "进入危险区域", "烟雾", "区域停留", "摔倒", "明火",
          "吸烟", "打架斗殴", "垃圾乱放", "电动车进楼",
          "载具占用车道", "挥手呼救"
        ]
      ],
      filterValue: [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12],
      filterIndex: null,
      scrollHeight: 0,
      choosen: 0,
      pageSize: 100,
      pendingPageSize: 5000,
      pageNum: 1,
      warnIsAll: false,
      hisIsAll: false,
      caseType: null,
      warningLevel: null,
      warnData: [],
      historyData: [],
      dealIcon: [
        "../../../static/20230910-194834.png",
        "../../../static/attention.png",
      ],
      showDeal: false,
      content: "",
      id: null,
      index: 0,
      quickDealTexts: ["已到现场核实，风险已解除", "已通知负责人跟进", "误报，现场无异常"],
      dataFetchInterval: null, // 定时器ID
      isRefreshing: false, // 正在刷新状态
    };
  },
  computed: {
    currentList() {
      return this.choosen === 0 ? this.warnData : this.historyData;
    },
    activeDealItem() {
      return this.currentList[this.index] || {};
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    this.safeAreaTop = info.safeArea.height;
    this.$nextTick(() => {
      this.updateScrollHeight();
      setTimeout(() => {
        this.updateScrollHeight();
      }, 80);
    });
	
	// 监听 WebSocket 发送的新报警事件
	uni.$on('newAlarm', () => {
			// 只有在查看待处理警情时自动刷新
		if (this.choosen === 0) {
			this.pageNum = 1;
			this.warnIsAll = false;
			this.getRealList();
		}
	});
  },
  onUnload() {
    uni.$off('newAlarm');
  },
  onShow() {
    // console.log("realShow");
    this.choosen = 0;
    this.caseType = null;
    this.filterIndex = null;
    this.warningLevel = null;
    this.statusIndex = null;
	this.statusList= "nomore";
	this.hisIsAll = false;
	this.warnIsAll = false;
    this.$nextTick(() => {
      this.updateScrollHeight();
    });
    this.getRealList();
  },
   // beforeDestroy() {
   //    clearInterval(this.dataFetchInterval); // 组件销毁前清除定时器
   //  },
  methods: {
    switchTab(tab) {
      if (this.choosen === tab) return;
      this.choosen = tab;
      this.pageNum = 1;
      this.hisIsAll = false;
      this.warnIsAll = false;
      this.statusList = "nomore";
      if (tab === 0) {
        this.getRealList();
      } else {
        this.getHistoryList();
      }
    },
    isVisibleAlarm(item) {
      return ![6, 9, 13].includes(Number(item && item.caseType));
    },
    isPendingAlarm(item) {
      if (!item) return false;
      const status = Number(item.status);
      return status === 0 || item.deal === "未处理";
    },
    isPendingAlarmVisible(item) {
      return this.isVisibleAlarm(item) && this.isPendingAlarm(item);
    },
    isProcessedAlarm(item) {
      if (!item) return false;
      const status = Number(item.status);
      return status === 1 || item.deal === "已处理";
    },
    isProcessedAlarmVisible(item) {
      return this.isVisibleAlarm(item) && this.isProcessedAlarm(item);
    },
    levelClass(level) {
      const num = Number(level);
      if (num >= 3) return 'is-high';
      if (num === 2) return 'is-mid';
      return 'is-low';
    },
    levelText(level) {
      const num = Number(level);
      if (num >= 3) return '高风险';
      if (num === 2) return '中风险';
      return '低风险';
    },
    updateScrollHeight() {
      this.scrollHeight = 0;
    },
    alert(index) {
		console.log(this.warnData[index].phone)
      uni.makePhoneCall({
        phoneNumber: this.warnData[index].phone,
      });
    },
    setFilter(e) {
		this.pageNum = 1;
		this.hisIsAll = false;
		this.warnIsAll = false;
      this.caseType = this.filterValue[e.indexs[0]];
      this.filterIndex = e.indexs[0];
      this.showFilter = false;
      if (this.choosen) {
        this.getHistoryList();
      } else {
        this.getRealList();
      }
    },
    setStatus(e) {
		this.pageNum = 1;
		this.hisIsAll = false;
		this.warnIsAll = false;
      this.warningLevel = this.statusValue[e.indexs[0]];
      this.statusIndex = e.indexs[0];
      this.showStatus = false;
      if (this.choosen) {
        this.getHistoryList();
      } else {
        this.getRealList();
      }
    },
    getMore(e) {
		this.statusList = 'loading'
		// console.log(this.hisIsAll)
      if (this.choosen && !this.hisIsAll) {
        this.pageNum++;
        const data = {
          pageNum: this.pageNum,
          pageSize: this.pageSize,
        };
        if (this.caseType) {
          data.caseType = this.caseType;
        }
        if (this.warningLevel) {
          data.warningLevel = this.warningLevel;
        }
        uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
			console.log('data',data)
          const filteredList = data.data.alarmList.filter(this.isProcessedAlarmVisible);
          this.historyData.push(...filteredList);
          if (data.data.count < this.pageSize) {
			  // console.log(data.data.count)
            this.hisIsAll = true;
            this.statusList = "nomore";
          }
          this.historyData.map((item) => {
            this.$set(item, "moveX", 0);
          });
          this.scrollTop = this.top;
        });
      } else if (this.choosen && this.hisIsAll) {
		  this.statusList = 'nomore'
        return;
      } else if (!this.choosen && !this.warnIsAll) {
        // console.log("0 more");
        this.pageNum++;
        const pageSize = this.pendingPageSize;
        const data = {
          pageNum: this.pageNum,
          pageSize,
          status: 0,
        };
        // console.log(data);
        if (this.caseType) {
          data.caseType = this.caseType;
        }
        if (this.warningLevel) {
          data.warningLevel = this.warningLevel;
        }
        uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
          console.log(data);
          const filteredList = (data.data.alarmList || []).filter(this.isPendingAlarmVisible);
          this.warnData.push(...filteredList);
          if ((data.data.alarmList || []).length < pageSize) {
            this.warnIsAll = true;
            this.statusList = "nomore";
          }
          this.warnData.map((item) => {
            this.$set(item, "moveX", 0);
          });
        });
      } else if (!this.choosen && this.warnIsAll) {
		  this.statusList = 'nomore'
        return;
      }
    },
    getTop(e) {
      this.top = e.detail.scrollTop;
    },
    getRealList() {
			this.statusList = 'loading'
	      const data = {
	        pageNum: this.pageNum,
	        pageSize: this.pendingPageSize,
	        status: 0,
	      };
      if (this.caseType) {
        data.caseType = this.caseType;
      }
      if (this.warningLevel) {
        data.warningLevel = this.warningLevel;
      }
      uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
        // console.log(data);
        this.warnData = (data.data.alarmList || []).filter(this.isPendingAlarmVisible);
        if (!this.warnData.length) this.statusList = 'nomore';
        if ((data.data.alarmList || []).length < this.pendingPageSize) {
          this.warnIsAll = true;
          this.statusList = 'nomore';
        }
        this.warnData.map((item) => {
          this.$set(item, "moveX", 0);
        });
      });
    },
    getHistoryList() {
		this.statusList = 'loading'
      const data = {
        pageNum: this.pageNum,
        pageSize: this.pageSize,
      };
      if (this.caseType) {
        data.caseType = this.caseType;
      }
      if (this.warningLevel) {
        data.warningLevel = this.warningLevel;
      }
      uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
        this.historyData = data.data.alarmList.filter(this.isProcessedAlarmVisible);
		if(!this.historyData.length) this.statusList = 'nomore'
        if (data.data.count < this.pageSize) {
          this.hisIsAll = true;
		  this.statusList = 'nomore'
        }
        this.historyData.map((item) => {
          this.$set(item, "moveX", 0);
        });
      });
    },
    reset() {
      if (this.isRefreshing) return;
      this.isRefreshing = true;
      setTimeout(() => { this.isRefreshing = false; }, 800); // 动效时长

      this.caseType = null;
      this.filterIndex = null;
      this.warningLevel = null;
      this.statusIndex = null;
      this.pageNum = 1;
	  this.hisIsAll = false;
	  this.warnIsAll = false;
      if (this.choosen) {
        this.getHistoryList();
      } else {
        this.getRealList();
      }
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.reLaunch({ url: "/pages/manage/controls/controls" });
      }
    },
    startMove(e, item) {
      this.startX = e.touches[0].clientX;
    },
    moving(e, item) {
      let dis = e.touches[0].clientX - this.startX;
      let move = function (dis) {
        item.moveX = dis;
      };
      // const throttlePush = throttle(move,10);
      if (item.moveX <= -100 && dis < 0) return;
      // throttlePush(dis);
      move(dis);
      if (item.moveX > 0) item.moveX = 0;
    },
    stopMove(e, item) {
      if (item.moveX < -40) item.moveX = -100;
      else item.moveX = 0;
    },
    check(index) {
      const item = this.choosen ? this.historyData[index] : this.warnData[index];
      this.resetX(index);
      this.openDetail(item);
    },
    openDetail(item) {
      if (!item || !item.id) {
        uni.$showMsg("报警ID缺失，无法查看详情");
        return;
      }
      uni.navigateTo({
        url: `/pages/manage/realtime/detail?id=${item.id}`,
      });
    },
    deal(index) {
      this.index = index;
      const item = this.currentList[index] || {};
      this.id = item.id || null;
      this.content = item.content || '';
      this.showDeal = true;
      this.resetX(index);
    },
    resetX(index) {
      const target = this.choosen ? this.historyData[index] : this.warnData[index];
      if (target) this.$set(target, 'moveX', 0);
    },
    deleteItem(index) {
      this.resetX(index);
      uni.showModal({
        title: "警告",
        content: "是否要删除该项?",
        showCancel: true,
        success: () => {
          this.pageNum = 1;
          let alarmId = this.choosen
            ? this.historyData[index].id
            : this.warnData[index].id;
          uni.$http.delete(`/api/v1/alarm/${alarmId}`).then(() => {
            if (this.choosen) {
              this.getHistoryList();
            } else {
              this.getRealList();
            }
          });
        },
      });
    },
    setContent(val, id) {
      // console.log(val, id);
      this.content = val;
      this.id = id;
    },
    closeDealModal() {
      this.showDeal = false;
      this.content = "";
      this.id = null;
    },
    async sendDeal() {
      const content = String(this.content || '').trim();
      if (!content) {
        uni.showToast({
          title: "请填写处理说明",
          duration: 2000,
          icon: "none",
        });
        return;
      }
      const data = {
        id: this.id || (this.activeDealItem && this.activeDealItem.id),
        status: 1,
        processingContent: content,
      };
      if (!data.id) {
        uni.showToast({ title: "告警ID缺失", icon: "none" });
        return;
      }
      await uni.$http.put("/api/v1/alarm/update", data).then(() => {
        uni.showToast({ title: "已处理", icon: "success" });
        this.pageNum = 1;
        this.hisIsAll = false;
        this.warnIsAll = false;
        if (this.choosen) {
          this.getHistoryList();
        } else {
          this.getRealList();
        }
      });
      this.closeDealModal();
    },
  },
  watch: {
    choosen: {
      handler(newVal) {
        this.pageNum = 1;
        this.caseType = null;
        this.filterIndex = null;
        this.warningLevel = null;
        this.statusIndex = null;
		this.hisIsAll = false;
		this.warnIsAll = false;
        this.statusList = "loading";
        if (newVal === 1) {
          this.getHistoryList();
        } else {
          this.getRealList();
        }
      },
    },
  },
};
</script>

<style lang="scss" scoped>
.alarm-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 0 24rpx calc(128rpx + env(safe-area-inset-bottom));
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 12% 6%, rgba(56, 164, 255, 0.14) 0, rgba(56, 164, 255, 0) 250rpx),
    radial-gradient(circle at 88% 16%, rgba(220, 38, 38, 0.08) 0, rgba(220, 38, 38, 0) 280rpx),
    linear-gradient(180deg, #edf7ff 0%, #f5fbff 46%, #fbfdff 100%);
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
  top: 560rpx;
  background: rgba(220, 38, 38, 0.06);
}

.top-nav {
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.back-btn,
.setting-btn {
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

.header-card {
  margin-top: 8rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #1470d8, #38a4ff);
  box-shadow: 0 14rpx 34rpx rgba(20, 112, 216, 0.22);
  color: #fff;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.header-copy {
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
  line-height: 1.1;
}

.subtitle {
  margin-top: 10rpx;
  font-size: 23rpx;
  opacity: 0.86;
  line-height: 1.45;
}

.header-stat {
  width: 120rpx;
  height: 120rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.96);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.stat-num {
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1;
}

.stat-label {
  margin-top: 8rpx;
  font-size: 20rpx;
  font-weight: 800;
}

.header-stat.is-danger { color: #dc2626; }
.header-stat.is-success { color: #16a34a; }

.section-card {
  margin-top: 18rpx;
  padding: 18rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.10);
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.tab-row {
  display: flex;
  gap: 10rpx;
  padding: 6rpx;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
}

.tab-item {
  flex: 1;
  height: 58rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  font-size: 23rpx;
  font-weight: 800;
}

.tab-item.is-active {
  background: #1470d8;
  color: #fff;
  box-shadow: 0 8rpx 18rpx rgba(20, 112, 216, 0.18);
}

.filter-row {
  margin-top: 14rpx;
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.filter-chip {
  flex: 1;
  min-width: 0;
  height: 62rpx;
  padding: 0 18rpx;
  border-radius: 16rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8rpx;
  color: #475569;
  font-size: 22rpx;
  font-weight: 800;
}

.filter-chip text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.refresh-btn {
  width: 62rpx;
  height: 62rpx;
  border-radius: 16rpx;
  background: #edf6ff;
  border: 1rpx solid #dcebfa;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.refresh-btn.is-refreshing {
  animation: rotateReload 0.8s cubic-bezier(0.45, 0.05, 0.55, 0.95);
}

@keyframes rotateReload {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.alarm-list {
  flex: 1;
  min-height: 0;
  margin-top: 18rpx;
  padding-bottom: 10rpx;
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

.alarm-card {
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.95);
  border: 1rpx solid rgba(37, 99, 235, 0.10);
  box-shadow: 0 10rpx 28rpx rgba(30, 88, 150, 0.08);
  margin-bottom: 16rpx;
}

.card-top,
.event-row,
.meta-row,
.action-row {
  display: flex;
  align-items: center;
}

.card-top {
  justify-content: space-between;
  gap: 12rpx;
}

.camera-name {
  color: #102033;
  font-size: 28rpx;
  font-weight: 900;
}

.camera-area {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
}

.level-pill,
.deal-pill {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.level-pill.is-high {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.10);
}

.level-pill.is-mid {
  color: #d97706;
  background: rgba(245, 158, 11, 0.12);
}

.level-pill.is-low {
  color: #1470d8;
  background: rgba(20, 112, 216, 0.10);
}

.event-row {
  margin-top: 18rpx;
  gap: 10rpx;
}

.event-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.event-dot.is-high { background: #dc2626; }
.event-dot.is-mid { background: #f59e0b; }
.event-dot.is-low { background: #1470d8; }

.event-name {
  flex: 1;
  min-width: 0;
  color: #102033;
  font-size: 32rpx;
  font-weight: 900;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.deal-pill.is-pending {
  color: #dc2626;
  background: rgba(220, 38, 38, 0.08);
}

.deal-pill.is-done {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.10);
}

.meta-row {
  justify-content: space-between;
  margin-top: 14rpx;
  color: #64748b;
  font-size: 22rpx;
  font-weight: 700;
}

.content-note {
  margin-top: 14rpx;
  padding: 14rpx;
  border-radius: 16rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #475569;
  font-size: 22rpx;
  line-height: 1.45;
}

.action-row {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  align-items: center;
}

.action-btn {
  min-width: 112rpx;
  padding: 10rpx 16rpx;
  border-radius: 14rpx;
  font-size: 21rpx;
  font-weight: 900;
  text-align: center;
  box-sizing: border-box;
  margin-right: 4rpx;
}

.action-btn--primary {
  background: linear-gradient(135deg, #1470d8, #38a4ff);
  color: #fff;
}

.action-btn--ghost {
  background: rgba(37, 99, 235, 0.10);
  color: #1470d8;
}

.action-btn--call {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.empty-state {
  margin-top: 50rpx;
  padding: 48rpx 20rpx;
  text-align: center;
  color: #94a3b8;
}

.empty-title {
  color: #475569;
  font-size: 28rpx;
  font-weight: 900;
}

.empty-desc {
  margin-top: 10rpx;
  font-size: 22rpx;
}

.deal-modal {
  width: 100%;
  padding: 8rpx 0 4rpx;
}

.deal-title {
  color: #102033;
  font-size: 32rpx;
  font-weight: 900;
  text-align: center;
}

.deal-subtitle {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 22rpx;
  text-align: center;
}

.quick-title {
  margin-top: 22rpx;
  color: #475569;
  font-size: 22rpx;
  font-weight: 800;
}

.quick-result-row {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.quick-result {
  padding: 10rpx 14rpx;
  border-radius: 999rpx;
  background: #edf6ff;
  color: #1470d8;
  font-size: 21rpx;
  font-weight: 800;
}

.deal-textarea {
  margin-top: 16rpx;
  width: 100%;
  min-height: 180rpx;
  padding: 18rpx;
  box-sizing: border-box;
  border-radius: 18rpx;
  background: #f8fbff;
  border: 1rpx solid #dcebfa;
  color: #102033;
  font-size: 24rpx;
  line-height: 1.5;
}
</style>
