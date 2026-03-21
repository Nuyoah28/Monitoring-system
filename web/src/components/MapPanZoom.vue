<template>
  <div
    ref="canvasRef"
    class="map-canvas"
    :class="{ dragging: isDragging }"
    @wheel.prevent="onWheel"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <div class="map-layer" :style="layerStyle">
      <span
        v-for="point in points"
        :key="point.camera"
        class="point"
        :class="point.className"
        :style="point.style"
        :title="point.title"
        @pointerdown.stop
        @click.stop="emit('point-click', point)"
      ></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface MapPointItem {
  title: string
  camera: string
  className: string
  streamUrl?: string
  style?: {
    left?: string
    top?: string
  }
}

const props = withDefaults(
  defineProps<{
    points: MapPointItem[]
    imageUrl?: string
    minScale?: number
    maxScale?: number
  }>(),
  {
    imageUrl: '/assets/map.png',
    minScale: 1,
    maxScale: 4,
  }
)

const emit = defineEmits<{
  (e: 'point-click', point: MapPointItem): void
}>()

const canvasRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
const offsetX = ref(0)
const offsetY = ref(0)
const isDragging = ref(false)
const pointerId = ref<number | null>(null)
const dragStartX = ref(0)
const dragStartY = ref(0)
const dragOriginX = ref(0)
const dragOriginY = ref(0)

const layerStyle = computed(() => ({
  backgroundImage: `url('${props.imageUrl}')`,
  transform: `translate(${offsetX.value}px, ${offsetY.value}px) scale(${scale.value})`,
}))

const clampScale = (value: number) => {
  return Math.min(props.maxScale, Math.max(props.minScale, value))
}

const zoomTo = (targetScale: number, anchorX: number, anchorY: number) => {
  const nextScale = clampScale(targetScale)
  if (nextScale === scale.value) return

  const worldX = (anchorX - offsetX.value) / scale.value
  const worldY = (anchorY - offsetY.value) / scale.value

  scale.value = nextScale
  offsetX.value = anchorX - worldX * nextScale
  offsetY.value = anchorY - worldY * nextScale
}

const onWheel = (event: WheelEvent) => {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return

  const anchorX = event.clientX - rect.left
  const anchorY = event.clientY - rect.top
  const factor = event.deltaY < 0 ? 1.12 : 0.88
  zoomTo(scale.value * factor, anchorX, anchorY)
}

const onPointerDown = (event: PointerEvent) => {
  if (event.button !== 0) return
  if (!canvasRef.value) return

  pointerId.value = event.pointerId
  isDragging.value = true
  dragStartX.value = event.clientX
  dragStartY.value = event.clientY
  dragOriginX.value = offsetX.value
  dragOriginY.value = offsetY.value
  canvasRef.value.setPointerCapture(event.pointerId)
}

const onPointerMove = (event: PointerEvent) => {
  if (!isDragging.value || pointerId.value !== event.pointerId) return

  const moveX = event.clientX - dragStartX.value
  const moveY = event.clientY - dragStartY.value
  offsetX.value = dragOriginX.value + moveX
  offsetY.value = dragOriginY.value + moveY
}

const onPointerUp = (event: PointerEvent) => {
  if (pointerId.value !== event.pointerId) return
  if (canvasRef.value?.hasPointerCapture(event.pointerId)) {
    canvasRef.value.releasePointerCapture(event.pointerId)
  }

  isDragging.value = false
  pointerId.value = null
}
</script>

<style scoped>
.map-canvas {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  touch-action: none;
  user-select: none;
  cursor: grab;
}

.map-canvas.dragging {
  cursor: grabbing;
}

.map-layer {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  transform-origin: 0 0;
  will-change: transform;
}

</style>
