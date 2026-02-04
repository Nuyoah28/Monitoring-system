<template>
  <div class="panel">
      <div id="demoDiv">
          <div class="temperature">
              <div class="inhouse">
                  <img src="../../public/assets/weather/inweather.png" alt="室内温度">
                  <span>湿度</span>
                  <h3>{{ humidity }} %</h3>
              </div>
              <div class="outhouse">
                  <img src="../../public/assets/weather/outerweather.png" alt="室外温度">
                  <span>温度</span>
                  <h3>{{ temperature }} °C</h3>
              </div>
          </div>

          <div class="weather">
              <div class="day" v-for="(item, index) in day" :key="index">
                  <h4>{{ item.date.substring(5) }}</h4>
                  <img :src="getimg(item.dayweather)">
                  <span>{{ item.nighttemp }} ~ {{ item.daytemp }} °C</span>
              </div>
          </div>
      </div>

      <div class="panel-footer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import axios from 'axios';
import { useAlarmStore } from '@/stores/alarm';
import { useAppStore } from '@/stores/app';
import { useUserStore } from '@/stores/user';
import { storeToRefs } from 'pinia';

// 定义天气数据接口
interface WeatherDay {
  date: string;
  dayweather: string;
  daytemp: string;
  nighttemp: string;
}

// 定义后端返回的天气数据接口
interface WeatherData {
  id: number;
  monitorId: number;
  temperature: number;
  humidity: number;
  weather: string;
  createTime: string;
}

const alarmStore = useAlarmStore();
const appStore = useAppStore();
const userStore = useUserStore();
const { getFutureWeather } = storeToRefs(alarmStore);

// 当前摄像头的天气数据
const currentWeather = ref<WeatherData | null>(null);

// 湿度
const humidity = computed(() => currentWeather.value?.humidity ?? '--');
// 温度
const temperature = computed(() => currentWeather.value?.temperature ?? '--');
// 天气情况
const weather = computed(() => currentWeather.value?.weather ?? '--');
// 预测三天的数据
const day = computed(() => getFutureWeather.value);

const getimg = (state: string): string => {
    // console.log(state);
    if (state === '多云') {
        return require('../../public/assets/weather/cloud.png');
    } else if (state === '小雨') {
        return require('../../public/assets/weather/smallrain.png');
    } else if(state === '中雨'){
      return require('../../public/assets/weather/midrain.png')
    } else if(state === '大雨'){
      return require('../../public/assets/weather/bigrain.png')
    } else if(state === '阴'){
      return require('../../public/assets/weather/overcastsky.png')
    } else if(state === '暴雨'){
      return require('../../public/assets/weather/rainstorm.png')
    } else if(state === '雷阵雨'){
      return require('../../public/assets/weather/thundershower.png')
    } else {
      //晴
      return require('../../public/assets/weather/sun.png')
    }
};

// 从后端获取最新的天气数据
const fetchWeatherData = (): void => {
    const monitorId = appStore.getMonitorId;
    const token = userStore.token;

    if (monitorId === 0) {
        console.log('monitorId为0，跳过天气数据获取');
        return;
    }

    axios.get(`/api/v1/weather/newest/${monitorId}`, {
        headers: {
            'Authorization': token
        }
    })
    .then((response: any) => {
        console.log('收到天气数据:', response.data);
        if (response.data.code === '00000' && response.data.data) {
            currentWeather.value = response.data.data;
        }
    })
    .catch((error: any) => {
        console.log('天气数据获取失败:', error);
    });
};

let intervalId: number | null = null;

// 每2分钟获取一次天气数据
const startFetching = (): void => {
    intervalId = window.setInterval(() => {
        fetchWeatherData();
    }, 120000); // 每120000ms（2分钟）请求一次数据
};

onMounted(() => {
    fetchWeatherData(); // 初始获取天气数据
    startFetching(); // 开始定时获取数据
});

// 清理定时器
onUnmounted(() => {
    if(intervalId) {
        clearInterval(intervalId);
    }
});
</script>

<style scoped>
#demoDiv {
  width: 100%;
  height: 100%;
  color: white;
}

h2 {
  color: white;
}

.temperature span {
  font-size: 2rem;
  color: white;
  margin-left: 0.5rem;
}

.temperature {
  width: 30rem;
  height: 8rem;
  display: flex;
}

.temperature div {
  width: 50%;
  height: 80%;
  padding-top: 1rem;
}

.inhouse h3 {
  color: #4B9DD1;
}

.outhouse h3 {
  color: #A04157;
}

.temperature img {
  width: 2rem;
  height: 2rem;
}

h3 {
  margin-top: 0.8rem;
  font-size: 2rem;
}

.weather {
  margin-top: 0.8rem;
  width: 100%;
  display: flex;
  color: white;
}

.day {
  flex: 1;
  border-right: 0.25rem solid skyblue;
  font-size: 1.6rem;
}

.day:nth-child(3) {
  border-right: none;
}

.day img {
  display: block;
  width: 2.5rem;
  height: 2.5rem;
  margin: 0 auto;
  margin-bottom: 0.3rem;
}

h4 {
  font-size: 1.7rem;
  margin-bottom: 0.5rem;
}
</style>
