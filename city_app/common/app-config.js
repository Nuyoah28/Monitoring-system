export const APP_CONFIG = {
  manage: {
    loginApi: '/api/v1/user/login',
    successUrl: '/pages/manage/controls/controls',
    appType: 'manage',
    enableWebsocket: true,
    useSwitchTab: true,
  },
  owner: {
    loginApi: '/api/v1/user/owner/login',
    registerApi: '/api/v1/user/register',
    wxRegisterApi: '',
    successUrl: '/pages/owner/home/index',
    appType: 'owner',
    enableWebsocket: true,
    useSwitchTab: false,
  },
};
