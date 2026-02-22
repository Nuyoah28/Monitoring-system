<template>
  <div class="panel">
    <div class="chart-wrapper">
      <div class="chart" ref="piechart" id="demoDiv"></div>
      
      <!-- 自定义滚动图例 -->
      <div class="custom-legend" ref="legendDivRef" @mouseenter="stopScroll" @mouseleave="startScroll">
        <div class="scroll-content">
          <div v-for="(item, index) in scrollList" :key="'leg-' + index" class="legend-item" @click="toggleLegend(item.eventType)">
             <span class="legend-color" :style="{backgroundColor: getEchartsColor(index)}"></span>
             <span class="legend-name" :class="{ 'disabled-text': disabledLegends.includes(item.eventType) }">{{item.eventType}}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="panel-footer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import * as echarts from 'echarts';
import axios from 'axios';
import { useAlarmStore } from '@/stores/alarm';
import { storeToRefs } from 'pinia';

// 定义图表数据接口
interface ChartItem {
    eventType: string;
    eventCount: number;
}

const alarmStore = useAlarmStore();
const { getWeekStatistics } = storeToRefs(alarmStore);

const piechart = ref<HTMLDivElement>();
let mychart: any = null; // 保存echarts实例
const chartData = computed(() => getWeekStatistics.value);

// --- 自定义滚动图例相关 ---
const defaultColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#F8BD91', '#2CD6DB', '#C4D83B'];

const getEchartsColor = (index: number) => {
    if (!chartData.value || chartData.value.length === 0) return '#fff';
    const realIndex = index % chartData.value.length;
    return defaultColors[realIndex % defaultColors.length];
};

const legendDivRef = ref<HTMLElement | null>(null);
let scrollTimer: number | null = null;

const scrollList = computed(() => {
    if (!chartData.value || chartData.value.length === 0) return [];
    // 复制数据实现无缝滚动
    return [...chartData.value, ...chartData.value];
});

const startScroll = () => {
    if (scrollTimer) return;
    scrollTimer = window.setInterval(() => {
        if (legendDivRef.value) {
            legendDivRef.value.scrollTop += 1;
            if (legendDivRef.value.scrollTop >= legendDivRef.value.scrollHeight / 2) {
                legendDivRef.value.scrollTop = 0;
            }
        }
    }, 40);
};

const stopScroll = () => {
    if (scrollTimer) {
        clearInterval(scrollTimer);
        scrollTimer = null;
    }
};

const disabledLegends = ref<string[]>([]);
const toggleLegend = (name: string) => {
    if (!mychart) return;
    const idx = disabledLegends.value.indexOf(name);
    if (idx > -1) {
        disabledLegends.value.splice(idx, 1);
        mychart.dispatchAction({ type: 'legendSelect', name: name });
    } else {
        disabledLegends.value.push(name);
        mychart.dispatchAction({ type: 'legendUnSelect', name: name });
    }
};
// ----------------------


// 初始化图表
const initChart = (): void => {
    if(piechart.value) {
        mychart = echarts.init(piechart.value);

        // 设置初始的图表选项 (可以是空数据，稍后通过 axios 填充)
        mychart.setOption({
            color: defaultColors, // 锁定统一调色板以便图例取色
            title: {
                text: '近一周危险行为',
                textStyle: {
                    color: 'white',
                    fontSize: '1.5rem',
                },
            },
            tooltip: {
                trigger: 'item',
            },
            legend: {
                show: false, // 隐藏原生翻页图例，采用外置DOM滚动图例
            },
            series: [
                {
                    name: '危险警报',
                    type: 'pie',
                    radius: ['35%', '60%'], // 稍微缩减饼图半径给图例留空间
                    center: ['35%', '55%'], // 饼图向左靠一点点
                    avoidLabelOverlap: false,
                    padAngle: 6,
                    itemStyle: {
                        borderRadius: 10,
                    },
                    label: {
                        show: false,
                        position: 'center',
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '2rem',
                            fontWeight: 'bold',
                        },
                    },
                    labelLine: {
                        show: false,
                    },
                    data: [], // 初始时为空，后续会通过 axios 数据填充
                },
            ],
        });
    }
};

// 从Pinia获取数据
const fetchChartData = (): void => {
    // 直接从Pinia获取数据并更新图表
    updateChart(chartData.value);
};

// 更新图表
const updateChart = (data: ChartItem[]): void => {
    const processedData = data.map(item => ({
        value: item.eventCount, // 设定 y 轴的值
        name: item.eventType // 图例和 x 轴的名称
    }));

    if(mychart) {
        mychart.setOption({
            series: [
                {
                    data: processedData, // 将转换后的数据更新到图表中
                },
            ],
            legend: {
                data: data.map(item => item.eventType), // 更新图例为 eventType
            },
        });
    }
};

// 处理事件总线的回调函数
let alarmHandler: (() => void) | null = null;

onMounted(() => {
    // 初始化图表
    initChart();

    //测试使用，一会删了
    // updateChart(chartData.value);

    fetchChartData();
    
    // 监听数据变化，自动更新图表
    watch(chartData, (newData) => {
        updateChart(newData);
    }, { deep: true });
    
    // 启动自定义图例无缝滚动
    startScroll();

    // 获取事件总线实例
    const bus = (window as any).$bus;
    if(bus) {
        alarmHandler = () => {
            console.log('piechart1接收到报警信息，准备更新');
            
            fetchChartData();
        };
        bus.$on('alarm', alarmHandler);
    }

    // 监听窗口大小调整事件
    window.addEventListener("resize", () => {
        if(mychart) {
            mychart.resize();
        }
    });
});

onUnmounted(() => {
    // 移除事件监听
    const bus = (window as any).$bus;
    if(bus && alarmHandler) {
        bus.$off('alarm', alarmHandler);
    }
    
    // 销毁图表实例
    if(mychart) {
        mychart.dispose();
    }
    
    // 停止滚动图例
    stopScroll();
    
    // 移除窗口大小调整的监听事件
    window.removeEventListener("resize", () => {
        if(mychart) {
            mychart.resize();
        }
    });
});
</script>

<style scoped>
.chart-wrapper {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
}

#demoDiv {
  width: 65%;
  height: 100%;
}

.custom-legend {
  width: 35%;
  height: 70%;
  margin-top: 2rem;
  overflow: auto;
  color: white;
  box-sizing: border-box;
}

.custom-legend::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 0.8rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 8px;
  flex-shrink: 0;
}

.legend-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 1.1rem;
}

.disabled-text {
  color: #777;
  text-decoration: line-through;
}
</style>
