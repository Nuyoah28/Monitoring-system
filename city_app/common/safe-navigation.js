const INSTALL_KEY = '__citySafeNavigationInstalled__';
const LOCK_WINDOW_MS = 700;
const STACK_LIMIT_BEFORE_REDIRECT = 9;

const getPageStackLength = () => {
  try {
    return getCurrentPages().length;
  } catch (e) {
    return 0;
  }
};

const callMaybe = (fn, payload) => {
  if (typeof fn === 'function') fn(payload);
};

export function installSafeNavigation() {
  if (typeof uni === 'undefined' || uni[INSTALL_KEY]) return;

  const raw = {
    navigateTo: uni.navigateTo && uni.navigateTo.bind(uni),
    redirectTo: uni.redirectTo && uni.redirectTo.bind(uni),
    reLaunch: uni.reLaunch && uni.reLaunch.bind(uni),
    switchTab: uni.switchTab && uni.switchTab.bind(uni),
    navigateBack: uni.navigateBack && uni.navigateBack.bind(uni),
  };

  let locked = false;
  let unlockTimer = null;

  const unlockSoon = (delay = LOCK_WINDOW_MS) => {
    if (unlockTimer) clearTimeout(unlockTimer);
    unlockTimer = setTimeout(() => {
      locked = false;
      unlockTimer = null;
    }, delay);
  };

  const wrapRouteMethod = (methodName) => {
    const original = raw[methodName];
    if (typeof original !== 'function') return;

    uni[methodName] = (options = {}) => {
      const normalized = options && typeof options === 'object' ? options : {};
      const skipSafeNavigation = Boolean(normalized.__skipSafeNavigation);
      const cleanOptions = { ...normalized };
      delete cleanOptions.__skipSafeNavigation;

      if (skipSafeNavigation) {
        return original(cleanOptions);
      }

      if (locked) {
        const result = { errMsg: `${methodName}:fail navigation locked` };
        callMaybe(normalized.fail, result);
        callMaybe(normalized.complete, result);
        return;
      }

      locked = true;
      const realMethodName = methodName === 'navigateTo' && getPageStackLength() >= STACK_LIMIT_BEFORE_REDIRECT
        ? 'redirectTo'
        : methodName;
      const realMethod = raw[realMethodName] || original;

      try {
        unlockSoon(realMethodName === 'navigateBack' ? 350 : LOCK_WINDOW_MS);
        return realMethod({
          ...cleanOptions,
          fail(res) {
            locked = false;
            callMaybe(normalized.fail, res);
          },
          complete(res) {
            callMaybe(normalized.complete, res);
            unlockSoon(realMethodName === 'navigateBack' ? 350 : LOCK_WINDOW_MS);
          },
        });
      } catch (e) {
        locked = false;
        throw e;
      }
    };
  };

  ['navigateTo', 'redirectTo', 'reLaunch', 'switchTab', 'navigateBack'].forEach(wrapRouteMethod);

  Object.defineProperty(uni, INSTALL_KEY, {
    value: true,
    enumerable: false,
    configurable: false,
  });
}
