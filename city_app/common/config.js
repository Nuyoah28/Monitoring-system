/**
 * 全局网络与资源配置中心。
 * 修改这里的主机、端口或资源地址后，移动端页面会自动复用。
 */

export const NETWORK_CONFIG = {
    IP: '172.20.10.2',
    LOCAL_IP: '172.20.10.2',
    BACKEND_PORT: '10215',
    AI_AGENT_PORT: '5050',
    DEMO_VIDEO_HOST: '172.20.10.2',
    DEMO_VIDEO_PORT: '8848'
};

export const API_BASE_URL = `http://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;
export const WS_ALARM_URL = `ws://${NETWORK_CONFIG.IP}:${NETWORK_CONFIG.BACKEND_PORT}`;
export const AI_HTTP_URL = `http://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;
export const AI_WS_URL = `ws://${NETWORK_CONFIG.LOCAL_IP}:${NETWORK_CONFIG.AI_AGENT_PORT}`;

export const DEMO_VIDEO_BASE_URL = `http://${NETWORK_CONFIG.DEMO_VIDEO_HOST}:${NETWORK_CONFIG.DEMO_VIDEO_PORT}/video`;

const buildDemoVideoUrl = (fileName) => `${DEMO_VIDEO_BASE_URL}/${fileName}`;

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
    return value;
};
