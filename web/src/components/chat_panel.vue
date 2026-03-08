<template>
  <div class="panel chat-panel" :class="{ expanded: isExpanded, inline: isInline }" :style="panelStyle">
    <div class="chat-header" @mousedown="onDragStart">
      <span>智能助手</span>
      <button v-if="!isInline" class="toggle-btn" type="button" @click.stop="toggleExpand">
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
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue';
import { useUserStore } from '@/stores/user';
import { agentBaseUrl } from '@/config/config';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface ChatPanelProps {
  layout?: 'floating' | 'inline';
}

const props = withDefaults(defineProps<ChatPanelProps>(), {
  layout: 'floating'
});

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
const isInline = computed(() => props.layout === 'inline');

const canSend = computed(() => question.value.trim().length > 0 && !isStreaming.value);
const panelStyle = computed(() => ({
  left: isInline.value ? 'auto' : `${position.value.x}px`,
  top: isInline.value ? 'auto' : `${position.value.y}px`
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
  if (!isInline.value) {
    nextTick(() => {
      const panel = document.querySelector('.chat-panel') as HTMLElement | null;
      const width = panel?.offsetWidth || 416;
      const height = panel?.offsetHeight || 288;
      position.value = {
        x: Math.max(16, window.innerWidth - width - 24),
        y: Math.max(16, window.innerHeight - height - 24)
      };
    });
  }
  nextTick(() => {
    if (isInline.value) {
      position.value = { x: 0, y: 0 };
    }
  });
  scrollToBottom();
});

const toggleExpand = (): void => {
  if (isInline.value) return;
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
  if (isInline.value) return;
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
  --panel-bg: linear-gradient(145deg, rgba(246, 251, 255, 0.94), rgba(231, 242, 252, 0.9));
  --panel-border: rgba(110, 140, 168, 0.28);
  --assistant-bubble: #ffffff;
  --user-bubble: #d8ecff;
  --text-main: #1f2a37;
  --text-muted: #60758d;
  --accent: #2f89d9;
  position: fixed;
  width: 26rem;
  height: 18rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  color: var(--text-main);
  resize: both;
  overflow: hidden;
  min-width: 20rem;
  min-height: 14rem;
  max-width: 70vw;
  max-height: 80vh;
  background: var(--panel-bg);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(24, 44, 70, 0.2);
  padding: 0.7rem 0.8rem;
}

.chat-panel.inline {
  position: relative;
  left: auto !important;
  top: auto !important;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 24rem;
  max-width: none;
  max-height: none;
  resize: none;
  box-shadow: 0 8px 20px rgba(18, 38, 62, 0.14);
  border-radius: 12px;
  padding: 0.65rem 0.7rem;
}

.chat-panel.inline .chat-messages {
  min-height: 0;
  overflow-y: auto;
}

.chat-panel.expanded {
  width: 42rem;
  height: 74vh;
  max-width: 86vw;
}

.chat-panel.inline.expanded {
  width: 100%;
  height: 100%;
  max-width: none;
}

.chat-header {
  font-size: 1rem;
  font-weight: 700;
  text-align: left;
  margin: 0 0 0.65rem;
  cursor: move;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.45rem 0.65rem;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.54);
  border: 1px solid rgba(138, 165, 190, 0.22);
}

.toggle-btn {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(108, 139, 166, 0.35);
  color: #2f4f6c;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.22rem 0.66rem;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #f5fbff;
  color: #1f435f;
  border-color: rgba(94, 132, 166, 0.55);
}

.chat-messages {
  flex: 1;
  min-height: 8rem;
  overflow-y: auto;
  padding: 0.65rem 0.6rem 0.3rem;
  text-align: left;
  font-size: 0.9rem;
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid rgba(125, 155, 180, 0.18);
  border-radius: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(115, 150, 179, 0.52) transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(115, 150, 179, 0.55);
  border-radius: 999px;
}

.chat-message {
  margin-bottom: 0.75rem;
}

.chat-role {
  font-size: 0.76rem;
  color: var(--text-muted);
  margin-bottom: 0.28rem;
}

.chat-content {
  white-space: pre-wrap;
  line-height: 1.5;
  overflow-wrap: anywhere;
  padding: 0.5rem 0.62rem;
  border-radius: 10px;
  border: 1px solid rgba(118, 149, 177, 0.2);
  box-shadow: 0 2px 10px rgba(68, 96, 124, 0.08);
}

.chat-message.user .chat-content {
  color: #0f395a;
  background: var(--user-bubble);
}

.chat-message.assistant .chat-content {
  color: #24384d;
  background: var(--assistant-bubble);
}

.chat-typing {
  font-size: 0.8rem;
  color: #5d7188;
  padding: 0.2rem 0.1rem;
}

.chat-input {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.7rem;
  align-items: center;
}

.send-btn,
.stop-btn {
  flex-shrink: 0;
  border-radius: 10px;
}

.stop-tts-btn {
  flex-shrink: 0;
}

.voice-btn {
  flex-shrink: 0;
  border-color: rgba(112, 144, 172, 0.35);
  background: rgba(255, 255, 255, 0.86);
}

.recording-dot {
  color: #f56c6c;
  animation: blink 0.8s ease-in-out infinite;
}

:deep(.chat-input .el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(112, 144, 172, 0.26) inset;
  background: rgba(255, 255, 255, 0.92);
}

:deep(.chat-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--accent) inset;
}

:deep(.chat-content p),
:deep(.chat-content ul),
:deep(.chat-content ol),
:deep(.chat-content pre) {
  margin: 0.15rem 0;
}

:deep(.chat-content code) {
  background: #eef5fb;
  padding: 0.08rem 0.28rem;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .chat-panel {
    min-width: 18rem;
    width: 90vw;
    max-width: 90vw;
    height: 52vh;
    min-height: 16rem;
  }

  .chat-panel.expanded {
    width: 92vw;
    height: 76vh;
  }

  .chat-panel.inline,
  .chat-panel.inline.expanded {
    width: 100%;
    max-width: 100%;
    min-height: 20rem;
    height: 100%;
  }
}

@keyframes blink {
  50% { opacity: 0.4; }
}
</style>
