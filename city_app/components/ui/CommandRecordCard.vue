<template>
  <view class="command-record-card" @tap="$emit('tap')">
    <view class="command-record-card__head">
      <view class="command-record-card__title">{{ title }}</view>
      <view class="command-record-card__tag" :class="'command-record-card__tag--' + tone" v-if="tag">{{ tag }}</view>
    </view>
    <view class="command-record-card__desc" v-if="desc">{{ desc }}</view>
    <view class="command-record-card__meta" v-if="meta">{{ meta }}</view>
    <slot></slot>
  </view>
</template>

<script>
export default {
  name: 'CommandRecordCard',
  props: {
    title: { type: String, default: '' },
    desc: { type: String, default: '' },
    meta: { type: String, default: '' },
    tag: { type: String, default: '' },
    tone: { type: String, default: 'blue' },
  },
};
</script>

<style scoped lang="scss">
.command-record-card {
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(205, 225, 246, 0.92);
  box-shadow: 0 10rpx 26rpx rgba(4, 29, 54, 0.10);
  padding: 22rpx;
  box-sizing: border-box;
}

.command-record-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.command-record-card__title {
  min-width: 0;
  color: #0f2238;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.35;
}

.command-record-card__tag {
  flex-shrink: 0;
  min-height: 42rpx;
  padding: 0 14rpx;
  border-radius: 999rpx;
  background: rgba(24, 168, 255, 0.12);
  color: #0b6fc6;
  border: 1rpx solid rgba(24, 168, 255, 0.18);
  display: flex;
  align-items: center;
  font-size: 21rpx;
  font-weight: 900;
}

.command-record-card__tag--green { background: rgba(22, 163, 74, 0.10); color: #15803d; border-color: rgba(22, 163, 74, 0.18); }
.command-record-card__tag--amber { background: rgba(245, 158, 11, 0.12); color: #b45309; border-color: rgba(245, 158, 11, 0.20); }
.command-record-card__tag--red { background: rgba(239, 68, 68, 0.10); color: #dc2626; border-color: rgba(239, 68, 68, 0.18); }
.command-record-card__tag--rose { background: rgba(219, 39, 119, 0.10); color: #be185d; border-color: rgba(219, 39, 119, 0.18); }

.command-record-card__desc,
.command-record-card__meta {
  margin-top: 10rpx;
  color: #61758e;
  font-size: 22rpx;
  line-height: 1.45;
}
</style>
