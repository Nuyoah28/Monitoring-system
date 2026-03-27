<template>
  <view class="map-shell">
    <view class="gesture-tip">双指缩放/拖动地图</view>
    <view
      id="viewport"
      class="viewport"
      @touchstart="onTouchStart"
      @touchmove.prevent="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
      @tap="clearActivePoint"
      >
        <view class="map-canvas" :style="canvasStyle">
          <view class="map-content" :style="contentStyle">
            <image class="map-image" :src="mapUrl" mode="aspectFit"></image>

          <view
            v-for="point in pointInfos"
            :key="point.id"
            class="marker"
            :style="{ left: point.x + '%', top: point.y + '%' }"
            @tap.stop="showPointDetail(point)"
          >
            <view class="dot"></view>
            <text class="label">{{ point.name }}</text>
          </view>
          </view>
        </view>
    </view>

    <view class="info-panel">
      <view class="point-title">{{ currentPoint.name }} 监控信息</view>
      <view class="point-row">
        <text class="key">状态</text>
        <text :class="['value', currentPoint.running ? 'online' : 'offline']">
          {{ currentPoint.running ? "在线" : "离线" }}
        </text>
      </view>
      <view class="point-row">
        <text class="key">负责人</text>
        <text class="value">{{ currentPoint.leader }}</text>
      </view>
      <view class="point-row">
        <text class="key">位置</text>
        <text class="value">{{ currentPoint.area }}</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: "MonitorMap",
  props: {
    monitorList: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      mapUrl: "../../../static/map.png",
      demoPoints: [
        { id: 1, defaultName: "监测点A", x: 28, y: 34 },
        { id: 2, defaultName: "监测点B", x: 56, y: 48 },
        { id: 3, defaultName: "监测点C", x: 73, y: 33 },
      ],
      activePoint: null,
      scale: 1,
      translateX: 0,
      translateY: 0,
      minScale: 1,
      maxScale: 3,
      gestureType: "none",
      startPoint: { x: 0, y: 0 },
      startCenter: { x: 0, y: 0 },
      startDistance: 0,
      startScale: 1,
      startTranslateX: 0,
      startTranslateY: 0,
      viewportWidth: 0,
      viewportHeight: 0,
      imageRatio: 16 / 9,
      contentWidth: 0,
      contentHeight: 0,
      contentLeft: 0,
      contentTop: 0,
    };
  },
  mounted() {
    this.$nextTick(() => {
      this.updateViewportSize();
      this.loadImageRatio();
      setTimeout(() => {
        this.updateViewportSize();
      }, 80);
      setTimeout(() => {
        this.updateViewportSize();
      }, 220);
    });
  },
  computed: {
    canvasStyle() {
      return {
        transform: `translate3d(${this.translateX}px, ${this.translateY}px, 0) scale(${this.scale})`,
      };
    },
    contentStyle() {
      const hasSize = this.contentWidth > 0 && this.contentHeight > 0;
      if (!hasSize) {
        return {
          width: "100%",
          height: "100%",
          left: "0px",
          top: "0px",
        };
      }

      return {
        width: `${this.contentWidth}px`,
        height: `${this.contentHeight}px`,
        left: `${this.contentLeft}px`,
        top: `${this.contentTop}px`,
      };
    },
    currentPoint() {
      if (this.activePoint) {
        const latest = this.pointInfos.find((item) => item.id === this.activePoint.id);
        return latest || this.activePoint;
      }
      return this.pointInfos[0] || {
        id: 0,
        name: "暂无监控点",
        running: false,
        leader: "-",
        area: "-",
      };
    },
    pointInfos() {
      const source = Array.isArray(this.monitorList) ? this.monitorList.slice(0, 3) : [];
      return this.demoPoints.map((point, index) => {
        const monitor = source[index] || {};
        const running = typeof monitor.running === "boolean" ? monitor.running : monitor.deal === "正在运行";
        return {
          ...point,
          name: monitor.name || point.defaultName,
          running,
          leader: monitor.leader || "-",
          area: monitor.department || monitor.area || "-",
        };
      });
    },
  },
  methods: {
    loadImageRatio() {
      uni.getImageInfo({
        src: this.mapUrl,
        success: (res) => {
          if (res && res.width && res.height) {
            this.imageRatio = res.width / res.height;
            this.updateContentRect();
          }
        },
      });
    },
    updateContentRect() {
      if (!this.viewportWidth || !this.viewportHeight || !this.imageRatio) return;

      const viewportRatio = this.viewportWidth / this.viewportHeight;
      let width = 0;
      let height = 0;

      if (viewportRatio > this.imageRatio) {
        height = this.viewportHeight;
        width = height * this.imageRatio;
      } else {
        width = this.viewportWidth;
        height = width / this.imageRatio;
      }

      this.contentWidth = width;
      this.contentHeight = height;
      this.contentLeft = (this.viewportWidth - width) / 2;
      const centerTop = (this.viewportHeight - height) / 2;
      this.contentTop = Math.max(0, centerTop - 24);
    },
    updateViewportSize() {
      const query = uni.createSelectorQuery().in(this);
      query
        .select("#viewport")
        .boundingClientRect((rect) => {
          if (!rect) return;
          this.viewportWidth = rect.width || 0;
          this.viewportHeight = rect.height || 0;
          this.updateContentRect();
          this.clampTranslation();
        })
        .exec();
    },
    clamp(value, min, max) {
      return Math.min(Math.max(value, min), max);
    },
    clampTranslation() {
      if (!this.viewportWidth || !this.viewportHeight) return;

      const maxOffsetX = Math.max(0, ((this.scale - 1) * this.viewportWidth) / 2);
      const maxOffsetY = Math.max(0, ((this.scale - 1) * this.viewportHeight) / 2);

      this.translateX = this.clamp(this.translateX, -maxOffsetX, maxOffsetX);
      this.translateY = this.clamp(this.translateY, -maxOffsetY, maxOffsetY);
    },
    showPointDetail(point) {
      this.activePoint = point;
    },
    clearActivePoint() {
      this.activePoint = null;
    },
    getDistance(t1, t2) {
      const dx = t1.clientX - t2.clientX;
      const dy = t1.clientY - t2.clientY;
      return Math.sqrt(dx * dx + dy * dy);
    },
    getCenter(t1, t2) {
      return {
        x: (t1.clientX + t2.clientX) / 2,
        y: (t1.clientY + t2.clientY) / 2,
      };
    },
    onTouchStart(e) {
      const touches = e.touches || [];

      if (touches.length >= 2) {
        const t1 = touches[0];
        const t2 = touches[1];
        this.gestureType = "pinch";
        this.startDistance = this.getDistance(t1, t2);
        this.startCenter = this.getCenter(t1, t2);
        this.startScale = this.scale;
        this.startTranslateX = this.translateX;
        this.startTranslateY = this.translateY;
        this.activePoint = null;
        return;
      }

      if (touches.length === 1) {
        this.gestureType = "drag";
        this.startPoint = {
          x: touches[0].clientX,
          y: touches[0].clientY,
        };
        this.startTranslateX = this.translateX;
        this.startTranslateY = this.translateY;
      }
    },
    onTouchMove(e) {
      const touches = e.touches || [];

      if (this.gestureType === "pinch" && touches.length >= 2) {
        const t1 = touches[0];
        const t2 = touches[1];
        const distance = this.getDistance(t1, t2);
        const center = this.getCenter(t1, t2);

        const scaleFactor = distance / this.startDistance;
        const nextScale = this.startScale * scaleFactor;
        this.scale = this.clamp(nextScale, this.minScale, this.maxScale);

        this.translateX = this.startTranslateX + (center.x - this.startCenter.x);
        this.translateY = this.startTranslateY + (center.y - this.startCenter.y);
        this.clampTranslation();
        return;
      }

      if (this.gestureType === "drag" && touches.length === 1) {
        this.translateX = this.startTranslateX + (touches[0].clientX - this.startPoint.x);
        this.translateY = this.startTranslateY + (touches[0].clientY - this.startPoint.y);
        this.clampTranslation();
      }
    },
    onTouchEnd(e) {
      const touches = e.touches || [];

      if (touches.length >= 2) {
        const t1 = touches[0];
        const t2 = touches[1];
        this.gestureType = "pinch";
        this.startDistance = this.getDistance(t1, t2);
        this.startCenter = this.getCenter(t1, t2);
        this.startScale = this.scale;
        this.startTranslateX = this.translateX;
        this.startTranslateY = this.translateY;
        return;
      }

      if (touches.length === 1) {
        this.gestureType = "drag";
        this.startPoint = {
          x: touches[0].clientX,
          y: touches[0].clientY,
        };
        this.startTranslateX = this.translateX;
        this.startTranslateY = this.translateY;
        return;
      }

      this.gestureType = "none";
    },
  },
};
</script>

<style scoped lang="scss">
.map-shell {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .gesture-tip {
    position: absolute;
    top: 20rpx;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9;
    background: rgba(255, 255, 255, 0.9);
    color: #2e3f57;
    font-size: 22rpx;
    border-radius: 999rpx;
    padding: 10rpx 20rpx;
  }

  .viewport {
    position: relative;
    width: 100%;
    flex: 2;
    overflow: hidden;
    touch-action: none;
    background: #dcebf8;
  }

  .map-canvas {
    width: 100%;
    height: 100%;
    position: relative;
    transform-origin: center center;
  }

  .map-content {
    position: absolute;
  }

  .info-panel {
    flex: 1;
    margin: 16rpx 20rpx 20rpx;
    background: rgba(255, 255, 255, 0.96);
    border-radius: 24rpx;
    padding: 24rpx;
    box-shadow: 0 10rpx 28rpx rgba(0, 0, 0, 0.12);
    border: 1px solid rgba(0, 122, 255, 0.12);
    overflow: hidden;

    .point-title {
      font-size: 30rpx;
      color: #17283f;
      font-weight: 700;
      margin-bottom: 14rpx;
    }

    .point-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 8rpx;

      .key {
        font-size: 24rpx;
        color: #5d708b;
      }

      .value {
        font-size: 24rpx;
        color: #1a2a3a;
        font-weight: 600;
      }

      .online {
        color: #19b26b;
      }

      .offline {
        color: #ff5d5d;
      }
    }
  }

  .map-image {
    width: 100%;
    height: 100%;
    display: block;
  }

  .marker {
    position: absolute;
    transform: translate(-50%, -50%);
    width: 0;
    height: 0;

    .dot {
      position: absolute;
      left: 0;
      top: 0;
      transform: translate(-50%, -50%);
      width: 22rpx;
      height: 22rpx;
      border-radius: 50%;
      background: #ff5f5f;
      border: 4rpx solid #ffffff;
      box-shadow: 0 6rpx 20rpx rgba(255, 95, 95, 0.5);
      animation: pulse 1.8s infinite;
    }

    .label {
      position: absolute;
      left: 0;
      top: 16rpx;
      transform: translateX(-50%);
      padding: 6rpx 12rpx;
      border-radius: 10rpx;
      background: rgba(18, 35, 58, 0.86);
      color: #ffffff;
      font-size: 20rpx;
      white-space: nowrap;
    }
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  60% {
    transform: scale(1.25);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
