<script>
import websocket from '@/common/websocket.js';

const resolveLaunchTarget = () => {
  const token = uni.getStorageSync("token");
  const appType = uni.getStorageSync("appType");

  if (!token) {
    return {
      navType: "reLaunch",
      url: "/pages/shared/select/index",
    };
  }

  if (appType === "owner") {
    return {
      navType: "reLaunch",
      url: "/pages/owner/home/index",
    };
  }

  return {
    navType: "reLaunch",
    url: "/pages/manage/controls/controls",
  };
};

export default {
  onLaunch: function () {
    // console.log("App Launch");
    // #ifdef APP-PLUS
    try {
      if (typeof plus !== 'undefined') {
        let main = plus.android.runtimeMainActivity();
        let RingtoneManager = plus.android.importClass(
          "android.media.RingtoneManager"
        );
        let uri = RingtoneManager.getActualDefaultRingtoneUri(
          main,
          RingtoneManager.TYPE_NOTIFICATION
        );
        let MediaPlayer = plus.android.importClass("android.media.MediaPlayer");
        let player = MediaPlayer.create(main, uri);
        let check = 1;

      }
    } catch (e) {
      console.warn('[App] 原生推送/铃声初始化失败，不影响启动流程:', e);
    }
    // #endif

    const userId = uni.getStorageSync("userId");
    const appType = uni.getStorageSync("appType");
    const token = uni.getStorageSync("token");

    if (token && userId) {
      websocket.connect(userId);
    }

    const launchTarget = resolveLaunchTarget();
    uni.setStorageSync("__launch_target__", launchTarget);



    // 启动动画页作为统一入口，动画结束后再跳转业务页
    uni.reLaunch({
      url: "/pages/shared/launch/index",
    });
  },
  onShow: function () {
    // console.log("App Show");
    // App 从后台切回前台时，检查 WebSocket 连接状态
    const token = uni.getStorageSync("token");
    const userId = uni.getStorageSync("userId");
    const appType = uni.getStorageSync("appType");
    if (token && userId && !websocket.getStatus()) {
      websocket.connect(userId);
    }
  },
  onHide: function () {
    // console.log("App Hide");
  },
};
</script>

<style lang="scss">
@import "uview-ui/index.scss";
@import "./static/fonts/stylesheet.css";
page, .uni-page-body {
  min-height: 100% !important;
  background: #F5F7FB !important;
  color: #0F172A;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}

view,
text {
  box-sizing: border-box;
}
</style>
