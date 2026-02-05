<script>
import websocket from '@/common/websocket.js';

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
            // console.log("hi");
            uni.switchTab({
              url: "/pages/sys/realtime/realtime",
            });
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
    
    // 检查用户是否已登录
    const token = uni.getStorageSync("token");
    const userId = uni.getStorageSync("userId");
    
    if (token) {
      // 已登录：自动连接 WebSocket
      if (userId) {
        websocket.connect(userId);
      }
      
      setTimeout(() => {
        // console.log('hi')
        uni.switchTab({
          url: "/pages/sys/dateWatcher/dateWatcher",
        });
      }, 2000);
    } else {
      setTimeout(() => {
        uni.redirectTo({
          url: "/pages/sys/login/index",
        });
      }, 2000);
    }
  },
  onShow: function () {
    // console.log("App Show");
    // App 从后台切回前台时，检查 WebSocket 连接状态
    const token = uni.getStorageSync("token");
    const userId = uni.getStorageSync("userId");
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
page {
  height: 100%;
}
</style>
