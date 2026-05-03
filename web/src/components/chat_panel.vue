<template>
  <div class="chat-panel" :class="[layout, { 'realtime-active': isRealtimeConversationActive }]">
    <div v-if="layout !== 'stage'" class="chat-header">
      <div class="header-copy">
        <span class="chat-title">智能助手对话</span>
        <p class="chat-subtitle">
          {{ isRealtimeConversationActive ? '实时语音已开启，可直接说话' : '支持文字输入、单次语音和实时语音对话' }}
        </p>
      </div>
      <span class="state-pill" :class="{ active: isRealtimeConversationActive || isStreaming || isTtsPlaying }">
        {{ headerStateLabel }}
      </span>
    </div>

    <div v-if="quickReplies.length && layout !== 'stage'" class="quick-replies">
      <button
        v-for="reply in quickReplies"
        :key="reply"
        class="quick-reply"
        type="button"
        :disabled="isStreaming"
        @click="handleQuickReply(reply)"
      >
        {{ reply }}
      </button>
    </div>

    <div v-if="isRealtimeConversationActive" class="realtime-banner">
      <div class="realtime-copy">
        <strong>实时对话已开启</strong>
        <p>{{ realtimeBannerText }}</p>
      </div>
      <button class="banner-action" type="button" @click="stopRealtimeConversation">结束对话</button>
    </div>

    <div ref="messageBox" class="chat-messages">
      <div v-for="(msg, index) in messages" :key="index" class="chat-message" :class="[msg.role, { pending: msg.pending }]">
        <div class="chat-role">{{ msg.role === 'user' ? '我' : '助手' }}</div>
        <div v-if="msg.role === 'assistant'" class="chat-content" v-html="renderMarkdown(msg.content)"></div>
        <div v-else class="chat-content">{{ msg.content }}</div>
      </div>
      <div v-if="isStreaming" class="chat-typing">正在整理回复...</div>
    </div>

    <div class="chat-input">
      <div v-if="quickReplies.length && layout === 'stage'" class="quick-replies stage-shortcuts">
        <button
          v-for="reply in quickReplies"
          :key="reply"
          class="quick-reply"
          type="button"
          :disabled="isStreaming"
          @click="handleQuickReply(reply)"
        >
          {{ reply }}
        </button>
      </div>
      <el-input
        ref="messageInputRef"
        v-model="question"
        class="input-box"
        placeholder="请输入问题，回车发送"
        :disabled="isStreaming"
        @keyup.enter="handleEnterSend"
      />
      <el-tooltip content="单次语音提问" placement="top">
        <el-button
          :type="isRecording ? 'danger' : 'default'"
          circle
          class="voice-btn"
          :disabled="isStreaming"
          @click="toggleVoice"
        >
          <span v-if="!isRecording">语</span>
          <span v-else class="recording-dot">●</span>
        </el-button>
      </el-tooltip>
      <el-button class="realtime-btn" plain :type="isRealtimeConversationActive ? 'danger' : 'primary'" @click="toggleRealtimeConversation">
        {{ isRealtimeConversationActive ? '结束对话' : '开始对话' }}
      </el-button>
      <el-button type="primary" class="send-btn" :disabled="!canSend" @click="sendQuestion()">
        发送
      </el-button>
      <el-button v-if="isStreaming" type="danger" plain class="stop-btn" @click="stopStream">
        停止
      </el-button>
      <el-tooltip v-if="isTtsPlaying" content="停止语音播报" placement="top">
        <el-button type="warning" plain circle class="stop-tts-btn" @click="stopTtsPlayback(false)">
          停
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useUserStore } from '@/stores/user';
import { agentBaseUrl } from '@/config/config';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

type LayoutMode = 'floating' | 'inline' | 'stage';
type MessageRole = 'user' | 'assistant';
type VoiceInteractionState = 'idle' | 'listening' | 'speaking';

interface ChatPanelProps {
  layout?: LayoutMode;
  quickReplies?: string[];
}

interface ChatMessage {
  role: MessageRole;
  content: string;
  pending?: boolean;
}

interface SendQuestionOptions {
  autoSpeak?: boolean;
  fromRealtime?: boolean;
}

interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: null | (() => void);
  onresult: null | ((event: any) => void);
  onerror: null | ((event: any) => void);
  onend: null | (() => void);
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type RecognitionConstructor = new () => BrowserSpeechRecognition;

const props = withDefaults(defineProps<ChatPanelProps>(), {
  layout: 'floating',
  quickReplies: () => [],
});

const emit = defineEmits<{
  (e: 'streaming-change', value: boolean): void;
  (e: 'assistant-preview', text: string): void;
  (e: 'user-submit', text: string): void;
  (e: 'voice-state-change', state: VoiceInteractionState): void;
  (e: 'realtime-change', value: boolean): void;
}>();

const question = ref('');
const messages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '您好，我是智能助手，可帮您查询告警、环境和监控状态，支持文字与语音交互。',
  },
]);
const messageBox = ref<HTMLElement | null>(null);
const messageInputRef = ref<any>(null);
const isStreaming = ref(false);
const isRecording = ref(false);
const isTtsPlaying = ref(false);
const isRealtimeConversationActive = ref(false);
const isRealtimeListening = ref(false);
const realtimeTranscript = ref('');
const voiceState = ref<VoiceInteractionState>('idle');

let abortController: AbortController | null = null;
let currentTtsAudio: HTMLAudioElement | null = null;
let mediaStream: MediaStream | null = null;
let audioContext: AudioContext | null = null;
let processor: ScriptProcessorNode | null = null;
let source: MediaStreamAudioSourceNode | null = null;
let sampleRate = 16000;
let recordedChunks: Int16Array[] = [];
let realtimeRecognition: BrowserSpeechRecognition | null = null;
let realtimeRestartTimer: number | null = null;
let realtimeStopRequested = false;
let realtimeSubmitting = false;
let speechEndHandler: (() => void) | null = null;

const canSend = computed(() => Boolean(question.value.trim()) && !isStreaming.value);
const headerStateLabel = computed(() => {
  if (isRealtimeConversationActive.value) {
    if (isStreaming.value) return '处理中';
    if (isTtsPlaying.value) return '播报中';
    if (isRealtimeListening.value) return '倾听中';
    return '实时对话';
  }
  if (isStreaming.value) return '处理中';
  if (isRecording.value) return '录音中';
  if (isTtsPlaying.value) return '播报中';
  return '准备就绪';
});
const realtimeBannerText = computed(() => {
  if (isStreaming.value) {
    return '已收到您的语音问题，正在整理回答。';
  }
  if (isTtsPlaying.value) {
    return '正在为您播报结果，播报结束后会自动继续倾听。';
  }
  if (realtimeTranscript.value.trim()) {
    return `识别中：${realtimeTranscript.value.trim()}`;
  }
  return '请直接说话，我会在您停顿后自动回答。';
});

const getRecognitionConstructor = (): RecognitionConstructor | null => {
  if (typeof window === 'undefined') {
    return null;
  }
  const browserWindow = window as Window & {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  };
  return browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition || null;
};

const updateVoiceState = (state: VoiceInteractionState): void => {
  if (voiceState.value === state) {
    return;
  }
  voiceState.value = state;
  emit('voice-state-change', state);
};

const setStreaming = (value: boolean): void => {
  isStreaming.value = value;
  emit('streaming-change', value);
};

const scrollToBottom = (): void => {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight;
    }
  });
};

const appendMessage = (message: ChatMessage): ChatMessage => {
  messages.value.push(message);
  scrollToBottom();
  return message;
};

const focusInput = (): void => {
  nextTick(() => {
    messageInputRef.value?.focus?.();
  });
};

const renderMarkdown = (content: string): string => {
  const html = marked.parse(content || '', { breaks: true }) as string;
  return DOMPurify.sanitize(html);
};

const emitAssistantPreview = (text: string): void => {
  emit('assistant-preview', text);
  scrollToBottom();
};

const PUBLIC_AGENT_ERROR_MESSAGE = '抱歉，智能助手暂时不可用，请稍后重试。';
const PUBLIC_VOICE_ERROR_MESSAGE = '抱歉，语音服务暂时不可用，请稍后重试。';

const cleanupRecording = (): void => {
  if (processor) {
    processor.disconnect();
    processor.onaudioprocess = null;
    processor = null;
  }
  if (source) {
    source.disconnect();
    source = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  if (audioContext) {
    void audioContext.close();
    audioContext = null;
  }
};

const stopSpeechSynthesis = (): void => {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  speechEndHandler?.();
  speechEndHandler = null;
};

const scheduleRealtimeRestart = (delay = 420): void => {
  if (realtimeRestartTimer !== null) {
    window.clearTimeout(realtimeRestartTimer);
  }
  realtimeRestartTimer = window.setTimeout(() => {
    realtimeRestartTimer = null;
    if (!isRealtimeConversationActive.value || isRecording.value || isStreaming.value || isTtsPlaying.value || isRealtimeListening.value) {
      return;
    }
    try {
      realtimeStopRequested = false;
      realtimeRecognition?.start();
    } catch (error) {
      console.error('Failed to restart realtime recognition', error);
      scheduleRealtimeRestart(760);
    }
  }, delay);
};

const stopRealtimeRecognition = (manual = false): void => {
  realtimeStopRequested = manual;
  if (!realtimeRecognition) {
    isRealtimeListening.value = false;
    return;
  }
  try {
    realtimeRecognition.stop();
  } catch (error) {
    void error;
  }
  isRealtimeListening.value = false;
};

const stopTtsPlayback = (resumeRealtime: boolean): void => {
  if (currentTtsAudio) {
    currentTtsAudio.pause();
    currentTtsAudio.currentTime = 0;
    currentTtsAudio = null;
  }
  stopSpeechSynthesis();
  isTtsPlaying.value = false;
  if (voiceState.value === 'speaking') {
    updateVoiceState('idle');
  }
  if (resumeRealtime && isRealtimeConversationActive.value) {
    scheduleRealtimeRestart(240);
  }
};

const playBrowserSpeech = (text: string, resumeRealtime: boolean): Promise<void> =>
  new Promise((resolve) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      if (resumeRealtime && isRealtimeConversationActive.value) {
        scheduleRealtimeRestart(280);
      } else {
        updateVoiceState('idle');
      }
      resolve();
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = 1;
    utterance.pitch = 1;
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find((voice) => voice.lang.toLowerCase().includes('zh'));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    const finalize = () => {
      speechEndHandler = null;
      isTtsPlaying.value = false;
      updateVoiceState('idle');
      if (resumeRealtime && isRealtimeConversationActive.value) {
        scheduleRealtimeRestart(260);
      }
      resolve();
    };

    speechEndHandler = finalize;
    utterance.onend = finalize;
    utterance.onerror = finalize;
    updateVoiceState('speaking');
    isTtsPlaying.value = true;
    window.speechSynthesis.speak(utterance);
  });

const speakText = async (text: string, resumeRealtime: boolean): Promise<void> => {
  const cleanText = text.trim();
  if (!cleanText) {
    return;
  }

  stopTtsPlayback(false);

  try {
    const response = await fetch(`${agentBaseUrl}/tts/audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text: cleanText }),
    });
    const data = await response.json();
    const playUrl = data?.data?.play_url;
    if (!playUrl) {
      throw new Error('Missing TTS play url');
    }

    const audio = new Audio(playUrl);
    currentTtsAudio = audio;
    isTtsPlaying.value = true;
    updateVoiceState('speaking');

    await new Promise<void>((resolve, reject) => {
      audio.addEventListener(
        'ended',
        () => {
          resolve();
        },
        { once: true },
      );
      audio.addEventListener(
        'error',
        () => {
          reject(new Error('Audio playback failed'));
        },
        { once: true },
      );
      audio.play().catch(reject);
    });

    currentTtsAudio = null;
    isTtsPlaying.value = false;
    updateVoiceState('idle');
    if (resumeRealtime && isRealtimeConversationActive.value) {
      scheduleRealtimeRestart(260);
    }
  } catch (error) {
    console.error('Failed to play TTS audio, fallback to browser voice', error);
    currentTtsAudio = null;
    await playBrowserSpeech(cleanText, resumeRealtime);
  }
};

const handleSsePayload = (assistantMessage: ChatMessage, payload: any): void => {
  if (payload?.type === 'chunk') {
    const content = String(payload.content || '');
    if (content.startsWith('[REPLACE]')) {
      assistantMessage.content = content.replace(/^\[REPLACE\]/, '');
    } else {
      assistantMessage.content += content;
    }
    emitAssistantPreview(assistantMessage.content.trim());
    return;
  }

  if (payload?.type === 'error') {
    assistantMessage.content = assistantMessage.content || PUBLIC_AGENT_ERROR_MESSAGE;
    emitAssistantPreview(assistantMessage.content.trim());
  }
};

const sendQuestion = async (draftQuestion?: string, options: SendQuestionOptions = {}): Promise<void> => {
  const text = (typeof draftQuestion === 'string' ? draftQuestion : question.value).trim();
  if (!text || isStreaming.value) {
    return;
  }

  stopTtsPlayback(false);
  if (isRealtimeListening.value) {
    stopRealtimeRecognition(false);
  }

  const userStore = useUserStore();
  userStore.hydrateFromSessionStorage();
  const token = userStore.token;
  appendMessage({ role: 'user', content: text });
  emit('user-submit', text);
  question.value = '';
  const assistantMessage = appendMessage({ role: 'assistant', content: '' });
  setStreaming(true);

  abortController = new AbortController();
  try {
    const response = await fetch(`${agentBaseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ question: text }),
      signal: abortController.signal,
    });

    if (!response.ok || !response.body) {
      throw new Error(`请求失败：${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || '';
      for (const rawEvent of events) {
        const lines = rawEvent
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.replace(/^data:\s?/, ''));
        if (!lines.length) {
          continue;
        }
        handleSsePayload(assistantMessage, JSON.parse(lines.join('')));
      }
    }

    if (buffer.trim()) {
      const lines = buffer
        .split('\n')
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.replace(/^data:\s?/, ''));
      if (lines.length) {
        handleSsePayload(assistantMessage, JSON.parse(lines.join('')));
      }
    }

    if (!assistantMessage.content.trim()) {
      assistantMessage.content = '当前没有拿到有效回复，请稍后再试。';
      emitAssistantPreview(assistantMessage.content);
    }
  } catch (error: any) {
    if (error?.name !== 'AbortError') {
      assistantMessage.content = PUBLIC_AGENT_ERROR_MESSAGE;
      emitAssistantPreview(assistantMessage.content);
    }
  } finally {
    setStreaming(false);
    abortController = null;
  }

  if ((options.autoSpeak || isRealtimeConversationActive.value) && assistantMessage.content.trim()) {
    await speakText(assistantMessage.content, options.fromRealtime || isRealtimeConversationActive.value);
  }
};

const floatTo16BitPCM = (float32Array: Float32Array): Int16Array => {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, float32Array[i]));
    int16Array[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return int16Array;
};

const encodeWav = (samples: Int16Array, rate: number): Blob => {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeString = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i += 1) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  };
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i += 1) {
    view.setInt16(44 + i * 2, samples[i], true);
  }
  return new Blob([buffer], { type: 'audio/wav' });
};

const sendVoiceToAgent = async (wavBlob: Blob): Promise<void> => {
  stopTtsPlayback(false);
  updateVoiceState('idle');
  const userStore = useUserStore();
  userStore.hydrateFromSessionStorage();
  const token = userStore.token;
  const recognizedMessage = appendMessage({ role: 'user', content: '正在识别语音...', pending: true });
  setStreaming(true);

  const formData = new FormData();
  formData.append('audio', wavBlob, 'voice.wav');
  formData.append('return_tts', 'true');

  try {
    const response = await fetch(`${agentBaseUrl}/chat/voice`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const data = await response.json();
    if (data?.code !== '00000' || !data?.data) {
      throw new Error(data?.message || '语音请求失败');
    }

    const recognizedText = String(data.data.question || '(语音提问)');
    recognizedMessage.content = recognizedText;
    recognizedMessage.pending = false;
    emit('user-submit', recognizedText);

    const answer = String(data.data.answer || '');
    if (answer) {
      appendMessage({ role: 'assistant', content: answer });
      emitAssistantPreview(answer);
    }
    setStreaming(false);

    if (data.data.audio_base64) {
      stopTtsPlayback(false);
      currentTtsAudio = new Audio(`data:audio/mpeg;base64,${data.data.audio_base64}`);
      isTtsPlaying.value = true;
      updateVoiceState('speaking');
      await new Promise<void>((resolve) => {
        currentTtsAudio?.addEventListener('ended', resolve, { once: true });
        currentTtsAudio?.addEventListener('error', resolve, { once: true });
        currentTtsAudio?.play().catch(resolve);
      });
      currentTtsAudio = null;
      isTtsPlaying.value = false;
      updateVoiceState('idle');
    }
  } catch (error: any) {
    recognizedMessage.content = PUBLIC_VOICE_ERROR_MESSAGE;
    recognizedMessage.pending = false;
    appendMessage({ role: 'assistant', content: '抱歉，当前无法完成语音提问，请稍后重试或改用文字输入。' });
    emitAssistantPreview('抱歉，当前无法完成语音提问，请稍后重试或改用文字输入。');
    setStreaming(false);
  }
};

const startRecording = async (): Promise<void> => {
  if (isRealtimeConversationActive.value) {
    await stopRealtimeConversation();
  }

  const AudioContextCtor =
    window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextCtor || !navigator.mediaDevices?.getUserMedia) {
    appendMessage({ role: 'assistant', content: '当前浏览器不支持录音，请改用文字输入。' });
    emitAssistantPreview('当前浏览器不支持录音，请改用文字输入。');
    return;
  }

  try {
    recordedChunks = [];
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContextCtor({ sampleRate: 16000 });
    sampleRate = audioContext.sampleRate;
    source = audioContext.createMediaStreamSource(mediaStream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      recordedChunks.push(floatTo16BitPCM(inputData));
    };
    source.connect(processor);
    processor.connect(audioContext.destination);
    isRecording.value = true;
    updateVoiceState('listening');
  } catch (error) {
    console.error('Failed to start recording', error);
    cleanupRecording();
    appendMessage({ role: 'assistant', content: '无法访问麦克风，请检查浏览器权限设置。' });
    emitAssistantPreview('无法访问麦克风，请检查浏览器权限设置。');
    updateVoiceState('idle');
  }
};

const stopRecordingAndSend = async (): Promise<void> => {
  if (!isRecording.value) {
    return;
  }
  isRecording.value = false;
  cleanupRecording();

  const totalLength = recordedChunks.reduce((sum, chunk) => sum + chunk.length, 0);
  if (totalLength < 1200) {
    recordedChunks = [];
    appendMessage({ role: 'assistant', content: '录音时间太短了，请再说一次。' });
    emitAssistantPreview('录音时间太短了，请再说一次。');
    updateVoiceState('idle');
    return;
  }

  const merged = new Int16Array(totalLength);
  let offset = 0;
  for (const chunk of recordedChunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  recordedChunks = [];
  await sendVoiceToAgent(encodeWav(merged, sampleRate));
};

const toggleVoice = async (): Promise<void> => {
  if (isRecording.value) {
    await stopRecordingAndSend();
    return;
  }
  await startRecording();
};

const ensureRealtimeRecognition = (): boolean => {
  if (realtimeRecognition) {
    return true;
  }

  const RecognitionCtor = getRecognitionConstructor();
  if (!RecognitionCtor) {
    appendMessage({ role: 'assistant', content: '当前浏览器暂不支持实时语音对话，建议使用最新版 Chrome 或 Edge。' });
    emitAssistantPreview('当前浏览器暂不支持实时语音对话，建议使用最新版 Chrome 或 Edge。');
    return false;
  }

  realtimeRecognition = new RecognitionCtor();
  realtimeRecognition.lang = 'zh-CN';
  realtimeRecognition.continuous = true;
  realtimeRecognition.interimResults = true;
  realtimeRecognition.maxAlternatives = 1;

  realtimeRecognition.onstart = () => {
    realtimeStopRequested = false;
    isRealtimeListening.value = true;
    realtimeTranscript.value = '';
    updateVoiceState('listening');
  };

  realtimeRecognition.onresult = (event: any) => {
    let finalText = '';
    let interimText = '';
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      const transcript = String(result?.[0]?.transcript || '').trim();
      if (!transcript) {
        continue;
      }
      if (result.isFinal) {
        finalText += transcript;
      } else {
        interimText += transcript;
      }
    }

    realtimeTranscript.value = (finalText || interimText).trim();
    if (!finalText.trim() || realtimeSubmitting || isStreaming.value) {
      return;
    }

    realtimeSubmitting = true;
    stopRealtimeRecognition(false);
    void sendQuestion(finalText.trim(), { autoSpeak: true, fromRealtime: true }).finally(() => {
      realtimeSubmitting = false;
      realtimeTranscript.value = '';
      if (isRealtimeConversationActive.value && !isStreaming.value && !isTtsPlaying.value) {
        scheduleRealtimeRestart(340);
      }
    });
  };

  realtimeRecognition.onerror = (event: any) => {
    isRealtimeListening.value = false;
    if (!isRealtimeConversationActive.value) {
      return;
    }
    const errorType = String(event?.error || '');
    if (errorType === 'not-allowed' || errorType === 'service-not-allowed') {
      appendMessage({ role: 'assistant', content: '实时语音权限被拒绝，请允许浏览器使用麦克风后重试。' });
      emitAssistantPreview('实时语音权限被拒绝，请允许浏览器使用麦克风后重试。');
      void stopRealtimeConversation();
      return;
    }
    if (errorType === 'no-speech' || errorType === 'aborted') {
      scheduleRealtimeRestart(360);
      return;
    }
    console.error('Realtime speech recognition error', event);
    scheduleRealtimeRestart(760);
  };

  realtimeRecognition.onend = () => {
    isRealtimeListening.value = false;
    if (realtimeStopRequested) {
      realtimeStopRequested = false;
      if (!isTtsPlaying.value && !isStreaming.value) {
        updateVoiceState('idle');
      }
      return;
    }
    if (isRealtimeConversationActive.value && !isStreaming.value && !isTtsPlaying.value && !realtimeSubmitting) {
      scheduleRealtimeRestart(320);
      return;
    }
    if (!isTtsPlaying.value && !isStreaming.value) {
      updateVoiceState('idle');
    }
  };

  return true;
};

const startRealtimeConversation = async (): Promise<boolean> => {
  if (isRealtimeConversationActive.value) {
    return true;
  }
  if (isRecording.value) {
    await stopRecordingAndSend();
  }
  stopTtsPlayback(false);
  if (!ensureRealtimeRecognition()) {
    return false;
  }
  isRealtimeConversationActive.value = true;
  emit('realtime-change', true);
  question.value = '';
  focusInput();
  scheduleRealtimeRestart(80);
  return true;
};

const stopRealtimeConversation = async (): Promise<boolean> => {
  if (!isRealtimeConversationActive.value) {
    stopTtsPlayback(false);
    return false;
  }
  isRealtimeConversationActive.value = false;
  emit('realtime-change', false);
  realtimeTranscript.value = '';
  if (realtimeRestartTimer !== null) {
    window.clearTimeout(realtimeRestartTimer);
    realtimeRestartTimer = null;
  }
  stopRealtimeRecognition(true);
  stopTtsPlayback(false);
  if (!isStreaming.value && !isRecording.value) {
    updateVoiceState('idle');
  }
  return false;
};

const toggleRealtimeConversation = async (): Promise<boolean> => {
  if (isRealtimeConversationActive.value) {
    await stopRealtimeConversation();
    return false;
  }
  return startRealtimeConversation();
};

const handleQuickReply = async (reply: string): Promise<void> => {
  await sendQuestion(reply, { autoSpeak: isRealtimeConversationActive.value });
};

const prepareQuestion = async (draftQuestion = ''): Promise<void> => {
  question.value = draftQuestion;
  focusInput();
};

const sendPresetQuestion = async (presetQuestion: string): Promise<void> => {
  await sendQuestion(presetQuestion, { autoSpeak: isRealtimeConversationActive.value });
};

const stopStream = (): void => {
  abortController?.abort();
  abortController = null;
  setStreaming(false);
  if (!isTtsPlaying.value && !isRecording.value && !isRealtimeListening.value) {
    updateVoiceState('idle');
  }
};

const handleEnterSend = async (): Promise<void> => {
  await sendQuestion(undefined, { autoSpeak: isRealtimeConversationActive.value });
};

defineExpose({
  focusInput,
  sendPresetQuestion,
  prepareQuestion,
  startRealtimeConversation,
  stopRealtimeConversation,
  toggleRealtimeConversation,
});

onMounted(() => {
  scrollToBottom();
});

onBeforeUnmount(() => {
  stopStream();
  if (isRecording.value) {
    cleanupRecording();
  }
  if (realtimeRestartTimer !== null) {
    window.clearTimeout(realtimeRestartTimer);
  }
  stopRealtimeRecognition(true);
  stopTtsPlayback(false);
});
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  color: #22384d;
}

.chat-header,
.quick-replies,
.realtime-banner,
.chat-input {
  flex-shrink: 0;
}

.chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.header-copy {
  min-width: 0;
}

.chat-title {
  display: block;
  font-size: 1.08rem;
  font-weight: 700;
  color: #21384d;
}

.chat-subtitle {
  margin: 0.18rem 0 0;
  font-size: 0.82rem;
  color: #6d8094;
  line-height: 1.45;
}

.state-pill {
  padding: 0.34rem 0.72rem;
  border-radius: 999px;
  border: 1px solid rgba(117, 149, 177, 0.22);
  background: rgba(255, 255, 255, 0.82);
  color: #4f6882;
  font-size: 0.76rem;
  white-space: nowrap;
}

.state-pill.active {
  border-color: rgba(70, 145, 224, 0.34);
  color: #1e6db7;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.quick-reply,
.banner-action {
  border: 1px solid rgba(117, 149, 177, 0.2);
  background: rgba(255, 255, 255, 0.82);
  color: #214c74;
  border-radius: 999px;
  padding: 0.38rem 0.82rem;
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-reply:hover,
.banner-action:hover {
  background: #eef6ff;
  border-color: rgba(70, 145, 224, 0.36);
}

.realtime-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.72rem 0.85rem;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(224, 245, 255, 0.9), rgba(243, 251, 255, 0.92));
  border: 1px solid rgba(126, 197, 255, 0.22);
}

.realtime-copy strong {
  display: block;
  font-size: 0.88rem;
  color: #17456e;
}

.realtime-copy p {
  margin: 0.2rem 0 0;
  font-size: 0.78rem;
  color: #5a7490;
  line-height: 1.55;
}

.chat-messages {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0.25rem 0.3rem 0.1rem 0.1rem;
  overscroll-behavior: contain;
}

.chat-message {
  margin-bottom: 0.75rem;
  min-width: 0;
}

.chat-role {
  margin-bottom: 0.24rem;
  font-size: 0.76rem;
  color: #72869a;
}

.chat-content {
  padding: 0.72rem 0.82rem;
  border-radius: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  overflow-x: auto;
  max-width: 100%;
  border: 1px solid rgba(120, 151, 178, 0.14);
  box-shadow: 0 5px 18px rgba(56, 84, 112, 0.08);
}

.chat-message.assistant .chat-content {
  background: rgba(255, 255, 255, 0.96);
  color: #22384d;
}

.chat-message.user .chat-content {
  background: rgba(216, 237, 255, 0.94);
  color: #133d61;
}

.chat-message.pending .chat-content {
  opacity: 0.78;
}

.chat-typing {
  font-size: 0.8rem;
  color: #657b91;
  padding: 0.3rem 0.1rem;
}

.chat-input {
  display: flex;
  align-items: center;
  gap: 0.48rem;
}

.input-box {
  min-width: 0;
  flex: 1;
}

.realtime-btn,
.send-btn,
.stop-btn,
.voice-btn,
.stop-tts-btn {
  flex-shrink: 0;
  border-radius: 12px;
}

.recording-dot {
  color: #f56c6c;
  animation: blink 0.9s ease-in-out infinite;
}

:deep(.input-box .el-input__wrapper) {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 0 0 1px rgba(112, 144, 172, 0.2) inset;
}

:deep(.input-box .el-input__inner) {
  color: #111827;
}

:deep(.chat-content p),
:deep(.chat-content ul),
:deep(.chat-content ol),
:deep(.chat-content pre) {
  margin: 0.15rem 0;
}

:deep(.chat-content pre),
:deep(.chat-content table) {
  max-width: 100%;
  overflow: auto;
}

:deep(.chat-content table) {
  display: block;
  border-collapse: collapse;
}

:deep(.chat-content code) {
  background: rgba(233, 242, 250, 0.95);
  padding: 0.08rem 0.28rem;
  border-radius: 4px;
}

.chat-panel.stage {
  position: absolute;
  inset: 0;
  z-index: 18;
  pointer-events: none;
  color: #e8f5ff;
}

.chat-panel.stage .quick-replies,
.chat-panel.stage .realtime-banner,
.chat-panel.stage .chat-messages,
.chat-panel.stage .chat-input,
.chat-panel.stage .chat-typing {
  pointer-events: auto;
}

.chat-panel.stage .quick-reply,
.chat-panel.stage .banner-action {
  background:
    linear-gradient(180deg, rgba(18, 53, 86, 0.92), rgba(9, 28, 47, 0.82));
  border-color: rgba(126, 197, 255, 0.26);
  color: #dff1ff;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.03),
    0 10px 26px rgba(4, 12, 24, 0.2);
}

.chat-panel.stage .quick-reply:hover,
.chat-panel.stage .banner-action:hover {
  background: rgba(16, 44, 72, 0.92);
  border-color: rgba(126, 197, 255, 0.34);
}

.chat-panel.stage .realtime-banner {
  position: absolute;
  right: 1.35rem;
  bottom: 11.55rem;
  width: min(20.5rem, 34vw);
  padding: 0.9rem 0.88rem 0.82rem;
  border-radius: 18px;
  background:
    radial-gradient(circle at 0% 0%, rgba(126, 197, 255, 0.14), transparent 32%),
    linear-gradient(135deg, rgba(12, 39, 62, 0.94), rgba(10, 30, 49, 0.88));
  border: 1px solid rgba(126, 197, 255, 0.2);
  box-shadow: 0 16px 32px rgba(4, 12, 24, 0.22);
  overflow: hidden;
}

.chat-panel.stage .realtime-copy strong {
  color: #e8f5ff;
  font-size: 0.84rem;
}

.chat-panel.stage .realtime-copy p {
  color: rgba(214, 236, 255, 0.82);
  font-size: 0.74rem;
  line-height: 1.5;
}

.chat-panel.stage .chat-messages {
  position: absolute;
  left: 1.35rem;
  top: 4.85rem;
  bottom: 1.35rem;
  width: min(21.5rem, calc(100% - 25.5rem));
  padding: 0.72rem 0.42rem 0.18rem 0.22rem;
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(9, 28, 47, 0.8), rgba(6, 18, 33, 0.58));
  border: 1px solid rgba(126, 197, 255, 0.18);
  box-shadow:
    0 18px 38px rgba(2, 10, 19, 0.24),
    inset 0 0 0 1px rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(18px);
  scrollbar-color: rgba(126, 197, 255, 0.42) transparent;
}

.chat-panel.stage .chat-role {
  color: rgba(192, 222, 246, 0.72);
  font-size: 0.64rem;
  margin-bottom: 0.12rem;
}

.chat-panel.stage .chat-content {
  padding: 0.54rem 0.7rem;
  border-radius: 16px;
  border-color: rgba(126, 197, 255, 0.14);
  box-shadow: 0 8px 22px rgba(4, 12, 24, 0.18);
  font-size: 0.76rem;
  line-height: 1.46;
}

.chat-panel.stage :deep(.chat-content p),
.chat-panel.stage :deep(.chat-content ul),
.chat-panel.stage :deep(.chat-content ol),
.chat-panel.stage :deep(.chat-content pre),
.chat-panel.stage :deep(.chat-content blockquote) {
  margin: 0.06rem 0;
}

.chat-panel.stage :deep(.chat-content ul),
.chat-panel.stage :deep(.chat-content ol) {
  padding-left: 1rem;
}

.chat-panel.stage :deep(.chat-content li) {
  margin: 0.04rem 0;
}

.chat-panel.stage :deep(.chat-content li p) {
  margin: 0;
}

.chat-panel.stage .chat-message.assistant .chat-content {
  background: linear-gradient(180deg, rgba(10, 30, 52, 0.92), rgba(7, 22, 39, 0.82));
  color: #eff7ff;
  border-color: rgba(151, 223, 255, 0.16);
  box-shadow:
    0 18px 34px rgba(2, 11, 24, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.03);
}

.chat-panel.stage .chat-message.user .chat-content {
  background: linear-gradient(180deg, rgba(226, 241, 255, 0.96), rgba(194, 224, 248, 0.94));
  color: #153e61;
  border-color: rgba(177, 214, 242, 0.48);
}

.chat-panel.stage .chat-typing {
  color: rgba(214, 236, 255, 0.82);
}

.chat-panel.stage .chat-input {
  position: absolute;
  right: 1.35rem;
  bottom: 1.35rem;
  width: min(20.5rem, 34vw);
  padding: 0.92rem 0.82rem 0.78rem;
  flex-wrap: wrap;
  align-items: center;
  border-radius: 24px;
  background:
    radial-gradient(circle at 100% 0%, rgba(126, 197, 255, 0.14), transparent 28%),
    linear-gradient(180deg, rgba(11, 33, 55, 0.92), rgba(8, 22, 39, 0.82));
  border: 1px solid rgba(126, 197, 255, 0.18);
  box-shadow:
    0 18px 38px rgba(2, 10, 19, 0.24),
    inset 0 0 0 1px rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(18px);
  gap: 0.38rem;
  overflow: hidden;
}

.chat-panel.stage .stage-shortcuts {
  width: 100%;
  margin-bottom: 0.02rem;
  gap: 0.34rem;
}

.chat-panel.stage .stage-shortcuts .quick-reply {
  white-space: nowrap;
  padding: 0.22rem 0.52rem;
  font-size: 0.7rem;
  border-radius: 999px;
}

.chat-panel.stage .input-box {
  flex: 1 1 100%;
}

.chat-panel.stage .realtime-btn {
  flex: 1 1 8rem;
  font-size: 0.76rem;
}

.chat-panel.stage .send-btn {
  flex: 0 0 auto;
  font-size: 0.76rem;
}

.chat-panel.stage .voice-btn,
.chat-panel.stage .stop-btn,
.chat-panel.stage .stop-tts-btn {
  flex: 0 0 auto;
}

.chat-panel.stage :deep(.input-box .el-input__wrapper) {
  background: rgba(246, 250, 255, 0.94);
  padding: 0 0.72rem;
  min-height: 2.45rem;
}

.chat-panel.stage :deep(.input-box .el-input__inner) {
  color: #111827;
  font-size: 0.84rem;
}

@media (max-width: 1280px) {
  .realtime-banner {
    flex-wrap: wrap;
  }

  .chat-input {
    flex-wrap: wrap;
  }

  .input-box {
    flex-basis: 100%;
  }

  .chat-panel.stage .chat-messages,
  .chat-panel.stage .chat-input,
  .chat-panel.stage .realtime-banner {
    width: min(18rem, calc(100% - 2rem));
  }

  .chat-panel.stage .chat-messages {
    top: 4.6rem;
  }
}

@media (max-width: 900px) {
  .chat-panel.stage .quick-replies,
  .chat-panel.stage .realtime-banner,
  .chat-panel.stage .chat-input {
    right: 1rem;
  }

  .chat-panel.stage .chat-messages {
    left: 1rem;
    top: auto;
    width: calc(100% - 2rem);
    max-height: 9.8rem;
  }

  .chat-panel.stage .chat-input {
    width: calc(100% - 2rem);
  }

  .chat-panel.stage .realtime-banner {
    bottom: 11.8rem;
    width: calc(100% - 2rem);
  }
}

@media (max-width: 760px) {
  .chat-panel.stage .chat-messages {
    top: auto;
    bottom: 9.15rem;
    max-height: 7.8rem;
  }

  .chat-panel.stage .realtime-banner {
    bottom: 19.8rem;
  }
}

@keyframes blink {
  50% {
    opacity: 0.35;
  }
}
</style>
