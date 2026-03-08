<template>
  <div class="agent-page">
    <DashboardLayout @open-profile="goProfile">
    <div class="col">
      <article class="card agent-chat-card">
        <h3>智能助手对话</h3>
        <ChatPanel layout="inline" />
      </article>
      <article class="card">
        <h3>快捷指令</h3>
        <div class="slim-tags">
          <button class="btn" type="button">推送巡检任务</button>
          <button class="btn" type="button">生成处置预案</button>
          <button class="btn" type="button">导出告警日报</button>
        </div>
      </article>
    </div>

    <div class="col">
      <article class="card">
        <h3>多路监控</h3>
        <div class="monitor-grid">
          <div
            v-for="tile in cameraTiles"
            :key="tile"
            class="video-tile"
            @click="openFocus(tile)"
          >
            {{ tile }}
          </div>
        </div>
      </article>
      <article class="card">
        <h3>联动结果</h3>
        <div class="chart-wrap" style="min-height:160px; display:grid; place-items:center; color:var(--sub);">
          联动结果/图表挂载位
        </div>
      </article>
    </div>

    <div class="col">
      <article class="card">
        <h3>待办事项</h3>
        <div class="alarms">
          <div class="alarm">通知巡检队前往地库入口处理明火</div>
          <div class="alarm mid">复核北门跌倒告警视频</div>
          <div class="alarm mid">检查西区违停处置进度</div>
        </div>
      </article>
      <article class="card">
        <h3>人员信息</h3>
        <div class="kpi-grid">
          <div class="kpi">
            <div class="name">今日值班时长</div>
            <div class="num">6.5h</div>
          </div>
          <div class="kpi">
            <div class="name">已处置告警</div>
            <div class="num">12</div>
          </div>
          <div class="kpi">
            <div class="name">待办</div>
            <div class="num" style="color:#f8cb71;">3</div>
          </div>
          <div class="kpi">
            <div class="name">逾期</div>
            <div class="num" style="color:#ff8d8d;">1</div>
          </div>
        </div>
      </article>
    </div>

    </DashboardLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DashboardLayout from '@/components/DashboardLayout.vue'
import ChatPanel from '@/components/chat_panel.vue'
import axios from 'axios'

const router = useRouter()
const cameraTiles = ref<string[]>(['北门实时画面', '地库入口实时画面', '中庭实时画面'])

const fetchMonitors = async () => {
  try {
    const { data } = await axios.get('/monitor')
    if (data.code === '00000') {
      const monitors: Array<{ name: string }> = data.data || []
      if (monitors.length) {
        cameraTiles.value = monitors.slice(0, 3).map(item => item.name)
      }
    }
  } catch (e) {
    // 保持默认静态
  }
}

onMounted(() => {
  fetchMonitors()
})

const goProfile = () => router.push('/home')
const openFocus = (camera: string) => {
  // 预留：打开大屏或跳转
  console.log('open focus', camera)
}
</script>

<style scoped>
.agent-page {
  height: 100vh;
  overflow: hidden;
}

.agent-page :deep(.dash) {
  height: 100vh;
  overflow: hidden;
}

.col {
  grid-template-rows: minmax(0, 1fr) auto;
}

.agent-chat-card {
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-chat-card :deep(.chat-panel.inline) {
  flex: 1;
  min-height: 0;
}

@media (max-width: 760px) {
  .agent-page,
  .agent-page :deep(.dash) {
    height: auto;
    overflow: visible;
  }

  .col {
    grid-template-rows: auto;
  }

  .agent-chat-card {
    min-height: 24rem;
    height: auto;
  }
}
</style>
