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

    <!-- 新增：Mamba-YOLO 智能助手 (悬浮球 + 展开框) -->
    <!-- 1. 悬浮小球状态 -->
    <div 
      class="ai-floating-ball" 
      v-show="flvPlayer && !isPanelExpanded"
      :style="{ left: panelPosition.x + 'px', top: panelPosition.y + 'px' }"
      @mousedown="startDrag"
      @click="togglePanel"
    >
      <div class="ball-core">
        <i class="el-icon-service"></i>
      </div>
      <div class="ball-ring"></div>
    </div>

    <!-- 2. 展开的 HUD 面板 -->
    <div 
      class="ai-prompt-panel hud-style" 
      v-show="flvPlayer && isPanelExpanded"
      :style="{ left: panelPosition.x + 'px', top: panelPosition.y + 'px' }"
    >
      <!-- HUD 四个角的科幻折线 -->
      <span class="hud-angle hud-tl"></span>
      <span class="hud-angle hud-tr"></span>
      <span class="hud-angle hud-bl"></span>
      <span class="hud-angle hud-br"></span>

      <!-- 拖拽手柄 & 头部 -->
      <div 
        class="panel-header drag-handle" 
        @mousedown="startDrag"
      >
        <div class="title">动态目标侦测</div>
        <div class="hud-collapse" @click.stop="isPanelExpanded = false">收起</div>
      </div>
      
      <!-- 对话/提示信息区 -->
      <div class="panel-chat">
        <div class="chat-msg">
          <span class="chat-role">系统</span>
          <span class="chat-text">欢迎使用 Mamba-YOLO 开放世界目标提取系统。请输入你想要侦测的物体（如：红色电动车，戴帽子的人），多个目标请用逗号分隔。</span>
        </div>
        <div class="chat-msg" v-if="activePrompts.length > 0">
          <span class="chat-role" style="color:#52eecb;">侦测中</span>
          <span class="chat-text">
            <el-tag 
              v-for="(p, index) in activePrompts" 
              :key="index" 
              size="mini" 
              effect="dark" 
              closable
              @close="removePrompt(index)"
              class="prompt-tag"
            >{{ p.zh }} {{ p.en ? `(${p.en})` : '' }}</el-tag>
          </span>
        </div>
      </div>

      <!-- 底部输入框区 -->
      <div class="panel-footer-input">
        <input 
          type="text" 
          v-model="customPrompts" 
          placeholder="请输入侦测目标，回车下发" 
          class="hud-input"
          @keyup.enter="submitCustomPrompts"
        />
        <button 
          class="hud-send-btn" 
          @click="submitCustomPrompts" 
          :disabled="isPromptSubmitting"
        >
          {{ isPromptSubmitting ? '下发中' : '下发' }}
        </button>
      </div>
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
import { baseUrl, algorithmUrl, rtmpAddress } from '@/config/config';

// 定义监控项接口
interface MonitorItem {
  id?: number; // 监控项ID，用于API调用
  name: string;
  number: string;
  leader: string;
  running: boolean;
  video: string | null;
}

// === 动态提示词相关状态 ===
const customPrompts = ref<string>(''); // 用户输入框绑定的值
const activePrompts = ref<{zh: string, en: string}[]>([]); // 当前正在生效的自定义检测词
const isPromptSubmitting = ref<boolean>(false);
const isPanelExpanded = ref<boolean>(false); // 控制是显示球还是面板

// === 拖拽相关状态 ===
const panelPosition = reactive({ x: typeof window !== 'undefined' ? window.innerWidth - 350 : 800, y: typeof window !== 'undefined' ? window.innerHeight - 400 : 500 });
let isDragging = false;
let startMousePos = { x: 0, y: 0 };
let startPanelPos = { x: 0, y: 0 };
let hasMoved = false; // 用于区分点击和拖拽

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
    try {
      flvPlayer.value = flvjs.createPlayer({
        type: 'flv',
        url: rtmpAddress,
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

// ==========================================
// 核心：Mamba-YOLO 动态提示词下发逻辑
// ==========================================
const submitCustomPrompts = async () => {
  if (!customPrompts.value.trim()) {
    ElMessage.warning('提示词不能为空呀，你想找什么？');
    return;
  }
  
  // 处理中文逗号和分号为英文逗号
  const newInputs = customPrompts.value
    .replace(/，/g, ',')
    .replace(/；/g, ',')
    .replace(/;/g, ',')
    .split(',')
    .map(p => p.trim())
    .filter(p => p.length > 0);

  if (newInputs.length === 0) return;

  // 提取现有的中文词汇，追加新的词汇，并去重
  const existingZhs = activePrompts.value.map(item => item.zh);
  const combinedZhs = Array.from(new Set([...existingZhs, ...newInputs]));

  await syncPromptsToBackend(combinedZhs, '添加');
  
  // 如果追加成功，清空输入框
  customPrompts.value = '';
};

// ==========================================
// 删除一个提词 Tag 的逻辑
// ==========================================
const removePrompt = async (index: number) => {
  const newPrompts = [...activePrompts.value];
  newPrompts.splice(index, 1);
  const remainingZhs = newPrompts.map(item => item.zh);
  await syncPromptsToBackend(remainingZhs, '移除');
};

// ==========================================
// 共用的将数组同步到后端的逻辑
// ==========================================
const syncPromptsToBackend = async (promptsListZh: string[], actionName: string) => {
  isPromptSubmitting.value = true;
  try {
    const userStore = useUserStore();
    const token = userStore.token;
    // 使用后端的转发代理接口，而不是直接连接算法端，以保证跨内网和鉴全能成功穿透
    const response = await axios.post(`/api/v1/monitor/update_prompt`, {
      prompts: promptsListZh
    }, {
      headers: {
        Authorization: token
      }
    });

    if (response.data.code === '00000') {
      ElMessage.success(`🚀 AI 侦测指令已${actionName}并下发！`);
      // 后端会返回对应的英文翻译 translated 数组
      const translatedEn = response.data.data || response.data.translated || [];
      activePrompts.value = promptsListZh.map((zhStr, idx) => ({
        zh: zhStr,
        en: translatedEn[idx] || ''
      }));
    } else {
      ElMessage.error(`指令${actionName}失败: ` + (response.data.message || response.data.msg || '未知错误'));
    }
  } catch (error: any) {
    if (error.response && error.response.data) {
      ElMessage.error(`指令${actionName}失败: ` + (error.response.data.message || '未知异常'));
    } else {
      ElMessage.error('网络请求失败，算法节点未就绪或已掉线。');
    }
    console.error(`下发提示词(${actionName})出错:`, error);
  } finally {
    isPromptSubmitting.value = false;
  }
};

// ==========================================
// 拖拽与切换面板控制逻辑
// ==========================================
const togglePanel = () => {
  if (!hasMoved) {
    isPanelExpanded.value = !isPanelExpanded.value;
  }
};

const startDrag = (e: MouseEvent) => {
  isDragging = true;
  hasMoved = false; // 重置移动标志
  startMousePos = { x: e.clientX, y: e.clientY };
  startPanelPos = { x: panelPosition.x, y: panelPosition.y };
  
  document.addEventListener('mousemove', drag);
  document.addEventListener('mouseup', endDrag);
  // 防止拖拽时选中文本
  e.preventDefault();
};

const drag = (e: MouseEvent) => {
  if (!isDragging) return;
  const dx = e.clientX - startMousePos.x;
  const dy = e.clientY - startMousePos.y;
  
  // 设置一个简单的容差值，区分轻微抖动和真实的拖拽
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    hasMoved = true;
  }
  
  panelPosition.x = startPanelPos.x + dx;
  panelPosition.y = startPanelPos.y + dy;
};

const endDrag = () => {
  isDragging = false;
  document.removeEventListener('mousemove', drag);
  document.removeEventListener('mouseup', endDrag);
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

/* AI 智能助手面板样式 (悬浮 HUD 风格) */
.hud-style {
  background: rgba(14, 42, 98, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(41, 128, 255, 0.3);
  border-radius: 4px;
  padding: 20px;
  width: 420px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 0 20px rgba(41, 128, 255, 0.1);
}

.ai-prompt-panel {
  position: fixed; /* 悬浮层 */
  color: #fff;
  z-index: 9999;
}

/* 4个角的科技感折线 */
.hud-angle {
  position: absolute;
  width: 15px;
  height: 15px;
  border: 2px solid transparent;
}
.hud-tl { top: -1px; left: -1px; border-top-color: #22d3e9; border-left-color: #22d3e9; }
.hud-tr { top: -1px; right: -1px; border-top-color: #22d3e9; border-right-color: #22d3e9; }
.hud-bl { bottom: -1px; left: -1px; border-bottom-color: #22d3e9; border-left-color: #22d3e9; }
.hud-br { bottom: -1px; right: -1px; border-bottom-color: #22d3e9; border-right-color: #22d3e9; }

/* 拖拽手柄 & 头部 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.drag-handle {
  cursor: grab;
  user-select: none;
}
.drag-handle:active {
  cursor: grabbing;
}
.title {
  font-size: 1.2rem;
  letter-spacing: 1px;
}
.hud-collapse {
  font-size: 0.9rem;
  color: #c0c4cc;
  border: 1px solid #c0c4cc;
  border-radius: 12px;
  padding: 2px 10px;
  cursor: pointer;
  transition: all 0.3s;
}
.hud-collapse:hover {
  color: #fff;
  border-color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

/* 聊天历史区域 */
.panel-chat {
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 20px;
  max-height: 200px;
  overflow-y: auto;
}
.chat-msg {
  display: flex;
  margin-bottom: 10px;
}
.chat-role {
  color: #a0cfff;
  white-space: nowrap;
  margin-right: 15px;
}
.chat-text {
  color: #e4e7ed;
}

/* 底部输入框区 */
.panel-footer-input {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
.hud-input {
  flex: 1;
  border: none;
  border-radius: 4px;
  padding: 0 15px;
  height: 38px;
  background: #ffffff;
  color: #333;
  outline: none;
  font-size: 0.95rem;
}
.hud-input::placeholder {
  color: #999;
}
.hud-send-btn {
  background: #a0cfff;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0 20px;
  height: 38px;
  cursor: pointer;
  font-size: 1rem;
  letter-spacing: 2px;
  transition: background 0.3s;
}
.hud-send-btn:hover {
  background: #79bbff;
}
.hud-send-btn:disabled {
  background: #c8e1fa;
  cursor: not-allowed;
}
.prompt-tag {
  background-color: rgba(34, 211, 233, 0.2);
  border-color: #22d3e9;
  color: #22d3e9;
  margin-right: 5px;
  margin-bottom: 5px;
}

/* 悬浮小球样式 */
.ai-floating-ball {
  position: fixed;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  cursor: grab;
  z-index: 10000;
  display: flex;
  justify-content: center;
  align-items: center;
}
.ai-floating-ball:active {
  cursor: grabbing;
}
.ball-core {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #22d3e9, #409eff);
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 4px 15px rgba(34, 211, 233, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.5rem;
  color: #fff;
  z-index: 2;
  transition: transform 0.3s;
}
.ai-floating-ball:hover .ball-core {
  transform: scale(1.05);
}
.ball-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  border: 2px solid rgba(34, 211, 233, 0.3);
  animation: pulse 2s infinite ease-out;
  z-index: 1;
}
@keyframes pulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.3); opacity: 0; }
}
</style>