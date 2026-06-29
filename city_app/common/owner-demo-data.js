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

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const randDelta = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
const gaussian = (x, center, width, amplitude) =>
  amplitude * Math.exp(-Math.pow(x - center, 2) / (2 * width * width));

const expectAqi = (h) => clamp(Math.round(58 + gaussian(h, 8, 1.8, 45) + gaussian(h, 18, 2.0, 50)), 40, 140);
const expectHumidity = (h) => clamp(Math.round(72 + gaussian(h, 14, 3.6, -26)), 30, 85);
const expectPm25 = (h) => clamp(Math.round(34 + gaussian(h, 8, 1.7, 36) + gaussian(h, 18, 1.9, 44)), 16, 95);
const expectGas = (h) => clamp(Math.round(6 + gaussian(h, 7, 1.0, 11) + gaussian(h, 12, 1.1, 15) + gaussian(h, 18, 1.2, 18)), 4, 38);
const expectTemperature = (h) => clamp(Math.round(21 + gaussian(h, 14, 4.0, 11)), 10, 38);

const expectParkingPercent = (h) => clamp(Math.round(82 + gaussian(h, 11.5, 3.5, -38)), 42, 93);

const zoneOccupancyAdjust = (name, base, h) => {
  switch (name) {
    case '地库A区': return clamp(base + 3, 0, 100);
    case '地库B区': return clamp(base + 6, 0, 100);
    case '地面东侧': return clamp(Math.max(base - 8, 28) + (h >= 9 && h <= 17 ? 6 : 0), 0, 100);
    case '地面西侧': return clamp(Math.max(base - 10, 24) + (h >= 9 && h <= 17 ? 4 : 0), 0, 100);
    default: return base;
  }
};

const expectTodayTraffic = (hourFloat) => {
  const inRate = (h) => Math.max(1, Math.round(2 + gaussian(h, 18, 2.0, 24) + gaussian(h, 12, 2.5, 9)));
  const outRate = (h) => Math.max(1, Math.round(2 + gaussian(h, 8, 2.0, 22) + gaussian(h, 12, 2.5, 9)));
  let totalIn = 2;
  let totalOut = 1;
  for (let h = 0; h < hourFloat; h++) {
    totalIn += inRate(h);
    totalOut += outRate(h);
  }
  return { totalIn, totalOut, inRate, outRate };
};

export const createOwnerDemoParkingRealtime = (monitorId = 1) => {
  const now = new Date();
  const h = now.getHours() + now.getMinutes() / 60;
  const basePercent = expectParkingPercent(h);

  const zones = [
    { areaCode: 'A', areaName: '地库A区', totalSpaces: 56 },
    { areaCode: 'B', areaName: '地库B区', totalSpaces: 48 },
    { areaCode: 'EAST', areaName: '地面东侧', totalSpaces: 32 },
    { areaCode: 'WEST', areaName: '地面西侧', totalSpaces: 28 },
  ].map((item) => {
    const adjustedPercent = zoneOccupancyAdjust(item.areaName, basePercent, h);
    const minuteNoise = Math.round(Math.sin(now.getMinutes() * 0.5) * 2);
    const finalPercent = clamp(adjustedPercent + minuteNoise, 10, 98);
    const occupiedSpaces = Math.round((finalPercent / 100) * item.totalSpaces);
    return {
      areaCode: item.areaCode,
      areaName: item.areaName,
      totalSpaces: item.totalSpaces,
      occupiedSpaces: Math.max(0, Math.min(item.totalSpaces, occupiedSpaces)),
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
    updateTime: formatDateTime(now),
    zones,
  };
};

export const createDemoParkingRealtime = createOwnerDemoParkingRealtime;

export const createOwnerDemoParkingTraffic = (monitorId = 1) => {
  const now = new Date();
  const h = now.getHours() + now.getMinutes() / 60;
  const traffic = expectTodayTraffic(h);
  const todayInCount = traffic.totalIn;
  const todayOutCount = traffic.totalOut;

  const latestInCount = Math.round(traffic.inRate(h) * 0.2 + Math.abs(Math.sin(now.getMinutes()) * 1.5));
  const latestOutCount = Math.round(traffic.outRate(h) * 0.2 + Math.abs(Math.cos(now.getMinutes()) * 1.5));

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
    updateTime: formatDateTime(now),
  };
};

export const createDemoParkingTraffic = createOwnerDemoParkingTraffic;

export const createOwnerDemoEnvironment = (monitorId = 1) => {
  const seed = Number(monitorId) || 1;
  const now = new Date();
  const h = now.getHours() + now.getMinutes() / 60;

  const aqiVal = expectAqi(h) + (seed % 3 - 1) * 5;
  const humVal = expectHumidity(h) + (seed % 3 - 1) * 3;
  const pmVal = expectPm25(h) + (seed % 3 - 1) * 4;
  const tempVal = expectTemperature(h) + (seed % 3 - 1) * 0.8;

  return {
    monitorId: seed,
    deviceCode: `DEMO-ENV-${seed}`,
    temperature: Number((tempVal + Math.sin(now.getMinutes() * 0.5) * 0.2).toFixed(1)),
    humidity: Math.round(humVal + Math.cos(now.getMinutes() * 0.5) * 1.5),
    pm25: Math.round(pmVal + Math.sin(now.getMinutes() * 0.5) * 2),
    combustibleGas: Math.round(expectGas(h) + (seed % 3 - 1) * 2 + Math.cos(now.getMinutes() * 0.5) * 1),
    aqi: Math.round(aqiVal + Math.sin(now.getMinutes() * 0.5) * 3),
    createTime: formatDateTime(now),
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
