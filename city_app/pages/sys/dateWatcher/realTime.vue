<template>
  <view class="body">
    <!-- 顶部数据总览：赛博清晨明亮玻璃面板 -->
    <view class="total">
      <view class="item">
        <view class="label">今日报警数</view>
        <view class="num highlight">{{ upTotal.todayNew || 0 }}</view>
      </view>
      <view class="item">
        <view class="label">总报警数</view>
        <view class="num">{{ upTotal.total || 0 }}</view>
      </view>
      <view class="item">
        <view class="label">较昨日变化</view>
        <view class="num">{{ upTotal.dayChange || 0 }}</view>
      </view>
    </view>
    
    <!-- 中间图表区：保持透明通透 -->
    <view class="chart-section">
      <ring-chart></ring-chart>
    </view>
    
    <!-- 12宫格列表：白璃拟态卡片 -->
    <scroll-view scroll-y="true" class="list-scroll">
      <view class="grid-layout">
        <view 
          v-for="(cat, index) in categoryConfigs" 
          :key="index"
          class="cat-card"
        >
          <view class="icon-box" :style="{ backgroundColor: cat.iconBg }">
            <image :src="'../../../static/' + cat.iconImg" mode="aspectFit"></image>
          </view>
          <view class="info">
            <view class="name">{{ cat.name }}</view>
            <view class="stats">
              <text class="val">{{ getData(cat.name).total }}</text>
              <text class="unit">次</text>
            </view>
            <view class="trend">
              今日 <text class="plus">+{{ getData(cat.name).todayNew }}</text>
            </view>
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
        { name: '进入危险区域', iconImg: 'alarm.png', iconBg: 'rgba(76, 217, 100, 0.1)' },
        { name: '烟雾', iconImg: 'fuck.png', iconBg: 'rgba(0, 210, 255, 0.1)' },
        { name: '区域停留', iconImg: 'watch.png', iconBg: 'rgba(84, 130, 53, 0.1)' },
        { name: '摔倒', iconImg: 'fall.png', iconBg: 'rgba(255, 152, 0, 0.1)' },
        { name: '明火', iconImg: 'fire.png', iconBg: 'rgba(244, 67, 54, 0.1)' },
        { name: '吸烟', iconImg: 'smoke.png', iconBg: 'rgba(233, 30, 99, 0.1)' },
        { name: '打架斗殴', iconImg: 'fist.png', iconBg: 'rgba(255, 193, 7, 0.1)' },
        { name: '垃圾乱放', iconImg: 'white-rubbish.png', iconBg: 'rgba(96, 125, 139, 0.1)' },
        { name: '冰面', iconImg: 'analysis.png', iconBg: 'rgba(33, 150, 243, 0.1)' },
        { name: '载具占用车道', iconImg: 'alert.png', iconBg: 'rgba(233, 30, 99, 0.1)' },
        { name: '电动车进楼', iconImg: 'alert.png', iconBg: 'rgba(255, 193, 7, 0.1)' },
        { name: '挥手呼救', iconImg: 'fuck.png', iconBg: 'rgba(156, 39, 176, 0.1)' }
      ]
    };
  },
  methods: {
    getInfo() {
      uni.$http.get("/api/v1/alarm/realtime").then((res) => {
        if (res.data.code === "D0400") {
          uni.showToast({ title: "登录失效，请重新登录！", icon: "none" });
          uni.removeStorage({
            key: "token",
            success: () => uni.reLaunch({ url: "/pages/manage/login/index" }),
          });
        }
        if (res.data.code === "00000") {
          this.upTotal = res.data.data.alarmTotal || {};	
          this.caseList = res.data.data.alarmCaseTypeTotalList || [];
        }
      });
    },
    getData(name) {
      if (!this.caseList) return { total: 0, todayNew: 0 };
      const item = this.caseList.find(item => item.caseTypeName === name);
      return item ? item : { total: 0, todayNew: 0 };
    }
  },
  mounted() { this.getInfo(); },
  onShow() { this.getInfo(); },
};
</script>

<style lang="scss" scoped>
.body {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding-top: 20rpx;
  background: transparent; /* 承接父级的浅色渐变 */
}

.total {
  width: 92%;
  margin: 0 auto 30rpx auto;
  padding: 40rpx 0;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 32rpx;
  box-shadow: 0 16rpx 40rpx rgba(100, 150, 200, 0.1);
  display: flex;
  justify-content: space-around;
  flex-shrink: 0;

  .item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;

    .label {
      font-size: 24rpx;
      color: rgba(26, 42, 58, 0.5);
      margin-bottom: 12rpx;
    }

    .num {
      font-size: 48rpx;
      font-weight: 800;
      color: #1A2A3A;
      
      &.highlight {
        color: #007AFF;
      }
    }
  }
}

.chart-section {
  width: 92%;
  height: 300rpx;
  margin: 0 auto 30rpx auto;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 32rpx;
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.list-scroll {
  flex: 1;
  min-height: 0;
  width: 100%;

  .grid-layout {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    padding: 10rpx 4% 40rpx 4%;
  }
}

.cat-card {
  width: 48.5%;
  height: 200rpx;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 28rpx;
  border: 1px solid rgba(255, 255, 255, 0.4);
  margin-bottom: 24rpx;
  display: flex;
  align-items: center;
  padding: 0 24rpx;
  box-sizing: border-box;
  box-shadow: 0 8rpx 24rpx rgba(150, 180, 210, 0.05);
  transition: all 0.2s;

  &:active {
    transform: scale(0.97);
    background: rgba(255, 255, 255, 0.9);
  }

  .icon-box {
    width: 80rpx;
    height: 80rpx;
    border-radius: 20rpx;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 20rpx;
    flex-shrink: 0;

    image {
      width: 60%;
      height: 60%;
      filter: drop-shadow(0 2rpx 4rpx rgba(0,0,0,0.05));
    }
  }

  .info {
    flex: 1;
    overflow: hidden;

    .name {
      font-size: 26rpx;
      font-weight: 600;
      color: #1A2A3A;
      margin-bottom: 6rpx;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .stats {
      margin-bottom: 4rpx;
      .val {
        font-size: 34rpx;
        font-weight: 700;
        color: #1A2A3A;
      }
      .unit {
        font-size: 20rpx;
        color: rgba(26, 42, 58, 0.4);
        margin-left: 4rpx;
      }
    }

    .trend {
      font-size: 22rpx;
      color: rgba(26, 42, 58, 0.5);
      
      .plus {
        color: #007AFF;
        font-weight: 600;
      }
    }
  }
}
</style>
