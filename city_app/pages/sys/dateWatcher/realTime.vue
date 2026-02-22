<template>
  <view class="body">
    <view class="total">
      <view class="left">
        <span>今日报警数：{{ upTotal.todayNew }}</span>
        <span>总报警数：{{ upTotal.total }}</span>
        <span>较昨日变化：{{ upTotal.dayChange }}</span>
      </view>
      <view class="right">
        <image
          src="../../../static/analysis.png"
          mode="aspectFit"
          alt=""
        ></image>
      </view>
    </view>
    <view class="chart">
      <ring-chart></ring-chart>
    </view>
    <scroll-view scroll-y="true" class="category-scroll">
      <view class="category">
        <view 
          v-for="(cat, index) in categoryConfigs" 
          :key="index"
          class="cat-block"
          :style="{ backgroundColor: cat.bg }"
        >
          <view class="title">
            <view class="icon">
              <!-- 为了防止不同大小的图标拉伸，使用 aspectFit; 注意：打包时可能会遇到静态资源路径动态拼接的问题，安全起见可以用 require 计算 -->
              <image :src="'../../../static/' + cat.icon" mode="aspectFit"></image>
            </view>
            <view class="titleText" :style="{ color: cat.color }">{{ cat.name }}</view>
          </view>
          <view class="text">
            <span>总事件数：{{ getData(cat.name).total }}</span>
            <span>今日新增：{{ getData(cat.name).todayNew }}</span>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import ringChart from "../../../components/ringChart.vue";
export default {
  components: { ringChart },
  data() {
    return {
      upTotal: {},
      caseList: [],
      categoryConfigs: [
        { name: '进入危险区域', icon: 'alarm.png', bg: '#d6f6db', color: '#42a852' },
        { name: '烟雾', icon: 'fuck.png', bg: '#dbfdf7', color: '#1db095' },
        { name: '区域停留', icon: 'watch.png', bg: '#e2f0d9', color: '#548235' },
        { name: '摔倒', icon: 'fall.png', bg: '#ffe3c2', color: '#d79547' },
        { name: '明火', icon: 'fire.png', bg: '#e7e3fe', color: '#9c8eee' },
        { name: '吸烟', icon: 'smoke.png', bg: '#ffd9d9', color: '#c47a7a' },
        { name: '打架斗殴', icon: 'fist.png', bg: '#f5f6cc', color: '#a89f42' },
        { name: '垃圾乱放', icon: 'rubbish.png', bg: '#e0ece4', color: '#7a9e9f' },
        { name: '冰面', icon: 'analysis.png', bg: '#e3f2fd', color: '#1565c0' },
        { name: '载具占用车道', icon: 'alert.png', bg: '#fce4ec', color: '#c2185b' },
        { name: '电动车进楼', icon: 'alert.png', bg: '#fff0e5', color: '#f58220' },
        { name: '挥手呼救', icon: 'fist.png', bg: '#f3e5f5', color: '#6a1b9a' }
      ]
    };
  },
  methods: {
    getInfo() {
      uni.$http.get("/api/v1/alarm/realtime").then((res) => {
		  // console.log('res',res.data);
        if (res.data.code === "D0400") {
          uni.showToast({
            title: "登录失效，请重新登录！",
            duration: 1500,
            icon: "none",
          });
          uni.removeStorage({
            key: "token",
            success: () => {
              uni.reLaunch({
                url: "/pages/sys/login/index",
              });
            },
          });
        }
        if (res.data.code != "00000") {
          uni.showToast({
            title: "数据加载失败！",
            duration: 1500,
            icon: "none",
          });
        }
        if (res.data.code === "00000") {
		  console.log('res.data.data',res.data.data)
          this.upTotal = res.data.data.alarmTotal;	
		  // console.log('res.data.data.alarmCaseTypeTotalList',res.data.data.alarmCaseTypeTotalList[0].total)
          this.caseList = res.data.data.alarmCaseTypeTotalList;
		  console.log('caseList',this.caseList);
        }
      });
    },
    getData(name) {
      if (!this.caseList) return { total: 0, todayNew: 0 };
      const item = this.caseList.find(item => item.caseTypeName === name);
      return item ? item : { total: 0, todayNew: 0 };
    }
  },
  mounted() {
    this.getInfo();
  },
  onShow() {
    this.getInfo();
  },
};
</script>

<style lang="scss" scoped>
.body {
  height: 95%;
  // border: 2px solid green;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-around;
  // margin-bottom: 20rpx;
  .total {
    // background-color: #7BBAF5;
    background-image: linear-gradient(to right, #4d87ef, #99dcf9);
    width: 99%;
    height: 16%;
    border-radius: 15rpx;
    display: flex;
    align-items: center;
    justify-content: space-around;
    .left {
      // border: 2px solid red;
      width: 70%;
      height: 80%;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: space-around;
      span {
        color: white;
        font-weight: 600;
        font-size: 15px;
      }
    }
    .right {
      // border: 2px solid red;
      width: 100rpx;
      height: 100rpx;
      image {
        width: 100%;
        height: 100%;
      }
    }
  }
  .chart {
    // border: 2px solid red;
    background-color: #e1edf6;
    width: 99%;
    height: 28%;
	// width: 200px;
    height: 400rpx;
    border-radius: 15rpx;
	// background-color: pink;
  }
  .category-scroll {
    width: 99%;
    height: 51%;
  }
  .category {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    padding-bottom: 20rpx; /* 给滚动留点空间 */
    
    .cat-block {
      width: 48%;
      height: 220rpx; /* 将相对高度改为绝对高度，使得滚动生效 */
      border-radius: 15rpx;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      margin-bottom: 15rpx;

      .title {
        margin-left: 5%;
        margin-top: 15rpx;
        margin-bottom: 10rpx;
        width: 80%;
        height: 60rpx;
        display: flex;
        justify-content: space-around;
        align-items: center;
        .icon {
          width: 35%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border-radius: 15rpx;
          image {
            width: 80%;
            height: 80%;
          }
        }
        .titleText {
          margin-left: 20rpx;
          width: 65%;
          font-size: 34rpx; /* 稍微调小以防字数超长 */
          font-weight: 700;
          white-space: nowrap;
        }
      }
      .text {
        margin-left: 5%;
        width: 80%;
        display: flex;
        flex-direction: column;
        span {
          font-size: 30rpx;
          font-weight: 700;
          margin-top: 5rpx;
        }
      }
    }
  }
}
</style>
