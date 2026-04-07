<template>
  <div class="line-panel">
    <div class="chart" ref="linechart"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import * as echarts from 'echarts';
import { useAlarmStore } from '@/stores/alarm';
import { storeToRefs } from 'pinia';

const alarmStore = useAlarmStore();
const { getAlarmList } = storeToRefs(alarmStore);

const linechart = ref<HTMLDivElement>();
let mychart: any = null;

// 模拟趋势数据，按小时统计过去24小时的报警数量
const trendData = computed(() => {
  const now = new Date();
  const data = [];
  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
    const hourStr = hour.getHours().toString().padStart(2, '0') + ':00';
    // 模拟数据，实际应该从后端获取
    const count = Math.floor(Math.random() * 10) + 1;
    data.push({
      time: hourStr,
      count: count
    });
  }
  return data;
});

// 初始化图表
const initChart = (): void => {
  if (linechart.value) {
    mychart = echarts.init(linechart.value);

    mychart.setOption({
      color: ['#5470c6'],
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        top: '12%',
        bottom: '12%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trendData.value.map(item => item.time),
        axisLabel: {
          color: '#d6e6ff',
          fontSize: 10
        },
        axisLine: {
          lineStyle: {
            color: '#d0d0d0'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#d6e6ff',
          fontSize: 10
        },
        axisLine: {
          lineStyle: {
            color: '#d0d0d0'
          }
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.1)'
          }
        }
      },
      series: [
        {
          name: '报警数量',
          type: 'line',
          stack: 'Total',
          smooth: true,
          lineStyle: {
            width: 4
          },
          areaStyle: {
            opacity: 0.42
          },
          symbol: 'circle',
          symbolSize: 8,
          emphasis: {
            focus: 'series',
            itemStyle: {
              borderWidth: 2,
              borderColor: 'rgba(255,255,255,0.85)'
            }
          },
          data: trendData.value.map(item => item.count)
        }
      ]
    });
  }
};

// 更新图表
const updateChart = (): void => {
  if (mychart) {
    mychart.setOption({
      xAxis: {
        data: trendData.value.map(item => item.time)
      },
      series: [
        {
          data: trendData.value.map(item => item.count)
        }
      ]
    });
  }
};

// 窗口大小改变时调整图表大小
const handleResize = (): void => {
  if (mychart) {
    mychart.resize();
  }
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (mychart) {
    mychart.dispose();
  }
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.line-panel {
  width: 100%;
  height: 100%;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
