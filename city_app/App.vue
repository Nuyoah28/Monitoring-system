<script>
import websocket from '@/common/websocket.js';

const COMMAND_DARK_COLOR = '#071525';

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

const syncNativeShellColor = () => {
  // #ifdef APP-PLUS
  if (typeof plus === 'undefined') return;
  try {
    if (plus.navigator && typeof plus.navigator.setStatusBarBackground === 'function') {
      plus.navigator.setStatusBarBackground(COMMAND_DARK_COLOR);
    }
    if (plus.os && plus.os.name === 'Android' && plus.android) {
      const main = plus.android.runtimeMainActivity();
      const window = main.getWindow();
      plus.android.importClass(window);
      const Color = plus.android.importClass('android.graphics.Color');
      const color = Color.parseColor(COMMAND_DARK_COLOR);
      if (typeof window.setNavigationBarColor === 'function') {
        window.setNavigationBarColor(color);
      }
      if (typeof window.setStatusBarColor === 'function') {
        window.setStatusBarColor(color);
      }
    }
  } catch (e) {
    console.warn('[App] 设置原生系统栏颜色失败：', e);
  }
  // #endif
};

const createNotificationPlayer = () => {
  // #ifdef APP-PLUS
  if (typeof plus === 'undefined' || !plus.android) return null;
  try {
    const main = plus.android.runtimeMainActivity();
    const RingtoneManager = plus.android.importClass("android.media.RingtoneManager");
    const uri = RingtoneManager.getActualDefaultRingtoneUri(main, RingtoneManager.TYPE_NOTIFICATION);
    const MediaPlayer = plus.android.importClass("android.media.MediaPlayer");
    return MediaPlayer.create(main, uri);
  } catch (e) {
    console.warn('[App] 初始化通知提示音失败：', e);
    return null;
  }
  // #endif
  return null;
};

const playNotificationSound = (player) => {
  // #ifdef APP-PLUS
  if (!player) return;
  try {
    if (typeof player.isPlaying === 'function' && player.isPlaying()) {
      player.seekTo(0);
      return;
    }
    if (typeof player.start === 'function') {
      player.start();
    }
  } catch (e) {
    console.warn('[App] 播放通知提示音失败：', e);
  }
  // #endif
};

const safeCreatePushMessage = (options) => {
  // #ifdef APP-PLUS
  if (typeof uni.createPushMessage !== 'function') return;
  try {
    uni.createPushMessage(options);
  } catch (e) {
    console.warn('[App] 创建系统推送失败：', e);
  }
  // #endif
};

const safeVibrateLong = () => {
  // #ifdef APP-PLUS
  if (typeof uni.vibrateLong !== 'function') return;
  try {
    uni.vibrateLong({
      fail: (err) => {
        console.log('[App] 振动失败：', err);
      },
    });
  } catch (e) {
    console.warn('[App] 调用振动异常：', e);
  }
  // #endif
};

export default {
  onLaunch: function () {
    // console.log("App Launch");
    // #ifdef APP-PLUS
    if(typeof plus !== 'undefined') {
        syncNativeShellColor();
        let player = createNotificationPlayer();
        let check = 1;
        let lastReceiveAt = 0;

        if (typeof uni.onPushMessage === 'function') uni.onPushMessage((res) => {
          // console.log(res);
          if (res.type === "click") {
            const currentAppType = uni.getStorageSync("appType");
            if (currentAppType === "owner") {
              uni.reLaunch({
                url: "/pages/owner/home/index",
              });
            } else {
              uni.reLaunch({
                url: "/pages/manage/controls/controls",
              });
            }
          } else if (res.type === "receive") {
            const now = Date.now();
            if (now - lastReceiveAt < 1200) return;
            lastReceiveAt = now;
            if (check === 0) {
              check = 1;
              return;
            }
            safeCreatePushMessage({
              title: (res.data && res.data.title) || '报警提醒',
              content: '您有一条新的报警信息，请及时处理',
              sound: "system",
            });
            check = 0;
            safeVibrateLong();
            // player.setLooping(false);
            // player.prepare();
            playNotificationSound(player);
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
      __skipSafeNavigation: true,
    });
  },
  onShow: function () {
    // console.log("App Show");
    syncNativeShellColor();
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
@import "./common/command-theme.scss";
page, .uni-page-body {
  min-height: 100% !important;
  background: #071525 !important;
  color: #0F2238;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}

view,
text {
  box-sizing: border-box;
}
</style>
