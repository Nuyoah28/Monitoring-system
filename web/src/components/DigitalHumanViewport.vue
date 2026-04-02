<template>
  <div
    class="digital-human-viewport"
    :class="[`mode-${renderMode}`, `state-${status}`, { loading: isInitializing }]"
    @click="handleViewportTap"
  >
    <div
      v-if="renderMode === 'live2d'"
      ref="live2dHost"
      class="render-layer live2d-host"
      @pointermove="handlePointerMove"
      @pointerleave="resetPointerFocus"
    ></div>

    <div v-if="renderMode === 'video'" class="render-layer video-host">
      <video
        ref="videoEl"
        class="digital-human-video"
        :poster="videoPoster || undefined"
        autoplay
        muted
        loop
        playsinline
        preload="auto"
        @canplay="handleVideoReady"
        @loadeddata="handleVideoReady"
        @error="handleVideoError"
      ></video>
    </div>

    <div v-if="showFallback" class="render-layer fallback-host">
      <slot name="fallback"></slot>
    </div>

    <div v-if="isInitializing" class="runtime-banner">助手加载中</div>
    <div v-else-if="runtimeNotice" class="runtime-banner muted">{{ runtimeNotice }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue';
import { agentBaseUrl } from '@/config/config';
import { digitalHumanConfig, type DigitalHumanMode } from '@/config/digitalHuman';

type AgentStageStatus = 'idle' | 'listening' | 'thinking' | 'speaking';

interface Props {
  status?: AgentStageStatus;
}

interface ExtendedWindow extends Window {
  PIXI?: unknown;
  Live2DCubismCore?: unknown;
  Live2D?: unknown;
}

const props = withDefaults(defineProps<Props>(), {
  status: 'idle',
});

const emit = defineEmits<{
  (e: 'avatar-tap', text: string): void;
}>();

const TAP_GREETING = '有什么能帮助您的？';
const externalScriptCache = new Map<string, Promise<void>>();

const live2dHost = ref<HTMLElement | null>(null);
const videoEl = ref<HTMLVideoElement | null>(null);
const renderMode = ref<DigitalHumanMode>(digitalHumanConfig.mode);
const isInitializing = ref(digitalHumanConfig.mode !== 'mascot');
const runtimeNotice = ref('');
const videoPoster = computed(() => digitalHumanConfig.video?.poster || '');
const activeVideoSrc = computed(() => {
  const video = digitalHumanConfig.video;
  if (!video) {
    return '';
  }
  if (props.status === 'speaking') {
    return video.speakingSrc || video.idleSrc;
  }
  if (props.status === 'listening') {
    return video.listeningSrc || video.idleSrc;
  }
  return video.idleSrc;
});
const showFallback = computed(() => renderMode.value === 'mascot');

const pixiApp = shallowRef<any>(null);
const live2dModel = shallowRef<any>(null);

let lipSyncFrame = 0;
let resizeObserver: ResizeObserver | null = null;
let lastMotionKey = '';
let greetingAudio: HTMLAudioElement | null = null;

const handleWindowResize = (): void => {
  if (renderMode.value === 'live2d') {
    syncLive2DLayout();
  }
};

const stopGreetingAudio = (): void => {
  if (greetingAudio) {
    greetingAudio.pause();
    greetingAudio.currentTime = 0;
    greetingAudio = null;
  }
};

const playGreetingWithBrowserVoice = (text: string): void => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
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

  window.speechSynthesis.speak(utterance);
};

const playGreeting = async (text: string): Promise<void> => {
  stopGreetingAudio();
  try {
    const response = await fetch(`${agentBaseUrl}/tts?text=${encodeURIComponent(text)}`);
    const data = await response.json();
    const audioBase64 = data?.data?.audio_base64;
    if (!audioBase64) {
      throw new Error('Missing greeting audio');
    }

    const audio = new Audio(`data:audio/mpeg;base64,${audioBase64}`);
    greetingAudio = audio;
    audio.addEventListener('ended', () => {
      greetingAudio = null;
    });
    audio.addEventListener('error', () => {
      greetingAudio = null;
    });
    await audio.play();
  } catch (error) {
    console.error('Failed to play greeting audio', error);
    playGreetingWithBrowserVoice(text);
  }
};

const loadExternalScript = (src: string, validator: () => boolean): Promise<void> => {
  if (!src) {
    return Promise.reject(new Error('Missing digital human runtime script.'));
  }
  if (validator()) {
    return Promise.resolve();
  }

  const cached = externalScriptCache.get(src);
  if (cached) {
    return cached;
  }

  const promise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector(`script[data-digital-human-script="${src}"]`) as HTMLScriptElement | null;
    const finish = () => {
      if (validator()) {
        resolve();
      } else {
        reject(new Error('Digital human runtime did not expose the expected global object.'));
      }
    };

    if (existing) {
      if (existing.dataset.loaded === 'true') {
        finish();
        return;
      }
      existing.addEventListener('load', finish, { once: true });
      existing.addEventListener('error', () => reject(new Error(`Failed to load runtime script: ${src}`)), {
        once: true,
      });
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.dataset.digitalHumanScript = src;
    script.onload = () => {
      script.dataset.loaded = 'true';
      finish();
    };
    script.onerror = () => reject(new Error(`Failed to load runtime script: ${src}`));
    document.head.appendChild(script);
  });

  externalScriptCache.set(src, promise);
  return promise;
};

const stopLipSyncLoop = (): void => {
  if (lipSyncFrame) {
    window.cancelAnimationFrame(lipSyncFrame);
    lipSyncFrame = 0;
  }
};

const destroyLive2D = (): void => {
  stopLipSyncLoop();
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (pixiApp.value) {
    pixiApp.value.destroy(true, {
      children: true,
      texture: true,
      baseTexture: true,
    });
    pixiApp.value = null;
  }
  if (live2dHost.value) {
    live2dHost.value.innerHTML = '';
  }
  live2dModel.value = null;
  lastMotionKey = '';
};

const syncLive2DLayout = (): void => {
  if (!live2dHost.value || !pixiApp.value || !live2dModel.value) {
    return;
  }

  const { width, height } = live2dHost.value.getBoundingClientRect();
  const safeWidth = Math.max(width, 1);
  const safeHeight = Math.max(height, 1);

  pixiApp.value.renderer.resize(safeWidth, safeHeight);

  const modelBounds = live2dModel.value.getLocalBounds?.() || {
    x: 0,
    y: 0,
    width: safeWidth,
    height: safeHeight,
  };
  const modelWidth = Math.max(modelBounds.width || 0, 1);
  const modelHeight = Math.max(modelBounds.height || 0, 1);
  const fitScale = Math.min(safeWidth / modelWidth, safeHeight / modelHeight);
  const config = digitalHumanConfig.live2d;
  const scale = fitScale * (config?.fitScale || 0.82);

  if (live2dModel.value.anchor?.set) {
    live2dModel.value.anchor.set(0.5, 1);
  } else if (live2dModel.value.pivot?.set) {
    live2dModel.value.pivot.set(modelBounds.x + modelWidth / 2, modelBounds.y + modelHeight);
  }

  live2dModel.value.scale.set(scale);
  live2dModel.value.position.set(
    safeWidth * (0.5 + (config?.positionX || 0)),
    safeHeight * (0.98 + (config?.positionY || 0)),
  );
};

const startLipSyncLoop = (): void => {
  stopLipSyncLoop();

  const tick = () => {
    const coreModel = live2dModel.value?.internalModel?.coreModel;
    if (coreModel?.setParameterValueById) {
      const time = window.performance.now();
      let mouthOpen = 0;

      if (props.status === 'speaking') {
        mouthOpen = 0.18 + ((Math.sin(time / 84) + 1) / 2) * 0.68;
      } else if (props.status === 'listening') {
        mouthOpen = 0.04 + ((Math.sin(time / 180) + 1) / 2) * 0.1;
      }

      try {
        coreModel.setParameterValueById('ParamMouthOpenY', mouthOpen);
        coreModel.setParameterValueById('PARAM_MOUTH_OPEN_Y', mouthOpen);
      } catch (error) {
        void error;
      }
    }

    lipSyncFrame = window.requestAnimationFrame(tick);
  };

  lipSyncFrame = window.requestAnimationFrame(tick);
};

const playLive2DMotion = async (group?: string): Promise<void> => {
  const model = live2dModel.value;
  if (!model || !group) {
    return;
  }
  try {
    await model.motion(group);
  } catch (error) {
    void error;
  }
};

const playLive2DMotionForStatus = async (status: AgentStageStatus): Promise<void> => {
  const config = digitalHumanConfig.live2d;
  if (!config) {
    return;
  }

  let group = config.idleMotionGroup;
  if (status === 'listening') {
    group = config.listeningMotionGroup || config.idleMotionGroup;
  } else if (status === 'speaking') {
    group = config.speakingMotionGroup || config.idleMotionGroup;
  }

  const motionKey = `${status}:${group || 'none'}`;
  if (motionKey === lastMotionKey) {
    return;
  }
  lastMotionKey = motionKey;
  await playLive2DMotion(group);
};

const initLive2D = async (): Promise<void> => {
  const config = digitalHumanConfig.live2d;
  if (!config || !live2dHost.value) {
    renderMode.value = 'mascot';
    isInitializing.value = false;
    runtimeNotice.value = '已切换为内置助手形象';
    return;
  }

  try {
    const PIXI = await import('pixi.js');
    (window as ExtendedWindow).PIXI = PIXI;

    await loadExternalScript(config.runtimeScriptUrl, () => {
      const browserWindow = window as ExtendedWindow;
      return config.cubismVersion === 4 ? Boolean(browserWindow.Live2DCubismCore) : Boolean(browserWindow.Live2D);
    });

    const live2dModule =
      config.cubismVersion === 2
        ? await import('pixi-live2d-display/cubism2')
        : await import('pixi-live2d-display/cubism4');

    const { width, height } = live2dHost.value.getBoundingClientRect();
    const app = new PIXI.Application({
      width: Math.max(width, 1),
      height: Math.max(height, 1),
      antialias: true,
      transparent: true,
      autoDensity: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
    });

    live2dHost.value.innerHTML = '';
    live2dHost.value.appendChild(app.view as HTMLCanvasElement);

    const canvas = live2dHost.value.querySelector('canvas');
    if (canvas) {
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      canvas.style.display = 'block';
    }

    const model = await live2dModule.Live2DModel.from(config.modelUrl);
    app.stage.addChild(model);
    model.interactive = true;
    model.buttonMode = true;

    pixiApp.value = app;
    live2dModel.value = model;
    renderMode.value = 'live2d';
    runtimeNotice.value = '';

    syncLive2DLayout();
    window.requestAnimationFrame(() => {
      syncLive2DLayout();
    });
    startLipSyncLoop();
    await playLive2DMotionForStatus(props.status);

    if ('ResizeObserver' in window) {
      resizeObserver = new ResizeObserver(() => syncLive2DLayout());
      resizeObserver.observe(live2dHost.value);
    }
  } catch (error) {
    destroyLive2D();
    renderMode.value = 'mascot';
    runtimeNotice.value = '助手形象加载失败，已切换为内置形象';
    console.error('Failed to initialize Live2D digital human', error);
  } finally {
    isInitializing.value = false;
  }
};

const syncVideoSource = async (): Promise<void> => {
  const video = videoEl.value;
  if (!video) {
    return;
  }

  const nextSrc = activeVideoSrc.value;
  if (!nextSrc) {
    renderMode.value = 'mascot';
    runtimeNotice.value = '已切换为内置助手形象';
    isInitializing.value = false;
    return;
  }

  if (video.dataset.activeSrc !== nextSrc) {
    video.dataset.activeSrc = nextSrc;
    video.src = nextSrc;
    video.load();
  }

  try {
    await video.play();
  } catch (error) {
    console.error('Failed to autoplay digital human video', error);
  }
};

const handleVideoReady = (): void => {
  isInitializing.value = false;
  runtimeNotice.value = '';
};

const handleVideoError = (): void => {
  renderMode.value = 'mascot';
  isInitializing.value = false;
  runtimeNotice.value = '助手形象加载失败，已切换为内置形象';
};

const handlePointerMove = (event: PointerEvent): void => {
  if (!live2dHost.value || !live2dModel.value || renderMode.value !== 'live2d') {
    return;
  }
  const rect = live2dHost.value.getBoundingClientRect();
  try {
    live2dModel.value.focus(event.clientX - rect.left, event.clientY - rect.top, false);
  } catch (error) {
    void error;
  }
};

const resetPointerFocus = (): void => {
  if (!live2dHost.value || !live2dModel.value || renderMode.value !== 'live2d') {
    return;
  }
  const rect = live2dHost.value.getBoundingClientRect();
  try {
    live2dModel.value.focus(rect.width / 2, rect.height / 2, true);
  } catch (error) {
    void error;
  }
};

const handleViewportTap = async (): Promise<void> => {
  emit('avatar-tap', TAP_GREETING);
  void playGreeting(TAP_GREETING);

  if (renderMode.value !== 'live2d' || !live2dModel.value) {
    return;
  }

  const config = digitalHumanConfig.live2d;
  await playLive2DMotion(config?.tapMotionGroup || config?.listeningMotionGroup || config?.idleMotionGroup);
};

const initViewport = async (): Promise<void> => {
  destroyLive2D();
  runtimeNotice.value = '';

  if (digitalHumanConfig.mode === 'live2d') {
    renderMode.value = 'live2d';
    isInitializing.value = true;
    await nextTick();
    await initLive2D();
    return;
  }

  if (digitalHumanConfig.mode === 'video') {
    renderMode.value = 'video';
    isInitializing.value = true;
    await nextTick();
    await syncVideoSource();
    return;
  }

  renderMode.value = 'mascot';
  isInitializing.value = false;
};

watch(
  () => props.status,
  (status) => {
    if (renderMode.value === 'live2d' && live2dModel.value) {
      void playLive2DMotionForStatus(status);
    }
    if (renderMode.value === 'video' && videoEl.value) {
      void syncVideoSource();
    }
  },
);

onMounted(() => {
  window.addEventListener('resize', handleWindowResize);
  void initViewport();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleWindowResize);
  destroyLive2D();
  stopGreetingAudio();
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
});
</script>

<style scoped>
.digital-human-viewport {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: auto;
}

.digital-human-viewport::before {
  content: '';
  position: absolute;
  inset: 12% 16% 6%;
  z-index: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(126, 197, 255, 0.18), transparent 68%);
  filter: blur(24px);
  pointer-events: none;
}

.render-layer {
  position: absolute;
  inset: 0;
}

.live2d-host,
.video-host,
.fallback-host {
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.live2d-host {
  z-index: 3;
}

.video-host {
  z-index: 2;
}

.fallback-host {
  z-index: 1;
}

.digital-human-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  filter: saturate(1.04) contrast(1.04);
}

.mode-live2d .live2d-host :deep(canvas),
.mode-video .digital-human-video {
  transition:
    transform 0.35s ease,
    filter 0.35s ease,
    opacity 0.35s ease;
}

.state-idle.mode-live2d .live2d-host :deep(canvas),
.state-idle.mode-video .digital-human-video {
  filter: drop-shadow(0 10px 24px rgba(79, 162, 255, 0.16));
}

.state-listening.mode-live2d .live2d-host :deep(canvas),
.state-listening.mode-video .digital-human-video {
  filter:
    drop-shadow(0 12px 28px rgba(248, 203, 113, 0.24))
    saturate(1.06);
}

.state-speaking.mode-live2d .live2d-host :deep(canvas),
.state-speaking.mode-video .digital-human-video {
  transform: scale(1.018);
  filter:
    drop-shadow(0 12px 34px rgba(83, 213, 165, 0.26))
    saturate(1.08)
    contrast(1.06);
}

.runtime-banner {
  position: absolute;
  left: 1rem;
  right: 1rem;
  bottom: 1rem;
  z-index: 6;
  padding: 0.6rem 0.8rem;
  border-radius: 999px;
  background: rgba(8, 26, 45, 0.84);
  border: 1px solid rgba(126, 197, 255, 0.16);
  color: #d9efff;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  backdrop-filter: blur(10px);
}

.runtime-banner.muted {
  background: rgba(8, 24, 42, 0.72);
  color: rgba(217, 239, 255, 0.86);
}

.mode-live2d .fallback-host,
.mode-video .fallback-host {
  opacity: 0;
  transition: opacity 0.35s ease;
}

.loading .fallback-host {
  opacity: 1;
}
</style>
