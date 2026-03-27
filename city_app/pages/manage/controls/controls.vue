<template>
  <view style="height: 100vh; width: 100vw; position: relative">
    <view class="main" :style="{ height: safeHeight + 'px', paddingTop: statusBarHeight + 'px' }" id="watchBox">
      <view class="header">
        <view class="topNav">
          <view
            class="left"
            :class="choosen === 1 ? 'choosen' : ''"
            @click="choosen = 1"
          >
            <span>监控位置</span>
          </view>
          <view
            class="right"
            :class="choosen === 2 ? 'choosen' : ''"
            @click="choosen = 2"
          >
            <span>监控列表</span>
          </view>
        </view>
        <view class="setting-btn" @click="jump">
          <u-icon name="setting" color="#666" size="44rpx"></u-icon>
        </view>
      </view>
      <MonitorMap v-show="choosen !== 2" :monitorList="warnData" />
      <scroll-view
        scroll-y="true"
        v-show="choosen === 2"
        class="content"
        :style="{ height: scrollHeight + 'px' }"
      >
        <view class="details" v-for="(item, index) in warnData" :key="item.id">
          <view class="deviceName">
            {{ item.name }}
          </view>
          <view class="positonAndtime">
            <view class="time"> 摄像头编号：{{ item.number }} </view>
            <view class="time"> 监控区域：{{ item.department }} </view>
            <view class="time"> 区域负责人：{{ item.leader }} </view>
          </view>
          <view class="buttons">
            <view class="button" @click="edit(index)">
              <image
                src="../../../static/edit.png"
                mode="aspectFit"
                style="height: 25px; width: 25px"
              ></image>
              <span style="color: #6787f9"> 编辑</span> </view
            >｜<view class="button" @click="editWorking(index)">
              <image
                :src="
                  !item.running
                    ? '../../../static/shutup.png'
                    : '../../../static/rubbish.png'
                "
                mode="aspectFit"
                style="height: 22px; width: 22px"
              ></image>
              <span :style="{ color: item.running ? '#FF5D5D' : '#6787F9' }">
                {{ item.running ? "停用" : "启用" }}</span
              >
            </view>
          </view>
          <view :class="item.deal === '正在运行' ? 'isDealt' : 'unDealt'">
            <span>{{ item.deal }}</span>
            <view class="img">
              <image
                :src="item.deal === '正在运行' ? dealIcon[0] : dealIcon[1]"
                mode="aspectFit"
                class="image"
              ></image>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
    <Edit
      :showEdit="showEdit"
      @change="changeShow"
      :warnData="warnData[index]"
      :monitorData="markersDetail[index]"
      v-if="showEdit"
    ></Edit>

  </view>
</template>

<script>
import Edit from "./components/edit.vue";
import MonitorMap from "./components/monitorMap.vue";
// import Map from "./components/map.vue"
export default {
  components: { Edit, MonitorMap },
  data() {
    return {
      showEdit: false,
      safeHeight: 0,
      statusBarHeight: 0,
      total: 0,
      working: 0,
      longitude: 0,
      latitude: 0,
      isShow: false,
      showDetail: false,
      index: 0,
      showDelete: false,
      choosen: 1,
      scrollHeight: 0,
      index: 0,
      markers: [],
      warnData: [],
      markersDetail: [],
      dealIcon: [
        "../../../static/20230910-194834.png",
        "../../../static/20230910-194949.png",
      ],
    };
  },
  methods: {
    async changeShow(bool) {
      // console.log("被触发了");
      if (bool) await this.getMonitor();
      this.showEdit = false;
    },
    jump() {
      uni.navigateTo({
        url: "/pages/manage/personal/setting/setting",
      });
    },
    test() {
      // console.log("hi");
      this.longitude = 116;
      this.latitude = 39;
    },
    edit(index) {
      this.index = index;
      this.showEdit = true;
    },
    async getMonitor() {
      await uni.$http.get("/api/v1/monitor").then(({ data }) => {
		console.log('data',data)
        this.warnData = data.data;
      });
    },
    async getMap() {
      await uni.$http.get("/api/v1/monitor/map").then(({ data }) => {
        const datas = data.data;
        console.log('map',datas);
        this.total = datas.total;
        this.working = datas.running;
        this.markersDetail = datas.monitorPosList;
        const markers = [];
        datas.monitorPosList.map((item) => {
          markers.push({
            id: item.id,
            latitude: item.latitude,
            longitude: item.longitude,
            iconPath: "../../../static/locate.png",
            width: 35,
            height: 35,
            title: item.name,
          });
        });
        this.markers = markers;
      });
    },
    showMarker(e) {
      const id = e.detail.markerId;
      // console.log(id);
      this.index = this.markersDetail.findIndex((item) => {
        return item.id === id;
      });
      this.showDetail = true;
    },
    editWorking(index) {
      const id = this.warnData[index].id;
      uni.showModal({
        showCancel: true,
        title: this.warnData[index].running
          ? "是否关闭摄像头？"
          : "是否启用摄像头？",
        success: async (res) => {
          if (res.confirm) {
            await uni.$http
              .post(`/api/v1/monitor/switch/${id}`)
              .then(({ data }) => {
                // console.log(data)
                if (data.code === "00000") {
                  this.getMonitor();
				  this.getMap();
                }
              });
          }
        },
      });
      // this.warnData[index].running = !this.warnData[index].running
    },
  },
  onLoad() {
    const info = uni.getWindowInfo();
    this.safeHeight = info.safeArea.height;
    this.statusBarHeight = info.statusBarHeight || 20;
    // console.log(this.safeHeight);
    const that = this;
    // this.$nextTick(() => {
    //   uni.getLocation({
    //     success: (res) => {
    //       that.longitude = res.longitude;
    //       that.latitude = res.latitude;
    //       setInterval(() => {
    //         let $map = uni.createMapContext("map1", that);
    //         let $appMap = $map.$getAppMap();
    //         $appMap.showUserLocation(true);
    //       }, 1000);
    //     },
    //   });
    // });
    let boxTop = 0;
    let headerHeight = 0;
    let boxHeight = 0;
    this.$nextTick(() => {
      const query = uni.createSelectorQuery().in(this);
      query
        .select("#watchBox")
        .boundingClientRect((data) => {
          // console.log("@", data);
          boxTop = data.top;
          boxHeight = data.height;
        })
        .exec();
      query
        .select(".header")
        .boundingClientRect((data) => {
          headerHeight = data.height;
          // console.log(data);
          that.scrollHeight = that.safeHeight - headerHeight - 12;
        })
        .exec();
      // console.log("hi");
    });
  },
  onShow(){
	  this.getMonitor();
  },
  watch:{
	  choosen:{
		  handler(newVal){
			  console.log(newVal)
			  if(newVal === 2){
				  this.getMonitor()
			  }
		  }
	  }
  }
};
</script>

<style lang="scss" scpoed>
.main {
  position: absolute;
  bottom: 0;
  // padding: 16rpx 32rpx;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-bottom: 0;
  // .alarmlist {
	 //  position: relative;
	 //  top: 25%;
  // }
  .map1 {
	position: absolute;
	// bottom: 0;
	height: 500px;
	width: 100%;
	top: 10%;
	background-color: pink;
  }
  .header {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20rpx;
    padding: 0 40rpx;
    box-sizing: border-box;
    height: 100rpx;
    z-index: 100;
    
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
      background: rgba(0, 0, 0, 0.05);
      backdrop-filter: blur(5px);
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
    }
  }
  .status {
    width: 85%;
    position: relative;
    top: 20rpx;
    left: 50%;
    transform: translate(-50%);
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 122, 255, 0.1);
    border-radius: 32rpx;
    color: #1A2A3A;
    display: flex;
    justify-content: space-around;
    padding: 10rpx 0;
    box-sizing: border-box;
    box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.05);
    z-index: 100;
  }
  .detail {

    margin: 0;
    padding: 24rpx;
    height: auto;
    width: 90%;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    display: flex;
    justify-content: space-between;
    border-radius: 32rpx;
    border: 1px solid rgba(255, 255, 255, 1);
    position: absolute;
    bottom: 24rpx;
    left: 50%;
    transform: translate(-50%);
    color: #1A2A3A;
    box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.15);
    .left {
      // width: 45%;
      // border: 2px solid blue;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
      align-items: flex-start;
      box-sizing: border-box;
      padding-left: 20rpx;
      .title {
        display: flex;
        align-items: center;
        justify-content: center;
        // border: 2px solid red;
        font-size: 32rpx;
        color: #1A2A3A;
        height: auto;
        font-weight: 700;
        margin-bottom: 12rpx;
      }
      .iconAndStatus {
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 100rpx;
        width: 240rpx;
        .icon {
          width: 100rpx;
          height: 100rpx;
          // border: 2px solid red;
          cover-image {
            width: 100%;
            height: 100%;
          }
        }
        .statuses {
          font-size: 0.8rem;
          width: 140rpx;
          height: 100rpx;
          line-height: 100rpx;
          font-weight: 700;
        }
        .running {
          color: #24f99a;
        }
        .stop {
          color: #f9b524;
        }
      }
    }
    .right {
      width: 55%;
      font-size: 24rpx;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: space-around;
      color: #6A7990;
      gap: 4rpx;
    }
  }
  .content {
    padding: 0 16rpx;
    padding-bottom: 120rpx; /* 紧贴 TabBar 上方 */
    box-sizing: border-box;
    flex: 1;
    .details {
      width: 100%;
      background: rgba(255, 255, 255, 0.82);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      margin-bottom: 30rpx;
      border-radius: 40rpx;
      border: 1px solid rgba(255, 255, 255, 1);
      padding: 32rpx;
      box-sizing: border-box;
      position: relative;
      box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.08);
      transition: all 0.3s ease;

      &:active {
        transform: scale(0.98);
      }

      .deviceName {
        color: #1A2A3A;
        font-size: 34rpx;
        font-weight: 700;
        margin-bottom: 20rpx;
        display: block;
      }
      .positonAndtime {
        display: flex;
        flex-direction: column;
        gap: 12rpx;
        margin-bottom: 30rpx;
        
        .time {
          font-size: 26rpx;
          color: #6A7990;
          font-weight: 500;
          display: flex;
          align-items: center;
          
          &::before {
            content: "";
            width: 8rpx;
            height: 8rpx;
            background: #007AFF;
            border-radius: 50%;
            margin-right: 12rpx;
            opacity: 0.5;
          }
        }
      }
      .buttons {
        display: flex;
        align-items: center;
        gap: 20rpx;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        padding-top: 24rpx;

        .button {
          display: flex;
          align-items: center;
          gap: 8rpx;
          padding: 8rpx 16rpx;
          border-radius: 12rpx;
          transition: background 0.2s;
          
          &:active {
            background: rgba(0, 122, 255, 0.05);
          }

          span {
            font-size: 26rpx;
            font-weight: 600;
          }
        }
      }
      .isDealt {
        position: absolute;
        top: 32rpx;
        right: 32rpx;
        color: #06bfa1;
        display: flex;
        align-items: center;
        background: rgba(6, 191, 161, 0.08);
        padding: 6rpx 16rpx;
        border-radius: 12rpx;
        font-size: 24rpx;

        .img {
          margin-left: 8rpx;
          width: 32rpx;
          height: 32rpx;
          .image {
            height: 100%;
            width: 100%;
          }
        }
      }
      .unDealt {
        position: absolute;
        top: 32rpx;
        right: 32rpx;
        color: #ff5d5d;
        display: flex;
        align-items: center;
        background: rgba(255, 93, 93, 0.08);
        padding: 6rpx 16rpx;
        border-radius: 12rpx;
        font-size: 24rpx;

        .img {
          margin-left: 8rpx;
          width: 32rpx;
          height: 32rpx;
          .image {
            height: 100%;
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
