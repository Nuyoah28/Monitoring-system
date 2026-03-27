<template>
  <view class="map" ref="map">
	  <web-view src="/static/html/map.html" class="web-view" style="width: 100%;height: 92%;position: relative;" :fullscreen="false">
		  
	  </web-view>
  </view>
</template>

<script>
var wv;//计划创建的webview
export default {
  name: 'map-1',
  data() {
	  return {
		 
	  }
  },
  
  onReady() {
  		// #ifdef APP-PLUS
  		    const currentWebview = this.$scope.$getAppWebview();
  		    if (currentWebview.children().length > 0) {
  		      const wv = currentWebview.children()[0];
  		      wv.setStyle({
  		        top: parseInt(this.webViewTop),
  		        height: parseInt(this.webViewHeight)
  		      });
  		    } else {
  		      console.warn('没有找到子webview');
  		    }
  		    // #endif
  	}
}
</script>

<style scoped>

.map {
	bottom: 0;
	height: 90%;
}
</style>
