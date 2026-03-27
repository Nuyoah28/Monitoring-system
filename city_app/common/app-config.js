export const APP_CONFIG = {
  manage: {
    loginApi: '/api/v1/user/login',
    successUrl: '/pages/sys/dateWatcher/dateWatcher',
    appType: 'manage',
    enableWebsocket: true,
    useSwitchTab: false,
  },
  owner: {
    loginApi: '/api/v1/user/login',
    successUrl: '/pages/owner/home/index',
    appType: 'owner',
    enableWebsocket: false,
    useSwitchTab: false,
  },
};
