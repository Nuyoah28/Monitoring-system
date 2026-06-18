<template>
  <view class="command-empty">
    <view class="command-empty__icon">
      <u-icon :name="icon" color="#7da2c7" size="42rpx"></u-icon>
    </view>
    <view class="command-empty__title">{{ title }}</view>
    <view class="command-empty__desc" v-if="desc">{{ desc }}</view>
  </view>
</template>

<script>
export default {
  name: 'CommandEmptyState',
  props: {
    title: { type: String, default: '暂无数据' },
    desc: { type: String, default: '' },
    icon: { type: String, default: 'empty-data' },
  },
};
</script>

<style scoped lang="scss">
.command-empty {
  min-height: 168rpx;
  border-radius: 24rpx;
  background: rgba(245, 250, 255, 0.92);
  border: 1rpx dashed #c7ddf3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24rpx;
  box-sizing: border-box;
}

.command-empty__icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #eaf4ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.command-empty__title {
  margin-top: 12rpx;
  color: #0f2238;
  font-size: 25rpx;
  font-weight: 900;
}

.command-empty__desc {
  margin-top: 6rpx;
  color: #61758e;
  font-size: 21rpx;
  font-weight: 700;
  text-align: center;
}
</style>
