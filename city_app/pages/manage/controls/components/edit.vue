<template>
  <u-modal
    :show="showEdit"
    :closeOnClickOverlay="true"
    :showCancelButton="true"
    @confirm="checkChange"
    @cancel="changeShow"
    @close="changeShow"
    width="348px"
  >
    <view class="informBox" v-show="showEdit">
      <view class="titleBox">
        <view class="title">{{ dialogTitle }}</view>
        <view class="img" @tap="locked = !locked">
          <image
            :src="locked ? '../../../static/lock.png' : '../../../static/unlock.png'"
            mode="aspectFit"
          ></image>
        </view>
      </view>

      <scroll-view scroll-y class="dialog-scroll">
        <view class="panel panel--preview">
          <view class="panel-head">
            <text>区域预览</text>
            <text class="panel-tag">当前截图画面</text>
          </view>

          <view class="preview-box">
            <image
              v-if="img"
              :src="img.replace(/[\r\n]/g, '')"
              mode="aspectFit"
              class="snapshot"
              @load="onSnapshotLoad"
            ></image>
            <view v-else class="snapshot placeholder">
              <text>截图加载中…</text>
            </view>
            <view
              class="border border--preview"
              v-for="(box, index) in border"
              :key="`preview-${index}`"
              :style="boxStyle(box)"
            ></view>
          </view>

          <view class="panel-tip">
            上方用于确认当前画面和已选区域，下方用于实际框选。
          </view>
        </view>

        <view class="panel panel--editor">
          <view class="panel-head panel-head--line">
            <text>区域编辑</text>
            <view class="action-chip action-chip--warn" @tap="resetBorder">清空区域</view>
          </view>
          <view class="panel-tip panel-tip--compact">
            请在截图上框选需要识别的区域，框选结果会同步到算法端。
          </view>

          <view class="editor-frame">
            <view
              class="draw-layer"
              :class="{ 'draw-layer--locked': locked }"
              @touchstart.stop.prevent="start"
              @touchmove.stop.prevent="move"
              @touchend.stop.prevent="stop"
              @touchcancel.stop.prevent="stop"
            ></view>
            <image
              v-if="img"
              :src="img.replace(/[\r\n]/g, '')"
              mode="aspectFit"
              class="snapshot"
            ></image>
            <view v-else class="snapshot placeholder">
              <text>截图加载中…</text>
            </view>
            <view
              class="border"
              v-for="(box, index) in border"
              :key="`img-${index}`"
              :style="boxStyle(box)"
            ></view>
          </view>
        </view>

        <view class="panel panel--abilities">
          <view class="panel-head panel-head--line">
            <text>识别能力</text>
            <view class="action-chip action-chip--ghost" @tap="resetAbilities">恢复默认</view>
          </view>
          <view class="panel-tip panel-tip--compact">
            勾选后保存即可生效，已选能力会在下次打开时回显。
          </view>

          <view class="options">
            <checkbox-group @change="checkboxChange" class="group">
              <view class="borderBox" v-for="item in ability" :key="item.value">
                <label class="uni-list-cell uni-list-cell-pd checkbox">
                  <view>
                    <checkbox :value="String(item.value)" :checked="item.checked" />
                  </view>
                  <view>{{ item.name }}</view>
                </label>
              </view>
            </checkbox-group>
          </view>
        </view>
      </scroll-view>
    </view>
  </u-modal>
</template>

<script>
import { throttle } from "lodash";

export default {
  name: "Edit",
  props: {
    showEdit: {
      type: Boolean,
      default: false,
    },
    warnData: {
      type: Object,
      default: () => ({}),
    },
    monitorData: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      locked: true,
      startPoint: {
        x: null,
        y: null,
      },
      border: [],
      sourceBorder: null,
      borData: {},
      painting: false,
      ability: [],
      img: "",
      moveThrottle: null,
      drawRect: {
        left: 0,
        top: 0,
        width: 328,
        height: 246,
      },
      sourceSize: {
        width: 640,
        height: 480,
      },
      imageRect: {
        left: 0,
        top: 0,
        width: 328,
        height: 246,
      },
    };
  },
  computed: {
    currentWarnData() {
      return this.warnData || {};
    },
    currentMonitorData() {
      return this.monitorData || {};
    },
    dialogTitle() {
      return this.currentWarnData.name || "未命名摄像头";
    },
  },
  created() {
    this.moveThrottle = throttle((newPoint) => {
      this.updateDraftBorder(newPoint);
    }, 32);
    this.resetAbilities();
  },
  beforeDestroy() {
    if (this.moveThrottle && this.moveThrottle.cancel) {
      this.moveThrottle.cancel();
    }
  },
  watch: {
    showEdit(val) {
      if (val) {
        this.initDialog();
      }
    },
  },
  methods: {
    initDialog() {
      this.locked = false;
      this.painting = false;
      this.startPoint = {
        x: null,
        y: null,
      };
      this.borData = {};
      this.img = "";
      this.sourceBorder = this.getInitialSourceBorder();
      this.border = this.sourceBorder ? [this.sourceBoxToDisplayBox(this.sourceBorder)] : [];
      this.resetAbilities();
      this.applyBackendAbilities();
      this.syncDangerAreaByBorder();
      this.getImg();
      this.queryDrawRect();
    },
    queryDrawRect() {
      this.$nextTick(() => {
        setTimeout(() => {
          uni
            .createSelectorQuery()
            .in(this)
            .select(".editor-frame")
            .boundingClientRect((rect) => {
              if (!rect || !rect.width || !rect.height) return;
              this.drawRect = {
                left: Number(rect.left) || 0,
                top: Number(rect.top) || 0,
                width: Number(rect.width) || 328,
                height: Number(rect.height) || 246,
              };
              this.updateImageRect();
            })
            .exec();
        }, 80);
      });
    },
    onSnapshotLoad(e) {
      const detail = (e && e.detail) || {};
      const width = Number(detail.width);
      const height = Number(detail.height);
      if (Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0) {
        this.sourceSize = { width, height };
      }
      this.updateImageRect();
      if (!this.painting && this.sourceBorder) {
        this.border = [this.sourceBoxToDisplayBox(this.sourceBorder)].filter(Boolean);
      }
    },
    updateImageRect() {
      const frameWidth = Number(this.drawRect.width) || 328;
      const frameHeight = Number(this.drawRect.height) || 246;
      const sourceWidth = Number(this.sourceSize.width) || 640;
      const sourceHeight = Number(this.sourceSize.height) || 480;
      const sourceRatio = sourceWidth / sourceHeight;
      const frameRatio = frameWidth / frameHeight;
      let width = frameWidth;
      let height = frameHeight;

      if (sourceRatio > frameRatio) {
        height = frameWidth / sourceRatio;
      } else {
        width = frameHeight * sourceRatio;
      }

      this.imageRect = {
        left: (frameWidth - width) / 2,
        top: (frameHeight - height) / 2,
        width,
        height,
      };
    },
    getInitialSourceBorder() {
      const data = this.currentWarnData;
      const legacyBorder = Array.isArray(data.border) ? data.border : [];
      if (legacyBorder.length) {
        const firstBox = legacyBorder
          .map((item) => this.normalizeBox(item))
          .filter(Boolean)[0];
        return firstBox || null;
      }

      const leftX = Number(data.leftX);
      const leftY = Number(data.leftY);
      const rightX = Number(data.rightX);
      const rightY = Number(data.rightY);
      if ([leftX, leftY, rightX, rightY].every((value) => Number.isFinite(value))) {
        return this.normalizeBox({ leftX, leftY, rightX, rightY });
      }

      return null;
    },
    normalizeBox(box) {
      if (!box) return null;
      const leftX = Number(box.leftX);
      const leftY = Number(box.leftY);
      const rightX = Number(box.rightX);
      const rightY = Number(box.rightY);
      if (![leftX, leftY, rightX, rightY].every((value) => Number.isFinite(value))) {
        return null;
      }
      const minX = Math.min(leftX, rightX);
      const maxX = Math.max(leftX, rightX);
      const minY = Math.min(leftY, rightY);
      const maxY = Math.max(leftY, rightY);
      if (maxX - minX < 2 || maxY - minY < 2) {
        return null;
      }
      return {
        leftX: minX,
        leftY: minY,
        rightX: maxX,
        rightY: maxY,
      };
    },
    boxStyle(box) {
      const normalized = this.normalizeBox(box);
      if (!normalized) return {};
      return {
        width: normalized.rightX - normalized.leftX + "px",
        height: normalized.rightY - normalized.leftY + "px",
        top: normalized.leftY + "px",
        left: normalized.leftX + "px",
      };
    },
    async getImg() {
      if (!this.currentWarnData.id) return;
      try {
        const { data } = await uni.$http.get(`/api/v1/monitor/image/${this.currentWarnData.id}`);
        this.img = ("data:image/png;base64," + (data && data.message ? data.message : "")).replace(/[\r\n]/g, "");
      } catch (error) {
        console.warn("[edit-area] 获取监控截图失败：", error);
        this.img = "";
      }
    },
    start(e) {
      if (this.locked) return;
      this.queryDrawRect();
      const point = this.getTouchPoint(e);
      if (!point) return;
      this.startPoint.x = point.x;
      this.startPoint.y = point.y;
      this.painting = true;
      this.border = [];
      this.borData = {
        maxX: point.x,
        minX: point.x,
        maxY: point.y,
        minY: point.y,
      };
    },
    move(e) {
      if (this.locked || !this.painting) return;
      const point = this.getTouchPoint(e);
      if (!point) return;
      if (this.moveThrottle) {
        this.moveThrottle(point);
      }
    },
    stop(e) {
      if (this.locked) return;
      if (this.painting && e) {
        const point = this.getTouchPoint(e);
        if (point) this.updateDraftBorder(point);
      }
      if (this.moveThrottle && this.moveThrottle.cancel) {
        this.moveThrottle.cancel();
      }
      this.painting = false;
      const box = this.normalizeBox({
        leftX: this.borData.minX,
        leftY: this.borData.minY,
        rightX: this.borData.maxX,
        rightY: this.borData.maxY,
      });
      this.border = box ? [box] : [];
      this.sourceBorder = box ? this.displayBoxToSourceBox(box) : null;
      this.syncDangerAreaByBorder();
      this.borData = {};
    },
    getTouchPoint(e) {
      const touch =
        (e && e.touches && e.touches[0]) ||
        (e && e.changedTouches && e.changedTouches[0]) ||
        (e && e.detail) ||
        null;
      if (!touch) return null;

      const rect = this.drawRect || {};
      const pickNumber = (...values) => {
        for (const value of values) {
          const numberValue = Number(value);
          if (Number.isFinite(numberValue)) return numberValue;
        }
        return NaN;
      };
      const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

      const width = Number(rect.width) || 328;
      const height = Number(rect.height) || 246;
      const rectLeft = Number(rect.left) || 0;
      const rectTop = Number(rect.top) || 0;
      const absoluteX = pickNumber(touch.clientX, touch.pageX, touch.screenX);
      const absoluteY = pickNumber(touch.clientY, touch.pageY, touch.screenY);
      let relativeX = pickNumber(touch.offsetX, touch.x);
      let relativeY = pickNumber(touch.offsetY, touch.y);

      if (Number.isFinite(relativeX) && (relativeX > width || relativeX < 0)) {
        relativeX -= rectLeft;
      }
      if (Number.isFinite(relativeY) && (relativeY > height || relativeY < 0)) {
        relativeY -= rectTop;
      }

      const x = Number.isFinite(absoluteX)
        ? absoluteX - rectLeft
        : relativeX;
      const y = Number.isFinite(absoluteY)
        ? absoluteY - rectTop
        : relativeY;

      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      return {
        x: clamp(x, 0, width),
        y: clamp(y, 0, height),
      };
    },
    updateDraftBorder(newPoint) {
      if (!newPoint || !Number.isFinite(Number(this.startPoint.x)) || !Number.isFinite(Number(this.startPoint.y))) {
        return;
      }
      const minX = Math.min(this.startPoint.x, newPoint.x);
      const maxX = Math.max(this.startPoint.x, newPoint.x);
      const minY = Math.min(this.startPoint.y, newPoint.y);
      const maxY = Math.max(this.startPoint.y, newPoint.y);
      this.borData = { minX, maxX, minY, maxY };
      const box = this.normalizeBox({
        leftX: minX,
        leftY: minY,
        rightX: maxX,
        rightY: maxY,
      });
      this.border = box ? [box] : [];
    },
    sourceBoxToDisplayBox(box) {
      const normalized = this.normalizeBox(box);
      if (!normalized) return null;
      const sourceWidth = Number(this.sourceSize.width) || 640;
      const sourceHeight = Number(this.sourceSize.height) || 480;
      const imageRect = this.imageRect || {};
      const displayLeft = Number(imageRect.left) || 0;
      const displayTop = Number(imageRect.top) || 0;
      const displayWidth = Number(imageRect.width) || 328;
      const displayHeight = Number(imageRect.height) || 246;

      return this.normalizeBox({
        leftX: displayLeft + normalized.leftX / sourceWidth * displayWidth,
        leftY: displayTop + normalized.leftY / sourceHeight * displayHeight,
        rightX: displayLeft + normalized.rightX / sourceWidth * displayWidth,
        rightY: displayTop + normalized.rightY / sourceHeight * displayHeight,
      });
    },
    displayBoxToSourceBox(box) {
      const normalized = this.normalizeBox(box);
      if (!normalized) return null;
      const sourceWidth = Number(this.sourceSize.width) || 640;
      const sourceHeight = Number(this.sourceSize.height) || 480;
      const imageRect = this.imageRect || {};
      const displayLeft = Number(imageRect.left) || 0;
      const displayTop = Number(imageRect.top) || 0;
      const displayWidth = Number(imageRect.width) || 328;
      const displayHeight = Number(imageRect.height) || 246;
      const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

      const convertX = (value) => clamp(Math.round((value - displayLeft) / displayWidth * sourceWidth), 0, sourceWidth);
      const convertY = (value) => clamp(Math.round((value - displayTop) / displayHeight * sourceHeight), 0, sourceHeight);

      return this.normalizeBox({
        leftX: convertX(normalized.leftX),
        leftY: convertY(normalized.leftY),
        rightX: convertX(normalized.rightX),
        rightY: convertY(normalized.rightY),
      });
    },
    changeShow() {
      this.$emit("change", false);
    },
    resetAbilities() {
      this.ability = [
        {
          name: "危险区域",
          value: 1,
          checked: false,
        },
        {
          name: "挥手",
          value: 2,
          checked: false,
        },
        {
          name: "摔倒",
          value: 3,
          checked: false,
        },
        {
          name: "明火",
          value: 4,
          checked: false,
        },
        {
          name: "吸烟",
          value: 5,
          checked: false,
        },
        {
          name: "打拳",
          value: 6,
          checked: false,
        },
        {
          name: "垃圾检测",
          value: 8,
          checked: false,
        },
        {
          name: "积冰检测",
          value: 9,
          checked: false,
        },
        {
          name: "电瓶车",
          value: 10,
          checked: false,
        },
        {
          name: "载具占道",
          value: 11,
          checked: false,
        },
      ];
    },
    applyBackendAbilities() {
      const backendCheckedList = Array.isArray(this.currentWarnData.ability)
        ? this.currentWarnData.ability
        : [];
      this.ability.forEach((item) => {
        const match = backendCheckedList.find((backendItem) => Number(backendItem && backendItem.value) === Number(item.value));
        item.checked = !!(match && match.checked);
      });
    },
    syncDangerAreaByBorder() {
      if (this.hasValidBorder()) {
        this.setAbilityChecked(1, true);
      }
    },
    setAbilityChecked(value, checked) {
      const target = this.ability.find((item) => Number(item.value) === Number(value));
      if (target) {
        target.checked = checked;
      }
    },
    isAbilityChecked(value) {
      const target = this.ability.find((item) => Number(item.value) === Number(value));
      return !!(target && target.checked);
    },
    resetBorder() {
      this.border = [];
      this.sourceBorder = null;
      this.painting = false;
      this.borData = {};
      this.setAbilityChecked(1, false);
    },
    hasValidBorder() {
      return !!this.normalizeBox(this.border && this.border[0]);
    },
    buildPayload() {
      const displayBorder = this.normalizeBox(this.border && this.border[0]);
      const sourceBorder = displayBorder ? this.displayBoxToSourceBox(displayBorder) : null;
      const hasBorder = !!sourceBorder;

      if (!hasBorder && this.isAbilityChecked(1)) {
        uni.showToast({
          title: "请先绘制识别区域",
          icon: "none",
        });
        return null;
      }

      const payload = {
        id: this.currentWarnData.id,
        name: this.currentWarnData.name,
        area: this.currentWarnData.department,
        leader: this.currentWarnData.leader,
        ip: this.currentWarnData.video,
        longitude: this.currentMonitorData.longitude,
        latitude: this.currentMonitorData.latitude,
        fall: this.isAbilityChecked(3),
        flame: this.isAbilityChecked(4),
        smoke: this.isAbilityChecked(5),
        wave: this.isAbilityChecked(2),
        punch: this.isAbilityChecked(6),
        rubbish: this.isAbilityChecked(8),
        ice: this.isAbilityChecked(9),
        ebike: this.isAbilityChecked(10),
        vehicle: this.isAbilityChecked(11),
        dangerArea: hasBorder,
      };

      if (hasBorder) {
        payload.leftX = Math.floor(sourceBorder.leftX);
        payload.leftY = Math.floor(sourceBorder.leftY);
        payload.rightX = Math.floor(sourceBorder.rightX);
        payload.rightY = Math.floor(sourceBorder.rightY);
      }

      return payload;
    },
    async checkChange() {
      const payload = this.buildPayload();
      if (!payload) return;

      uni.showModal({
        title: "警告",
        content: "确定修改?",
        showCancel: true,
        success: async (res) => {
          if (!res.confirm) return;
          try {
            const { data } = await uni.$http.post("/api/v1/monitor/update", payload);
            if (data && data.code === "00000") {
              uni.showToast({ title: "保存成功", icon: "success" });
              this.$emit("change", true);
            } else {
              uni.showToast({ title: (data && data.message) || "保存失败", icon: "none" });
            }
          } catch (error) {
            console.warn("[edit-area] 保存失败：", error);
            uni.showToast({ title: "保存失败", icon: "none" });
          }
        },
      });
    },
    checkboxChange(e) {
      const values = (((e && e.detail && e.detail.value) || (e && e.target && e.target.value)) || []).map((value) => String(value));
      this.ability.forEach((item) => {
        item.checked = values.includes(String(item.value));
      });
      this.syncDangerAreaByBorder();
    },
    limitation(item) {
      item.time = Math.abs(item.time);
    },
  },
};
</script>

<style lang="scss" scoped>
.informBox {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-sizing: border-box;

  .border {
    border: 1px dotted red;
    position: absolute;
    background-color: rgba(red, 0.4);
    z-index: 15;
    box-sizing: border-box;
    pointer-events: none;
  }

  .titleBox {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12rpx;

    .title {
      font-size: 34rpx;
      font-weight: bold;
      color: #1a2a3a;
      line-height: 1.3;
      padding-right: 12rpx;
    }

    .img {
      width: 48rpx;
      height: 48rpx;
      flex-shrink: 0;

      image {
        height: 100%;
        width: 100%;
      }
    }
  }

  .dialog-scroll {
    width: 100%;
    max-height: 74vh;
    box-sizing: border-box;
  }

  .panel {
    width: 100%;
    padding: 18rpx;
    border-radius: 20rpx;
    background: #fff;
    border: 1rpx solid #dcebfa;
    box-sizing: border-box;
    margin-bottom: 14rpx;
  }

  .panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12rpx;
    margin-bottom: 12rpx;

    text {
      font-size: 26rpx;
      font-weight: 800;
      color: #1a2a3a;
    }
  }

  .panel-head--line {
    margin-bottom: 10rpx;
  }

  .panel-tag {
    font-size: 18rpx;
    color: #64748b;
    font-weight: 600;
    flex-shrink: 0;
  }

  .panel-tip {
    margin-top: 10rpx;
    font-size: 20rpx;
    color: #64748b;
    line-height: 1.45;
  }

  .preview-box {
    width: 328px;
    max-width: 100%;
    height: 190px;
    margin: 0 auto;
    position: relative;
    border-radius: 16rpx;
    overflow: hidden;
    background: #edf6ff;
  }

  .border--preview {
    z-index: 6;
    border-color: rgba(220, 38, 38, 0.8);
    background-color: rgba(220, 38, 38, 0.14);
  }

  .editor-frame {
    overflow: hidden;
    width: 328px;
    max-width: 100%;
    height: 246px;
    position: relative;
    border-radius: 16rpx;
    background: #edf6ff;
    margin: 10rpx auto 0;
    touch-action: none;
  }

  .snapshot {
    width: 100%;
    height: 100%;
  }

  .placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    font-size: 22rpx;
    background: linear-gradient(180deg, #f7fbff 0%, #eef6ff 100%);
  }

  .draw-layer {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10;
    width: 100%;
    height: 100%;
    background: transparent;
    touch-action: none;
  }

  .draw-layer--locked {
    pointer-events: none;
  }

  .action-chip {
    min-width: 90rpx;
    padding: 8rpx 14rpx;
    border-radius: 999rpx;
    text-align: center;
    font-size: 20rpx;
    font-weight: 800;
    box-sizing: border-box;
  }

  .action-chip--warn {
    background: #fff1f2;
    color: #dc2626;
  }

  .action-chip--ghost {
    background: #edf6ff;
    color: #1470d8;
  }

  .options {
    width: 100%;

    .group {
      display: flex;
      flex-wrap: wrap;
      width: 100%;
      padding: 0;
      box-sizing: border-box;
      gap: 10rpx;
    }

    .borderBox {
      width: calc(50% - 5rpx);
      box-sizing: border-box;

      .checkbox {
        display: flex;
        align-items: center;
        gap: 10rpx;
        border: 1px solid #d8e5f5;
        padding: 10rpx 12rpx;
        width: 100%;
        border-radius: 14rpx;
        background: #f8fbff;
        box-sizing: border-box;
        font-size: 22rpx;
        color: #1f2d3d;
      }

      .time {
        width: 36%;
        height: 36px;
        background-color: #e5e5e5;
        border-radius: 4px;
      }
    }
  }
}
</style>
