/**
 * WebSocket 报警推送工具
 * 用于接收后端实时推送的报警消息
 */

import { WS_ALARM_URL } from './config.js';

let isConnected = false;
let isConnecting = false;
let reconnectTimer = null;
let heartbeatTimer = null;
let socketTask = null;
let currentUserId = null;

// WebSocket 服务器地址（根据环境配置）
const WS_BASE_URL = WS_ALARM_URL;

/**
 * 连接 WebSocket
 * @param {string} userId 用户ID
 */
function connect(userId) {
    if (isConnected || isConnecting) {
        console.log('[WebSocket] 已经连接，无需重复连接');
        return;
    }

    // 保存 userId 用于重连
    currentUserId = userId;

    const url = `${WS_BASE_URL}/ws/alarm/${userId}`;
    console.log('[WebSocket] 正在连接:', url);
    isConnecting = true;

    try {
        socketTask = uni.connectSocket({
            url: url,
            success: () => {
                console.log('[WebSocket] 连接请求已发送');
            },
            fail: (err) => {
                console.error('[WebSocket] 连接失败:', err);
                isConnecting = false;
                scheduleReconnect(userId);
            }
        });

        if (!socketTask || typeof socketTask.onOpen !== 'function') {
            isConnecting = false;
            scheduleReconnect(userId);
            return;
        }

        socketTask.onOpen(() => {
            console.log('[WebSocket] 连接成功');
            isConnected = true;
            isConnecting = false;
            startHeartbeat();
        });

        socketTask.onMessage((res) => {
            console.log('[WebSocket] 收到消息:', res.data);
            // 心跳响应不需要解析
            if (res.data === 'pong' || res.data === 'ping') {
                return;
            }
            try {
                const data = JSON.parse(res.data);
                handleMessage(data);
            } catch (e) {
                console.log('[WebSocket] 消息解析失败:', e);
            }
        });

        socketTask.onClose(() => {
            console.log('[WebSocket] 连接已关闭');
            isConnected = false;
            isConnecting = false;
            socketTask = null;
            stopHeartbeat();
            if (currentUserId) {
                scheduleReconnect(currentUserId);
            }
        });

        socketTask.onError((err) => {
            console.error('[WebSocket] 发生错误:', err);
            isConnected = false;
            isConnecting = false;
        });
    } catch (e) {
        console.error('[WebSocket] 创建连接异常:', e);
        isConnecting = false;
        return;
    }
}

function handleMessage(data) {
    if (data.type === 'NEW_ALARM') {
        console.log('[WebSocket] 收到新报警:', data);

        const alarmData = data.data || {};
        const appType = uni.getStorageSync('appType');

        if (appType === 'owner') {
            const areaText = alarmData.department || '附近区域';
            const eventText = alarmData.eventName || '异常事件';
            uni.showModal({
                title: '⚠️ 社区报警提醒',
                content: `【${areaText}】发生${eventText}，请注意安全。`,
                showCancel: false,
                confirmText: '查看通知',
                success: (res) => {
                    if (res.confirm) {
                        uni.navigateTo({ url: '/pages/owner/features/notice/index' });
                    }
                }
            });
            uni.vibrateLong();
            return;
        }

        // 区分“原生常态告警”和“AI自定义下发动态监测(caseType=13)”
        if (alarmData.caseType === 13) {
            // 给负责人的特快专递消息
            uni.showModal({
                title: '🎯 [特急] AI 目标抓拍通知',
                content: `您关注的动态目标监控点【${alarmData.name || '摄像头区域'}】刚刚抓拍到目标，请立即核实处理！`,
                showCancel: false,
                confirmText: '去查看',
                success: (res) => {
                    if (res.confirm) {
                        uni.navigateTo({ url: '/pages/manage/realtime/realtime' });
                    }
                }
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
                success: (res) => {
                    if (res.confirm) {
                        uni.navigateTo({ url: '/pages/manage/realtime/realtime' });
                    }
                }
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
        if (socketTask && typeof socketTask.close === 'function') {
            socketTask.close({});
        }
    } catch (e) {
        console.log('[WebSocket] 关闭连接异常:', e);
    }
    isConnected = false;
    isConnecting = false;
    socketTask = null;
    console.log('[WebSocket] 已断开连接');
}

function startHeartbeat() {
    stopHeartbeat();
    heartbeatTimer = setInterval(() => {
        if (isConnected && socketTask && typeof socketTask.send === 'function') {
            socketTask.send({
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
    return isConnected || isConnecting;
}

export default {
    connect,
    disconnect,
    getStatus
};
