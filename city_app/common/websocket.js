/**
 * WebSocket 报警推送工具
 * 用于接收后端实时推送的报警消息
 */

let isConnected = false;
let reconnectTimer = null;
let heartbeatTimer = null;

// WebSocket 服务器地址（根据环境配置）
const WS_BASE_URL = 'ws://localhost:10215';  // 开发环境
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

/**
 * 处理收到的消息
 */
function handleMessage(data) {
    if (data.type === 'NEW_ALARM') {
        console.log('[WebSocket] 收到新报警:', data);

        // 使用模态弹窗确保用户看到
        uni.showModal({
            title: '⚠️ 报警提醒',
            content: data.message || '您有新的报警信息',
            showCancel: false,
            confirmText: '知道了',
            success: (res) => console.log('[WebSocket] 模态框已确认', res),
            fail: (err) => console.error('[WebSocket] 模态框调用失败', err)
        });

        // 振动提醒
        uni.vibrateLong();

        // 触发全局事件刷新列表
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
