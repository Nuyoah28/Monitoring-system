<template>
  <el-dialog
    title="报警信息"
    class="dialog"
    v-model="localDialogVisible"
    width="30%"
    :before-close="handleClose">
    <span>
      <div class="video">
        <video ref="videoElement" muted controls @error="handleVideoError"></video>
        <div v-if="videoLoadError" class="video-error-message">
          视频加载失败: {{ videoErrorMessage }}
        </div>
      </div>
      <el-table
      :data="tableData"
        stripe
      style="width: 100%">
      <el-table-column width="30">
      </el-table-column>
      <el-table-column
        prop="key">
      </el-table-column>
      <el-table-column
        prop="val"
        width="160">
      </el-table-column>
    </el-table>
    </span>
    <span slot="footer" class="dialog-footer">
      <el-button @click="closeDialog">取 消</el-button>
      <el-button type="primary" @click="closeDialog">确 定</el-button>
    </span>
  </el-dialog>
</template>
  
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import flvjs from 'flv.js';
import { useUserStore } from '@/stores/user';
import axios from 'axios';

// 定义props类型
interface TableItem {
  key: string;
  val: any;
}

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

// 初始化表格数据
const tableData = ref<TableItem[]>([
  {
    key: '事件类型',
    val: props.item.eventName,
  }, 
  {
    key: '区域',
    val: props.item.department,
  },
  {
    key: '时间',
    val: props.item.date,
  }, 
  {
    key: '等级',
    val: props.item.level,
  },
  {
    key: '处理结果',
    val: props.item.deal,
  }
]);

const closeDialog = (): void => {
  console.log('关闭了');
  
  // 关闭对话框前销毁播放器实例
  destroyFlvPlayer();
  
  localDialogVisible.value = false; // 修改本地变量
  emit('updateDialogVisible1', localDialogVisible.value); // 通知父组件更新
};

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
    
    video = response?.data?.chartData || props.item.video;  // 将响应数据绑定到组件状态中，如果API返回undefined则使用传入的视频URL
    const playUrl = withNoCache(video || props.item.video || '');
    if (flvjs.isSupported() && videoElement.value) {
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
  (newVal) => {
    // 如果需要根据新值更新表格数据
    // 先销毁旧的播放器实例
    destroyFlvPlayer();
    
    tableData.value = [
      {
        key: '事件类型',
        val: newVal.eventName,
      }, 
      {
        key: '区域',
        val: newVal.department,
      },
      {
        key: '时间',
        val: newVal.date,
      }, 
      {
        key: '等级',
        val: newVal.level,
      },
      {
        key: '处理结果',
        val: newVal.deal,
      }
    ];
  },
  { deep: true }
);
</script>
  
  <style lang="less" scoped>
  .video {
    height: 20rem;
    position: relative;
    
    video {
        width: 95%;
        height: 100%;
        margin: 0 auto;
        // margin-top: 0.5rem;
        object-fit: cover; /* 使视频填充容器并裁剪超出部分 */
      }
      
    .video-error-message {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background-color: rgba(0, 0, 0, 0.7);
      color: #fff;
      padding: 10px 20px;
      border-radius: 4px;
      font-size: 14px;
      text-align: center;
      z-index: 10;
      width: 90%;
      word-wrap: break-word;
    }
  }
  

  </style>
  
