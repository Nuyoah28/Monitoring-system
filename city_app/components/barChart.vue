<template>
  <view class="charts-box">
    <qiun-data-charts
      v-if="!isEmpty"
      type="radar"
      :opts="opts"
      :chartData="chartData"
      :canvas2d="true"
      canvasId="alarmCaseTypeBarChart"
    />
    <view v-else class="empty-state">
      <text class="empty-title">暂无报警类型分布</text>
      <text class="empty-desc">当前时间跨度内没有有效报警数据</text>
    </view>
  </view>
</template>

<script>
const DEPRECATED_CASE_TYPES = ["冰面", "结冰", "路面积冰"];
const CASE_TYPE_ORDER = [
  "进入危险区域",
  "烟雾",
  "区域停留",
  "摔倒",
  "明火",
  "吸烟",
  "打架斗殴",
  "打架",
  "垃圾乱放",
  "电动车进楼",
  "载具占用车道",
  "挥手呼救"
];
const CASE_TYPE_LABELS = {
  "进入危险区域": "危险区",
  "区域停留": "停留",
  "打架斗殴": "打架",
  "垃圾乱放": "垃圾",
  "电动车进楼": "电动车",
  "载具占用车道": "占车道",
  "挥手呼救": "挥手"
};

export default {
  props: {
    range: {
      required: true,
      type: Number
    }
  },
  data() {
    return {
      result: {
        name: [],
        data: []
      },
      isEmpty: true,
      chartData: {},
      opts: {
        color: ["#0F86FF"],
        padding: [8, 8, 8, 8],
        enableScroll: false,
        fontSize: 11,
        fontColor: "#425466",
        legend: {
          show: false,
          position: "bottom",
          fontColor: "#1A2A3A"
        },
        yAxis: {
          fontColor: "#1A2A3A",
          gridColor: "rgba(0, 0, 0, 0.05)"
        },
        extra: {
          radar: {
            gridType: "radar",
            gridColor: "rgba(15, 134, 255, 0.14)",
            gridCount: 4,
            opacity: 0.28,
            max: 1,
            border: true,
            borderWidth: 2,
            linearType: "custom",
            labelShow: true,
            labelColor: "#425466",
            labelPointShow: true,
            labelPointRadius: 2,
            labelPointColor: "#9CCBFF"
          }
        }
      }
    };
  },
  methods: {
    getTypeName(item) {
      return String(
        item.period ||
        item.caseTypeName ||
        item.name ||
        item.typeName ||
        ""
      ).trim();
    },
    getTypeCount(item) {
      return Number(item.cnt || item.total || item.count || item.value || 0);
    },
    isDeprecatedType(name) {
      return DEPRECATED_CASE_TYPES.some(type => name.includes(type));
    },
    getDisplayName(name) {
      return CASE_TYPE_LABELS[name] || name;
    },
    formatGraphData(graph3) {
      if (!Array.isArray(graph3)) {
        return [];
      }

      const countMap = {};
      graph3.forEach(item => {
        const name = this.getTypeName(item);
        if (!name || this.isDeprecatedType(name)) return;
        countMap[name] = (countMap[name] || 0) + this.getTypeCount(item);
      });

      const orderedNames = CASE_TYPE_ORDER.filter(name => Object.prototype.hasOwnProperty.call(countMap, name));
      const extraNames = Object.keys(countMap)
        .filter(name => !CASE_TYPE_ORDER.includes(name))
        .sort((a, b) => countMap[b] - countMap[a]);

      return [...orderedNames, ...extraNames].map(name => ({
        name: this.getDisplayName(name),
        cnt: countMap[name]
      }));
    },
    async getData(range) {
      const data = {
        defer: range
      };
      try {
        const res = await uni.$http.get("/api/v1/alarm/query/cnt/history", data);
        if (res.data.code !== "00000") {
          uni.showToast({
            title: "获取图表数据失败",
            duration: 1500,
            icon: "none"
          });
          return;
        }

        const graph3 = res.data.data && res.data.data.graph3 ? res.data.data.graph3 : [];
        const radarData = this.formatGraphData(graph3);
        this.result = {
          name: radarData.map(item => item.name),
          data: radarData.map(item => item.cnt)
        };
      } catch (err) {
        console.error("barChart GET Error:", err);
        uni.showToast({
          title: "网络请求异常",
          duration: 1500,
          icon: "none"
        });
      }
    },
    async getServerData(range) {
      await this.getData(range);
      const maxCount = Math.max(...this.result.data, 0);
      this.isEmpty = !this.result.name.length || maxCount <= 0;
      this.opts = {
        ...this.opts,
        extra: {
          ...this.opts.extra,
          radar: {
            ...this.opts.extra.radar,
            max: Math.max(1, Math.ceil(maxCount * 1.2))
          }
        }
      };

      const res = {
        categories: this.result.name,
        series: [
          {
            name: "报警类型数量",
            data: this.result.data
          }
        ]
      };
      this.chartData = this.isEmpty ? {} : JSON.parse(JSON.stringify(res));
    }
  },
  watch: {
    range: {
      handler(newVal) {
        if (newVal) {
          this.getServerData(newVal);
        }
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.charts-box {
  width: 100%;
  height: 100%;
  position: relative;
}

.empty-state {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(15, 134, 255, 0.08), rgba(0, 210, 255, 0.04));
  border: 1px dashed rgba(15, 134, 255, 0.24);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #1A2A3A;
}

.empty-desc {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #6B7A90;
}
</style>
