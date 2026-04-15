<template>
    <view class="charts-box">
      <qiun-data-charts 
        type="radar"
        :opts="opts"
        :chartData="chartData"
        :canvas2d="true"
        canvasId="tyaNrdVFWiyYPbHnUdTKToUdjvIIkrAf"
      />
    </view>
  </template>
  
  <script>
  export default {
  props: {
    range: {
      required: true ,
      type: Number
    }
  },
    data() {
      return {
        result: {},
        chartData: {},
        opts: {
          color: ["#00d2ff","#007aff","#FAC858","#EE6666","#73C0DE","#3CA272","#FC8452","#9A60B4","#ea7ccc"],
          padding: [5,5,5,5],
          fontColor: "#FFFFFF",
          dataLabel: false, /* 雷达图一般关掉数据标签防止拥挤 */
          legend: {
            show: true,
            position: "right",
            lineHeight: 25,
            fontColor: "#1A2A3A"
          },
          xAxis: {
            show: true,
            textColor: "#1A2A3A"
          },
          extra: {
            radar: {
              gridType: "radar",
              gridColor: "rgba(0,0,0,0.1)",
              gridCount: 3,
              opacity: 0.3, /* 增加一点透明度以在亮色背景下更清晰 */
              max: 0,
              radius: 50,
              labelColor: "#1A2A3A" /* 切换为深色分类文字 */
            }
          }
        }
      };
    },
    mounted() {
      // 依赖 watch 的 immediate: true 进行初次加载，移除这里的重复调用
    },
    onShow() {
      // 页面展示刷新逻辑
    },
    methods: {
      async getData(range) {
        let data = {
          defer: range
        }
        await uni.$http.get("/api/v1/alarm/query/cnt/history" , data)
        .then(res => {
          if(res.data.code !== "00000") {
            uni.showToast({
              title: "获取图表数据失败",
              duration: 1500,
              icon: "none",
            })
          }
          else {
            let temp = {
              name:[],
              data:[]
            }
            res.data.data.graph3.forEach(item => {
              temp.name.push(item.period);
              temp.data.push(item.cnt);
            });
            this.result = temp;
          }
        })
      },
      async getServerData(range) {
        let res = {
          categories: [],
          series: [
            {
              name: "各事件发生数量",
              data: []
            },
          ]
        };
        await this.getData(range);
        res.categories = this.result.name;
        res.series[0].data = this.result.data;
        setTimeout(() => {
          this.chartData = JSON.parse(JSON.stringify(res));
        }, 500);
      },
    },
    watch: {
      range: {
        handler: function(newVal) {
          if (newVal) {
            this.getServerData(newVal);
          }
        },
        immediate: true,
      }
    }
  };
  </script>
  
  <style scoped>
    /* 请根据实际需求修改父元素尺寸，组件自动识别宽高 */
    .charts-box {
      width: 100%;
      /* height: 300px; */
      height: 100%;
    }
  </style>