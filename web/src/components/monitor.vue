<template>
  <div class="panel">
    <div id="demoDiv">
      <div class="videoDiv">
        <video ref="videoElement" class="video-js vjs-default-skin" controls autoplay></video>
      </div>

      <el-button @click="drawer = true" type="primary" class="btn">
        点击查看监控列表
      </el-button>

      <el-drawer
        title="监控列表"
        v-model="drawer"
        :direction="direction"
        :before-close="handleClose">
        <div class="lists">
          <div
            class="list"
            v-for="(item, index) in monitorLists"
            :key="index"
            @click="checkmonitor(index)">
            <div class="t1">
              <div class="t11">{{ item.name }}</div>
              <div class="t12">
                <div class="text4" :style="item.running ? fontStyle[0] : fontStyle[1]">
                  {{ item.running ? '正在运行' : '已停用' }}
                </div>
                <div class="img4">
                  <img :src="item.running ? require('../../public/assets/running.png') : require('../../public/assets/unrunning.png')" alt="">
                </div>
              </div>
            </div>
            <div class="t2">
              <div class="t21">
                <h4>摄像头编号：{{ item.number }}</h4>
                <h4>区域负责人：{{ item.leader }}</h4>
              </div>
              <div class="t22">
                <el-button type="primary" icon="el-icon-edit" @click.stop="openEditForm(item, index)" class="t22btn">编辑</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-drawer>
      
      <!-- 编辑监控信息的对话框 -->
      <el-dialog
        v-model="editDialogVisible"
        title="编辑监控信息"
        width="500px"
        :before-close="closeEditForm">
        <el-form :model="currentMonitor" :rules="formRules" ref="editFormRef" label-width="100px">
          <el-form-item label="监控名称" prop="name">
            <el-input v-model="currentMonitor.name" placeholder="请输入监控名称"></el-input>
          </el-form-item>
          <el-form-item label="摄像头编号" prop="number">
            <el-input v-model="currentMonitor.number" placeholder="请输入摄像头编号"></el-input>
          </el-form-item>
          <el-form-item label="区域负责人" prop="leader">
            <el-input v-model="currentMonitor.leader" placeholder="请输入区域负责人"></el-input>
          </el-form-item>
          <el-form-item label="运行状态" prop="running">
            <el-switch
              v-model="currentMonitor.running"
              active-text="运行中"
              inactive-text="已停用">
            </el-switch>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeEditForm">取消</el-button>
            <el-button type="primary" @click="submitEditForm">确定</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
    <div class="panel-footer"></div>
  </div>
  
</template>
  
<script setup lang="ts">
// import videojs from 'video.js'; // 引入 video.js
// import 'video.js/dist/video-js.css'; // 引入 video.js 样式
// import 'videojs-flash'; // 引入 RTMP 支持
import flvjs from 'flv.js';
// import Hls from 'hls.js';
import { ref, onMounted, onUnmounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import { useAppStore } from '@/stores/app';
import { ElMessage } from 'element-plus'
import axios from 'axios';
import { baseUrl } from '@/config/config';

// 定义监控项接口
interface MonitorItem {
  id?: number; // 监控项ID，用于API调用
  name: string;
  number: string;
  leader: string;
  running: boolean;
  video: string | null;
}

const flvPlayer = ref<any>(null); // 更改为 flvPlayer
const drawer = ref<boolean>(false);
const direction = ref<string>('rtl');
const editDialogVisible = ref<boolean>(false);
const currentMonitor = ref<MonitorItem>({
  name: '',
  number: '',
  leader: '',
  running: true,
  video: null,
});
const currentMonitorIndex = ref<number>(-1);
const editFormRef = ref();

const monitorLists = ref<MonitorItem[]>([]);

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入监控名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  number: [
    { required: true, message: '请输入摄像头编号', trigger: 'blur' },
    { min: 1, max: 20, message: '长度在 1 到 20 个字符', trigger: 'blur' }
  ],
  leader: [
    { required: true, message: '请输入区域负责人', trigger: 'blur' },
    { min: 1, max: 20, message: '长度在 1 到 20 个字符', trigger: 'blur' }
  ]
};

const fontStyle = reactive<{color: string}[]>([
  { color: '#06BFA1' },
  { color: 'red' },
]);

const router = useRouter();

const initializeVideoPlayer = (videoUrl: string): void => {
  if (flvjs.isSupported()) {
    const videoElement = document.querySelector('video'); // 获取视频元素
    if(videoElement && flvPlayer.value) {
      flvPlayer.value.destroy(); // 先销毁之前的播放器实例
      flvPlayer.value = null; // 清空引用
    }
    console.log('videourl', videoUrl);
    //使用临时的001.flv，等物联网端接入后，再替换为动态的视频链接
    try {
      flvPlayer.value = flvjs.createPlayer({
        type: 'flv',
        url:  baseUrl + '/video/001.flv', //videoUrl 
      }, {
        enableWorker: false, // 禁用worker模式以减少复杂性
        enableStashBuffer: false, // 减少缓冲区以提高稳定性
        stashInitialSize: 128, // 设置初始缓冲区大小
      });
      if(videoElement) {
        flvPlayer.value.attachMediaElement(videoElement);
        flvPlayer.value.load();
        // 使用用户交互播放视频
        videoElement.addEventListener('click', () => {
            const playPromise = flvPlayer.value.play();
            if (playPromise && typeof playPromise.catch === 'function') {
              playPromise.catch((error: any) => {
                console.log('Autoplay failed:', error);
              });
            }
          });
        
        // 添加错误处理
        flvPlayer.value.on(flvjs.Events.ERROR, (err: any) => {
          console.error('FLV Player Error:', err);
        });
      }
    } catch (error) {
      console.error('Failed to initialize FLV player:', error);
    }
  }
};

const getVideoData = (): void => {
  // const video = 'http://play1.city-guardian.top/live/test.flv?auth_key=1728140343-0-0-4233a23962cf2a9e8eb3fd7d5b36ac2f'
  // initializeVideoPlayer(video);

  const userStore = useUserStore();
  const appStore = useAppStore();
  // 从 sessionStorage 恢复 monitorId 状态
  appStore.hydrateFromSessionStorage();
  
  const token = userStore.token;
  
  
  axios.get('/api/v1/monitor', {
    headers: {
      Authorization: token,
    },
  }).then((response: any) => {
    if (response.data.code === 'D0400') {
      ElMessage({
        message: 'token过期，请重新登录',
        type: 'warning',
      });   
      router.push('/login');
    } else {
      console.log('获取监控列表成功', response);
      const data = response.data.data;
      monitorLists.value = data; // 更新监控列表

      const id = appStore.getMonitorId;
      
      // 在这里调用初始化视频播放器，将数据传递进去
      if (data[id]?.video) {
        console.log('video',data[id].video);
        initializeVideoPlayer(data[id].video);
      }
    }
  })
  .catch((error: any) => {
    console.error('Error fetching video data:', error);
  });
};

const handleClose = (done: (() => void) | undefined): void => {
  // 在关闭抽屉之前，暂停视频
  if (flvPlayer.value) {
    flvPlayer.value.pause(); // 暂停视频
  }
  
  // 检查是否有未保存的更改需要确认，如果没有则直接关闭
  // 这里简化处理，直接关闭而不询问
  if (done) {
    done();
  } else {
    // 如果没有传入done函数（例如直接调用），则手动设置drawer为false
    drawer.value = false;
  }
};

const checkmonitor = (index: number): void => {
  const selectedVideoUrl = monitorLists.value[index].video;
  const appStore = useAppStore();
  // 使用 Pinia store 设置 monitorId
  appStore.setMonitorId(index);

  // 调用播放视频的函数
  playFlvVideo(selectedVideoUrl);
  // 关闭 el-drawer
  drawer.value = false;
};

// 打开编辑表单
const openEditForm = (item: any, index: number): void => {
  // 复制当前监控项到临时对象，排除不需要编辑的字段
  currentMonitor.value = {
    name: item.name,
    number: item.number,
    leader: item.leader,
    running: item.running,
    video: item.video,
    id: item.id
  };
  currentMonitorIndex.value = index;
  editDialogVisible.value = true;
};

// 关闭编辑表单
const closeEditForm = (): void => {
  editDialogVisible.value = false;
  // 重置表单验证
  if (editFormRef.value) {
    editFormRef.value.clearValidate();
  }
};

// 提交编辑表单
const submitEditForm = async () => {
  if (editFormRef.value) {
    // 验证表单
    await editFormRef.value.validate(async (valid: boolean) => {
      if (valid) {
        try {
          // 调用后端API更新监控信息
          const userStore = useUserStore();
          const token = userStore.token;
          
          // 准备更新数据，保留原始的不可编辑字段值
          const originalItem = monitorLists.value[currentMonitorIndex.value];
          const updateData = {
            name: currentMonitor.value.name,
            leader: currentMonitor.value.leader,
            running: currentMonitor.value.running,
          };
          console.log('updateData',updateData);
          // 尝试使用后端API更新监控信息
          let response = await axios.post('/api/v1/monitor/update', updateData, {
            headers: {
              'Authorization': token,
              'Content-Type': 'application/json'
            }
          });
        
          if (response.data.code === '00000') {
            // 更新本地监控列表中的对应项，保留原始的不可编辑字段
            monitorLists.value[currentMonitorIndex.value] = {
              ...currentMonitor.value,
              video: originalItem.video
            };
            
            // 显示成功消息
            ElMessage({
              message: '监控信息更新成功',
              type: 'success',
            });
            
            // 关闭对话框
            closeEditForm();
          } else if (response.data.code === 'D0400') {
            ElMessage({
              message: 'token过期，请重新登录',
              type: 'warning',
            });   
            router.push('/login');
          } else {
            ElMessage({
              message: response.data.message || '更新失败',
              type: 'error',
            });
          }
        } catch (error: any) {
          console.error('更新监控信息失败:', error);
          ElMessage({
            message: '更新监控信息失败，请稍后重试',
            type: 'error',
          });
        }
      } else {
        console.log('表单验证失败');
      }
    });
  }
};

const playFlvVideo = (videoUrl: string | null): void => {
  if (videoUrl) {
    initializeVideoPlayer(videoUrl); // 调用初始化播放器方法
  } else {
    console.warn('No video URL provided, cannot play video');
  }
};

onMounted(() => {
  getVideoData();
});

onUnmounted(() => {
  if (flvPlayer.value) {
    flvPlayer.value.unload(); // 卸载媒体资源
    flvPlayer.value.destroy(); // 销毁 flv.js 播放器实例
    flvPlayer.value = null; // 清空引用
  }
});
</script>

<style scoped>
#demoDiv {
  width: 32rem;
  height: 19rem;
  position: relative;
}

.list {
  width: 85%;
  height: 8rem;
  margin: 0 auto;
  border-radius: 1.2rem;
  background-color: #e8eefe;
  margin-bottom: 2rem;
  padding: 1rem 1.7rem;
  cursor: pointer;
  color: #636b95;
}

.list .t1 {
  display: flex;
  justify-content: space-between;
}

.list .t1 .t11 {
  font-size: 1.8rem;
  font-weight: 600;
}

.list .t1 .t12 {
  display: flex;
}

.list .t1 .t12 .text4 {
  margin-right: 0.8rem;
  font-size: 1.5rem;
}

.list .t1 .t12 .img4 img {
  width: 1.7rem;
  height: 1.7rem;
}

.list .t2 {
  margin-top: 0.6rem;
  display: flex;
}

.list .t2 .t21 {
  flex: 3;
}

.list .t2 .t21 h4 {
  font-size: 1.2rem;
  text-align: left;
}

.list .t2 .t22 {
  flex: 2;
}

.list .t2 .t22 .t22btn {
  margin-top: 1.2rem;
  margin-left: 2.5rem;
}

.btn {
  width: 12rem;
  position: absolute;
  top: -3%;
  right: 0%;
}

.videoDiv {
  width: 100%;
  height: 93%;
  margin-top: 0.8rem;
}

.panel {
  padding: 0 0;
}

video {
  width: 100%;
  height: 100%;
  margin: 0 auto;
  margin-top: -0.6rem;
  object-fit: cover; /* 使视频填充容器并裁剪超出部分 */
}
</style>