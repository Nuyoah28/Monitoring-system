<template>
  <view class="command-stat" :class="'command-stat--' + tone" @tap="$emit('tap')">
    <view class="command-stat__label">{{ label }}</view>
    <view class="command-stat__value">{{ value }}</view>
    <view class="command-stat__desc" v-if="desc">{{ desc }}</view>
  </view>
</template>

<script>
export default {
  name: 'CommandStatCard',
  props: {
    label: { type: String, default: '' },
    value: { type: [String, Number], default: '--' },
    desc: { type: String, default: '' },
    tone: { type: String, default: 'blue' },
  },
};
</script>

<style scoped lang="scss">
.command-stat {
  min-height: 122rpx;
  border-radius: 24rpx;
  padding: 18rpx;
  box-sizing: border-box;
  background: #fff;
  border: 1rpx solid #cde1f6;
  box-shadow: 0 10rpx 22rpx rgba(4, 29, 54, 0.10);
  border-top: 5rpx solid #18a8ff;
}

.command-stat--green { border-top-color: #16a34a; }
.command-stat--amber { border-top-color: #f59e0b; }
.command-stat--red { border-top-color: #ef4444; }
.command-stat--rose { border-top-color: #db2777; }
.command-stat--slate { border-top-color: #64748b; }

.command-stat__label {
  color: #61758e;
  font-size: 21rpx;
  font-weight: 800;
}

.command-stat__value {
  margin-top: 10rpx;
  color: #0f2238;
  font-size: 38rpx;
  line-height: 1;
  font-weight: 900;
}

.command-stat__desc {
  margin-top: 8rpx;
  color: #61758e;
  font-size: 20rpx;
  font-weight: 700;
}
</style>
