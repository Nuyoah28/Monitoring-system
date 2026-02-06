<template>
  <div class="panel chat-panel" :style="panelStyle">
    <div class="chat-header" @mousedown="onDragStart">智能助手</div>
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
      <el-button type="primary" class="send-btn" :disabled="!canSend" @click="sendQuestion">
        发送
      </el-button>
      <el-button v-if="isStreaming" type="danger" plain class="stop-btn" @click="stopStream">
        停止
      </el-button>
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
const isDragging = ref<boolean>(false);
const dragOffset = ref<{ x: number; y: number }>({ x: 0, y: 0 });

const canSend = computed(() => question.value.trim().length > 0 && !isStreaming.value);
const panelStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`
}));

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
}

.chat-header {
  font-size: 1.25rem;
  text-align: left;
  margin: 0.5rem 0;
  cursor: move;
  user-select: none;
}

.chat-messages {
  flex: 1;
  min-height: 8rem;
  max-height: 11rem;
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
</style>
