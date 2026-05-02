export const OWNER_DEMO_FALLBACK_ENABLED = true;
export const DEMO_FALLBACK_ENABLED = OWNER_DEMO_FALLBACK_ENABLED;

const pad = (num) => String(num).padStart(2, '0');

const formatDateTime = (date) => {
  const target = date instanceof Date ? date : new Date();
  return `${target.getFullYear()}-${pad(target.getMonth() + 1)}-${pad(target.getDate())} ${pad(target.getHours())}:${pad(target.getMinutes())}:${pad(target.getSeconds())}`;
};

const minutesAgo = (minutes) => formatDateTime(new Date(Date.now() - minutes * 60 * 1000));

export const createOwnerDemoNotices = () => [
  {
    id: 'demo-notice-parking',
    message: '地下停车区车位较充足，建议晚高峰车辆优先从东门进入。',
    timestamp: minutesAgo(8),
    source: 'demo',
  },
  {
    id: 'demo-notice-maintenance',
    message: '今晚 22:00 至 23:30 将进行公共照明巡检，请留意出行安全。',
    timestamp: minutesAgo(42),
    source: 'demo',
  },
  {
    id: 'demo-notice-weather',
    message: '今日空气质量良好，社区步道与儿童活动区均可正常使用。',
    timestamp: minutesAgo(96),
    source: 'demo',
  },
];

export const createOwnerDemoParkingRealtime = (monitorId = 1) => {
  const tick = Math.floor(Date.now() / 9000);
  const zones = [
    { areaCode: 'A', areaName: '地库A区', totalSpaces: 56, baseOccupied: 30, swing: 8 },
    { areaCode: 'B', areaName: '地库B区', totalSpaces: 48, baseOccupied: 26, swing: 7 },
    { areaCode: 'EAST', areaName: '地面东侧', totalSpaces: 32, baseOccupied: 18, swing: 5 },
    { areaCode: 'WEST', areaName: '地面西侧', totalSpaces: 28, baseOccupied: 20, swing: 4 },
  ].map((item, index) => {
    const offset = Math.round(Math.sin((tick + index + item.areaCode.length) * 0.72) * item.swing);
    return {
      areaCode: item.areaCode,
      areaName: item.areaName,
      totalSpaces: item.totalSpaces,
      occupiedSpaces: Math.max(0, Math.min(item.totalSpaces, item.baseOccupied + offset)),
    };
  });

  const totalSpaces = zones.reduce((sum, item) => sum + item.totalSpaces, 0);
  const occupiedSpaces = zones.reduce((sum, item) => sum + item.occupiedSpaces, 0);
  const freeSpaces = Math.max(totalSpaces - occupiedSpaces, 0);

  return {
    monitorId,
    source: 'local-demo',
    totalSpaces,
    occupiedSpaces,
    freeSpaces,
    occupancyRate: totalSpaces ? Math.round((occupiedSpaces / totalSpaces) * 100) : 0,
    updateTime: formatDateTime(new Date()),
    zones,
  };
};

export const createDemoParkingRealtime = createOwnerDemoParkingRealtime;

export const createOwnerDemoParkingTraffic = (monitorId = 1) => {
  const tick = Math.floor(Date.now() / 9000);
  const latestInCount = 5 + Math.abs((tick + monitorId * 3) % 8);
  const latestOutCount = 4 + Math.abs((tick + monitorId * 2) % 7);
  const todayInCount = 188 + Math.abs(tick % 24);
  const todayOutCount = 163 + Math.abs(tick % 18);

  return {
    monitorId,
    source: 'local-demo',
    todayInCount,
    todayOutCount,
    todayNetFlow: todayInCount - todayOutCount,
    todayTotalFlow: todayInCount + todayOutCount,
    latestInCount,
    latestOutCount,
    latestNetFlow: latestInCount - latestOutCount,
    latestTotalFlow: latestInCount + latestOutCount,
    updateTime: formatDateTime(new Date()),
  };
};

export const createDemoParkingTraffic = createOwnerDemoParkingTraffic;

export const createOwnerDemoEnvironment = (monitorId = 1) => {
  const seed = Number(monitorId) || 1;
  return {
    monitorId: seed,
    deviceCode: `DEMO-ENV-${seed}`,
    temperature: 23.4 + seed * 0.4,
    humidity: 52 + seed,
    pm25: 28 + seed * 3,
    combustibleGas: 7 + seed,
    aqi: 48 + seed * 4,
    createTime: formatDateTime(new Date()),
    source: 'local-demo',
  };
};

export const createOwnerDemoRepairs = () => [
  {
    id: 'demo-repair-1',
    deviceName: '楼道照明',
    location: '3号楼 2单元',
    reportTime: minutesAgo(150),
    status: 0,
    source: 'demo',
  },
];

export const createOwnerDemoVisitors = () => [
  {
    id: 'demo-visitor-1',
    visitorName: '李女士',
    visitTime: minutesAgo(-55),
    source: 'demo',
  },
];
