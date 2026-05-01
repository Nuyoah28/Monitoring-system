<template>
	<view class="charts-box" ref="chart">
	    <qiun-data-charts
	    		class="mychart"
	      type="ring"
	      :opts="opts"
	      :chartData="chartData"
	      :canvas2d="true"
	      canvasId="WuTrqYCMnPwHxXPfqJkQyBBqgUGzcZuk"
	    />
	</view>
		
      
</template>
  
  <script>
  export default {
    data() {
      return {
        chartData:{},
        result:[],
        opts: {
          rotate: false,
          rotateLock: false,
          color: ["#1890FF","#91CB74","#FAC858","#EE6666","#73C0DE","#3CA272","#FC8452","#9A60B4","#ea7ccc","#f56c6c","#e6a23c","#67c23a"],
          padding: [0, 0, 0, 0], // 去除周围留白
          dataLabel: false, // 核心逻辑：关掉饼图外围的引线标签，让饼基本盘放大数倍！
          enableScroll: false,
          legend: {
            show: true,
            position: "right",
            lineHeight: 18,
            margin: 2,
            fontColor: "#1A2A3A"
          },
          title: {
            name: "",
            fontSize: 15,
            color: "#666666"
          },
          subtitle: {
            name: "",
            fontSize: 25,
            color: "#7cb5ec"
          },
          extra: {
            ring: {
              ringWidth: 35, // 圆环稍微加粗，增加视觉质感
              activeOpacity: 0.5,
              activeRadius: 10,
              offsetAngle: 0,
              labelWidth: 15,
              border: true,
              borderWidth: 2,
              borderColor: "white"
            }
          }
        }
      };
    },
    mounted() {

      this.$nextTick(() => {
		  setTimeout(() => {
			this.getServerData();
		  }, 800); // 延迟 800ms 确保元素渲染完毕
		});
		// this.getServerData();
		// this.$nextTick(() => {
		//         this.getServerData();
		//     });
    },
    onShow(){

      this.getServerData();
	  // this.$nextTick(() => {
	  //         this.getServerData();
	  //     });
    },
    methods: {
      async getData() {
        await uni.$http.get("/api/v1/alarm/realtime")
        .then(res => {
          if(res.data.code !== "00000") {
            uni.showToast({
              title: "获取图表数据失败",
              duration: 1500,
              icon: "none",
            })
          }
          else {
            const list = res.data.data.alarmCaseTypeTotalList || [];
            const getVal = (name) => {
                const item = list.find(i => i.caseTypeName === name);
                return item ? item.total : 0;
            };

            const targetNames = [
              '进入危险区域', '烟雾', '区域停留', '摔倒', '明火',
              '吸烟', '打架斗殴', '垃圾乱放', '电动车进楼',
              '载具占用车道', '挥手呼救'
            ];
            this.result = targetNames.map(name => {
                return { name: name, value: getVal(name) };
            }).filter(item => item.value > 0);
          }
        })
      },
      async getServerData() {
        let res = {
          series:[
            {
              data:[],
            }
          ]
        }
        await this.getData();
        res.series[0].data = this.result;
        // console.log('唤醒',res);
        setTimeout(() => {
          this.chartData = JSON.parse(JSON.stringify(res));
		  console.log('chart',this.chartData)
        }, 500);
		
      },
    }
  };
  </script>
  
 <style scoped>
   .charts-box {
     width: 100%;
     height: 100%; /* 确保有足够的高度来渲染图表 */
   }

</style>
