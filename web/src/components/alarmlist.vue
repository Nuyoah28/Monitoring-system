<template>
    <div class="panel">
        <div class="title">最新报警列表</div>
        <div id="demoDiv">
            <div v-for="(item, index) in alarmlist" 
            :key="item.id" class="itemlist" 
            :style="itemlist1[getcolor(item.eventName)]"
            @click="showDetail(item)">
                <div class="itemlist">
                    <div class="text-content">
                        <h3>{{ index + 1 }} {{ item.eventName }} -- {{ item.department }}</h3>
                    </div>
                    <img :src="item.deal === '已处理' ? require('../../public/assets/checked.png') : require('../../public/assets/unchecked.png')" alt="">
                </div>
            </div>
        </div>
        <dialog1 v-if="dialogVisible1" :item="item" @updateDialogVisible1="handleDialogVisibility"></dialog1>

        <div class="panel-footer"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import dialog1 from './dialog1.vue';
import axios from 'axios';
import { useAlarmStore } from '@/stores/alarm';
import { useUserStore } from '@/stores/user';
import { storeToRefs } from 'pinia';
import { ElMessage } from 'element-plus';
import { baseUrl } from '@/config/config';
import { webSocketBaseUrl } from '@/config/config';
// 无需重新定义AlarmItem接口，使用store中定义的

const router = useRouter();
const alarmStore = useAlarmStore();
const userStore = useUserStore();
const { getAlarmList } = storeToRefs(alarmStore);

const dialogVisible1 = ref<boolean>(false);
const item = ref<any>('');
const alarmlist = computed(() => getAlarmList.value);
const pageNum = ref<number>(1);
const pageSize = ref<number>(30);

// WebSocket相关变量
let websocket: WebSocket | null = null;
let reconnectTimer: number | null = null;
const reconnectInterval = 3000; // 重连间隔时间（毫秒）
const wsUrl = ref<string>(''); // WebSocket连接地址

const itemlist1 = [
    {
        // 挥手
        'backgroundColor': '#F1948A'
    },
    {
        // 摔倒
        'backgroundColor': '#F8BD91'
    },
    {
        // 吸烟
        'backgroundColor': '#ffd9d9'
    },
    {
        // 进入危险区域
        'backgroundColor': '#7ABDD8'
    },
    {
        // 打拳
        'backgroundColor': '#F1948A'
    },
    {
        // 明火
        'backgroundColor': '#e7e3fe'
    },
    {
        // 区域停留
        'backgroundColor': '#2CD6DB'
    },
    {
        // 吸烟
        'backgroundColor': '#C4D83B'
    },
    {
        // 否则
        'backgroundColor': '#7ABDD8'
    }
];

const getcolor = (type: string): number => {
    if (type === '摔倒') return 1;
    else if (type === '烟雾') return 2;
    else if (type === '进入危险区域') return 3;
    //明火
    else if (type === '明火') return 5;
    else if(type === '区域停留') return 6;
    else if(type === '吸烟') return 7;
    else return 8;
};

const showDetail = (itemData: any): void => {
    dialogVisible1.value = true;
    console.log('item', itemData);
    console.log("由于物联网端还未接入，为了调试，前端固定设置这个视频链接");
    itemData.video = baseUrl + '/video/001.flv';//暂定为后端路径
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
    };

    const token = userStore.token;
    axios.get('/api/v1/alarm/query', {
        params: data,
        headers: {
            'Authorization': token
        }
    })
        .then((response: any) => {
            // console.log('收到报警查询数据',response.data.data);
            console.log('response:', response);
            const newAlarmList = response.data.data.alarmList;
            console.log('newAlarmList', newAlarmList);
            if (newAlarmList.length > 0) {
                // 将数据存储到Pinia中
                alarmStore.setAlarmList(newAlarmList);

                // 根据报警列表更新统计数据
                alarmStore.updateStatisticsFromAlarms();

                // 检查是否有新数据变化，如果有则触发报警事件
                if(alarmStore.getAlarmList.length > 0){
                    const bus = (window as any).$bus;
                    if(bus) {
                        bus.$emit('alarm');  // 触发事件总线'alarm'事件
                    }

                    ElMessage({
                        message: '您有报警新消息',
                        type: 'warning'
                    });
                }
            }
        })
        .catch((error: any) => {
            console.log('报警数据查询失败');

            console.log('Error fetching alarm list:', error);
            if (error.response && (error.response.status === 401 || error.response.data.code === 'D0400')) {
                // Token过期或无效，跳转到登录页
                ElMessage({
                    message: 'token过期，请重新登录',
                    type: 'warning'
                });
                router.push('/login');
            }
        });
};

// 初始化WebSocket连接
const initWebSocket = (): void => {
    // 从userStore获取userId
    const userId = userStore.userId; 

    if (!userId) {
        console.warn('userId不存在，无法建立WebSocket连接');
        return;
    }

    // 构建WebSocket连接地址
    wsUrl.value = `${webSocketBaseUrl}/ws/alarm/${userId}`;

    console.log('正在连接WebSocket:', wsUrl.value);

    try {
        websocket = new WebSocket(wsUrl.value);

        websocket.onopen = () => {
            console.log('WebSocket连接成功');
            // 清除重连定时器
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        websocket.onmessage = (event: MessageEvent) => {
            console.log('收到WebSocket消息:', event.data);

            try {
                const message = JSON.parse(event.data);

                // 处理报警消息
                if (message && message.alarmList) {
                    // 将新的报警消息添加到store中
                    alarmStore.setAlarmList(message.alarmList);

                    // 更新统计数据
                    alarmStore.updateStatisticsFromAlarms();

                    // 触发报警事件
                    const bus = (window as any).$bus;
                    if (bus) {
                        bus.$emit('alarm');
                    }

                    // 显示提示消息
                    ElMessage({
                        message: '收到新的报警消息',
                        type: 'warning'
                    });
                }
            } catch (error) {
                console.error('解析WebSocket消息失败:', error);
            }
        };

        websocket.onerror = (error: Event) => {
            console.error('WebSocket连接错误:', error);
            // 尝试重新连接
            attemptReconnect();
        };

        websocket.onclose = (event: CloseEvent) => {
            console.log('WebSocket连接关闭:', event.code, event.reason);
            // 如果不是正常关闭，尝试重新连接
            if (event.code !== 1000) {
                attemptReconnect();
            }
        };
    } catch (error) {
        console.error('创建WebSocket连接失败:', error);
        attemptReconnect();
    }
};

// 尝试重新连接
const attemptReconnect = (): void => {
    if (reconnectTimer) {
        return; // 已经有重连定时器在运行
    }

    console.log(`将在 ${reconnectInterval / 1000} 秒后尝试重新连接WebSocket...`);

    reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null;
        initWebSocket();
    }, reconnectInterval);
};

// 关闭WebSocket连接
const closeWebSocket = (): void => {
    if (websocket) {
        // 移除事件监听器，防止重复触发
        websocket.onopen = null;
        websocket.onmessage = null;
        websocket.onerror = null;
        websocket.onclose = null;

        // 关闭连接
        websocket.close();
        websocket = null;
        console.log('WebSocket连接已关闭');
    }

    // 清除重连定时器
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
};


//let intervalId: number | null = null;

onMounted(() => {
    // 初始获取报警列表（可选，如果需要初始数据）
    fetchAlarmList();

    // 初始化WebSocket连接
    initWebSocket();
});

// 清理WebSocket连接
onUnmounted(() => {
    closeWebSocket();
});
</script>

<style lang="less" scoped>
#demoDiv {
    width: 80%;
    height: 90%;
    margin-left: 2.2rem;
    margin-top: 1rem;
    overflow: auto;
}

#demoDiv::-webkit-scrollbar {
    width: 0;
    height: 0;
}

.itemlist {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 2.8rem;
    margin-top: 0.8rem;
    margin-bottom: 1.5rem;
    border-radius: 0.8rem;
    text-align: left;
    box-sizing: border-box;
    padding-top: 0.2rem;
    cursor: pointer;
    
    .text-content {
        flex: 1; /* 占据剩余空间 */
        min-width: 0; /* 关键：允许flex子项收缩到内容以下 */
        margin-left: 1.2rem;
        display: flex; /* 让文字垂直居中 */
        align-items: center;
    }

    h3 {
        font-size: 1.4rem; /* 稍微调小字体 */
        margin: 0;
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        width: 100%; /* 确保在min-width:0的父容器内生效 */
    }

    img {
        margin-top: 0.2rem;
        margin-right: 1rem;
        width: 2rem;
        height: 2rem;
        flex-shrink: 0; /* 防止图片被压缩 */
    }
}

.panel {
    color: white;
    display: flex;
}

.title {
    width: 2rem;
    font-size: 1.8rem;
    padding-top: 1.2rem;
    font-weight: 600;
}
</style>
