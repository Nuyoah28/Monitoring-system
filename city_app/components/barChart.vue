<template>
  <view class="charts-box">
    <qiun-data-charts
      type="radar"
      :opts="opts"
      :chartData="chartData"
      :canvas2d="true"
      canvasId="alarmCaseTypeBarChart"
    />
  </view>
</template>

<script>
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
      chartData: {},
      opts: {
        color: ["#1890FF"],
        padding: [12, 12, 12, 12],
        enableScroll: false,
        legend: {
          show: true,
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
            gridColor: "rgba(0, 0, 0, 0.08)",
            gridCount: 4,
            opacity: 0.2,
            border: true,
            borderWidth: 2,
            linearType: "custom"
          }
        }
      }
    };
  },
  methods: {
    formatGraphData(graph3) {
      if (!Array.isArray(graph3)) {
        return [];
      }
      return graph3
        .map(item => ({
          name: item.period || "",
          cnt: Number(item.cnt || 0)
        }))
        .sort((a, b) => b.cnt - a.cnt);
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
        const rankedData = this.formatGraphData(graph3);
        this.result = {
          name: rankedData.map(item => item.name),
          data: rankedData.map(item => item.cnt)
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
      const res = {
        categories: this.result.name,
        series: [
          {
            name: "报警类型数量",
            data: this.result.data
          }
        ]
      };
      this.chartData = JSON.parse(JSON.stringify(res));
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
}
</style>
