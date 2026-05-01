<template>
  <div class="alarm-panel">
    <div class="panel-head">
      <h3>最新报警列表</h3>
    </div>
    <div class="list" ref="demoDivRef" @mouseenter="stopScroll" @mouseleave="startScroll">
      <div class="scroll-content">
        <div
          v-for="(item, index) in scrollList"
          :key="'roll-' + index"
          class="item"
          :style="getItemStyle(item)"
          @click="showDetail(item)"
        >
          <div class="item-main">
            <div class="text">
              <div class="line1">{{ item.eventName || '未命名告警' }}</div>
              <div class="line2">{{ item.department || item.location || '未标注位置' }} · {{ item.date || item.time || item.createTime || '--' }}</div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!alarmlist.length" class="empty">暂无报警数据</div>
    </div>
    <dialog1 v-if="dialogVisible1" :item="item" @updateDialogVisible1="handleDialogVisibility"></dialog1>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import dialog1 from './dialog1.vue'
import axios from 'axios'
import { useAlarmStore } from '@/stores/alarm'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { alarmDefaultVideo, demoAlarmVideoMap } from '@/config/config'
import { AlarmSocketClient, type AlarmSocketMessage } from '@/utils/alarmSocket'
// 无需重新定义AlarmItem接口，使用store中定义的

const router = useRouter();
const alarmStore = useAlarmStore();
const userStore = useUserStore();
const { getAlarmList } = storeToRefs(alarmStore);

const dialogVisible1 = ref<boolean>(false);
const item = ref<any>(null);
const alarmlist = computed(() => getAlarmList.value.filter((item: any) => ![6, 9, 13].includes(Number(item?.caseType))));

// 备用报警数据
const mockAlarms = ref([
  {
    eventName: '电动车进楼检测',
    department: '北门入口',
    date: new Date().toLocaleString(),
    level: 2,
    location: '北门',
    createTime: new Date().toISOString(),
    video: demoAlarmVideoMap.bike,
    id: 1, name: '平台设备', deal: '未处理', content: '检测到电动车进楼', phone: '13800000001'
  },
  {
    eventName: '烟雾火灾告警',
    department: '车库入口',
    date: new Date().toLocaleString(),
    level: 3,
    location: '车库',
    createTime: new Date().toISOString(),
    video: demoAlarmVideoMap.fire,
    id: 2, name: '平台设备', deal: '未处理', content: '检测到大面积烟雾', phone: '13800000002'
  },
  {
    eventName: '垃圾桶溢出告警',
    department: '东侧步道',
    date: new Date().toLocaleString(),
    level: 1,
    location: '东侧',
    createTime: new Date().toISOString(),
    video: demoAlarmVideoMap.garbage,
    id: 3, name: '平台设备', deal: '未处理', content: '垃圾堆积如山啦', phone: '13800000003'
  }
]);
const scrollList = computed(() => {
    const list = alarmlist.value?.length > 0 ? alarmlist.value : mockAlarms.value;
    if (!list || list.length === 0) return [];
    return [...list, ...list];
});
const pageNum = ref<number>(1);
const pageSize = ref<number>(30);

const demoDivRef = ref<HTMLElement | null>(null);
let scrollTimer: number | null = null;

const startScroll = () => {
    if (scrollTimer) return;
    scrollTimer = window.setInterval(() => {
        if (demoDivRef.value) {
            demoDivRef.value.scrollTop += 1;
            // 滚动到总高度的一半时，也就是走完第一轮数据，无缝重置回 0
            if (demoDivRef.value.scrollTop >= demoDivRef.value.scrollHeight / 2) {
                demoDivRef.value.scrollTop = 0;
            }
        }
    }, 40); // 修改毫秒数可调节滚动速度
};

const stopScroll = () => {
    if (scrollTimer) {
        clearInterval(scrollTimer);
        scrollTimer = null;
    }
};

// WebSocket连接由统一客户端封装管理
let alarmSocketClient: AlarmSocketClient | null = null
let alarmSocketRefreshTimer: number | null = null

const itemlist1 = [
    {
        // 0: 挥手 (wave)
        'backgroundColor': '#F1948A'
    },
    {
        // 1: 摔倒 (fall / staggering / falling down)
        'backgroundColor': '#F8BD91'
    },
    {
        // 2: 烟雾/火灾相关
        'backgroundColor': '#ffd9d9'
    },
    {
        // 3: 进入危险区域
        'backgroundColor': '#7ABDD8'
    },
    {
        // 4: 暴力打架 (punch)
        'backgroundColor': '#E74C3C' 
    },
    {
        // 5: 明火
        'backgroundColor': '#e7e3fe'
    },
    {
        // 6: 区域停留
        'backgroundColor': '#2CD6DB'
    },
    {
        // 7: 吸烟
        'backgroundColor': '#C4D83B'
    },
    {
        // 8: 路面积冰 (ice on road)
        'backgroundColor': '#AED6F1'
    },
    {
        // 9: 垃圾乱扔 (garbage on ground)
        'backgroundColor': '#D2B4DE'
    },
    {
        // 10: 违规停车 (electric scooter / vehicle)
        'backgroundColor': '#F7DC6F'
    },
    {
        // 11: 默认 (其他/未知)
        'backgroundColor': '#85929E'
    }
];

const severityColor = (level: number) => {
    if (level >= 3) {
        return {
            backgroundColor: '#ffe1e1',
            borderColor: 'rgba(231, 76, 60, 0.5)'
        }
    }
    if (level === 2) {
        return {
            backgroundColor: '#fff2db',
            borderColor: 'rgba(248, 189, 145, 0.5)'
        }
    }
    return {
        backgroundColor: '#e9f5ff',
        borderColor: 'rgba(122, 189, 216, 0.5)'
    }
}

const getItemStyle = (item: any) => {
    const level = Number(item?.level)
    if (!Number.isNaN(level)) {
        return severityColor(level)
    }
    return itemlist1[getcolor(item.eventName)]
}

const getcolor = (type: string): number => {
    // 处理各种算法推过来的准确中文名 (兼容 NTU-60 映射和 Mamba-YOLO 名称)
    if (type.includes('挥手') || type.includes('wave')) return 0;
    else if (type.includes('摔倒') || type.includes('fall') || type.includes('staggering')) return 1;
    else if (type.includes('烟')) return 2;
    else if (type.includes('危险区域')) return 3;
    else if (type.includes('打架') || type.includes('punch') || type.includes('暴力')) return 4;
    else if (type.includes('火')) return 5;
    else if (type.includes('停留')) return 6;
    else if (type.includes('吸烟')) return 7;
    // Mamba-YOLO World 开放世界检测项
    else if (type.includes('路面积冰') || type.includes('结冰')) return 8;
    else if (type.includes('垃圾') || type.includes('garbage')) return 9;
    else if (type.includes('电动车') || type.includes('人行道驻车') || type.includes('scooter') || type.includes('vehicle')) return 10;
    
    // 找不到匹配项返回默认灰色
    return 11;
};

const showDetail = (itemData: any): void => {
    dialogVisible1.value = true;
    console.log('item', itemData);
    // 使用 itemData 中的视频链接，如果没有则使用默认值
    if (!itemData.video) {
        itemData.video = alarmDefaultVideo;
    }
    item.value = itemData;
};

const handleDialogVisibility = (res: boolean): void => {
    dialogVisible1.value = res;
};

// 一次性获取所有报警消息
const fetchAlarmList = (): void => {
  const data = {
    pageNum: pageNum.value,
    pageSize: pageSize.value,
    status: 0,
  }

  axios
    .get('/alarm/query', { params: data })
    .then((response: any) => {
      const res = response.data
      const newAlarmList = (res?.data?.alarmList || res?.data?.list || []).filter((item: any) => ![6, 9, 13].includes(Number(item?.caseType)))
      if (newAlarmList.length > 0) {
        alarmStore.setAlarmList(newAlarmList)
        alarmStore.updateStatisticsFromAlarms()

        if (alarmStore.getAlarmList.length > 0) {
          const bus = (window as any).$bus
          if (bus) {
            bus.$emit('alarm')
          }

          ElMessage({
            message: '您有报警新消息',
            type: 'warning',
          })
        }
      }
    })
    .catch((error: any) => {
      console.log('启用备用报警数据');
      // 服务暂不可用时启用备用数据
      alarmStore.setAlarmList(mockAlarms.value);
      alarmStore.updateStatisticsFromAlarms();
      
      const bus = (window as any).$bus
      if (bus) {
        bus.$emit('alarm')
      }

      ElMessage({
        message: '已启用备用报警数据',
        type: 'info',
      })
    })
}

// 初始化WebSocket连接
const resolveCurrentUserId = () => {
    if (userStore.userId) return userStore.userId
    const sessionUserId = Number(sessionStorage.getItem('userId') || 0)
    return Number.isFinite(sessionUserId) ? sessionUserId : 0
}

const refreshAlarmListFromSocket = () => {
    if (alarmSocketRefreshTimer !== null) {
        window.clearTimeout(alarmSocketRefreshTimer)
    }
    alarmSocketRefreshTimer = window.setTimeout(() => {
        alarmSocketRefreshTimer = null
        fetchAlarmList()
    }, 300)
}

const initWebSocket = (): void => {
    const userId = resolveCurrentUserId()
    if (!userId || alarmSocketClient) {
        if (!userId) console.warn('userId不存在，无法建立WebSocket连接')
        return
    }

    alarmSocketClient = new AlarmSocketClient({
        userId,
        onAlarm: async (message: AlarmSocketMessage) => {
            console.log('收到WebSocket报警消息:', message)
            refreshAlarmListFromSocket()
            const bus = (window as any).$bus
            if (bus) {
                bus.$emit('alarm')
            }
            ElMessage({
                message: message.message || '收到新的报警消息',
                type: 'warning'
            })
        },
        onOpen: () => console.log('WebSocket连接成功'),
        onClose: () => console.log('WebSocket连接关闭'),
        onError: (error: Event) => console.error('WebSocket连接错误:', error),
    })
    alarmSocketClient.connect()
}

// 关闭WebSocket连接
const closeWebSocket = (): void => {
    if (alarmSocketRefreshTimer !== null) {
        window.clearTimeout(alarmSocketRefreshTimer)
        alarmSocketRefreshTimer = null
    }
    alarmSocketClient?.close()
    alarmSocketClient = null
    console.log('WebSocket连接已关闭')
}


//let intervalId: number | null = null;

onMounted(() => {
  fetchAlarmList()
  initWebSocket()
  startScroll()
})

// 清理WebSocket连接
onUnmounted(() => {
  closeWebSocket()
  stopScroll()
})
</script>

<style scoped>
.alarm-panel {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(99, 184, 255, 0.12), rgba(13, 30, 52, 0.5));
  border: 1px solid rgba(99, 184, 255, 0.35);
  border-radius: 10px;
  color: #d6e6ff;
  padding: 10px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.panel-head h3 {
  margin: 0;
}

.muted {
  color: var(--sub);
  font-size: 12px;
}

.list {
  flex: 1;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(138, 185, 229, 0.75) transparent;
}

.list::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.list::-webkit-scrollbar-thumb {
  background: rgba(138, 185, 229, 0.72);
  border-radius: 999px;
}

.list::-webkit-scrollbar-track {
  background: transparent;
}

.scroll-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 6px;
}


.item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(99, 184, 255, 0.25);
  background: rgba(255, 255, 255, 0.9);
  color: #0a1b2f;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.1s ease;
}

.item:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.item-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  width: 100%;
}

.text {
  display: flex;
  flex-direction: row;
  gap: 8px;
  min-width: 0;
  align-items: center;
}

.line1 {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #0a1b2f;
  font-size: 13px;
}

.line2 {
  color: #4a5768;
  font-size: 11px;
  white-space: nowrap;
}

.status {
  display: none;
}

.empty {
  text-align: center;
  color: var(--sub);
  padding: 20px 0;
}
</style>
