<template>
  <div class="simulate-app">
    <h1>大屏演示遥控器</h1>
    <p>在一个单独的窗口或副屏中打开此页面，点击下方按钮即可向大屏发送实时报警推送（纯前端模拟）。</p>
    
    <div class="btn-group">
      <button class="sim-btn bike" @click="sendAlarm('bike')">⚡ 电动车进楼</button>
      <button class="sim-btn fire" @click="sendAlarm('fire')">🔥 烟雾火灾</button>
      <button class="sim-btn garbage" @click="sendAlarm('garbage')">🗑️ 垃圾桶溢出</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { baseUrl } from '@/config/config'

const channel = new BroadcastChannel('demonstration_channel');

const sendAlarm = async (type: string) => {
  // 1. 本地广播 (仅限同浏览器，作为即时反馈保留)
  channel.postMessage({
    action: 'trigger_alarm',
    type: type
  });
  
  // 2. 后端中转 (关键！解决跨设备问题)
  // 根据类型映射后端需要的 caseType
  // 1:进入危险区域, 5:明火, 10:电动车进楼, 8:垃圾乱放
  let caseType = 1;
  let clipId = 'SIM_BIKE';
  
  if (type === 'bike') {
    caseType = 10;
    clipId = 'SIM_BIKE_DEMO';
  } else if (type === 'fire') {
    caseType = 5;
    clipId = 'SIM_FIRE_DEMO';
  } else if (type === 'garbage') {
    caseType = 8;
    clipId = 'SIM_GARBAGE_DEMO';
  }

  try {
    // 调用后端现成的接收接口
    await axios.post(`${baseUrl}/api/v1/alarm/receive`, null, {
      params: {
        cameraId: 1,
        caseType: caseType,
        clipId: clipId
      }
    });
    ElMessage({ message: '演示指令已通过云端同步到所有设备', type: 'success' });
  } catch (err) {
    console.error('指令中转失败:', err);
    ElMessage({ message: '本地指令已发送，但云端转发失败，请检查后端服务', type: 'warning' });
  }
}
</script>

<style scoped>
.simulate-app {
  padding: 40px;
  background: #0f172a;
  min-height: 100vh;
  color: #fff;
  text-align: center;
  font-family: sans-serif;
}

h1 {
  margin-bottom: 10px;
  color: #63b8ff;
}

p {
  color: #94a3b8;
  margin-bottom: 40px;
}

.btn-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 300px;
  margin: 0 auto;
}

.sim-btn {
  padding: 15px 20px;
  font-size: 18px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.1s, opacity 0.2s;
  color: white;
}

.sim-btn:active {
  transform: scale(0.95);
}

.sim-btn:hover {
  opacity: 0.9;
}

.bike { background: #eab308; }
.fire { background: #ef4444; }
.garbage { background: #3b82f6; }
</style>
