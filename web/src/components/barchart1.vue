<template>
    <div class="panel">
        <div class="chart" ref="barchart" id="demoDiv"></div>
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
const { getDayStatistics } = storeToRefs(alarmStore);

const barchart = ref<HTMLDivElement>();
let mychart: any = null; // 保存echarts实例
const chartData = computed(() => getDayStatistics.value);

// 初始化图表
const initChart = (): void => {
    if(barchart.value) {
        mychart = echarts.init(barchart.value);
        mychart.setOption({
            title: {
                text: '今日危险事件统计',
                textStyle: {
                    color: 'white',
                    fontSize: '1.5rem',
                },
            },
            tooltip: {
                trigger: 'axis',
                // trigger:'item',
                axisPointer: {
                    type: 'cross',
                },
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '8%', // 增加底部空间放文字
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: [],
                axisLabel: {
                    color: 'white',
                    fontSize: '0.9rem', // 稍微变小
                    interval: 0,
                    rotate: 25, // 旋转标签，防止文字堆叠在一起
                },
            },
            yAxis: {
                type: 'value',
                minInterval: 1, // 确保刻度为整数
                name: '单位：次', // 添加单位
                nameTextStyle: {
                    color: 'white',
                    fontSize: '1rem',
                    padding: [0, 0, 0, 10] // name 的位置微调
                },
                axisLabel: {
                    color: 'white',
                    fontSize: '1rem',
                },
            },
            series: [
                {
                    name: ['数量'],
                    type: 'bar',
                    data: [],
                    colorBy: 'data',
                    showBackground: true,
                    itemStyle: {
                        borderRadius: 8,
                    },
                    barWidth: '40%', // 改为相对比例
                    barMaxWidth: 35, // 限制最大宽度
                },
            ],
            
        });

        // 添加窗口大小改变的监听事件
        window.addEventListener('resize', () => {
            if(mychart) {
                mychart.resize();
            }
        });
    }
};

// 从Pinia获取数据
const fetchData = (): void => {
    // 直接从Pinia获取数据并更新图表
    updateChart(chartData.value);
};

// 更新图表
const updateChart = (data: ChartItem[]): void => {
    console.log('更新图表', data);
    
    const processedData = data.map(item => ({
        value: item.eventCount, // 设定 y 轴的值
        name: item.eventType // 图例和 x 轴的名称
    }));

    // console.log('chartData',processedData);              

    if(mychart) {
        mychart.setOption({
            series: [
                {
                    data: processedData, // 将转换后的数据更新到图表中
                },
            ],
            xAxis: {
                data: data.map(item => item.eventType)
            },
        });
    }
};

// 处理事件总线的回调函数
let alarmHandler: (() => void) | null = null;

onMounted(() => {
    initChart(); // 初始化图表
    
    //测试，截图使用，一会删了
    // updateChart(chartData.value);

    fetchData(); // 首次获取数据
    
    // 监听数据变化，自动更新图表
    watch(chartData, (newData) => {
        updateChart(newData);
    }, { deep: true });
    
    // 获取事件总线实例
    const bus = (window as any).$bus;
    if(bus) {
        alarmHandler = () => {
            console.log('barchart1接收到报警信息，准备更新');
            fetchData(); // 获取数据
        };
        bus.$on('alarm', alarmHandler);
    }
});

onUnmounted(() => {
    console.log('即将销毁');
    
    // 移除事件监听
    const bus = (window as any).$bus;
    if(bus && alarmHandler) {
        bus.$off('alarm', alarmHandler);
    }
    
    // 销毁图表实例
    if(mychart) {
        mychart.dispose();
    }
    
    // 移除窗口大小改变的监听事件
    window.removeEventListener('resize', () => {
        if(mychart) {
            mychart.resize();
        }
    });
});
</script>

<style scoped lang="less">
    #demoDiv {
        width: 32rem;
        height: 19rem;
    }
</style>
