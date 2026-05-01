export type LngLat = [number, number]

export interface FixedMapPoint {
  title: string
  camera: string
  longitude: number
  latitude: number
}

const getEnvString = (name: string, fallback: string) => {
  const value = process.env[name]
  return value && value.trim() ? value.trim() : fallback
}

const getEnvNumber = (name: string, fallback: number) => {
  const raw = process.env[name]
  const value = Number(raw)
  return Number.isFinite(value) ? value : fallback
}

const getEnvList = (name: string, fallback: string[]) => {
  const raw = process.env[name]
  if (!raw || !raw.trim()) return fallback
  const result = raw
    .split(',')
    .map((item: string) => item.trim())
    .filter(Boolean)
  return result.length ? result : fallback
}

const trimRightSlash = (value: string) => value.replace(/\/+$/, '')
const toWsBase = (value: string) => trimRightSlash(value).replace(/^http/i, 'ws')

const defaultApiBaseUrl = 'http://localhost:10215'
const defaultAlgorithmUrl = 'http://localhost:6006'
const defaultAgentBaseUrl = 'http://localhost:5050'
const defaultDemoVideoBaseUrl = 'http://localhost:8848/video'

const demoVideoFileMap = {
  bike: '\u7535\u52a8\u8f66\u8fdb\u697c.mp4',
  fire: '\u706b\u707e\u70df\u96fe.mp4',
  garbage: '\u5783\u573e\u6876\u6ea2\u51fa.mp4',
  defaultFlv: '001.flv',
  extraFlv01: '002.flv',
  extraFlv02: '003.flv',
} as const

export const baseUrl = trimRightSlash(getEnvString('VUE_APP_API_BASE_URL', defaultApiBaseUrl))
export const algorithmUrl = trimRightSlash(getEnvString('VUE_APP_ALGORITHM_URL', defaultAlgorithmUrl))
export const agentBaseUrl = trimRightSlash(getEnvString('VUE_APP_AGENT_BASE_URL', defaultAgentBaseUrl))
export const webSocketBaseUrl = trimRightSlash(
  getEnvString('VUE_APP_WS_BASE_URL', toWsBase(baseUrl)),
)

export const demoVideoBaseUrl = trimRightSlash(
  getEnvString('VUE_APP_DEMO_VIDEO_BASE_URL', defaultDemoVideoBaseUrl),
)

const buildDemoVideoUrl = (fileName: string) => `${demoVideoBaseUrl}/${fileName}`

export const demoAlarmVideoMap = {
  bike: buildDemoVideoUrl(demoVideoFileMap.bike),
  fire: buildDemoVideoUrl(demoVideoFileMap.fire),
  garbage: buildDemoVideoUrl(demoVideoFileMap.garbage),
} as const

const demoAlarmClipVideoMap: Record<string, string> = {
  SIM_BIKE: demoAlarmVideoMap.bike,
  SIM_FIRE: demoAlarmVideoMap.fire,
  SIM_GARBAGE: demoAlarmVideoMap.garbage,
}

export const resolveDemoAlarmVideo = (clipIdOrType?: string) => {
  if (!clipIdOrType) return ''
  const value = String(clipIdOrType)
  if (demoAlarmClipVideoMap[value]) return demoAlarmClipVideoMap[value]
  if (value.includes('SIM_BIKE')) return demoAlarmVideoMap.bike
  if (value.includes('SIM_FIRE')) return demoAlarmVideoMap.fire
  if (value.includes('SIM_GARBAGE')) return demoAlarmVideoMap.garbage
  if (value === 'bike') return demoAlarmVideoMap.bike
  if (value === 'fire') return demoAlarmVideoMap.fire
  if (value === 'garbage') return demoAlarmVideoMap.garbage
  return value
}

export const defaultStreamList = [
  'http://123.56.248.17:8080/live/raw.flv',
  buildDemoVideoUrl(demoVideoFileMap.defaultFlv),
  buildDemoVideoUrl(demoVideoFileMap.extraFlv01),
  buildDemoVideoUrl(demoVideoFileMap.extraFlv02),
]

export const rtmpAddressList = getEnvList('VUE_APP_MONITOR_STREAMS', defaultStreamList)
export const rtmpAddress = rtmpAddressList[0] || ''
export const alarmDefaultVideo = getEnvString(
  'VUE_APP_ALARM_DEFAULT_VIDEO',
  rtmpAddress || buildDemoVideoUrl(demoVideoFileMap.defaultFlv),
)
export const simulateChannelName = getEnvString('VUE_APP_SIMULATE_CHANNEL', 'demonstration_channel')

export const amapConfig = {
  key: getEnvString('VUE_APP_AMAP_KEY', 'd8250863b36679ef600aa2c28bb90ab0'),
  version: getEnvString('VUE_APP_AMAP_VERSION', '1.4.15'),
  defaultCenter: [
    getEnvNumber('VUE_APP_AMAP_CENTER_LNG', 117.01187872107023),
    getEnvNumber('VUE_APP_AMAP_CENTER_LAT', 39.1443426861701),
  ] as LngLat,
  fixedPoints: [
    {
      title: '\u4e09\u53f7\u697c\u76d1\u6d4b\u70b9',
      camera: '\u4e09\u53f7\u697c\u76d1\u6d4b\u70b9',
      longitude: 117.01280287680027,
      latitude: 39.144625636831215,
    },
    {
      title: '\u4e5d\u53f7\u697c\u76d1\u6d4b\u70b9',
      camera: '\u4e5d\u53f7\u697c\u76d1\u6d4b\u70b9',
      longitude: 117.0122804687718,
      latitude: 39.143983680256035,
    },
    {
      title: '\u5357\u95e8\u76d1\u6d4b\u70b9',
      camera: '\u5357\u95e8\u76d1\u6d4b\u70b9',
      longitude: 117.01346569650909,
      latitude: 39.14355698741387,
    },
  ] as FixedMapPoint[],
} as const
