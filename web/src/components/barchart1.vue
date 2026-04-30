<template>
  <div class="bar-panel">
    <div class="chart" ref="barchart"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { useAlarmStore } from '@/stores/alarm'

interface ChartItem {
  eventType: string
  eventCount: number
}

const props = withDefaults(defineProps<{
  data?: ChartItem[]
  title?: string
  seriesName?: string
}>(), {
  data: undefined,
  title: '重点排行',
  seriesName: '数量',
})

const alarmStore = useAlarmStore()
const { getDayStatistics } = storeToRefs(alarmStore)
const barchart = ref<HTMLDivElement>()
let mychart: echarts.ECharts | null = null

const chartData = computed(() => props.data ?? getDayStatistics.value)
const normalizedData = computed(() => chartData.value.map(item => ({
  name: item.eventType || '未知类型',
  value: Number(item.eventCount || 0),
})))

const updateChart = (): void => {
  if (!mychart) return
  mychart.setOption({
    title: {
      text: props.title,
      textStyle: {
        color: '#eaf6ff',
        fontSize: 13,
        fontWeight: 600,
      },
      top: 2,
      left: 4,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      top: 34,
      bottom: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: normalizedData.value.map(item => item.name),
      axisLabel: {
        color: '#d6e6ff',
        fontSize: 10,
        interval: 0,
        rotate: normalizedData.value.length > 4 ? 24 : 0,
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
      splitLine: {
        lineStyle: { color: 'rgba(255, 255, 255, 0.1)' },
      },
    },
    series: [
      {
        name: props.seriesName,
        type: 'bar',
        data: normalizedData.value.map(item => item.value),
        colorBy: 'data',
        showBackground: true,
        backgroundStyle: { color: 'rgba(126, 197, 255, 0.08)' },
        itemStyle: { borderRadius: 8 },
        barWidth: '40%',
        barMaxWidth: 34,
      },
    ],
  })
}

const handleResize = (): void => {
  mychart?.resize()
}

let alarmHandler: (() => void) | null = null

onMounted(() => {
  if (barchart.value) {
    mychart = echarts.init(barchart.value)
    updateChart()
  }

  const bus = (window as any).$bus
  if (bus) {
    alarmHandler = updateChart
    bus.$on('alarm', alarmHandler)
  }

  window.addEventListener('resize', handleResize)
})

watch(chartData, updateChart, { deep: true })
watch(() => props.title, updateChart)
watch(() => props.seriesName, updateChart)

onUnmounted(() => {
  const bus = (window as any).$bus
  if (bus && alarmHandler) bus.$off('alarm', alarmHandler)
  mychart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.bar-panel {
  width: 100%;
  height: 100%;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
