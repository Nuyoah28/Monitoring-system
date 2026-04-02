<template>
  <view style="height: 100vh; width: 100vw; position: relative">
    <view class="warnBox" id="warnBox" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="title">
        <view class="back-btn" @tap="goBack">
          <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
        </view>
        <view class="topNav">
          <view
            class="left"
            :class="choosen === 0 ? 'choosen' : ''"
            @click="choosen = 0"
          >
            <span>实时警报</span>
          </view>
          <view
            class="right"
            :class="choosen === 1 ? 'choosen' : ''"
            @click="choosen = 1"
          >
            <span>历史事件</span>
          </view>
        </view>
        <view class="setting-btn" @click="jump">
          <u-icon name="setting" color="#666" size="44rpx"></u-icon>
        </view>
      </view>
      <view class="second">
        <view class="options">
          <view class="selector" @tap="showFilter = true">
            <view class="icon">
              <image
                src="../../../static/7d163ad9-885d-47cb-a29e-043e5a9933ac.png"
                mode="aspectFit"
                class="img"
              ></image>
            </view>
            <view class="timeText">
              {{
                filterIndex !== null
                  ? filters[0][filterIndex]
                  : "请选择事件名称"
              }}
            </view>
          </view>
          <view class="selector" @tap="showStatus = true">
            <view class="icon">
              <image
                src="../../../static/5de7d537-e96d-4269-ad0a-684f3443643d.png"
                mode="aspectFit"
                class="img"
              ></image>
            </view>
            <view class="timeText">
              {{
                statusIndex !== null ? status[0][statusIndex] : "请选择警报级别"
              }}
            </view>
          </view>
        </view>
        <view class="icons" @click="reset">
          <u-icon 
            name="reload" 
            color="#007AFF" 
            size="44rpx" 
            :class="{ 'rotate-anim': isRefreshing }"
          ></u-icon>
        </view>
      </view>
      <scroll-view
        class="content"
        scroll-y="true"
        :scroll-top="scrollTop"
        :style="{ height: scrollHeight + 'px' }"
        @scrolltolower="getMore"
        @scroll="getTop"
      >
        <view
          class="box"
          v-for="(item, index) in choosen === 0 ? warnData : historyData"
          :key="item.id"
          @touchstart="startMove($event, item)"
          @touchmove="moving($event, item)"
          @touchend="stopMove($event, item)"
          :style="{ transform: 'translateX(' + item.moveX + 'px)' }"
        >
          <view class="details" :class="item.moveX === 0 ? 'bor' : ''" @tap.stop="openDetail(item)">
            <view class="deviceName">
              {{ item.name }}
            </view>
            <view class="happen">
              <view class="event">
                {{ item.eventName }}
              </view>
              <view v-for="l in item.level" :key="l" class="stars">
                <image src="../../../static/start.png" mode="aspectFit"></image>
              </view>
            </view>
            <view class="positonAndtime">
              <view class="time">
                {{ item.date }}
              </view>
              <view class="position">
                {{ item.department }}
              </view>
            </view>
            <view
              class="buttons"
              v-show="item.deal === '未处理'"
              @click="alert(index)"
            >
              <image src="../../../static/alert.png" mode="aspectFit"></image>
            </view>
            <view :class="item.deal === '已处理' ? 'isDealt' : 'unDealt'">
              <span>{{ item.deal }}</span>
              <view class="img">
                <image
                  :src="item.deal === '已处理' ? dealIcon[0] : dealIcon[1]"
                  mode="aspectFit"
                  class="image"
                ></image>
              </view>
            </view>
          </view>
          <view class="deleteBox">
            <view class="edit" @tap="check(index)">
              查看<image
                src="../../../static/watch.png"
                mode="aspectFit"
              ></image>
            </view>
            <view class="deal" @tap="deal(index)">
              处理<image
                src="../../../static/pencil.png"
                mode="aspectFit"
              ></image>
            </view>
            <view class="delete" @tap="deleteItem(index)" v-show="!choosen">
              删除<image
                src="../../../static/white-rubbish.png"
                mode="aspectFit"
              ></image>
            </view>
            <view class="finish" @tap="deleteItem(index)" v-show="choosen">
              完成<image
                src="../../../static/finish.png"
                mode="aspectFit"
              ></image>
            </view>
          </view>
        </view>
        <u-loadmore :status="statusList"></u-loadmore>
      </scroll-view>
      <u-modal
        style="position: absolute"
        :show="showDeal"
        :closeOnClickOverlay="true"
        @close="showDeal = false"
        @confirm="sendDeal"
        showCancelButton
        @cancel="showDeal = false"
        width="348px"
      >
        <edit
          v-if="showDeal"
          @getContent="setContent"
          :warnData="choosen === 0 ? warnData[index] : historyData[index]"
        ></edit>
      </u-modal>

      <!-- 弹窗选择器独立放置，避免父级 transform/relative 干扰定位 -->
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
    </view>
  </view>
</template>

<script>
import edit from "./components/edit.vue";
export default {
  components: {
    edit,
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
      status: [["1级", "2级", "3级"]],
      statusValue: [1, 2, 3],
      statusIndex: null,
      filters: [
        [
          "进入危险区域", "烟雾", "区域停留", "摔倒", "明火", 
          "吸烟", "打架斗殴", "垃圾乱放", "冰面", "电动车进楼", 
          "载具占用车道", "挥手呼救"
        ]
      ],
      filterValue: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      filterIndex: null,
      scrollHeight: 0,
      choosen: 0,
      pageSize: 6,
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
	  dataFetchInterval: null, // 定时器ID
	  isRefreshing: false, // 正在刷新状态
    };
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
		// 只有在查看实时警报时自动刷新
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
	buildTodayRange() {
	  const now = new Date();
	  const y = now.getFullYear();
	  const m = String(now.getMonth() + 1).padStart(2, "0");
	  const d = String(now.getDate()).padStart(2, "0");
	  return {
		startTime: `${y}-${m}-${d} 00:00:00`,
		endTime: `${y}-${m}-${d} 23:59:59`,
	  };
	},
	updateScrollHeight() {
	  const query = uni.createSelectorQuery().in(this);
	  query.select("#warnBox").boundingClientRect();
	  query.select(".content").boundingClientRect();
	  query.exec((res) => {
		const box = res && res[0];
		const content = res && res[1];
		if (!box || !content) return;
		const height = box.height - (content.top - box.top);
		this.scrollHeight = Math.max(220, height);
	  });
	},
	// startDataFetch() {
	// 	this.dataFetchInterval = setInterval(() => {

	// 	  const data = {
	// 		pageNum: this.pageNum,
	// 		pageSize: this.pageSize,
	// 		status: 0,
	// 	  };

	// 	  uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
	// 		  if(this.warnData1&&this.warnData1!=data.data.alarmList){
	// 			  this.warnData1 = data.data.alarmList;
	// 			  uni.showModal({
	// 			  	content: '您有一条报警新消息',
	// 			  	showCancel: false
	// 			  });
	// 			  this.getRealList()
	// 		  }
	// 	  });
	// 	}, 1000); // 每秒执行
	//   },
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
          const filteredList = data.data.alarmList.filter(item => item.caseType !== 13);
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
        const range = this.buildTodayRange();
        const data = {
          pageNum: this.pageNum,
          pageSize: this.pageSize,
          status: 0,
          startTime: range.startTime,
          endTime: range.endTime,
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
          const filteredList = data.data.alarmList.filter(item => item.caseType !== 13);
          this.warnData.push(...filteredList);
          if (data.data.count < this.pageSize) {
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
	  const range = this.buildTodayRange();
      const data = {
        pageNum: this.pageNum,
        pageSize: this.pageSize,
        status: 0,
        startTime: range.startTime,
        endTime: range.endTime,
      };
      if (this.caseType) {
        data.caseType = this.caseType;
      }
      if (this.warningLevel) {
        data.warningLevel = this.warningLevel;
      }
      uni.$http.get("/api/v1/alarm/query", data).then(({ data }) => {
        // console.log(data);
        this.warnData = data.data.alarmList.filter(item => item.caseType !== 13);
		if(!this.warnData.length) this.statusList = 'nomore'
        if (data.data.count < this.pageSize) {
          this.warnIsAll = true;
		  this.statusList = 'nomore'
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
        this.historyData = data.data.alarmList.filter(item => item.caseType !== 13);
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
    jump() {
      uni.navigateTo({
        url: "/pages/manage/personal/setting/setting",
      });
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
      } else {
        uni.switchTab({ url: "/pages/manage/controls/controls" });
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
      this.showDeal = true;
      this.resetX(index);
    },
    resetX(index) {
      if (this.choosen) {
        this.historyData[index].moveX = 0;
      } else this.warnData[index].moveX = 0;
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
    async sendDeal() {
      if (this.conten === "") {
        uni.showToast({
          title: "内容不能为空",
          duration: 2000,
          icon: "none",
        });
        return;
      }
      const data = {
        id: this.id,
        status: 1,
        processingContent: this.content,
      };
      await uni.$http.put("/api/v1/alarm/update", data).then(({ data }) => {
        // console.log(data);
        if (this.choosen) {
          this.getHistoryList();
        } else {
          this.getRealList();
        }
      });
      this.showDeal = false;
      this.content = "";
      this.id = null;
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
.warnBox {
  position: absolute;
  bottom: 0;
  padding: 20rpx 32rpx;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;

    .title {
      width: 100%;
      position: relative;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 16rpx;
      margin-bottom: 5rpx;
      padding-bottom: 0rpx;
      height: 100rpx;
    
    .topNav {
      display: flex;
      background: rgba(0, 122, 255, 0.05);
      padding: 6rpx;
      border-radius: 20rpx;
      gap: 4rpx;
      
      .left, .right {
        padding: 10rpx 28rpx;
        border-radius: 16rpx;
        transition: all 0.3s ease;
        cursor: pointer;

        span {
          font-size: 28rpx;
          color: rgba(26, 42, 58, 0.5);
          font-weight: 500;
        }
      }
      
      .choosen {
        background: #FFFFFF;
        box-shadow: 0 4rpx 12rpx rgba(0, 122, 255, 0.1);
        
        span {
          color: #007AFF !important;
          font-weight: 700;
        }
      }
    }
    
    .setting-btn {
      width: 60rpx;
      height: 60rpx;
      position: absolute;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(0, 0, 0, 0.05);
      backdrop-filter: blur(5px);
      -webkit-backdrop-filter: blur(5px);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
    }

    .back-btn {
      width: 60rpx;
      height: 60rpx;
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(255, 255, 255, 0.85);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 4rpx 12rpx rgba(0, 122, 255, 0.08);
      cursor: pointer;
    }

  }

  /* 筛选器区域：亮色玻璃感 */
  .second {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30rpx;
    
    .options {
      display: flex;
      gap: 20rpx;
      flex: 1;
      
      .selector {
        flex: 1;
        height: 80rpx;
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 122, 255, 0.1);
        border-radius: 20rpx;
        display: flex;
        align-items: center;
        padding: 0 20rpx;
        position: relative;
        
        .icon {
          width: 32rpx;
          height: 32rpx;
          margin-right: 12rpx;
          opacity: 0.6;
          display: flex;
          align-items: center;
          
          .img {
            width: 100%;
            height: 100%;
          }
        }
        
        .timeText {
          font-size: 26rpx;
          color: #1A2A3A;
          font-weight: 500;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
    }
    
    .icons {
      width: 80rpx;
      height: 80rpx;
      margin-left: 20rpx;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #FFFFFF;
      box-shadow: 0 4rpx 16rpx rgba(0, 122, 255, 0.1);
      border-radius: 20rpx;
      cursor: pointer;
      transition: all 0.3s ease;

      &:active {
        transform: scale(0.9);
      }

      .rotate-anim {
        animation: rotateReload 0.8s cubic-bezier(0.45, 0.05, 0.55, 0.95);
      }
    }
  }

  @keyframes rotateReload {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* 警报列表：呼吸感白玻璃卡片 */
  .content {
    flex: 1;
    width: 100%;
    padding: 0 16rpx;
    padding-top: 16rpx;
    padding-bottom: 120rpx; /* 紧贴 TabBar 上方，减少冗余留白 */
    box-sizing: border-box;
    
    .box {
      width: 100%;
      margin-bottom: 24rpx;
      position: relative;
      background: transparent;
      overflow: visible; /* 允许侧滑展开显示 */

      .details {
        width: 100%;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 1);
        border-radius: 40rpx;
        padding: 32rpx;
        box-sizing: border-box;
        box-shadow: 0 12rpx 48rpx rgba(26, 42, 58, 0.12);
        display: flex;
        flex-direction: column;
        gap: 16rpx;
        transition: all 0.3s ease;

        &.bor {
          /* 未移动状态的边角样式 */
        }

        .deviceName {
          color: rgba(26, 42, 58, 0.5);
          font-size: 24rpx;
          font-weight: 600;
          letter-spacing: 1rpx;
        }

        .happen {
          display: flex;
          align-items: center;
          gap: 12rpx;
          margin: 4rpx 0;
          
          .event {
            color: #1A2A3A;
            font-size: 40rpx;
            font-weight: 900;
          }
          
          .stars {
            display: flex;
            align-items: center;
            width: 32rpx;
            height: 32rpx;
            
            image {
              width: 100%;
              height: 100%;
            }
          }
        }

        .positonAndtime {
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          .time, .position {
            font-size: 24rpx;
            color: rgba(26, 42, 58, 0.6);
            font-weight: 500;
          }
        }

        /* 状态标记：精致小胶囊 */
        .isDealt, .unDealt {
          margin-top: 10rpx;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 8rpx;
          font-size: 24rpx;
          font-weight: bold;
          
          .img {
            width: 32rpx;
            height: 32rpx;
            
            .image {
              width: 100%;
              height: 100%;
            }
          }
        }
        
        .isDealt { color: #07C160; }
        .unDealt { color: #FA9D3B; }

        /* 电话报警按钮 */
        .buttons {
          position: absolute;
          top: 30rpx;
          right: 30rpx;
          width: 80rpx;
          height: 80rpx;
          background: rgba(255, 77, 77, 0.1);
          border-radius: 50%;
          display: flex;
          justify-content: center;
          align-items: center;
          
          image {
            width: 44rpx;
            height: 44rpx;
          }
        }
      }

      /* 侧滑操作区 */
      .deleteBox {
        border-radius: 0 32rpx 32rpx 0;
        overflow: hidden;
        height: 100%;
        width: 100px;
        display: flex;
        position: absolute;
        right: -100px;
        top: 0;
        z-index: -1; /* 初始隐藏在后面 */
        
        .edit, .deal, .finish, .delete {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: center;
          color: #fff;
          font-size: 28rpx;
          
          image {
            width: 40rpx;
            height: 40rpx;
          }
        }
        
        .edit { background: #007AFF; }
        .deal { background: #FA9D3B; }
        .finish { background: #07C160; }
        .delete { background: #FF4D4F; }
      }
    }
  }
}
</style>
