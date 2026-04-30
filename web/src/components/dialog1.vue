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

const getVideoData = (): void => {
  // 重置视频错误状态
  videoLoadError.value = false;
  videoErrorMessage.value = '';
  
  console.log('获取视频', props.item.video);

  // 检查是否有有效的视频URL
  if (!props.item.video) {
    console.log('没有提供视频URL');
    return;
  }

  // 验证URL格式
  try {
    new URL(props.item.video);
  } catch (error) {
    console.error('无效的视频URL格式:', props.item.video);
    return;
  }

  // 确保先销毁之前的播放器实例
  destroyFlvPlayer();

  const token = userStore.token;
  console.log('token', userStore.token);
  axios.get('/monitor', {
    headers: {
      Authorization: token,
    },
  }).then((response: any) => {
    console.log('dialog', response?.data?.chartData);
    
    // 优先播放传过来的报警录像短片，如果没有再使用后台默认配置的监控通道流
    video = props.item.video || response?.data?.chartData;

    // --- 模拟演示视频重定向逻辑 ---
    // 当后端收到 SIM_ 开头的 clipId 时，前端将其重定向到本地 8848 端口的演示视频
    if (video && typeof video === 'string') {
      video = resolveDemoAlarmVideo(video);
    }

    const playUrl = withNoCache(video || '');
    const isMp4 = playUrl.toLowerCase().split('?')[0].endsWith('.mp4');
    
    if (isMp4) {
      // MP4 文件使用原生 video 标签播放
      if (videoElement.value) {
        videoElement.value.src = playUrl;
        videoElement.value.load();
      }
    } else if (flvjs.isSupported() && videoElement.value) {
      try {
        flvPlayer = flvjs.createPlayer({
          type: 'flv',
          url: playUrl
        }, {
          enableWorker: false,
          lazyLoad: false, // 改为false以避免某些问题
          deferLoadAfterSourceOpen: false,
          statisticsInfoReportInterval: 600,
          autoCleanupSourceBuffer: true, // 自动清理缓冲区
        } as any);
        flvPlayer.attachMediaElement(videoElement.value);
        flvPlayer.load();
        
        // 监听播放错误
        flvPlayer.on(flvjs.Events.ERROR, (errType: any, errDetail: any) => {
          console.error('FLV播放器错误:', errType, errDetail);
          // 销毁当前播放器实例
          destroyFlvPlayer();
          // 尝试使用原生video标签播放
          if (videoElement.value) {
            videoElement.value.src = playUrl;
            videoElement.value.load();
          }
        });

        // 使用用户交互播放视频
        videoElement.value.addEventListener('click', () => {
          if (flvPlayer && !flvPlayer.hasPlayerStarted()) {
            const playPromise = flvPlayer.play();
            if (playPromise && typeof playPromise.catch === 'function') {
              playPromise.catch((error: any) => {
                console.log('Autoplay failed:', error);
              });
            }
          }
        });
      } catch (error) {
        console.error('创建FLV播放器失败:', error);
        // 如果flv.js创建失败，尝试使用原生video标签
        if (videoElement.value) {
          videoElement.value.src = playUrl;
          videoElement.value.load();
        }
      }
    } else {
      // 如果浏览器不支持flv.js，使用原生video标签
      if (videoElement.value) {
        videoElement.value.src = playUrl;
        videoElement.value.load();
      }
    }
  })
  .catch((error: any) => {
      console.error('Error fetching video data:', error);
      // 如果API调用失败，仍然尝试直接播放视频URL
      if (flvjs.isSupported() && videoElement.value && props.item.video) {
        try {
          const fallbackPlayUrl = withNoCache(props.item.video);
          flvPlayer = flvjs.createPlayer({
            type: 'flv',
            url: fallbackPlayUrl
          }, {
            enableWorker: false,
            lazyLoad: false,
            deferLoadAfterSourceOpen: false,
            statisticsInfoReportInterval: 600,
            autoCleanupSourceBuffer: true,
          });
          
          flvPlayer.attachMediaElement(videoElement.value);
          flvPlayer.load();
          
          flvPlayer.on(flvjs.Events.ERROR, (errType: any, errDetail: any) => {
            console.error('FLV播放器错误:', errType, errDetail);
            // 销毁当前播放器实例
            destroyFlvPlayer();
            // 最后的备选方案：使用原生video标签
            if (videoElement.value) {
              videoElement.value.src = fallbackPlayUrl;
              videoElement.value.load();
            }
          });
        } catch (err) {
          console.error('直接播放视频也失败了:', err);
          if (videoElement.value) {
            videoElement.value.src = withNoCache(props.item.video || '');
            videoElement.value.load();
          }
        }
      } else if (videoElement.value) {
        // 不支持flv.js的情况下，使用原生video标签
        videoElement.value.src = withNoCache(props.item.video || '');
        videoElement.value.load();
      }
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
  
