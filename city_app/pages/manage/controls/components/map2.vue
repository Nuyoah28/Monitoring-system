<template>
	<view class="global">
		<view class="header">															
			<view id="allmap" class="map"></view>
		</view>		
	</view>
</template>
 
<script>	
	export default {		
		data() {
			return {
							
			}
		},		
		mounted() {
						
		},
		methods: {			
			
		}
	}
</script>
 
<script module="map" lang="renderjs">
	import { mymap } from "@/api/map.js";	
	var map = null;
	export default {
		data() {
			return {
				ak: 'Udc5Wc9ZWfXlKoikxaxRyb2k3KJI8faY'
			}
		},
		mounted() {			
			document.getElementById('allmap').style.height = '500px'; // 强制设置高度

				// ================百度地图==================
				mymap(this.ak).then((mymap) => {
					// 创建百度地图实例				
					map = new BMapGL.Map("allmap");
					const mapContainer = document.getElementById('allmap');
					console.log('Map container height:', mapContainer.clientHeight); // 调试输出容器的高度
					console.log(map, 'this.map ')
					var point = new BMapGL.Point(117.147001,39.0682);  // 创建点坐标 
					  map.centerAndZoom(point, 18);                 // 初始化地图，设置中心点坐标和地图级别
				
					  map.enableScrollWheelZoom(true);     //开启鼠标滚轮缩放
				
					  map.setHeading(0);   //设置地图旋转角度
					  map.setTilt(0);       //设置地图的倾斜角度
				
					  var scaleCtrl = new BMapGL.ScaleControl();  // 添加比例尺控件
					  map.addControl(scaleCtrl);
					  var zoomCtrl = new BMapGL.ZoomControl();  // 添加缩放控件
					  map.addControl(zoomCtrl);
				
					  var cityCtrl = new BMapGL.CityListControl();  // 添加城市列表控件
					  map.addControl(cityCtrl);
				
				
					  // 创建标记点并添加到地图上
					  var marker = new BMapGL.Marker(point); // 创建标记点
					  map.addOverlay(marker); // 将标记点添加到地图上
				
					  // 将地图中心设置为标记点的位置
					  map.setCenter(point); // 设置地图中心为标记点										
				});
		},
		methods: {			
			updateEcharts(newValue, oldValue, ownerInstance, instance) {
				// 监听 service 层数据变更
				
				// app端监听数据变化调用方法								
			},			
			onClick(event, ownerInstance) {
				// 调用 service 层的方法					
			},			
		}
	}
</script>
<style>	
<style lang="scss" scoped>
	    
	.global {
		height: 500px;  // 让父元素满屏
		width: 100%;
		
		.header {
			height: 500px;
			width: 100%;
			
			.map {
				width: 100%;
				height: 500px;
			}
		}
	}
	
</style>
 
 