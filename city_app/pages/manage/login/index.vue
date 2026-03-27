<template>
  <app-login
    :loginApi="config.loginApi"
    :successUrl="config.successUrl"
    :appType="config.appType"
    :enableWebsocket="config.enableWebsocket"
    :useSwitchTab="config.useSwitchTab"
  />
</template>

<script>
import AppLogin from '@/components/auth/app-login.vue';
import { APP_CONFIG } from '@/common/app-config.js';

export default {
  components: {
    AppLogin,
  },
  data() {
    return {
      config: APP_CONFIG.manage,
    };
  },
};
</script>
