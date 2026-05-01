<template>
  <div class="simulate-app">
    <div class="simulate-shell">
      <div class="simulate-hero">
        <span class="simulate-badge">联动控制台</span>
        <h1>事件联动控制台</h1>
        <p>用于联动报警场景触发与跨端消息同步，支持值守人员快速校验平台联动链路。</p>
      </div>

      <div class="btn-group">
        <button class="sim-btn bike" @click="sendAlarm('bike')">
          <span class="sim-icon">01</span>
          <span class="sim-copy">
            <strong>电动车进楼</strong>
            <em>高危场景联动预警</em>
          </span>
        </button>
        <button class="sim-btn fire" @click="sendAlarm('fire')">
          <span class="sim-icon">02</span>
          <span class="sim-copy">
            <strong>烟雾火灾</strong>
            <em>火情感知与快速响应</em>
          </span>
        </button>
        <button class="sim-btn garbage" @click="sendAlarm('garbage')">
          <span class="sim-icon">03</span>
          <span class="sim-copy">
            <strong>垃圾桶溢出</strong>
            <em>环境异常事件推送</em>
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { baseUrl, simulateChannelName } from '@/config/config'

const channel = new BroadcastChannel(simulateChannelName)

const sendAlarm = async (type: string) => {
  channel.postMessage({
    action: 'trigger_alarm',
    type: type
  })

  let caseType = 1
  let clipId = 'SIM_BIKE'

  if (type === 'bike') {
    caseType = 10
    clipId = 'SIM_BIKE'
  } else if (type === 'fire') {
    caseType = 5
    clipId = 'SIM_FIRE'
  } else if (type === 'garbage') {
    caseType = 8
    clipId = 'SIM_GARBAGE'
  }

  try {
    await axios.post(`${baseUrl}/api/v1/alarm/receive`, null, {
      params: {
        cameraId: 1,
        caseType: caseType,
        clipId: clipId
      }
    })
    ElMessage({ message: '联动指令已同步到所有设备', type: 'success' })
  } catch (err) {
    console.error('指令中转失败:', err)
    ElMessage({ message: '本地指令已发送，但云端转发失败，请检查后端服务', type: 'warning' })
  }
}
</script>

<style scoped>
.simulate-app {
  min-height: 100vh;
  min-height: 100dvh;
  padding: 24px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 12% 16%, rgba(103, 190, 255, 0.18), transparent 24%),
    radial-gradient(circle at 86% 20%, rgba(75, 230, 168, 0.1), transparent 18%),
    linear-gradient(135deg, #05101d, #0b1f35 56%, #123050);
  color: #fff;
}

.simulate-shell {
  width: min(840px, 100%);
  padding: 28px;
  border: 1px solid rgba(126, 197, 255, 0.22);
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(10, 24, 41, 0.88), rgba(7, 17, 30, 0.9));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 30px 60px rgba(2, 10, 20, 0.42);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.simulate-hero {
  margin-bottom: 24px;
}

.simulate-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(126, 197, 255, 0.24);
  background: rgba(17, 47, 75, 0.48);
  color: #cde8ff;
  font-size: 12px;
  letter-spacing: 0.14em;
}

h1 {
  margin: 16px 0 10px;
  font-size: 40px;
  letter-spacing: 0.06em;
  color: #f7fbff;
}

p {
  margin: 0;
  color: rgba(214, 230, 255, 0.76);
  line-height: 1.8;
  font-size: 15px;
}

.btn-group {
  display: grid;
  gap: 16px;
}

.sim-btn {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(126, 197, 255, 0.16);
  background:
    linear-gradient(180deg, rgba(15, 39, 64, 0.78), rgba(8, 20, 35, 0.88));
  color: white;
  cursor: pointer;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.sim-btn:hover {
  transform: translateY(-2px);
  border-color: rgba(126, 232, 255, 0.34);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 20px 32px rgba(2, 10, 20, 0.26);
}

.sim-btn:active {
  transform: scale(0.99);
}

.sim-icon {
  width: 56px;
  height: 56px;
  display: inline-grid;
  place-items: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  font-family: var(--font-data);
  font-size: 24px;
  letter-spacing: 0.08em;
  color: #f7fbff;
}

.sim-copy {
  display: grid;
  gap: 4px;
}

.sim-copy strong {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.sim-copy em {
  font-style: normal;
  color: rgba(214, 230, 255, 0.72);
  font-size: 13px;
}

.bike .sim-icon {
  background: linear-gradient(135deg, rgba(246, 200, 107, 0.88), rgba(242, 148, 50, 0.72));
  color: #1d1403;
}

.fire .sim-icon {
  background: linear-gradient(135deg, rgba(255, 140, 140, 0.92), rgba(237, 81, 81, 0.74));
  color: #240808;
}

.garbage .sim-icon {
  background: linear-gradient(135deg, rgba(103, 190, 255, 0.9), rgba(47, 127, 241, 0.76));
  color: #04162d;
}

@media (max-width: 760px) {
  .simulate-app {
    padding: 12px;
  }

  .simulate-shell {
    padding: 18px;
    border-radius: 22px;
  }

  h1 {
    font-size: 30px;
  }

  .sim-btn {
    grid-template-columns: 1fr;
  }

  .sim-icon {
    width: 48px;
    height: 48px;
  }
}
</style>
