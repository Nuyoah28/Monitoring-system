<template>
  <view
    class="agent-stage"
    id="ai-stage"
    :class="['state-' + state, { 'live2d-ready': live2dReady, 'live2d-failed': live2dFailed }]"
    @tap="$emit('tap')"
  >
    <view class="agent-grid"></view>
    <view class="agent-glow glow-one"></view>
    <view class="agent-glow glow-two"></view>
    <view class="agent-orbit orbit-one"><view></view></view>
    <view class="agent-orbit orbit-two"><view></view></view>
    <view class="agent-light"></view>

    <view class="live2d-layer">
      <view class="live2d-host" :prop="live2dConfig" :change:prop="live2dRenderer.update"></view>
    </view>

    <view class="agent-portrait-wrap">
      <view class="agent-back-halo"></view>
      <view class="agent-portrait">
        <view class="agent-hair hair-back"></view>
        <view class="agent-neck"></view>
        <view class="agent-body-shape">
          <view class="agent-collar collar-left"></view>
          <view class="agent-collar collar-right"></view>
          <view class="agent-core"></view>
        </view>
        <view class="agent-face">
          <view class="agent-bang bang-left"></view>
          <view class="agent-bang bang-right"></view>
          <view class="agent-eye eye-left"></view>
          <view class="agent-eye eye-right"></view>
          <view class="agent-cheek cheek-left"></view>
          <view class="agent-cheek cheek-right"></view>
          <view class="agent-mouth"></view>
        </view>
      </view>
    </view>

    <view class="agent-status-card">
      <view class="agent-status-top">
        <view class="agent-status-dot"></view>
        <text class="agent-state-pill">{{ statusText }}</text>
      </view>
      <text v-if="subtitle" class="agent-status-subtitle">{{ subtitle }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'VirtualAgentCard',
  props: {
    state: {
      type: String,
      default: 'idle',
    },
    statusText: {
      type: String,
      default: '随时待命',
    },
    subtitle: {
      type: String,
      default: '',
    },
    modelUrl: {
      type: String,
      default: './static/live2d/haru/haru_greeter_t03.model3.json',
    },
    pixiScriptUrl: {
      type: String,
      default: './static/live2d-runtime/pixi.min.js',
    },
    runtimeScriptUrl: {
      type: String,
      default: './static/live2d-runtime/live2dcubismcore.min.js',
    },
    live2dScriptUrl: {
      type: String,
      default: './static/live2d-runtime/pixi-live2d-cubism4.min.js',
    },
    cubismVersion: {
      type: Number,
      default: 4,
    },
    fitScale: {
      type: Number,
      default: 0.88,
    },
    positionX: {
      type: Number,
      default: 0,
    },
    positionY: {
      type: Number,
      default: 0.08,
    },
    idleMotionGroup: {
      type: String,
      default: 'Idle',
    },
    listeningMotionGroup: {
      type: String,
      default: 'Idle',
    },
    thinkingMotionGroup: {
      type: String,
      default: 'Idle',
    },
    speakingMotionGroup: {
      type: String,
      default: 'Idle',
    },
  },
  data() {
    return {
      live2dReady: false,
      live2dFailed: false,
    };
  },
  computed: {
    live2dConfig() {
      return {
        state: this.state,
        modelUrl: this.modelUrl,
        pixiScriptUrl: this.pixiScriptUrl,
        runtimeScriptUrl: this.runtimeScriptUrl,
        live2dScriptUrl: this.live2dScriptUrl,
        cubismVersion: Number(this.cubismVersion) === 2 ? 2 : 4,
        fitScale: Number(this.fitScale) || 0.88,
        positionX: Number(this.positionX) || 0,
        positionY: Number(this.positionY) || 0.08,
        motions: {
          idle: this.idleMotionGroup,
          listening: this.listeningMotionGroup,
          thinking: this.thinkingMotionGroup,
          speaking: this.speakingMotionGroup,
        },
      };
    },
  },
  methods: {
    setLive2DReady() {
      this.live2dReady = true;
      this.live2dFailed = false;
    },
    setLive2DFailed() {
      this.live2dReady = false;
      this.live2dFailed = true;
      this.$emit('failed');
    },
  },
};
</script>

<script module="live2dRenderer" lang="renderjs">
const scriptCache = {};

function normalizeAssetUrl(src) {
  if (!src || src.indexOf('://') > -1 || src.indexOf('file://') === 0 || src.indexOf('blob:') === 0) {
    return src;
  }
  const cleanSrc = src.charAt(0) === '/' ? src.slice(1) : src.replace(/^\.\//, '');
  try {
    return new URL(cleanSrc, window.location.href).href;
  } catch (error) {
    return `./${cleanSrc}`;
  }
}

function loadScript(src, validator) {
  const normalizedSrc = normalizeAssetUrl(src);
  if (!normalizedSrc) return Promise.reject(new Error('missing script'));
  if (validator && validator()) return Promise.resolve();
  if (scriptCache[normalizedSrc]) return scriptCache[normalizedSrc];

  scriptCache[normalizedSrc] = new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[data-live2d-renderer="${normalizedSrc}"]`);
    const finish = () => {
      if (!validator || validator()) resolve();
      else reject(new Error('script loaded without expected global'));
    };

    if (existing) {
      if (existing.dataset.loaded === 'true') {
        finish();
        return;
      }
      existing.addEventListener('load', finish, { once: true });
      existing.addEventListener('error', reject, { once: true });
      return;
    }

    const script = document.createElement('script');
    script.src = normalizedSrc;
    script.async = true;
    script.dataset.live2dRenderer = normalizedSrc;
    script.onload = () => {
      script.dataset.loaded = 'true';
      finish();
    };
    script.onerror = () => reject(new Error(`load failed: ${normalizedSrc}`));
    document.head.appendChild(script);
  });

  return scriptCache[normalizedSrc];
}

export default {
  data() {
    return {
      app: null,
      model: null,
      host: null,
      root: null,
      config: null,
      lipSyncFrame: 0,
      lastMotionKey: '',
      resizeHandler: null,
      ownerInstance: null,
      initializing: false,
    };
  },
  beforeDestroy() {
    this.destroyLive2D();
  },
  methods: {
    update(config, oldConfig, ownerInstance) {
      if (!config || !config.modelUrl) return;
      this.config = config;
      this.ownerInstance = ownerInstance || this.ownerInstance;

      if (!this.root || !this.host) {
        this.host = this.getHostElement();
        this.root = this.getRootElement();
      }

      if (!this.app && !this.initializing) {
        this.initLive2D(config, 0);
        return;
      }

      if (this.app && this.model) {
        this.syncLayout();
        this.playMotionForState(config.state);
      }
    },
    getHostElement() {
      if (!this.$el) return null;
      if (this.$el.classList && this.$el.classList.contains('live2d-host')) return this.$el;
      if (this.$el.querySelector) {
        const host = this.$el.querySelector('.live2d-host');
        if (host) return host;
      }
      if (this.$el.closest) {
        const root = this.$el.closest('.agent-stage');
        if (root) return root.querySelector('.live2d-host');
      }
      return document.querySelector('#ai-stage .live2d-host');
    },
    getRootElement() {
      if (this.host && this.host.closest) return this.host.closest('.agent-stage');
      if (!this.$el) return null;
      if (this.$el.classList && this.$el.classList.contains('agent-stage')) return this.$el;
      if (this.$el.closest) return this.$el.closest('.agent-stage');
      return document.querySelector('#ai-stage');
    },
    async initLive2D(config, retryCount = 0) {
      this.initializing = true;
      try {
        this.host = this.getHostElement();
        this.root = this.getRootElement();
        if (!this.root || !this.host) {
          if (retryCount < 12) {
            window.setTimeout(() => {
              this.initializing = false;
              this.initLive2D(config, retryCount + 1);
            }, 120);
            return;
          }
          throw new Error('missing live2d host');
        }

        await loadScript(config.pixiScriptUrl, () => Boolean(window.PIXI));
        await loadScript(config.runtimeScriptUrl, () => {
          return config.cubismVersion === 4 ? Boolean(window.Live2DCubismCore) : Boolean(window.Live2D);
        });
        await loadScript(config.live2dScriptUrl, () => {
          return Boolean(window.PIXI && window.PIXI.live2d && window.PIXI.live2d.Live2DModel);
        });

        const PIXI = window.PIXI;
        const rect = this.host.getBoundingClientRect();
        const width = Math.max(rect.width || 1, 1);
        const height = Math.max(rect.height || 1, 1);
        const app = new PIXI.Application({
          width,
          height,
          antialias: true,
          transparent: true,
          autoDensity: true,
          resolution: Math.min(window.devicePixelRatio || 1, 2),
        });

        this.host.innerHTML = '';
        this.host.appendChild(app.view);
        app.view.style.width = '100%';
        app.view.style.height = '100%';
        app.view.style.display = 'block';

        const model = await PIXI.live2d.Live2DModel.from(normalizeAssetUrl(config.modelUrl));
        model.interactive = true;
        model.buttonMode = true;
        app.stage.addChild(model);

        this.app = app;
        this.model = model;
        this.syncLayout();
        this.playMotionForState(config.state);
        this.startLipSyncLoop();

        this.resizeHandler = () => this.syncLayout();
        window.addEventListener('resize', this.resizeHandler);
        this.root.classList.add('live2d-ready');
        this.root.classList.remove('live2d-failed');
        if (this.ownerInstance) this.ownerInstance.callMethod('setLive2DReady');
      } catch (error) {
        this.destroyLive2D();
        if (this.root) {
          this.root.classList.remove('live2d-ready');
          this.root.classList.add('live2d-failed');
        }
        if (this.ownerInstance) this.ownerInstance.callMethod('setLive2DFailed');
        console.error('Live2D renderer failed', error);
      } finally {
        this.initializing = false;
      }
    },
    syncLayout() {
      if (!this.host || !this.app || !this.model || !this.config) return;
      const rect = this.host.getBoundingClientRect();
      const width = Math.max(rect.width || 1, 1);
      const height = Math.max(rect.height || 1, 1);
      this.app.renderer.resize(width, height);

      const bounds = this.model.getLocalBounds ? this.model.getLocalBounds() : { x: 0, y: 0, width, height };
      const modelWidth = Math.max(bounds.width || 1, 1);
      const modelHeight = Math.max(bounds.height || 1, 1);
      const fitScale = Math.min(width / modelWidth, height / modelHeight);
      const scale = fitScale * (this.config.fitScale || 0.82);

      if (this.model.anchor && this.model.anchor.set) {
        this.model.anchor.set(0.5, 1);
      } else if (this.model.pivot && this.model.pivot.set) {
        this.model.pivot.set(bounds.x + modelWidth / 2, bounds.y + modelHeight);
      }

      this.model.scale.set(scale);
      this.model.position.set(
        width * (0.5 + (this.config.positionX || 0)),
        height * (0.98 + (this.config.positionY || 0)),
      );
    },
    startLipSyncLoop() {
      this.stopLipSyncLoop();
      const tick = () => {
        const coreModel = this.model && this.model.internalModel && this.model.internalModel.coreModel;
        if (coreModel && coreModel.setParameterValueById && this.config) {
          const time = window.performance.now();
          let mouthOpen = 0;
          if (this.config.state === 'speaking') {
            mouthOpen = 0.18 + ((Math.sin(time / 84) + 1) / 2) * 0.68;
          } else if (this.config.state === 'listening') {
            mouthOpen = 0.04 + ((Math.sin(time / 180) + 1) / 2) * 0.1;
          }
          try {
            coreModel.setParameterValueById('ParamMouthOpenY', mouthOpen);
            coreModel.setParameterValueById('PARAM_MOUTH_OPEN_Y', mouthOpen);
          } catch (error) {}
        }
        this.lipSyncFrame = window.requestAnimationFrame(tick);
      };
      this.lipSyncFrame = window.requestAnimationFrame(tick);
    },
    stopLipSyncLoop() {
      if (this.lipSyncFrame) {
        window.cancelAnimationFrame(this.lipSyncFrame);
        this.lipSyncFrame = 0;
      }
    },
    playMotionForState(state) {
      if (!this.model || !this.config || !this.config.motions) return;
      const group = this.config.motions[state] || this.config.motions.idle;
      const key = `${state}:${group || 'none'}`;
      if (!group || key === this.lastMotionKey) return;
      this.lastMotionKey = key;
      try {
        const motion = this.model.motion(group);
        if (motion && typeof motion.catch === 'function') motion.catch(() => {});
      } catch (error) {}
    },
    destroyLive2D() {
      this.stopLipSyncLoop();
      if (this.resizeHandler) {
        window.removeEventListener('resize', this.resizeHandler);
        this.resizeHandler = null;
      }
      if (this.app) {
        try {
          this.app.destroy(true, { children: true, texture: true, baseTexture: true });
        } catch (error) {}
      }
      if (this.host) this.host.innerHTML = '';
      this.app = null;
      this.model = null;
      this.lastMotionKey = '';
    },
  },
};
</script>

<style lang="scss">
.agent-stage {
  position: relative;
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
  margin: 0;
  border-radius: 0;
  overflow: hidden;
  background:
    radial-gradient(680rpx 560rpx at 22% 8%, rgba(120, 213, 255, 0.42) 0%, rgba(120, 213, 255, 0) 70%),
    radial-gradient(720rpx 620rpx at 88% 14%, rgba(113, 156, 255, 0.3) 0%, rgba(113, 156, 255, 0) 72%),
    radial-gradient(760rpx 520rpx at 50% 94%, rgba(84, 226, 192, 0.22) 0%, rgba(84, 226, 192, 0) 70%),
    linear-gradient(180deg, rgba(9, 32, 66, 0.98) 0%, rgba(7, 25, 51, 0.98) 52%, rgba(4, 17, 36, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.agent-grid,
.agent-glow,
.agent-orbit,
.agent-light,
.agent-back-halo {
  position: absolute;
  pointer-events: none;
}

.agent-grid {
  inset: 0;
  opacity: 0.62;
  background-image:
    linear-gradient(rgba(124, 207, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(124, 207, 255, 0.08) 1px, transparent 1px);
  background-size: 54rpx 54rpx;
  transform: perspective(760rpx) rotateX(58deg) translateY(120rpx);
  transform-origin: center bottom;
}

.agent-glow {
  border-radius: 50%;
  filter: blur(10rpx);
}

.glow-one {
  width: 360rpx;
  height: 360rpx;
  left: 18rpx;
  top: 120rpx;
  background: rgba(93, 189, 255, 0.24);
  animation: agentDrift 6s ease-in-out infinite;
}

.glow-two {
  width: 320rpx;
  height: 320rpx;
  right: -30rpx;
  bottom: 180rpx;
  background: rgba(88, 233, 190, 0.18);
  animation: agentDrift 7s ease-in-out infinite reverse;
}

.agent-orbit {
  left: 50%;
  top: 46%;
  border-radius: 50%;
  border: 1px solid rgba(148, 223, 255, 0.2);
}

.agent-orbit view {
  position: absolute;
  right: 16rpx;
  top: 28rpx;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #bff4ff;
  box-shadow: 0 0 18rpx rgba(177, 240, 255, 0.86);
}

.orbit-one {
  width: 520rpx;
  height: 520rpx;
  margin-left: -260rpx;
  margin-top: -260rpx;
  animation: agentSpin 18s linear infinite;
}

.orbit-two {
  width: 390rpx;
  height: 390rpx;
  margin-left: -195rpx;
  margin-top: -195rpx;
  opacity: 0.72;
  animation: agentSpinReverse 13s linear infinite;
}

.agent-light {
  left: 50%;
  top: -120rpx;
  width: 260rpx;
  height: 660rpx;
  border-radius: 130rpx;
  background: linear-gradient(180deg, rgba(166, 232, 255, 0.3), rgba(166, 232, 255, 0));
  filter: blur(22rpx);
  transform: translateX(-50%) rotate(8deg);
}

.live2d-layer {
  position: absolute;
  left: 50%;
  top: calc(var(--status-bar-height, 0px) + 112rpx);
  bottom: 230rpx;
  width: 86%;
  max-width: 760rpx;
  z-index: 6;
  opacity: 0;
  transform: translateX(-50%);
  transition: opacity 0.35s ease;
  pointer-events: none;
}

.live2d-host {
  width: 100%;
  height: 100%;
}

.live2d-host canvas {
  width: 100% !important;
  height: 100% !important;
  display: block;
}

.live2d-ready .live2d-layer {
  opacity: 1;
}

.live2d-ready .agent-portrait-wrap {
  opacity: 0;
  transform: translateX(-50%) scale(0.96);
  pointer-events: none;
}

.live2d-failed .live2d-layer {
  opacity: 0;
}

.agent-portrait-wrap {
  position: absolute;
  left: 50%;
  bottom: 276rpx;
  width: 340rpx;
  height: 340rpx;
  z-index: 5;
  transform: translateX(-50%) scale(0.82);
  animation: agentFloat 4.8s ease-in-out infinite;
  transition: opacity 0.32s ease, transform 0.32s ease;
  transform-origin: center bottom;
}

.agent-back-halo {
  left: 52rpx;
  top: 22rpx;
  width: 190rpx;
  height: 190rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(145, 225, 255, 0.28) 0%, rgba(145, 225, 255, 0) 70%);
  animation: agentPulse 2.8s ease-in-out infinite;
}

.agent-portrait {
  position: absolute;
  left: 42rpx;
  bottom: -12rpx;
  width: 214rpx;
  height: 260rpx;
}

.agent-hair {
  position: absolute;
  left: 39rpx;
  top: 16rpx;
  width: 136rpx;
  height: 142rpx;
  border-radius: 76rpx 76rpx 58rpx 58rpx;
  background: linear-gradient(135deg, #82d8ff 0%, #3e83d3 48%, #12345d 100%);
  box-shadow: 0 8rpx 24rpx rgba(33, 128, 202, 0.28);
}

.agent-neck {
  position: absolute;
  left: 85rpx;
  top: 142rpx;
  width: 44rpx;
  height: 46rpx;
  border-radius: 0 0 22rpx 22rpx;
  background: linear-gradient(180deg, #eaf6ff 0%, #b9d7f7 100%);
  z-index: 3;
}

.agent-body-shape {
  position: absolute;
  left: 28rpx;
  bottom: 0;
  width: 158rpx;
  height: 92rpx;
  border-radius: 80rpx 80rpx 20rpx 20rpx;
  background: linear-gradient(135deg, #153f70 0%, #0d2b52 58%, #081e3a 100%);
  z-index: 2;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.agent-collar {
  position: absolute;
  top: 8rpx;
  width: 58rpx;
  height: 46rpx;
  border-radius: 12rpx;
  border-top: 5rpx solid rgba(115, 206, 255, 0.9);
}

.collar-left {
  left: 32rpx;
  transform: rotate(34deg);
}

.collar-right {
  right: 32rpx;
  transform: rotate(-34deg);
}

.agent-core {
  position: absolute;
  left: 66rpx;
  top: 45rpx;
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  background: radial-gradient(circle, #fff 0%, #8ee7ff 45%, rgba(142, 231, 255, 0) 72%);
  box-shadow: 0 0 24rpx rgba(142, 231, 255, 0.85);
}

.agent-face {
  position: absolute;
  left: 51rpx;
  top: 44rpx;
  width: 112rpx;
  height: 126rpx;
  border-radius: 58rpx 58rpx 52rpx 52rpx;
  background: linear-gradient(180deg, #f8fbff 0%, #d9ebff 58%, #b5d2f2 100%);
  z-index: 4;
  box-shadow: inset 0 -8rpx 14rpx rgba(71, 130, 190, 0.12);
}

.agent-bang {
  position: absolute;
  top: -18rpx;
  width: 62rpx;
  height: 48rpx;
  background: linear-gradient(135deg, #80d5ff 0%, #3d82d2 100%);
  border-radius: 40rpx 40rpx 18rpx 18rpx;
}

.bang-left {
  left: -3rpx;
  transform: rotate(-16deg);
}

.bang-right {
  right: -3rpx;
  transform: rotate(16deg);
}

.agent-eye {
  position: absolute;
  top: 54rpx;
  width: 22rpx;
  height: 10rpx;
  border-radius: 50%;
  background: #245c93;
  box-shadow: inset 0 0 0 4rpx #79d5ff, 0 0 8rpx rgba(121, 213, 255, 0.42);
  animation: agentBlink 6s ease-in-out infinite;
}

.eye-left {
  left: 26rpx;
}

.eye-right {
  right: 26rpx;
}

.agent-cheek {
  position: absolute;
  top: 77rpx;
  width: 17rpx;
  height: 8rpx;
  border-radius: 50%;
  background: rgba(122, 190, 246, 0.25);
}

.cheek-left {
  left: 17rpx;
}

.cheek-right {
  right: 17rpx;
}

.agent-mouth {
  position: absolute;
  left: 43rpx;
  top: 84rpx;
  width: 26rpx;
  height: 8rpx;
  border-bottom: 4rpx solid #5797d7;
  border-radius: 0 0 18rpx 18rpx;
  transform-origin: center top;
}

.agent-status-card {
  position: absolute;
  left: 28rpx;
  right: auto;
  top: calc(var(--status-bar-height, 0px) + 112rpx);
  z-index: 8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 260rpx;
  padding: 10rpx 16rpx;
  border-radius: 22rpx;
  background: rgba(7, 27, 54, 0.32);
  border: 1px solid rgba(139, 219, 255, 0.14);
  box-shadow: 0 10rpx 28rpx rgba(0, 13, 38, 0.12);
  backdrop-filter: blur(8px);
}

.agent-status-top {
  display: flex;
  align-items: center;
}

.agent-status-dot {
  width: 12rpx;
  height: 12rpx;
  margin-right: 10rpx;
  border-radius: 50%;
  background: #8ee7ff;
  box-shadow: 0 0 16rpx rgba(142, 231, 255, 0.85);
  animation: agentPulse 1.6s ease-in-out infinite;
}

.agent-state-pill {
  color: #dff7ff;
  font-size: 22rpx;
  font-weight: 700;
}

.agent-status-subtitle {
  display: none;
  margin-top: 6rpx;
  color: rgba(204, 229, 244, 0.78);
  font-size: 19rpx;
  line-height: 1.35;
}

.agent-stage.state-listening .agent-status-dot {
  background: #f4b959;
  box-shadow: 0 0 16rpx rgba(244, 185, 89, 0.85);
}

.agent-stage.state-thinking .agent-core,
.agent-stage.state-thinking .agent-back-halo {
  animation-duration: 1.2s;
}

.agent-stage.state-speaking .agent-mouth {
  animation: agentTalk 0.72s ease-in-out infinite;
}

.agent-stage.state-speaking .agent-core,
.agent-stage.state-speaking .agent-back-halo {
  animation: agentPulse 1.2s ease-in-out infinite;
}

.agent-stage.state-speaking .agent-status-dot {
  background: #35d4a0;
  box-shadow: 0 0 16rpx rgba(53, 212, 160, 0.85);
}

@keyframes agentFloat {
  0%,
  100% {
    transform: translateX(-50%) scale(0.82) translateY(0);
  }
  50% {
    transform: translateX(-50%) scale(0.82) translateY(-10rpx);
  }
}

@keyframes agentDrift {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(14rpx, -10rpx, 0) scale(1.04);
  }
}

@keyframes agentPulse {
  0%,
  100% {
    opacity: 0.82;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

@keyframes agentBlink {
  0%,
  44%,
  54%,
  100% {
    transform: scaleY(1);
  }
  48%,
  50% {
    transform: scaleY(0.18);
  }
}

@keyframes agentTalk {
  0%,
  100% {
    height: 8rpx;
    border-bottom-width: 4rpx;
    transform: scaleY(1);
  }
  50% {
    height: 15rpx;
    border-bottom-width: 7rpx;
    transform: scaleY(1.25);
  }
}

@keyframes agentMeter {
  0%,
  100% {
    height: 14rpx;
  }
  40% {
    height: 40rpx;
  }
  70% {
    height: 24rpx;
  }
}

@keyframes agentSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes agentSpinReverse {
  from {
    transform: rotate(360deg);
  }
  to {
    transform: rotate(0deg);
  }
}
</style>
