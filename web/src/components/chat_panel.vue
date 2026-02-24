<template>
  <div class="panel chat-panel" :class="{ expanded: isExpanded }" :style="panelStyle">
    <div class="chat-header" @mousedown="onDragStart">
      <span>智能助手</span>
      <button class="toggle-btn" type="button" @click.stop="toggleExpand">
        {{ isExpanded ? '收起' : '展开' }}
      </button>
    </div>
    <div ref="messageBox" class="chat-messages">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['chat-message', msg.role]">
        <div class="chat-role">{{ msg.role === 'user' ? '我' : '助手' }}</div>
        <div v-if="msg.role === 'assistant'" class="chat-content" v-html="renderMarkdown(msg.content)"></div>
        <div v-else class="chat-content">{{ msg.content }}</div>
      </div>
      <div v-if="isStreaming" class="chat-typing">正在生成回复...</div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="question"
        placeholder="请输入问题，回车发送"
        :disabled="isStreaming"
        @keyup.enter="sendQuestion"
      />
      <el-tooltip content="语音输入" placement="top">
        <el-button
          :type="isRecording ? 'danger' : 'default'"
          circle
          class="voice-btn"
          :disabled="isStreaming"
          @click="toggleVoice"
        >
          <span v-if="!isRecording">🎤</span>
          <span v-else class="recording-dot">●</span>
        </el-button>
      </el-tooltip>
      <el-button type="primary" class="send-btn" :disabled="!canSend" @click="sendQuestion">
        发送
      </el-button>
      <el-button v-if="isStreaming" type="danger" plain class="stop-btn" @click="stopStream">
        停止
      </el-button>
      <el-tooltip v-if="isTtsPlaying" content="停止语音播放" placement="top">
        <el-button type="warning" plain circle class="stop-tts-btn" @click="stopTtsPlayback">
          ⏹
        </el-button>
      </el-tooltip>
    </div>
    <div class="panel-footer"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue';
import { useUserStore } from '@/stores/user';
import { agentBaseUrl } from '@/config/config';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

type MessageRole = 'user' | 'assistant';
interface ChatMessage {
  role: MessageRole;
  content: string;
}

const question = ref<string>('');
const messages = ref<ChatMessage[]>([
  { role: 'assistant', content: '你好，我是智能助手，可以帮你查询告警、监控点、实时统计等信息。' }
]);
const isStreaming = ref<boolean>(false);
const messageBox = ref<HTMLElement | null>(null);
let abortController: AbortController | null = null;
const position = ref<{ x: number; y: number }>({ x: 0, y: 0 });
const isExpanded = ref<boolean>(false);
const isDragging = ref<boolean>(false);
const dragOffset = ref<{ x: number; y: number }>({ x: 0, y: 0 });

const canSend = computed(() => question.value.trim().length > 0 && !isStreaming.value);
const panelStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`
}));

// 语音输入
const isRecording = ref<boolean>(false);
// 语音播放：可随时停止
const isTtsPlaying = ref<boolean>(false);
let currentTtsAudio: HTMLAudioElement | null = null;
let mediaStream: MediaStream | null = null;
let audioContext: AudioContext | null = null;
let processor: ScriptProcessorNode | null = null;
let source: MediaStreamAudioSourceNode | null = null;
const recordedChunks = ref<Int16Array[]>([]);
let sampleRate = 16000;

function floatTo16BitPCM(float32Array: Float32Array): Int16Array {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return int16Array;
}

function encodeWAV(samples: Int16Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeStr = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };
  writeStr(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeStr(8, 'WAVE');
  writeStr(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  const offset = 44;
  for (let i = 0; i < samples.length; i++) view.setInt16(offset + i * 2, samples[i], true);
  return new Blob([buffer], { type: 'audio/wav' });
}

const startRecording = (): void => {
  recordedChunks.value = [];
  navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    mediaStream = stream;
    audioContext = new AudioContext({ sampleRate: 16000 });
    sampleRate = audioContext.sampleRate;
    const input = audioContext.createMediaStreamSource(stream);
    source = input;
    processor = audioContext.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0);
      recordedChunks.value.push(floatTo16BitPCM(inputData));
    };
    input.connect(processor);
    processor.connect(audioContext.destination);
    isRecording.value = true;
  }).catch((err) => {
    console.error('麦克风不可用', err);
    appendMessage('assistant', '[语音] 无法访问麦克风，请允许浏览器使用麦克风。');
  });
};

const stopRecordingAndSend = (): void => {
  if (!processor || !source || !audioContext) return;
  processor.disconnect();
  source.disconnect();
  if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
  isRecording.value = false;
  const totalLength = recordedChunks.value.reduce((acc, arr) => acc + arr.length, 0);
  const merged = new Int16Array(totalLength);
  let offset = 0;
  for (const arr of recordedChunks.value) {
    merged.set(arr, offset);
    offset += arr.length;
  }
  recordedChunks.value = [];
  if (merged.length < 1000) {
    appendMessage('assistant', '[语音] 录音太短，请重试。');
    return;
  }
  const wavBlob = encodeWAV(merged, sampleRate);
  sendVoiceToAgent(wavBlob);
};

const toggleVoice = (): void => {
  if (isRecording.value) {
    stopRecordingAndSend();
  } else {
    startRecording();
  }
};

const stopTtsPlayback = (): void => {
  if (currentTtsAudio) {
    currentTtsAudio.pause();
    currentTtsAudio.currentTime = 0;
    currentTtsAudio = null;
  }
  isTtsPlaying.value = false;
};

const sendVoiceToAgent = async (wavBlob: Blob): Promise<void> => {
  const userStore = useUserStore();
  userStore.hydrateFromSessionStorage();
  const token = userStore.token;

  appendMessage('assistant', '');
  isStreaming.value = true;
  const formData = new FormData();
  formData.append('audio', wavBlob, 'voice.wav');
  formData.append('return_tts', 'true');

  try {
    const res = await fetch(`${agentBaseUrl}/chat/voice`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData
    });
    const data = await res.json();
    if (data.code !== '00000' || !data.data) {
      const last = messages.value[messages.value.length - 1];
      if (last && last.role === 'assistant') last.content = `[语音] ${data.message || '请求失败'}`;
      else appendMessage('assistant', `[语音] ${data.message || '请求失败'}`);
      isStreaming.value = false;
      return;
    }
    const { question: recognized, answer, audio_base64 } = data.data;
    // 替换“正在生成”占位，改为用户消息 + 识别文字，再助手消息
    messages.value.pop();
    appendMessage('user', recognized || '(语音)');
    appendMessage('assistant', answer || '');
    if (audio_base64) {
      stopTtsPlayback();
      try {
        const audio = new Audio('data:audio/mpeg;base64,' + audio_base64);
        currentTtsAudio = audio;
        isTtsPlaying.value = true;
        audio.addEventListener('ended', () => {
          isTtsPlaying.value = false;
          currentTtsAudio = null;
        });
        audio.addEventListener('error', () => {
          isTtsPlaying.value = false;
          currentTtsAudio = null;
        });
        audio.play().catch(() => {
          isTtsPlaying.value = false;
          currentTtsAudio = null;
        });
      } catch (_) {
        isTtsPlaying.value = false;
        currentTtsAudio = null;
      }
    }
  } catch (err) {
    const last = messages.value[messages.value.length - 1];
    if (last && last.role === 'assistant') last.content = '[语音] 网络异常，请重试';
    else appendMessage('assistant', '[语音] 网络异常，请重试');
  } finally {
    isStreaming.value = false;
  }
};

const scrollToBottom = (): void => {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight;
    }
  });
};

const appendMessage = (role: MessageRole, content: string): void => {
  messages.value.push({ role, content });
  scrollToBottom();
};

const appendAssistantChunk = (chunk: string): void => {
  const last = messages.value[messages.value.length - 1];
  if (last && last.role === 'assistant') {
    last.content += chunk;
  } else {
    messages.value.push({ role: 'assistant', content: chunk });
  }
  scrollToBottom();
};

const renderMarkdown = (content: string): string => {
  const html = marked.parse(content, { breaks: true }) as string;
  return DOMPurify.sanitize(html);
};

const handleSseEvent = (rawEvent: string): void => {
  const dataLines = rawEvent
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.replace(/^data:\s?/, ''));
  if (!dataLines.length) return;

  const dataStr = dataLines.join('');
  try {
    const payload = JSON.parse(dataStr);
    const type = payload.type;
    if (type === 'chunk') {
      appendAssistantChunk(payload.content || '');
    } else if (type === 'error') {
      appendAssistantChunk(`\n[错误] ${payload.message || '未知错误'}`);
      isStreaming.value = false;
    }
  } catch (err) {
    appendAssistantChunk(`\n[解析失败] ${dataStr}`);
  }
};

const sendQuestion = async (): Promise<void> => {
  const q = question.value.trim();
  if (!q || isStreaming.value) return;

  const userStore = useUserStore();
  userStore.hydrateFromSessionStorage();
  const token = userStore.token;

  appendMessage('user', q);
  appendMessage('assistant', '');
  question.value = '';
  isStreaming.value = true;

  abortController = new AbortController();
  try {
    const response = await fetch(`${agentBaseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ question: q }),
      signal: abortController.signal
    });

    if (!response.ok || !response.body) {
      appendAssistantChunk(`\n[错误] 请求失败: ${response.status}`);
      isStreaming.value = false;
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        if (part.trim()) handleSseEvent(part);
      }
    }
  } catch (err: any) {
    if (err?.name !== 'AbortError') {
      appendAssistantChunk('\n[错误] 网络异常或服务不可用');
    }
  } finally {
    isStreaming.value = false;
    abortController = null;
  }
};

const stopStream = (): void => {
  if (abortController) {
    abortController.abort();
  }
  isStreaming.value = false;
};

onMounted(() => {
  nextTick(() => {
    const panel = document.querySelector('.chat-panel') as HTMLElement | null;
    const width = panel?.offsetWidth || 416;
    const height = panel?.offsetHeight || 288;
    position.value = {
      x: Math.max(16, window.innerWidth - width - 24),
      y: Math.max(16, window.innerHeight - height - 24)
    };
  });
  scrollToBottom();
});

const toggleExpand = (): void => {
  isExpanded.value = !isExpanded.value;
  nextTick(() => {
    const panel = document.querySelector('.chat-panel') as HTMLElement | null;
    const width = panel?.offsetWidth || 416;
    const height = panel?.offsetHeight || 288;
    position.value = {
      x: Math.min(position.value.x, Math.max(16, window.innerWidth - width - 16)),
      y: Math.min(position.value.y, Math.max(16, window.innerHeight - height - 16))
    };
  });
};

const onDragStart = (event: MouseEvent): void => {
  const panel = document.querySelector('.chat-panel') as HTMLElement | null;
  if (!panel) return;
  isDragging.value = true;
  dragOffset.value = {
    x: event.clientX - panel.getBoundingClientRect().left,
    y: event.clientY - panel.getBoundingClientRect().top
  };
  window.addEventListener('mousemove', onDragging);
  window.addEventListener('mouseup', onDragEnd);
};

const onDragging = (event: MouseEvent): void => {
  if (!isDragging.value) return;
  const panel = document.querySelector('.chat-panel') as HTMLElement | null;
  if (!panel) return;
  const width = panel.offsetWidth;
  const height = panel.offsetHeight;
  const nextX = event.clientX - dragOffset.value.x;
  const nextY = event.clientY - dragOffset.value.y;
  position.value = {
    x: Math.min(Math.max(0, nextX), window.innerWidth - width),
    y: Math.min(Math.max(0, nextY), window.innerHeight - height)
  };
};

const onDragEnd = (): void => {
  isDragging.value = false;
  window.removeEventListener('mousemove', onDragging);
  window.removeEventListener('mouseup', onDragEnd);
};
</script>

<style scoped>
.chat-panel {
  position: fixed;
  width: 26rem;
  height: 18rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  color: #fff;
  resize: both;
  overflow: hidden;
  min-width: 20rem;
  min-height: 14rem;
  max-width: 70vw;
  max-height: 80vh;
  /* 磨砂质感 */
  background: rgba(28, 32, 45, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24);
}

.chat-panel.expanded {
  width: 38rem;
  height: 70vh;
}

.chat-header {
  font-size: 1.25rem;
  text-align: left;
  margin: 0.5rem 0;
  cursor: move;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toggle-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
  font-size: 0.9rem;
  padding: 0.1rem 0.6rem;
  border-radius: 0.8rem;
  cursor: pointer;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.12);
}

.chat-messages {
  flex: 1;
  min-height: 8rem;
  overflow-y: auto;
  padding-right: 0.5rem;
  text-align: left;
  font-size: 0.95rem;
}

.chat-message {
  margin-bottom: 0.6rem;
}

.chat-role {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.2rem;
}

.chat-content {
  white-space: pre-wrap;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.chat-message.user .chat-content {
  color: #c6f6ff;
}

.chat-message.assistant .chat-content {
  color: #ffffff;
}

.chat-typing {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

.chat-input {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.send-btn,
.stop-btn {
  flex-shrink: 0;
}

.stop-tts-btn {
  flex-shrink: 0;
}

.voice-btn {
  flex-shrink: 0;
}

.recording-dot {
  color: #f56c6c;
  animation: blink 0.8s ease-in-out infinite;
}

@keyframes blink {
  50% { opacity: 0.4; }
}
</style>
