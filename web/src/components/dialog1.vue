<template>
  <div v-if="localDialogVisible" class="process-modal-mask detail-mask" role="dialog" aria-modal="true" @click.self="handleClose">
    <div class="process-modal-card detail-card">
      <div class="detail-head">
        <div>
          <h4>报警视频片段</h4>
          <p>{{ props.item.eventName || '报警事件' }} · {{ props.item.department || '未标注区域' }}</p>
        </div>
        <button class="detail-close" type="button" @click="handleClose" aria-label="关闭">×</button>
      </div>
      <div class="dialog-content">
        <div class="video">
          <video ref="videoElement" autoplay muted controls @error="handleVideoError"></video>
          <div v-if="videoLoadError" class="video-error-message">
            视频加载失败: {{ videoErrorMessage }}
          </div>
        </div>
        <p class="clip-summary">{{ clipSummary }}</p>
      </div>
    </div>
  </div>
</template>
  
<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
import flvjs from 'flv.js';
import { useUserStore } from '@/stores/user';
import axios from 'axios';
import { resolveDemoAlarmVideo } from '@/config/config';

interface DialogItem {
  eventName: string;
  department: string;
  date?: string;
  level?: string;
  deal?: string;
  video?: string;
  [key: string]: any; // 允许其他属性
}

interface Props {
  item: DialogItem;
}

const props = withDefaults(defineProps<Props>(), {
  item: () => ({
    eventName: '',
    department: '',
  })
});

// 定义 emits
const emit = defineEmits<{
  updateDialogVisible1: [visible: boolean];
}>();

const localDialogVisible = ref<boolean>(true);
const videoElement = ref<HTMLVideoElement | null>(null);
let video: any = null;
let flvPlayer: any = null; // 添加全局flvPlayer引用用于销毁

const clipSummary = computed(() => {
  const item = props.item || {};
  const eventName = item.eventName || '报警事件';
  const department = item.department || '未标注区域';
  const date = item.date || '--';
  const deal = item.deal || '未处理';
  return `${date}，${department} 发生 ${eventName}，当前状态：${deal}。`;
});

const withNoCache = (url: string): string => {
  if (!url) return url;
  const [base, hash = ''] = url.split('#');
  const connector = base.includes('?') ? '&' : '?';
  const nextUrl = `${base}${connector}_t=${Date.now()}`;
  return hash ? `${nextUrl}#${hash}` : nextUrl;
};

const resolvePlayableVideo = (source?: string | null): string => {
  if (!source) return '';
  return resolveDemoAlarmVideo(String(source));
};

// 视频错误状态
const videoLoadError = ref<boolean>(false);
const videoErrorMessage = ref<string>('');

const handleVideoError = (event: Event): void => {
  console.error('视频加载错误:', event);
  videoLoadError.value = true;
  const videoElement = event.target as HTMLVideoElement;
  if (videoElement?.error) {
    switch (videoElement.error.code) {
      case videoElement.error.MEDIA_ERR_ABORTED:
        videoErrorMessage.value = '视频加载被中止';
        break;
      case videoElement.error.MEDIA_ERR_NETWORK:
        videoErrorMessage.value = '网络错误导致视频加载失败';
        break;
      case videoElement.error.MEDIA_ERR_DECODE:
        videoErrorMessage.value = '视频解码失败';
        break;
      case videoElement.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
        videoErrorMessage.value = '不支持的视频格式或来源';
        break;
      default:
        videoErrorMessage.value = '未知错误导致视频加载失败';
        break;
    }
  } else {
    videoErrorMessage.value = '视频加载失败';
  }
};

const handleClose = (): void => {
  // 关闭对话框前销毁播放器实例
  destroyFlvPlayer();
  
  localDialogVisible.value = false; // 处理关闭操作
  emit('updateDialogVisible1', localDialogVisible.value); // 同时通知父组件
};

const userStore = useUserStore();

const playVideoSource = (source?: string | null): boolean => {
  const resolvedVideo = resolvePlayableVideo(source);
  if (!resolvedVideo || !videoElement.value) return false;

  video = resolvedVideo;
  const playUrl = withNoCache(resolvedVideo);
  const isMp4 = playUrl.toLowerCase().split('?')[0].endsWith('.mp4');

  if (isMp4) {
    videoElement.value.src = playUrl;
    videoElement.value.load();
    return true;
  }

  if (flvjs.isSupported()) {
    try {
      flvPlayer = flvjs.createPlayer({
        type: 'flv',
        url: playUrl
      }, {
        enableWorker: false,
        lazyLoad: false,
        deferLoadAfterSourceOpen: false,
        statisticsInfoReportInterval: 600,
        autoCleanupSourceBuffer: true,
      } as any);
      flvPlayer.attachMediaElement(videoElement.value);
      flvPlayer.load();

      flvPlayer.on(flvjs.Events.ERROR, (errType: any, errDetail: any) => {
        console.error('FLV播放器错误:', errType, errDetail);
        destroyFlvPlayer();
        if (videoElement.value) {
          videoElement.value.src = playUrl;
          videoElement.value.load();
        }
      });

      videoElement.value.addEventListener('click', () => {
        if (flvPlayer && !flvPlayer.hasPlayerStarted()) {
          const playPromise = flvPlayer.play();
          if (playPromise && typeof playPromise.catch === 'function') {
            playPromise.catch((error: any) => {
              console.log('Autoplay failed:', error);
            });
          }
        }
      }, { once: true });
      return true;
    } catch (error) {
      console.error('创建FLV播放器失败:', error);
    }
  }

  videoElement.value.src = playUrl;
  videoElement.value.load();
  return true;
};

const getVideoData = (): void => {
  videoLoadError.value = false;
  videoErrorMessage.value = '';
  destroyFlvPlayer();

  console.log('获取报警视频', props.item.video);

  // 报警详情优先播放报警记录中的片段。模拟推送保存的是 SIM_* 标识，这里会先转换成演示 mp4 地址。
  if (playVideoSource(props.item.video)) {
    return;
  }

  const token = userStore.token;
  axios.get('/monitor', {
    headers: {
      Authorization: token,
    },
  }).then((response: any) => {
    console.log('dialog', response?.data?.chartData);
    if (!playVideoSource(response?.data?.chartData)) {
      videoLoadError.value = true;
      videoErrorMessage.value = '没有可播放的视频地址';
    }
  })
  .catch((error: any) => {
    console.error('Error fetching video data:', error);
    videoLoadError.value = true;
    videoErrorMessage.value = '没有可播放的视频地址';
  });
};

// 销毁flv播放器实例
const destroyFlvPlayer = (): void => {
  if (flvPlayer) {
    flvPlayer.unload?.();
    flvPlayer.detachMediaElement?.();
    flvPlayer.destroy?.();
    flvPlayer = null;
  }
  if (videoElement.value) {
    videoElement.value.pause();
    videoElement.value.removeAttribute('src');
    videoElement.value.load();
  }
};

onMounted(() => {
  getVideoData();
});

// 组件卸载时销毁播放器
onUnmounted(() => {
  destroyFlvPlayer();
});

// 监听 dialogVisible1 的变化
watch(
  () => props.item,
  () => {
    destroyFlvPlayer();
    getVideoData();
  },
  { deep: true }
);
</script>
  
<style lang="less" scoped>
.process-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 13000;
  background: rgba(2, 10, 20, 0.62);
  display: grid;
  place-items: center;
  padding: 16px;
}

.process-modal-card {
  width: min(420px, 92vw);
  border-radius: 14px;
  border: 1px solid rgba(118, 183, 255, 0.3);
  background: linear-gradient(180deg, rgba(14, 43, 74, 0.95), rgba(9, 31, 54, 0.95));
  box-shadow: 0 22px 48px rgba(3, 16, 30, 0.48);
  padding: 14px;
}

.dialog-content {
  display: grid;
  gap: 10px;
}

.detail-card {
  width: min(1080px, 92vw);
  max-height: 92vh;
  overflow: hidden;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.detail-head h4 {
  margin: 0;
  font-size: 16px;
  color: #eaf5ff;
}

.detail-head p {
  margin: 4px 0 0;
  color: rgba(214, 230, 255, 0.68);
  font-size: 12px;
}

.detail-close {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(126, 197, 255, 0.28);
  background: rgba(12, 39, 66, 0.7);
  color: #cde8ff;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.video {
  height: min(68vh, 38rem);
  min-height: 28rem;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(126, 197, 255, 0.28);
  background: rgba(8, 27, 45, 0.72);

  video {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #020913;
  }

  .video-error-message {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(3, 14, 28, 0.82);
    color: #d6e8ff;
    border: 1px solid rgba(255, 123, 136, 0.52);
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    text-align: center;
    z-index: 10;
    width: min(90%, 420px);
    word-wrap: break-word;
  }
}

.clip-summary {
  margin: 0;
  border: 1px solid rgba(126, 197, 255, 0.36);
  color: #d8ebff;
  background: rgba(15, 45, 74, 0.72);
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .detail-card {
    width: min(96vw, 1080px);
    max-height: 90vh;
  }

  .video {
    height: 58vh;
    min-height: 16rem;
  }
}
</style>
  
