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
    navType: "switchTab",
    url: "/pages/manage/controls/controls",
  };
};

export default {
  onLaunch: function () {
    // console.log("App Launch");
    // #ifdef APP-PLUS
    if(typeof plus !== 'undefined') {
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
        
        uni.onPushMessage((res) => {
          // console.log(res);
          if (res.type === "click") {
            const currentAppType = uni.getStorageSync("appType");
            if (currentAppType === "owner") {
              uni.switchTab({
                url: "/pages/owner/home/index",
              });
            } else {
              uni.switchTab({
                url: "/pages/manage/monitor/index",
              });
            }
          } else if (res.type === "receive") {
            if (check === 0) {
              check = 1;
              return;
            }
            uni.createPushMessage({
              title: res.data.title,
              content: '您有一条新的报警信息，请及时处理',
              sound: "system",
            });
            check = 0;
            uni.vibrateLong({
              success: () => {
                console.log("success");
              },
              fail: (err) => {
                console.log(err);
              },
            });
            // player.setLooping(false);
            // player.prepare();
            player.start();
            // player.stop();
          }
        });
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
  height: 100% !important;
  background: #D5E7F5 !important; /* 更深一点的冰蓝背景 */
  background: linear-gradient(180deg, #D5E7F5 0%, #F0F7FF 100%) !important;
  background-attachment: fixed !important;
}
</style>
