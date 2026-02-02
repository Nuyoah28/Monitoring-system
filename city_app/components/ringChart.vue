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
          color: ["#1890FF","#91CB74","#FAC858","#EE6666","#73C0DE","#3CA272","#FC8452","#9A60B4","#ea7ccc"],
          padding: [5,5,5,5],
          dataLabel: true,
          enableScroll: false,
          legend: {
            show: true,
            position: "right",
            lineHeight: 25
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
              ringWidth: 30,
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

            this.result = [
              { name: '进入危险区域', value: getVal('进入危险区域') },
              { name: '区域停留', value: getVal('区域停留') },
              { name: '烟雾', value: getVal('烟雾') },
              { name: '摔倒', value: getVal('摔倒') },
              { name: '明火', value: getVal('明火') },
              { name: '吸烟', value: getVal('吸烟') },
              { name: '打架斗殴', value: getVal('打架斗殴') }
            ].filter(item => item.value > 0); // 只显示有数据的项，或者保留全部
            
            const targetNames = ['进入危险区域', '烟雾', '打架斗殴', '摔倒', '明火', '吸烟'];
            this.result = targetNames.map(name => {
                return { name: name, value: getVal(name) };
            });
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

    