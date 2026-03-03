/**
 * WebSocket 报警推送工具
 * 用于接收后端实时推送的报警消息
 */

let isConnected = false;
let reconnectTimer = null;
let heartbeatTimer = null;

// WebSocket 服务器地址（根据环境配置）
const WS_BASE_URL = 'ws://192.168.1.8:10215';
// const WS_BASE_URL = 'ws://192.168.3.135:10215';  // 开发环境 (旧)
// const WS_BASE_URL = 'ws://192.168.68.31:10215';  // 开发环境 (新)
// const WS_BASE_URL = 'ws://你的服务器地址:10215';  // 生产环境

/**
 * 连接 WebSocket
 * @param {string} userId 用户ID
 */ 
function connect(userId) {
    if (isConnected) {
        console.log('[WebSocket] 已经连接，无需重复连接');
        return;
    }

    // 保存 userId 用于重连
    currentUserId = userId;

    const url = `${WS_BASE_URL}/ws/alarm/${userId}`;
    console.log('[WebSocket] 正在连接:', url);

    try {
        uni.connectSocket({
            url: url,
            success: () => {
                console.log('[WebSocket] 连接请求已发送');
            },
            fail: (err) => {
                console.error('[WebSocket] 连接失败:', err);
                scheduleReconnect(userId);
            }
        });
    } catch (e) {
        console.error('[WebSocket] 创建连接异常:', e);
        return;
    }
}

// 保存当前用户ID用于重连
let currentUserId = null;

uni.onSocketOpen(() => {
    console.log('[WebSocket] 连接成功');
    isConnected = true;
    startHeartbeat();
});

uni.onSocketMessage((res) => {
    console.log('[WebSocket] 收到消息:', res.data);
    // 心跳响应不需要解析
    if (res.data === 'pong') {
        return;
    }
    try {
        const data = JSON.parse(res.data);
        handleMessage(data);
    } catch (e) {
        console.log('[WebSocket] 消息解析失败:', e);
    }
});

uni.onSocketClose(() => {
    console.log('[WebSocket] 连接已关闭');
    isConnected = false;
    stopHeartbeat();
    if (currentUserId) {
        scheduleReconnect(currentUserId);
    }
});

uni.onSocketError((err) => {
    console.error('[WebSocket] 发生错误:', err);
    isConnected = false;
});

function handleMessage(data) {
    if (data.type === 'NEW_ALARM') {
        console.log('[WebSocket] 收到新报警:', data);

        const alarmData = data.data || {};

        // 区分“原生常态告警”和“AI自定义下发动态监测(caseType=13)”
        if (alarmData.caseType === 13) {
            // 给负责人的特快专递消息
            uni.showModal({
                title: '🎯 [特急] AI 目标抓拍通知',
                content: `您关注的动态目标监控点【${alarmData.name || '摄像头区域'}】刚刚抓拍到目标，请立即核实处理！`,
                showCancel: false,
                confirmText: '收到',
                success: (res) => console.log('[WebSocket] 动态AI消息已确认', res)
            });
            // 振动提醒更强力（连震两次）
            uni.vibrateLong({ success: () => { setTimeout(() => uni.vibrateLong(), 500); } });
        } else {
            // 普通警报
            uni.showModal({
                title: '⚠️ 报警提醒',
                content: data.message || '您有新的常规报警信息，请及时处理。',
                showCancel: false,
                confirmText: '前往处理',
                success: (res) => console.log('[WebSocket] 常规报警确认', res)
            });
            uni.vibrateLong();
        }

        // 依然触发全局事件供页面刷新(页面流里已将 caseType=13 过滤，不会污染列表)
        uni.$emit('newAlarm', data);
    }
}

function disconnect() {
    stopHeartbeat();
    currentUserId = null;
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
    try {
        uni.closeSocket();
    } catch (e) {
        console.log('[WebSocket] 关闭连接异常:', e);
    }
    isConnected = false;
    console.log('[WebSocket] 已断开连接');
}

function startHeartbeat() {
    stopHeartbeat();
    heartbeatTimer = setInterval(() => {
        if (isConnected) {
            uni.sendSocketMessage({
                data: 'ping',
                fail: (err) => {
                    console.error('[WebSocket] 心跳发送失败:', err);
                }
            });
        }
    }, 30000);
}

function stopHeartbeat() {
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
}

function scheduleReconnect(userId) {
    if (reconnectTimer) return;

    console.log('[WebSocket] 5秒后尝试重连...');
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        const token = uni.getStorageSync('token');
        if (token) {
            connect(userId);
        }
    }, 5000);
}

function getStatus() {
    return isConnected;
}

export default {
    connect,
    disconnect,
    getStatus
};
