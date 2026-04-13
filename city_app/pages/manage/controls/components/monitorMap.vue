<template>
  <view class="map-shell">
    <map
      id="monitor-map"
      class="map-native"
      :longitude="mapCenter.longitude"
      :latitude="mapCenter.latitude"
      :scale="17"
      :markers="mapMarkers"
      :show-location="false"
      :enable-scroll="true"
      :enable-zoom="true"
      :enable-rotate="true"
      :enable-overlooking="true"
      @markertap="onMarkerTap"
    ></map>
  </view>
</template>

<script>
const DEFAULT_CENTER = {
  longitude: 117.01187872107023,
  latitude: 39.1443426861701,
};

const FIXED_POINTS = [
  {
    id: 1,
    name: "三号楼监测点",
    camera: "三号楼监测点",
    longitude: 117.01280287680027,
    latitude: 39.144625636831215,
  },
  {
    id: 2,
    name: "九号楼监测点",
    camera: "九号楼监测点",
    longitude: 117.0122804687718,
    latitude: 39.143983680256035,
  },
  {
    id: 3,
    name: "南门监测点",
    camera: "南门监测点",
    longitude: 117.01346569650909,
    latitude: 39.14355698741387,
  },
];

export default {
  name: "MonitorMap",
  props: {
    monitorList: {
      type: Array,
      default: () => [],
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.fitToPoints();
      setTimeout(() => this.fitToPoints(), 150);
    });
  },
  computed: {
    points() {
      const source = Array.isArray(this.monitorList) ? this.monitorList.slice(0, 3) : [];
      return FIXED_POINTS.map((base, index) => {
        const monitor = source[index] || {};
        const lon = Number(monitor.longitude);
        const lat = Number(monitor.latitude);
        return {
          ...base,
          id: Number(monitor.id) || base.id,
          name: monitor.name || base.name,
          camera: monitor.camera || monitor.name || base.camera,
          longitude: Number.isFinite(lon) ? lon : base.longitude,
          latitude: Number.isFinite(lat) ? lat : base.latitude,
        };
      });
    },
    mapCenter() {
      return this.points[0] || DEFAULT_CENTER;
    },
    mapMarkers() {
      return this.points.map((item) => ({
        id: item.id,
        longitude: item.longitude,
        latitude: item.latitude,
        iconPath: "/static/locate.png",
        width: 28,
        height: 28,
        callout: {
          content: item.camera || item.name,
          color: "#16a34a",
          fontSize: 11,
          borderRadius: 6,
          borderWidth: 1,
          borderColor: "#b7ebc6",
          bgColor: "#ffffff",
          padding: 5,
          display: "ALWAYS",
        },
        label: {
          content: item.camera || item.name,
          color: "#16a34a",
          fontSize: 11,
          borderRadius: 6,
          borderWidth: 1,
          borderColor: "#b7ebc6",
          bgColor: "#ffffff",
          padding: 5,
          anchorX: 16,
          anchorY: -26,
        },
      }));
    },
  },
  methods: {
    fitToPoints() {
      const points = this.points.map((item) => ({
        longitude: item.longitude,
        latitude: item.latitude,
      }));
      if (!points.length) return;
      const mapCtx = uni.createMapContext("monitor-map", this);
      if (mapCtx && mapCtx.includePoints) {
        mapCtx.includePoints({
          points,
          padding: [36, 36, 36, 36],
        });
      }
    },
    onMarkerTap(e) {
      const markerId = Number(e.detail && e.detail.markerId);
      const point = this.points.find((item) => item.id === markerId);
      if (point) {
        this.$emit("point-click", point);
      }
    },
  },
};
</script>

<style scoped lang="scss">
.map-shell {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 16rpx;
  background: #dcebf8;
}

.map-native {
  width: 100%;
  height: 100%;
}
</style>
