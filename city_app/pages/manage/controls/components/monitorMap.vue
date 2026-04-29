<template>
  <view class="map-shell">
    <!-- #ifdef H5 -->
    <div
      id="monitor-map-h5"
      ref="h5MapRoot"
      class="map-native h5-map"
      :class="{ 'h5-map--hidden': h5Error && !h5Map }"
    ></div>
    <view v-if="h5Error && !h5Map" class="map-fallback">
      <view class="fallback-grid"></view>
      <view class="fallback-tip">{{ h5Error }}，已切换示意地图</view>
      <view
        v-for="point in fallbackPoints"
        :key="point.markerId"
        class="fallback-point"
        :class="{ 'fallback-point--alert': point.hasAlert }"
        :style="point.style"
        @tap="onFallbackPointTap(point)"
      >
        <view class="fallback-label">
          <text class="fallback-name">{{ getH5LabelText(point) }}</text>
          <text v-if="point.hasAlert" class="fallback-status">告警 {{ point.alarmCount > 99 ? "99+" : point.alarmCount }}</text>
        </view>
        <view class="fallback-pin">
          <view v-if="point.hasAlert" class="fallback-pulse"></view>
          <image :src="point.hasAlert ? '/static/locate-red.png' : '/static/locate-blue.png'" mode="aspectFit"></image>
          <text v-if="point.hasAlert" class="fallback-badge">{{ point.alarmCount > 99 ? "99+" : point.alarmCount }}</text>
        </view>
      </view>
    </view>
    <!-- #endif -->

    <!-- #ifndef H5 -->
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
    <!-- #endif -->
  </view>
</template>

<script>
const H5_AMAP_WEB_KEY =
  (typeof process !== "undefined" && process.env && process.env.VUE_APP_AMAP_WEB_KEY) ||
  "b793c585623cb4d4901d36623652b730";
const H5_AMAP_SECURITY_JS_CODE =
  (typeof process !== "undefined" && process.env && process.env.VUE_APP_AMAP_SECURITY_JS_CODE) || "";

let amapLoadPromise = null;

const loadAmapJsSdk = () => {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("非浏览器环境，无法加载高德 JS SDK"));
  }
  if (window.AMap && window.AMap.Map) {
    return Promise.resolve(window.AMap);
  }
  if (amapLoadPromise) return amapLoadPromise;

  amapLoadPromise = new Promise((resolve, reject) => {
    if (H5_AMAP_SECURITY_JS_CODE) {
      window._AMapSecurityConfig = {
        securityJsCode: H5_AMAP_SECURITY_JS_CODE,
      };
    }
    const finishLoad = () => {
      if (window.AMap && window.AMap.Map) {
        resolve(window.AMap);
      } else {
        reject(new Error("高德 JS SDK 加载完成，但 AMap 对象不可用"));
      }
    };
    const appendScript = (protocol, allowHttpRetry = false) => {
      const script = document.createElement("script");
      script.src = `${protocol}//webapi.amap.com/maps?v=2.0&key=${H5_AMAP_WEB_KEY}`;
      script.async = true;
      script.onload = finishLoad;
      script.onerror = () => {
        if (allowHttpRetry && window.location && window.location.protocol === "http:") {
          appendScript("http:", false);
          return;
        }
        reject(new Error("高德 JS SDK 加载失败"));
      };
      document.head.appendChild(script);
    };

    appendScript("https:", true);
  });

  return amapLoadPromise;
};

const DEFAULT_CENTER = {
  longitude: 117.01187872107023,
  latitude: 39.1443426861701,
};

const FALLBACK_SPOTS = [
  [117.01280287680027, 39.144625636831215],
  [117.0122804687718, 39.143983680256035],
  [117.01346569650909, 39.14355698741387],
  [117.0113204687718, 39.14428368025603],
  [117.0121804687718, 39.14508368025604],
  [117.0130204687718, 39.14402368025603],
];

const normalizeName = (value) => String(value || "").replace(/\s+/g, "").toLowerCase();

const hashCode = (text) => {
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return hash;
};

const inferPseudoLngLat = (camera, department, index) => {
  const merged = `${department || ""} ${camera || ""}`;
  const text = merged.replace(/\s+/g, "");
  const baseLng = DEFAULT_CENTER.longitude;
  const baseLat = DEFAULT_CENTER.latitude;

  let lng = FALLBACK_SPOTS[index % FALLBACK_SPOTS.length][0];
  let lat = FALLBACK_SPOTS[index % FALLBACK_SPOTS.length][1];

  if (/东门|东侧|东区|东/.test(text)) {
    lng = baseLng + 0.00095;
    lat = baseLat + 0.00025;
  } else if (/西门|西侧|西区|西/.test(text)) {
    lng = baseLng - 0.00095;
    lat = baseLat + 0.00018;
  } else if (/南门|南侧|南区|南/.test(text)) {
    lng = baseLng + 0.00012;
    lat = baseLat - 0.00095;
  } else if (/北门|北侧|北区|北/.test(text)) {
    lng = baseLng + 0.00012;
    lat = baseLat + 0.00095;
  } else if (/车库|停车/.test(text)) {
    lng = baseLng - 0.00055;
    lat = baseLat - 0.00078;
  } else if (/电梯/.test(text)) {
    lng = baseLng + 0.0006;
    lat = baseLat - 0.00028;
  } else if (/楼道/.test(text)) {
    lng = baseLng + 0.00025;
    lat = baseLat + 0.00008;
  } else {
    const buildingMatch = text.match(/(\d+)号楼/);
    if (buildingMatch) {
      const buildingNo = Number(buildingMatch[1]);
      const angle = ((buildingNo * 47) % 360) * (Math.PI / 180);
      lng = baseLng + Math.cos(angle) * 0.00086;
      lat = baseLat + Math.sin(angle) * 0.00064;
    }
  }

  const h = hashCode(text || `idx-${index}`);
  const jitterLng = ((h % 17) - 8) * 0.000018;
  const jitterLat = ((Math.floor(h / 17) % 17) - 8) * 0.000014;
  return [lng + jitterLng, lat + jitterLat];
};

const APP_SAFE_MARKER_ICON = "/static/locate-blue.png";
const APP_ALERT_MARKER_ICON = "/static/locate-red.png";
const APP_ALERT_BADGE_ICONS = {
  1: "/static/locate-red-badge-1.png",
  2: "/static/locate-red-badge-2.png",
  3: "/static/locate-red-badge-3.png",
  4: "/static/locate-red-badge-4.png",
  5: "/static/locate-red-badge-5.png",
  6: "/static/locate-red-badge-6.png",
  7: "/static/locate-red-badge-7.png",
  8: "/static/locate-red-badge-8.png",
  9: "/static/locate-red-badge-9.png",
  plus: "/static/locate-red-badge-plus.png",
};

const pickAlarmCameraName = (item) =>
  String(item?.camera || item?.monitorName || item?.monitor || item?.deviceName || item?.name || "").trim();

const pickAlarmAreaName = (item) =>
  String(item?.department || item?.location || item?.area || "").trim();

const pickAlarmTitle = (item) =>
  String(item?.eventName || item?.caseTypeName || item?.message || item?.alarmName || item?.typeName || "待处理警情").trim();

const addAlarmInfo = (target, key, item) => {
  if (!key) return;
  if (!target[key]) {
    target[key] = { count: 0, latest: item };
  }
  target[key].count += 1;
};

export default {
  name: "MonitorMap",
  props: {
    monitorList: {
      type: Array,
      default: () => [],
    },
    alarmList: {
      type: Array,
      default: () => [],
    },
    pulseTick: {
      type: Number,
      default: 0,
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      h5Map: null,
      h5MarkerOverlays: [],
      h5Error: "",
      h5PulseStyleInjected: false,
      lastPointFitSignature: "",
    };
  },
  computed: {
    alarmCountMap() {
      const monitorSource = Array.isArray(this.monitorList) ? this.monitorList : [];
      const pendingAlarmList = Array.isArray(this.alarmList) ? this.alarmList : [];
      const idCounts = {};
      const cameraCounts = {};
      const areaCounts = {};

      pendingAlarmList.forEach((item) => {
        if (!this.isPendingAlarm(item)) return;
        const monitorId = item?.monitorId || item?.cameraId || item?.deviceId || item?.monitor_id;
        if (monitorId !== undefined && monitorId !== null && `${monitorId}` !== "") {
          addAlarmInfo(idCounts, String(monitorId), item);
          return;
        }

        const cameraName = pickAlarmCameraName(item);
        const cameraKey = normalizeName(cameraName);
        if (cameraKey) {
          addAlarmInfo(cameraCounts, cameraKey, item);
          return;
        }

        const areaName = pickAlarmAreaName(item);
        const areaKey = normalizeName(areaName);
        if (!areaKey) return;

        const matched = monitorSource.find((monitor) => {
          const monitorName = normalizeName(monitor?.name || monitor?.camera);
          const monitorDept = normalizeName(monitor?.department || monitor?.area || monitor?.location);
          return (
            areaKey === monitorDept ||
            (monitorName && (monitorName.includes(areaKey) || areaKey.includes(monitorName)))
          );
        });

        const matchedName = normalizeName(matched?.name || matched?.camera);
        if (matchedName) {
          addAlarmInfo(cameraCounts, matchedName, item);
          return;
        }

        addAlarmInfo(areaCounts, areaKey, item);
      });

      return { idCounts, cameraCounts, areaCounts };
    },
    points() {
      const source = Array.isArray(this.monitorList) && this.monitorList.length ? this.monitorList : [];
      const normalizedSource = source.length
        ? source
        : [
            { id: 1, name: "小区东门街道摄像头", department: "小区东门街道" },
            { id: 2, name: "小区西门街道摄像头", department: "小区西门街道" },
            { id: 3, name: "3号楼1单元门口摄像头", department: "3号楼1单元门口" },
          ];

      const basePoints = normalizedSource.map((monitor, index) => {
        const camera = monitor?.camera || monitor?.name || monitor?.location || `监测点${index + 1}`;
        const department = monitor?.department || monitor?.area || monitor?.location || "";

        const lon = Number(monitor?.longitude);
        const lat = Number(monitor?.latitude);
        const hasGeo = Number.isFinite(lon) && Number.isFinite(lat);
        const [fallbackLng, fallbackLat] = inferPseudoLngLat(camera, department, index);

        const sourceId = monitor?.id || monitor?.monitorId || index + 1;
        const alarmInfo = this.getAlarmInfo(sourceId, camera, department);

        return {
          markerId: index + 1,
          sourceId,
          name: monitor?.name || camera,
          camera,
          department,
          longitude: hasGeo ? lon : fallbackLng,
          latitude: hasGeo ? lat : fallbackLat,
          alarmCount: alarmInfo.count,
          latestAlarm: alarmInfo.latest,
          hasAlert: alarmInfo.count > 0,
        };
      });

      const collisionMap = {};
      return basePoints.map((item) => {
        const key = `${Number(item.longitude).toFixed(5)}_${Number(item.latitude).toFixed(5)}`;
        const repeatIndex = collisionMap[key] || 0;
        collisionMap[key] = repeatIndex + 1;
        if (repeatIndex === 0) return item;

        const angle = ((repeatIndex * 57) % 360) * (Math.PI / 180);
        const radius = 0.00006 + Math.floor((repeatIndex - 1) / 6) * 0.000025;
        return {
          ...item,
          longitude: item.longitude + Math.cos(angle) * radius,
          latitude: item.latitude + Math.sin(angle) * radius,
        };
      });
    },
    mapCenter() {
      const alertPoint = this.points.find((item) => item.hasAlert);
      return alertPoint || this.points[0] || DEFAULT_CENTER;
    },
    fallbackBounds() {
      const lngs = this.points.map((item) => Number(item.longitude)).filter(Number.isFinite);
      const lats = this.points.map((item) => Number(item.latitude)).filter(Number.isFinite);
      if (!lngs.length || !lats.length) {
        return {
          minLng: DEFAULT_CENTER.longitude - 0.0012,
          maxLng: DEFAULT_CENTER.longitude + 0.0012,
          minLat: DEFAULT_CENTER.latitude - 0.0012,
          maxLat: DEFAULT_CENTER.latitude + 0.0012,
        };
      }
      const minLng = Math.min(...lngs);
      const maxLng = Math.max(...lngs);
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const lngPad = Math.max((maxLng - minLng) * 0.18, 0.00028);
      const latPad = Math.max((maxLat - minLat) * 0.18, 0.00028);
      return {
        minLng: minLng - lngPad,
        maxLng: maxLng + lngPad,
        minLat: minLat - latPad,
        maxLat: maxLat + latPad,
      };
    },
    fallbackPoints() {
      const bounds = this.fallbackBounds;
      const lngSpan = Math.max(bounds.maxLng - bounds.minLng, 0.00001);
      const latSpan = Math.max(bounds.maxLat - bounds.minLat, 0.00001);
      return this.points.map((point) => {
        const left = ((Number(point.longitude) - bounds.minLng) / lngSpan) * 100;
        const top = (1 - (Number(point.latitude) - bounds.minLat) / latSpan) * 100;
        return {
          ...point,
          style: {
            left: `${Math.min(88, Math.max(12, left))}%`,
            top: `${Math.min(84, Math.max(16, top))}%`,
          },
        };
      });
    },
    mapMarkers() {
      return this.points.map((item) => {
        const labelText = this.getNativeLabelText(item);
        return {
          id: item.markerId,
          longitude: item.longitude,
          latitude: item.latitude,
          iconPath: this.getNativeMarkerIcon(item),
          width: item.hasAlert ? 38 : 30,
          height: item.hasAlert ? 38 : 30,
          zIndex: item.hasAlert ? 999 : 100,
          label: {
            content: labelText,
            color: item.hasAlert ? "#b91c1c" : "#0f4c81",
            fontSize: 11,
            borderRadius: 10,
            borderWidth: 1,
            borderColor: item.hasAlert ? "#fca5a5" : "#bfdbfe",
            bgColor: item.hasAlert ? "#fff1f2" : "#eff6ff",
            padding: 6,
            anchorX: item.hasAlert ? 22 : 18,
            anchorY: item.hasAlert ? -34 : -30,
          },
        };
      });
    },
  },
  watch: {
    points: {
      deep: true,
      handler() {
        const shouldFit = this.shouldRefitPoints();
        // #ifdef H5
        this.renderH5Markers(shouldFit);
        // #endif
        // #ifndef H5
        if (shouldFit) this.fitToPoints();
        // #endif
      },
    },
    pulseTick() {
      // App 真机端保持 marker 稳定，避免频繁重绘导致闪烁
    },
  },
  mounted() {
    this.$nextTick(() => {
      // #ifdef H5
      this.initH5Map();
      // #endif
      // #ifndef H5
      this.fitToPoints();
      setTimeout(() => this.fitToPoints(), 150);
      // #endif
    });
  },
  beforeDestroy() {
    // #ifdef H5
    if (this.h5Map) {
      this.h5Map.destroy();
      this.h5Map = null;
      this.h5MarkerOverlays = [];
    }
    // #endif
  },
  methods: {
    shouldRefitPoints() {
      const signature = this.points
        .map((item) => `${item.sourceId}:${Number(item.longitude).toFixed(6)},${Number(item.latitude).toFixed(6)}`)
        .join('|');
      if (signature === this.lastPointFitSignature) return false;
      this.lastPointFitSignature = signature;
      return true;
    },
    isPendingAlarm(item) {
      if (!item || typeof item !== "object") return false;
      if (item.status === 1 || item.status === true || String(item.status) === "1") return false;
      const dealText = String(item.deal || item.result || "");
      if (dealText.includes("已处理")) return false;
      return true;
    },
    getAlarmInfo(sourceId, camera, department) {
      if (sourceId !== undefined && sourceId !== null) {
        const idInfo = this.alarmCountMap.idCounts[String(sourceId)];
        if (idInfo && idInfo.count > 0) return idInfo;
      }
      const cameraKey = normalizeName(camera);
      const departmentKey = normalizeName(department);
      const cameraInfo = this.alarmCountMap.cameraCounts[cameraKey];
      if (cameraInfo && cameraInfo.count > 0) return cameraInfo;
      if (!departmentKey) return { count: 0, latest: null };
      const deptMonitors = (Array.isArray(this.monitorList) ? this.monitorList : []).filter((item) => {
        const dept = normalizeName(item?.department || item?.area || item?.location);
        return dept && dept === departmentKey;
      });
      if (deptMonitors.length !== 1) return { count: 0, latest: null };
      return this.alarmCountMap.areaCounts[departmentKey] || { count: 0, latest: null };
    },
    getMarkerLabelText(point) {
      if (!point) return "监测点";
      return point.alarmCount > 0
        ? `${point.camera || point.name}（${point.alarmCount}）`
        : point.camera || point.name || "监测点";
    },
    getNativeMarkerIcon(point) {
      if (!point || !point.hasAlert) return APP_SAFE_MARKER_ICON;
      const count = Number(point.alarmCount || 0);
      if (count >= 10) return APP_ALERT_BADGE_ICONS.plus;
      return APP_ALERT_BADGE_ICONS[count] || APP_ALERT_MARKER_ICON;
    },
    getNativeLabelText(point) {
      if (!point) return "监测点";
      const name = this.getShortText(point.camera || point.name || "监测点", 12);
      if (!point.hasAlert) return name;
      const count = this.getAlarmCountText(point.alarmCount);
      const title = this.getShortText(pickAlarmTitle(point.latestAlarm), 8);
      return `${name}｜${count}条告警｜${title}`;
    },
    getAlarmCountText(count) {
      return Number(count) > 9 ? "9+" : String(count || 0);
    },
    getH5LabelText(point) {
      if (!point) return "监测点";
      return this.getShortText(point.camera || point.name || "监测点", 14);
    },
    getShortText(value, maxLen = 12) {
      const text = String(value || "");
      if (text.length <= maxLen) return text;
      return `${text.slice(0, maxLen)}...`;
    },
    escapeHtml(text) {
      return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    },
    buildH5LabelHtml(point) {
      const text = this.escapeHtml(this.getH5LabelText(point));
      const count = Number(point.alarmCount) > 99 ? "99+" : String(point.alarmCount || "");
      const statusHtml = point.hasAlert
        ? `<span class="monitor-map-label-status monitor-map-label-status--alert">告警 ${count}</span>`
        : `<span class="monitor-map-label-status monitor-map-label-status--safe">正常</span>`;
      const alertClass = point.hasAlert ? "monitor-map-label--alert" : "monitor-map-label--safe";
      return `<div class="monitor-map-label ${alertClass}">
        <span class="monitor-map-label-text">${text}</span>
        ${statusHtml}
      </div>`;
    },
    buildH5MarkerHtml(point) {
      const count = Number(point.alarmCount) > 99 ? "99+" : String(point.alarmCount || "");
      const markerClass = point.hasAlert ? "monitor-map-marker monitor-map-marker--alert" : "monitor-map-marker";
      const badgeHtml = point.hasAlert
        ? `<span class="monitor-map-badge">
            <span class="monitor-map-badge-pulse"></span>
            <span class="monitor-map-badge-core">${count}</span>
          </span>`
        : "";
      return `<div class="${markerClass}">
        <img class="monitor-map-pin" src="${point.hasAlert ? APP_ALERT_MARKER_ICON : APP_SAFE_MARKER_ICON}" alt="pin" />
        ${badgeHtml}
      </div>`;
    },
    ensureH5PulseStyle() {
      // #ifndef H5
      return;
      // #endif

      // #ifdef H5
      if (typeof document === "undefined") return;
      let styleEl = document.getElementById("monitor-map-pulse-style");
      if (!styleEl) {
        styleEl = document.createElement("style");
        styleEl.id = "monitor-map-pulse-style";
        document.head.appendChild(styleEl);
      }
      styleEl.textContent = `
.monitor-map-marker {
  position: relative;
  width: 34px;
  height: 38px;
  filter: drop-shadow(0 3px 6px rgba(14, 116, 255, 0.28));
}
.monitor-map-pin {
  width: 34px;
  height: 34px;
  display: block;
  user-select: none;
  pointer-events: none;
}
.monitor-map-marker--alert .monitor-map-pin {
  filter: saturate(1.06);
}
.monitor-map-badge {
  position: absolute;
  right: -9px;
  top: -8px;
  width: 20px;
  height: 20px;
}
.monitor-map-badge-pulse {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  border: 2px solid rgba(239, 68, 68, 0.55);
  background: rgba(248, 113, 113, 0.2);
  will-change: transform, opacity;
  transform-origin: center;
  animation: monitor-map-pulse-ring 1.8s cubic-bezier(0.2, 0.7, 0.2, 1) infinite;
}
.monitor-map-badge-core {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: linear-gradient(180deg, #ef4444, #dc2626);
  color: #ffffff;
  font-size: 10.5px;
  font-weight: 700;
  line-height: 1;
  box-shadow: 0 2px 8px rgba(220, 38, 38, 0.42);
}
@keyframes monitor-map-pulse-ring {
  0% { transform: scale(0.78); opacity: 0.92; }
  65% { transform: scale(1.8); opacity: 0; }
  100% { transform: scale(1.8); opacity: 0; }
}
.monitor-map-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 210px;
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 12px;
  line-height: 1.2;
  backdrop-filter: blur(2px);
  box-shadow: 0 3px 12px rgba(15, 76, 129, 0.14);
}
.monitor-map-label--safe {
  border-color: #bfdbfe;
  background: rgba(239, 246, 255, 0.95);
  color: #0f4c81;
}
.monitor-map-label--alert {
  border-color: #fecaca;
  background: rgba(255, 241, 242, 0.96);
  color: #b91c1c;
}
.monitor-map-label-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 132px;
}
.monitor-map-label-status {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 2px 6px;
  font-size: 10.5px;
  font-weight: 700;
}
.monitor-map-label-status--safe {
  background: rgba(59, 130, 246, 0.12);
  color: #1d4ed8;
}
.monitor-map-label-status--alert {
  background: rgba(239, 68, 68, 0.14);
  color: #dc2626;
}`;
      this.h5PulseStyleInjected = true;
      // #endif
    },
    getH5MapContainer() {
      // #ifndef H5
      return null;
      // #endif

      // #ifdef H5
      let el = this.$refs.h5MapRoot;
      if (Array.isArray(el)) el = el[0];
      if (el && el.$el) el = el.$el;
      if (!el && this.$el && this.$el.querySelector) {
        el = this.$el.querySelector("#monitor-map-h5") || this.$el.querySelector(".h5-map");
      }
      return el || null;
      // #endif
    },
    async waitForH5MapContainer(maxRetry = 10) {
      // #ifndef H5
      return null;
      // #endif

      // #ifdef H5
      for (let i = 0; i < maxRetry; i += 1) {
        const el = this.getH5MapContainer();
        if (el) return el;
        await new Promise((resolve) => requestAnimationFrame(() => resolve()));
      }
      return null;
      // #endif
    },
    async initH5Map() {
      // #ifndef H5
      return;
      // #endif

      // #ifdef H5
      try {
        this.h5Error = "";
        const AMap = await loadAmapJsSdk();
        this.ensureH5PulseStyle();
        const container = await this.waitForH5MapContainer();
        if (!container) {
          throw new Error("地图容器未就绪");
        }

        if (!this.h5Map) {
          this.h5Map = new AMap.Map(container, {
            zoom: 17,
            center: [this.mapCenter.longitude, this.mapCenter.latitude],
            resizeEnable: true,
            viewMode: "2D",
          });
        }

        this.renderH5Markers(true);
      } catch (error) {
        const detail =
          (error && (error.message || error.info || (error.toString && error.toString()))) || "未知错误";
        this.h5Error = `地图加载失败：${detail}`;
        console.error("[MonitorMap] H5 地图初始化失败:", error);
      }
      // #endif
    },
    renderH5Markers(needFitView = false) {
      // #ifndef H5
      return;
      // #endif

      // #ifdef H5
      if (!this.h5Map || !(window.AMap && window.AMap.Marker)) return;
      const AMap = window.AMap;

      if (this.h5MarkerOverlays.length) {
        this.h5Map.remove(this.h5MarkerOverlays);
      }

      const markers = this.points.map((item) => {
        const marker = new AMap.Marker({
          position: [item.longitude, item.latitude],
          content: this.buildH5MarkerHtml(item),
          offset: new AMap.Pixel(-15, -30),
          zIndex: item.hasAlert ? 130 : 110,
          title: item.camera || item.name || "",
        });

        if (item.hasAlert) {
          marker.setLabel({
            direction: "top",
            content: this.buildH5LabelHtml(item),
          });
        }

        marker.on("click", () => {
          this.$emit("point-click", item);
        });

        return marker;
      });

      this.h5MarkerOverlays = markers;
      if (markers.length) {
        this.h5Map.add(markers);
        if (needFitView) {
          this.h5Map.setFitView(markers, false, [36, 36, 36, 36]);
        }
      }
      // #endif
    },
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
      const point = this.points.find((item) => item.markerId === markerId);
      if (point) {
        this.$emit("point-click", point);
      }
    },
    onFallbackPointTap(point) {
      this.$emit("point-click", point);
    },
  },
};
</script>

<style scoped lang="scss">
.map-shell {
  position: relative;
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

.h5-map--hidden {
  opacity: 0;
  pointer-events: none;
}

.map-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 24rpx;
  text-align: center;
  color: #1d4f7d;
  font-size: 24rpx;
  background: linear-gradient(180deg, rgba(220, 235, 248, 0.9), rgba(220, 235, 248, 0.95));
}

.map-fallback {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 16%, rgba(84, 166, 255, 0.18) 0, rgba(84, 166, 255, 0) 30%),
    radial-gradient(circle at 78% 74%, rgba(45, 212, 191, 0.14) 0, rgba(45, 212, 191, 0) 34%),
    linear-gradient(135deg, #edf6ff 0%, #f8fcff 100%);
}

.fallback-grid {
  position: absolute;
  inset: 0;
  opacity: 0.58;
  background-image:
    linear-gradient(rgba(73, 131, 183, 0.13) 1px, transparent 1px),
    linear-gradient(90deg, rgba(73, 131, 183, 0.13) 1px, transparent 1px);
  background-size: 32rpx 32rpx;
}

.fallback-tip {
  position: absolute;
  left: 18rpx;
  top: 16rpx;
  right: 18rpx;
  z-index: 2;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  color: #245f91;
  font-size: 20rpx;
  line-height: 1.35;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(87, 158, 221, 0.24);
  box-shadow: 0 6rpx 18rpx rgba(44, 99, 150, 0.12);
}

.fallback-point {
  position: absolute;
  z-index: 3;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.fallback-label {
  display: flex;
  align-items: center;
  gap: 8rpx;
  max-width: 260rpx;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  color: #0f4c81;
  font-size: 20rpx;
  line-height: 1;
  background: rgba(239, 246, 255, 0.94);
  border: 1px solid rgba(147, 197, 253, 0.92);
  box-shadow: 0 6rpx 18rpx rgba(15, 76, 129, 0.12);
}

.fallback-point--alert .fallback-label {
  color: #b91c1c;
  background: rgba(255, 241, 242, 0.96);
  border-color: rgba(252, 165, 165, 0.95);
}

.fallback-name {
  max-width: 150rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.fallback-status {
  flex-shrink: 0;
  padding: 4rpx 8rpx;
  border-radius: 999rpx;
  color: #dc2626;
  font-size: 18rpx;
  font-weight: 700;
  background: rgba(239, 68, 68, 0.14);
}

.fallback-pin {
  position: relative;
  width: 46rpx;
  height: 50rpx;
  margin-top: 4rpx;
}

.fallback-pin image {
  position: relative;
  z-index: 2;
  width: 46rpx;
  height: 46rpx;
  filter: drop-shadow(0 6rpx 12rpx rgba(37, 99, 235, 0.24));
}

.fallback-pulse {
  position: absolute;
  z-index: 1;
  left: 50%;
  top: 44%;
  width: 56rpx;
  height: 56rpx;
  margin-left: -28rpx;
  margin-top: -28rpx;
  border-radius: 999rpx;
  background: rgba(239, 68, 68, 0.18);
  border: 3rpx solid rgba(239, 68, 68, 0.4);
  animation: fallback-pulse 1.8s cubic-bezier(0.2, 0.7, 0.2, 1) infinite;
}

.fallback-badge {
  position: absolute;
  z-index: 4;
  right: -12rpx;
  top: -8rpx;
  min-width: 30rpx;
  height: 30rpx;
  padding: 0 6rpx;
  border-radius: 999rpx;
  text-align: center;
  line-height: 30rpx;
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 800;
  background: linear-gradient(180deg, #ef4444, #dc2626);
  box-shadow: 0 6rpx 16rpx rgba(220, 38, 38, 0.36);
}

@keyframes fallback-pulse {
  0% { transform: scale(0.72); opacity: 0.9; }
  68% { transform: scale(1.72); opacity: 0; }
  100% { transform: scale(1.72); opacity: 0; }
}

/* #ifdef H5 */
:deep(.amap-logo),
:deep(.amap-copyright) {
  display: none !important;
}
/* #endif */
</style>
