<template>
  <div class="line-panel">
    <div class="chart" ref="linechart"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface TrendPoint {
  label: string
  value: number
}

const props = withDefaults(defineProps<{
  points?: TrendPoint[]
  seriesName?: string
}>(), {
  points: () => [],
  seriesName: '报警数量',
})

const linechart = ref<HTMLDivElement>()
let mychart: echarts.ECharts | null = null

const chartPoints = computed(() => props.points || [])

const buildOption = () => ({
  color: ['#63b8ff'],
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'line',
      lineStyle: { color: 'rgba(126, 197, 255, 0.45)' },
    },
  },
  grid: {
    left: '3%',
    right: '4%',
    top: '12%',
    bottom: '12%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: chartPoints.value.map(item => item.label),
    axisLabel: {
      color: '#d6e6ff',
      fontSize: 10,
    },
    axisLine: {
      lineStyle: { color: 'rgba(214, 230, 255, 0.28)' },
    },
  },
  yAxis: {
    type: 'value',
    minInterval: 1,
    axisLabel: {
      color: '#d6e6ff',
      fontSize: 10,
    },
    axisLine: {
      lineStyle: { color: 'rgba(214, 230, 255, 0.28)' },
    },
    splitLine: {
      lineStyle: { color: 'rgba(255, 255, 255, 0.1)' },
    },
  },
  series: [
    {
      name: props.seriesName,
      type: 'line',
      smooth: true,
      lineStyle: { width: 3 },
      areaStyle: { opacity: 0.28 },
      symbol: 'circle',
      symbolSize: 7,
      emphasis: {
        focus: 'series',
        itemStyle: {
          borderWidth: 2,
          borderColor: 'rgba(255,255,255,0.85)',
        },
      },
      data: chartPoints.value.map(item => item.value),
    },
  ],
})

const updateChart = (): void => {
  if (!mychart) return
  mychart.setOption(buildOption())
}

const handleResize = (): void => {
  mychart?.resize()
}

onMounted(() => {
  if (linechart.value) {
    mychart = echarts.init(linechart.value)
    updateChart()
  }
  window.addEventListener('resize', handleResize)
})

watch(chartPoints, updateChart, { deep: true })
watch(() => props.seriesName, updateChart)

onUnmounted(() => {
  mychart?.dispose()
  window.removeEventListener('resize', handleResize)
})
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
