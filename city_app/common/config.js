/**
 * 全局网络与环境配置中心
 * 
 * 只需要在此处修改 IP 地址，全端（HTTP、WebSocket、AI大模型）将自动同步更新。
 */

export const NETWORK_CONFIG = {
    // ==========================================
    // ⬇️ 每次更换网络环境，只修改这一个 IP 即可 ⬇️
    // ==========================================
    // 远程后台服务器 IP
    IP: "123.56.248.17",
    
    // 你的本地电脑 IP (用于连接本地运行的 AI Agent)
    LOCAL_IP: "172.20.10.2",

    // Java 核心业务后台端口
    BACKEND_PORT: "10215",

    // Python AI 助手专属端口
    AI_AGENT_PORT: "5050"
};

// ==========================================
// 自动拼接好的完整路径，直接暴露供各处引入使用
// ==========================================

// 1. 基础业务后端请求地址 (API)
export const API_BASE_URL = `http://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;

// 2. 基础业务报警推送地址 (WebSocket)
export const WS_ALARM_URL = `ws://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;

// 3. AI 助手大模型文字/语音收发地址 (HTTP)
export const AI_HTTP_URL = `http://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;

// 4. AI 助手大模型流式对话地址 (WebSocket)
export const AI_WS_URL = `ws://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;
