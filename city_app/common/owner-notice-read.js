const NOTICE_READ_STORAGE_PREFIX = 'ownerNoticeReadKeys';
const LEGACY_NOTICE_ACK_KEY = 'ownerNoticeAck';
const MAX_READ_KEYS = 300;

const parseStoredValue = (value, fallback) => {
  if (!value) return fallback;
  if (typeof value !== 'string') return value;
  try {
    return JSON.parse(value);
  } catch (e) {
    return fallback;
  }
};

export const getOwnerNoticeReadStorageKey = () => {
  const userId = uni.getStorageSync('userId') || 'anonymous';
  return `${NOTICE_READ_STORAGE_PREFIX}:${userId}`;
};

export const getOwnerNoticeKey = (notice = {}) => {
  if (notice.id !== undefined && notice.id !== null && notice.id !== '') {
    return `id:${notice.id}`;
  }
  const time = notice.timestamp || notice.createTime || '';
  const message = notice.message || '';
  return `notice:${time}:${message}`;
};

export const getOwnerNoticeReadState = () => {
  let readKeys = [];
  let legacyTimestamp = 0;

  try {
    const stored = parseStoredValue(uni.getStorageSync(getOwnerNoticeReadStorageKey()), []);
    if (Array.isArray(stored)) {
      readKeys = stored;
    } else if (stored && Array.isArray(stored.readKeys)) {
      readKeys = stored.readKeys;
    }
  } catch (e) {
    readKeys = [];
  }

  try {
    const legacy = parseStoredValue(uni.getStorageSync(LEGACY_NOTICE_ACK_KEY), {});
    legacyTimestamp = Number((legacy && legacy.lastAcknowledgedNoticeTimestamp) || 0);
  } catch (e) {
    legacyTimestamp = 0;
  }

  return {
    readKeys: Array.from(new Set(readKeys.filter(Boolean))).slice(-MAX_READ_KEYS),
    legacyTimestamp,
  };
};

export const isOwnerNoticeRead = (notice, state = getOwnerNoticeReadState()) => {
  const key = getOwnerNoticeKey(notice);
  if (state.readKeys.indexOf(key) >= 0) return true;
  const timestamp = new Date((notice && (notice.timestamp || notice.createTime)) || 0).getTime();
  return Boolean(state.legacyTimestamp && timestamp && timestamp <= state.legacyTimestamp);
};

export const applyOwnerNoticeReadState = (notices = []) => {
  const state = getOwnerNoticeReadState();
  return notices.map(item => ({
    ...item,
    isRead: isOwnerNoticeRead(item, state),
  }));
};

export const markOwnerNoticeRead = (notice) => {
  if (!notice) return getOwnerNoticeReadState();

  const key = getOwnerNoticeKey(notice);
  const state = getOwnerNoticeReadState();
  const nextKeys = Array.from(new Set([...state.readKeys, key])).slice(-MAX_READ_KEYS);
  const timestamp = new Date(notice.timestamp || notice.createTime || 0).getTime();
  const nextLegacyTimestamp = Math.max(state.legacyTimestamp || 0, timestamp || 0);

  try {
    uni.setStorageSync(getOwnerNoticeReadStorageKey(), nextKeys);
    uni.setStorageSync(LEGACY_NOTICE_ACK_KEY, {
      lastAcknowledgedNoticeTimestamp: nextLegacyTimestamp || Date.now(),
    });
  } catch (e) {}

  return {
    readKeys: nextKeys,
    legacyTimestamp: nextLegacyTimestamp,
  };
};
