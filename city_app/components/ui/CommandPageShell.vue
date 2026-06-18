<template>
  <view class="command-page-shell" :style="{ paddingTop: topPadding + 'px' }">
    <slot></slot>
  </view>
</template>

<script>
export default {
  name: 'CommandPageShell',
  props: {
    topPadding: {
      type: Number,
      default: 0,
    },
  },
};
</script>

<style scoped lang="scss">
.command-page-shell {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  padding: 0 24rpx 140rpx;
  box-sizing: border-box;
  background:
    linear-gradient(125deg, rgba(32, 214, 210, 0.14) 0%, rgba(32, 214, 210, 0) 34%),
    linear-gradient(180deg, #071525 0%, #0d2740 300rpx, #edf5ff 640rpx, #f8fbff 100%);
}
</style>
