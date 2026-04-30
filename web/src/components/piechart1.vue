<template>
  <div class="pie-panel">
    <div class="chart" ref="piechart"></div>
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
  seriesName?: string
}>(), {
  data: undefined,
  seriesName: '报警类别',
})

const alarmStore = useAlarmStore()
const { getWeekStatistics } = storeToRefs(alarmStore)
const piechart = ref<HTMLDivElement>()
let mychart: echarts.ECharts | null = null

const chartData = computed(() => props.data ?? getWeekStatistics.value)
const defaultColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#F8BD91', '#2CD6DB', '#C4D83B']

const normalizedData = computed(() => {
  const seen: Record<string, number> = {}
  chartData.value.forEach(item => {
    const name = item.eventType || '未知类型'
    seen[name] = (seen[name] || 0) + Number(item.eventCount || 0)
  })
  return Object.entries(seen).map(([name, value]) => ({ name, value }))
})

const updateChart = (): void => {
  if (!mychart) return
  mychart.setOption({
    color: defaultColors,
    tooltip: { trigger: 'item' },
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
      data: normalizedData.value.map(item => item.name),
    },
    series: [
      {
        name: props.seriesName,
        type: 'pie',
        radius: ['50%', '65%'],
        center: ['32%', '50%'],
        avoidLabelOverlap: false,
        padAngle: 7,
        itemStyle: { borderRadius: 14 },
        label: { show: false, position: 'center' },
        emphasis: {
          label: {
            show: true,
            fontSize: '1.4rem',
            fontWeight: 'bold',
          },
        },
        labelLine: { show: false },
        data: normalizedData.value,
      },
    ],
  })
}

const handleResize = (): void => {
  mychart?.resize()
}

let alarmHandler: (() => void) | null = null

onMounted(() => {
  if (piechart.value) {
    mychart = echarts.init(piechart.value)
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
watch(() => props.seriesName, updateChart)

onUnmounted(() => {
  const bus = (window as any).$bus
  if (bus && alarmHandler) bus.$off('alarm', alarmHandler)
  mychart?.dispose()
  window.removeEventListener('resize', handleResize)
})
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
