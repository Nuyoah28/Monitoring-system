<template>
  <div class="pie-panel">
    <div class="chart" ref="piechart" id="demoDiv"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import * as echarts from 'echarts';
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

const defaultColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#F8BD91', '#2CD6DB', '#C4D83B'];


// 初始化图表
const initChart = (): void => {
    if(piechart.value) {
        mychart = echarts.init(piechart.value);

        // 设置初始的图表选项 (可以是空数据，稍后通过 axios 填充)
        mychart.setOption({
            color: defaultColors, // 锁定统一调色板以便图例取色
            tooltip: {
                trigger: 'item',
            },
            legend: {
                show: true,
                top: 6,
                left: 6,
                itemWidth: 12,
                itemHeight: 12,
                textStyle: {
                    color: '#d6e6ff',
                    fontSize: 12,
                },
                formatter: (name: string) => name,
            },
            series: [
                {
                    name: '危险警报',
                    type: 'pie',
                    radius: ['50%', '65%'],
                    center: ['32%', '50%'],
                    avoidLabelOverlap: false,
                    padAngle: 7,
                    itemStyle: {
                        borderRadius: 14,
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
    const seen: Record<string, number> = {};
    data.forEach(item => {
        seen[item.eventType] = (seen[item.eventType] || 0) + item.eventCount;
    });

    const processedData = Object.entries(seen).map(([eventType, eventCount]) => ({
        value: eventCount,
        name: eventType,
    }));

    if(mychart) {
        mychart.setOption({
            series: [
                {
                    data: processedData,
                },
            ],
            legend: {
                data: processedData.map(item => item.name),
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
    const bus = (window as any).$bus;
    if(bus && alarmHandler) {
        bus.$off('alarm', alarmHandler);
    }
    
    if(mychart) {
        mychart.dispose();
    }
});
</script>

<style scoped>
.pie-panel {
  width: 100%;
  height: 100%;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
