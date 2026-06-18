<template>
  <view class="command-feature-grid" :style="gridStyle">
    <view
      v-for="item in items"
      :key="item.key || item.path || item.label"
      class="command-feature"
      @tap="$emit('select', item)"
    >
      <view class="command-feature__icon" :class="'command-feature__icon--' + (item.tone || 'blue')">
        <u-icon v-if="item.icon" :name="item.icon" color="#ffffff" size="38rpx"></u-icon>
        <text v-else>{{ item.iconText || item.label.slice(0, 1) }}</text>
      </view>
      <view class="command-feature__label">{{ item.label }}</view>
      <view class="command-feature__hint" v-if="item.hint">{{ item.hint }}</view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'CommandFeatureGrid',
  props: {
    items: {
      type: Array,
      default: () => [],
    },
    columns: {
      type: Number,
      default: 3,
    },
  },
  computed: {
    gridStyle() {
      return {
        gridTemplateColumns: 'repeat(' + this.columns + ', 1fr)',
      };
    },
  },
};
</script>

<style scoped lang="scss">
.command-feature-grid {
  display: grid;
  gap: 14rpx;
}

.command-feature {
  min-height: 140rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(243, 249, 255, 0.98));
  border: 1rpx solid #cde1f6;
  box-shadow: 0 10rpx 22rpx rgba(4, 29, 54, 0.10);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 18rpx 10rpx;
  box-sizing: border-box;
}

.command-feature:active {
  transform: scale(0.98);
}

.command-feature__icon {
  width: 70rpx;
  height: 70rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 25rpx;
  font-weight: 900;
  border: 1rpx solid rgba(255, 255, 255, 0.42);
  box-shadow: 0 10rpx 18rpx rgba(4, 29, 54, 0.14);
}

.command-feature__icon--blue { background: linear-gradient(180deg, #0b6fc6 0%, #18a8ff 100%); }
.command-feature__icon--cyan { background: linear-gradient(180deg, #0891b2 0%, #20d6d2 100%); }
.command-feature__icon--green { background: linear-gradient(180deg, #15803d 0%, #22c55e 100%); }
.command-feature__icon--amber { background: linear-gradient(180deg, #d97706 0%, #fbbf24 100%); }
.command-feature__icon--red { background: linear-gradient(180deg, #ef4444 0%, #fb7185 100%); }
.command-feature__icon--purple { background: linear-gradient(180deg, #6d28d9 0%, #a78bfa 100%); }
.command-feature__icon--rose { background: linear-gradient(180deg, #db2777 0%, #fb7185 100%); }
.command-feature__icon--slate { background: linear-gradient(180deg, #1e293b 0%, #64748b 100%); }

.command-feature__label {
  margin-top: 12rpx;
  color: #0f2238;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1.2;
  text-align: center;
}

.command-feature__hint {
  margin-top: 5rpx;
  color: #61758e;
  font-size: 19rpx;
  font-weight: 700;
  line-height: 1.2;
  text-align: center;
}
</style>
