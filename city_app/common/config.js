/**
 * 全局网络与资源配置中心。
 * 修改这里的主机、端口或资源地址后，移动端页面会自动复用。
 */

export const NETWORK_CONFIG = {
    IP: '123.56.248.17',
    LOCAL_IP: '123.56.248.17',
    BACKEND_PORT: '10215',
    AI_AGENT_PORT: '5050',
    SRS_HTTP_PORT: '8080',
    SRS_RTMP_PORT: '1935',
    DEMO_VIDEO_HOST: '123.56.248.17',
    DEMO_VIDEO_PORT: '8848'
};

export const API_BASE_URL = `http://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;
export const WS_ALARM_URL = `ws://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;
export const AI_HTTP_URL = `http://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;
export const AI_WS_URL = `ws://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;
export const LIVE_STREAM_BASE_URL = `http://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.SRS_HTTP_PORT}/live`;
const DEMO_STATIC_BASE = `http://${NETWORK_CONFIG.DEMO_VIDEO_HOST}:${NETWORK_CONFIG.DEMO_VIDEO_PORT}/video`;

// [0] 是 ffmpeg 推到 SRS 的真实直播流（用 RTMP 协议，避开标准基座对 HTTP 明文流的拦截）；[1][2][3] 是 8848 静态文件服务器上的演示片段，与 web 端 defaultStreamList 对齐。
export const LIVE_STREAM_LIST = [
    `rtmp://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.SRS_RTMP_PORT}/live/raw`,
    `${DEMO_STATIC_BASE}/001.flv`,
    `${DEMO_STATIC_BASE}/002.flv`,
    `${DEMO_STATIC_BASE}/003.flv`
];

export const resolveLiveStreamUrl = (item) => {
    if (!item || !LIVE_STREAM_LIST.length) return LIVE_STREAM_LIST[0] || '';
    const name = String(item.name || '');
    if (/东门/.test(name)) return LIVE_STREAM_LIST[0];
    const id = Number(item.id || item.monitorId);
    if (!Number.isFinite(id) || id <= 0) return LIVE_STREAM_LIST[1];
    return LIVE_STREAM_LIST[1 + ((id - 1) % 3)];
};

export const DEMO_VIDEO_BASE_URL = `http://${NETWORK_CONFIG.DEMO_VIDEO_HOST}:${NETWORK_CONFIG.DEMO_VIDEO_PORT}/video`;

const buildDemoVideoUrl = (fileName) => `${DEMO_VIDEO_BASE_URL}/${encodeURIComponent(fileName)}`;

export const DEMO_ALARM_VIDEO_MAP = {
    bike: buildDemoVideoUrl('电动车进楼.mp4'),
    fire: buildDemoVideoUrl('火灾烟雾.mp4'),
    garbage: buildDemoVideoUrl('垃圾桶溢出.mp4')
};

const DEMO_ALARM_CLIP_VIDEO_MAP = {
    SIM_BIKE: DEMO_ALARM_VIDEO_MAP.bike,
    SIM_FIRE: DEMO_ALARM_VIDEO_MAP.fire,
    SIM_GARBAGE: DEMO_ALARM_VIDEO_MAP.garbage
};

export const ALARM_DEFAULT_VIDEO = DEMO_ALARM_VIDEO_MAP.bike;

export const resolveBackendAssetUrl = (urlOrPath) => {
    if (!urlOrPath) return '';
    const value = String(urlOrPath).trim();
    if (!value) return '';
    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith('//')) return value;
    if (value.startsWith('/')) return `${API_BASE_URL.replace(/\/+$/, '')}${value}`;
    return value;
};

const looksLikeAlarmClipKey = (value) => {
    return /\.flv($|[?#])/i.test(value) || /^[0-9a-f-]{24,}$/i.test(value);
};
export const resolveDemoAlarmVideo = (clipIdOrUrl) => {
    if (!clipIdOrUrl) return ALARM_DEFAULT_VIDEO;
    const value = String(clipIdOrUrl);

    if (DEMO_ALARM_CLIP_VIDEO_MAP[value]) return DEMO_ALARM_CLIP_VIDEO_MAP[value];
    if (value.includes('SIM_BIKE')) return DEMO_ALARM_VIDEO_MAP.bike;
    if (value.includes('SIM_FIRE')) return DEMO_ALARM_VIDEO_MAP.fire;
    if (value.includes('SIM_GARBAGE')) return DEMO_ALARM_VIDEO_MAP.garbage;
    if (value === 'bike') return DEMO_ALARM_VIDEO_MAP.bike;
    if (value === 'fire') return DEMO_ALARM_VIDEO_MAP.fire;
    if (value === 'garbage') return DEMO_ALARM_VIDEO_MAP.garbage;
    if (value.startsWith('/api/v1/alarm/clips/')) return resolveBackendAssetUrl(value);
    if (value.startsWith('/')) return resolveBackendAssetUrl(value);
    if (looksLikeAlarmClipKey(value)) return resolveBackendAssetUrl(`/api/v1/alarm/clips/${value}`);
    return value;
};
