export type DigitalHumanMode = 'live2d' | 'video' | 'mascot';

export interface Live2DProviderConfig {
  modelUrl: string;
  cubismVersion: 2 | 4;
  runtimeScriptUrl: string;
  fitScale: number;
  positionX: number;
  positionY: number;
  idleMotionGroup?: string;
  listeningMotionGroup?: string;
  speakingMotionGroup?: string;
  tapMotionGroup?: string;
  attribution?: string;
}

export interface VideoProviderConfig {
  idleSrc: string;
  listeningSrc?: string;
  speakingSrc?: string;
  poster?: string;
}

export interface DigitalHumanSettings {
  mode: DigitalHumanMode;
  live2d?: Live2DProviderConfig;
  video?: VideoProviderConfig;
}

const normalizeMode = (value?: string): DigitalHumanMode => {
  if (value === 'video' || value === 'mascot') {
    return value;
  }
  return 'live2d';
};

const envMode = normalizeMode(process.env.VUE_APP_DIGITAL_HUMAN_MODE);

export const digitalHumanConfig: DigitalHumanSettings = {
  mode: envMode,
  live2d: {
    // Default demo model from the pixi-live2d-display sample assets.
    // Replace these URLs with your licensed local model before final delivery if needed.
    modelUrl:
      process.env.VUE_APP_LIVE2D_MODEL_URL ||
      'https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display@0.4.0/test/assets/haru/haru_greeter_t03.model3.json',
      //'/live2d/huohuo/huohuo.model3.json',
    cubismVersion: Number(process.env.VUE_APP_LIVE2D_CUBISM_VERSION || 4) === 2 ? 2 : 4,
    runtimeScriptUrl:
      process.env.VUE_APP_LIVE2D_CUBISM_CORE_URL ||
      'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
    fitScale: Number(process.env.VUE_APP_LIVE2D_FIT_SCALE || 0.82),
    positionX: Number(process.env.VUE_APP_LIVE2D_POSITION_X || 0),
    positionY: Number(process.env.VUE_APP_LIVE2D_POSITION_Y || 0.08),
    idleMotionGroup: process.env.VUE_APP_LIVE2D_IDLE_MOTION || 'Idle',
    listeningMotionGroup: process.env.VUE_APP_LIVE2D_LISTENING_MOTION || 'Idle',
    speakingMotionGroup: process.env.VUE_APP_LIVE2D_SPEAKING_MOTION || 'Idle',
    tapMotionGroup: process.env.VUE_APP_LIVE2D_TAP_MOTION || 'Idle',
    attribution: 'Live2D demo model: Haru (Live2D Free Material License).',
  },
  video: {
    idleSrc: process.env.VUE_APP_DIGITAL_HUMAN_VIDEO_IDLE || '',
    listeningSrc: process.env.VUE_APP_DIGITAL_HUMAN_VIDEO_LISTENING || '',
    speakingSrc: process.env.VUE_APP_DIGITAL_HUMAN_VIDEO_SPEAKING || '',
    poster: process.env.VUE_APP_DIGITAL_HUMAN_VIDEO_POSTER || '',
  },
};

export const digitalHumanModeLabel: Record<DigitalHumanMode, string> = {
  live2d: 'Live2D 数字人',
  video: '视频数字人',
  mascot: '内置形象',
};
