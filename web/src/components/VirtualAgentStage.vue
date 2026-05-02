<template>
  <section class="virtual-agent" :data-state="status">
    <div class="stage-shell">
      <div class="stage-grid"></div>
      <div class="ambient ambient-a"></div>
      <div class="ambient ambient-b"></div>
      <div class="light-column"></div>
      <div class="halo halo-outer"></div>
      <div class="halo halo-inner"></div>
      <DigitalHumanViewport :status="status">
        <template #fallback>
          <svg class="avatar-portrait" viewBox="0 0 420 560" aria-hidden="true">
            <defs>
              <radialGradient id="bgAura" cx="50%" cy="38%" r="62%">
                <stop offset="0%" stop-color="rgba(138,220,255,0.62)" />
                <stop offset="45%" stop-color="rgba(92,162,232,0.26)" />
                <stop offset="100%" stop-color="rgba(10,26,46,0)" />
              </radialGradient>
              <linearGradient id="hairFill" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#8dd6ff" />
                <stop offset="40%" stop-color="#3d7bba" />
                <stop offset="100%" stop-color="#0b2e4f" />
              </linearGradient>
              <linearGradient id="hairShade" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#5fa8ef" />
                <stop offset="100%" stop-color="#092641" />
              </linearGradient>
              <linearGradient id="skinFill" x1="50%" y1="0%" x2="50%" y2="100%">
                <stop offset="0%" stop-color="#f4f8ff" />
                <stop offset="55%" stop-color="#d9e9ff" />
                <stop offset="100%" stop-color="#a7c5e8" />
              </linearGradient>
              <linearGradient id="skinShadow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#d2e6ff" />
                <stop offset="100%" stop-color="#8db4df" />
              </linearGradient>
              <linearGradient id="suitFill" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#12365d" />
                <stop offset="50%" stop-color="#0b2745" />
                <stop offset="100%" stop-color="#081b31" />
              </linearGradient>
              <linearGradient id="collarFill" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#74cbff" />
                <stop offset="100%" stop-color="#367fc6" />
              </linearGradient>
              <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#ffffff" />
                <stop offset="35%" stop-color="#97dfff" />
                <stop offset="100%" stop-color="rgba(151,223,255,0)" />
              </radialGradient>
            </defs>

            <g class="portrait-group">
              <ellipse cx="210" cy="250" rx="138" ry="176" fill="url(#bgAura)" class="body-aura" />
              <path
                d="M84 507C110 414 155 360 210 360C265 360 310 414 336 507L348 552H72L84 507Z"
                fill="url(#suitFill)"
              />
              <path
                d="M144 170C150 122 180 94 210 94C247 94 281 122 288 176L286 255C280 306 252 340 210 344C168 340 140 306 134 255L144 170Z"
                fill="url(#hairShade)"
              />
              <path
                d="M182 326C188 352 232 352 238 326L244 382C235 396 186 396 176 382L182 326Z"
                fill="url(#skinShadow)"
              />
              <path
                d="M148 178C152 136 178 112 210 112C242 112 268 136 272 178L268 248C262 293 239 327 210 330C181 327 158 293 152 248L148 178Z"
                fill="url(#skinFill)"
              />
              <path
                d="M154 163C169 120 192 103 210 103C243 103 272 124 282 165C262 148 236 140 210 140C184 140 165 146 154 163Z"
                fill="url(#hairFill)"
              />
              <path
                d="M141 160C118 194 115 268 134 318C111 303 96 271 95 231C94 183 108 140 142 116L156 130C149 140 145 149 141 160Z"
                fill="url(#hairFill)"
              />
              <path
                d="M279 160C302 194 305 268 286 318C309 303 324 271 325 231C326 183 312 140 278 116L264 130C271 140 275 149 279 160Z"
                fill="url(#hairFill)"
              />

              <g class="eye eye-left">
                <ellipse cx="184" cy="214" rx="18" ry="5.5" fill="#ffffff" fill-opacity="0.95" />
                <ellipse cx="184" cy="214" rx="7.2" ry="5.2" fill="#4cb8ff" />
                <circle cx="184" cy="214" r="2.8" fill="#ffffff" />
              </g>
              <g class="eye eye-right">
                <ellipse cx="236" cy="214" rx="18" ry="5.5" fill="#ffffff" fill-opacity="0.95" />
                <ellipse cx="236" cy="214" rx="7.2" ry="5.2" fill="#4cb8ff" />
                <circle cx="236" cy="214" r="2.8" fill="#ffffff" />
              </g>

              <path d="M209 222C214 238 214 252 210 266" fill="none" stroke="#88afd7" stroke-width="4" stroke-linecap="round" />
              <path d="M191 280C201 288 219 288 229 280" fill="none" stroke="#7abef6" stroke-width="4" stroke-linecap="round" class="mouth-line" />
              <ellipse cx="210" cy="284" rx="16" ry="6.2" fill="rgba(122,190,246,0.18)" class="lip-glow" />

              <path
                d="M102 512C128 425 164 382 210 382C256 382 292 425 318 512L328 552H92L102 512Z"
                fill="url(#suitFill)"
              />
              <path
                d="M172 384L210 438L248 384"
                fill="none"
                stroke="url(#collarFill)"
                stroke-width="7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <circle cx="210" cy="454" r="34" fill="url(#coreGlow)" class="chest-core" />
              <circle cx="210" cy="454" r="10" fill="#ffffff" fill-opacity="0.78" />
            </g>
          </svg>
        </template>
      </DigitalHumanViewport>

      <div class="voice-meter" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
// AI辅助生成：GPT-5 Codex, 2026-03-28。数字人舞台布局、SVG 形象与状态氛围表现逻辑。
import DigitalHumanViewport from '@/components/DigitalHumanViewport.vue';

type AgentStageStatus = 'idle' | 'listening' | 'thinking' | 'speaking';

interface VirtualAgentStageProps {
  title?: string;
  status?: AgentStageStatus;
  conversationActive?: boolean;
  previewText?: string;
}

withDefaults(defineProps<VirtualAgentStageProps>(), {
  title: '晓卫',
  status: 'idle',
  conversationActive: false,
  previewText: '',
});
</script>

<style scoped>
.virtual-agent {
  --stage-bg:
    radial-gradient(circle at 18% 16%, rgba(106, 204, 255, 0.22), transparent 24%),
    radial-gradient(circle at 68% 18%, rgba(126, 197, 255, 0.26), transparent 28%),
    radial-gradient(circle at 84% 74%, rgba(83, 213, 165, 0.14), transparent 28%),
    radial-gradient(circle at 50% 100%, rgba(126, 197, 255, 0.14), transparent 34%),
    linear-gradient(180deg, rgba(8, 28, 51, 0.97), rgba(7, 20, 38, 0.92));
  position: relative;
  min-height: 100%;
  height: 100%;
}

.stage-shell {
  position: relative;
  min-height: 100%;
  height: 100%;
  border-radius: 28px;
  overflow: hidden;
  border: 1px solid rgba(126, 197, 255, 0.24);
  background: var(--stage-bg);
  box-shadow:
    inset 0 0 0 1px rgba(126, 197, 255, 0.07),
    0 24px 48px rgba(2, 11, 24, 0.32);
}

.stage-shell :deep(.digital-human-viewport) {
  z-index: 5;
}

.stage-shell::before,
.stage-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.stage-shell::before {
  background:
    radial-gradient(circle at 50% 12%, rgba(255, 255, 255, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent 30%);
  z-index: 1;
}

.stage-shell::after {
  top: -45%;
  left: -30%;
  width: 160%;
  height: 55%;
  background: linear-gradient(180deg, rgba(151, 223, 255, 0.2), rgba(151, 223, 255, 0));
  transform: rotate(-8deg);
  filter: blur(18px);
  animation: sweep 5.8s ease-in-out infinite;
  z-index: 1;
}

.stage-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(123, 192, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(123, 192, 255, 0.05) 1px, transparent 1px);
  background-size: 2.8rem 2.8rem;
  transform: perspective(900px) rotateX(64deg) translateY(26%);
  transform-origin: center bottom;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.92), transparent 88%);
}

.ambient,
.light-column,
.halo,
.spark,
.signal-beam {
  position: absolute;
  pointer-events: none;
}

.ambient-a {
  inset: 12% auto auto 14%;
  width: 12rem;
  height: 12rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(126, 197, 255, 0.28), transparent 72%);
  filter: blur(8px);
  opacity: 0.76;
  animation: drift 8s ease-in-out infinite;
}

.ambient-b {
  inset: auto 8% 10% auto;
  width: 10.5rem;
  height: 10.5rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(83, 213, 165, 0.18), transparent 74%);
  filter: blur(12px);
  opacity: 0.52;
  animation: drift 10s ease-in-out infinite reverse;
}

.light-column {
  left: 50%;
  top: -12%;
  width: 13rem;
  height: 30rem;
  transform: translateX(-50%);
  background: linear-gradient(180deg, rgba(151, 223, 255, 0.32), rgba(151, 223, 255, 0));
  filter: blur(22px);
  opacity: 0.48;
}

.halo {
  left: 50%;
  top: 58%;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.halo-outer {
  width: 15rem;
  height: 15rem;
  border: 1px solid rgba(126, 197, 255, 0.12);
  box-shadow:
    0 0 28px rgba(126, 197, 255, 0.08),
    inset 0 0 16px rgba(126, 197, 255, 0.06);
  animation: spin 18s linear infinite;
}

.halo-inner {
  width: 10.8rem;
  height: 10.8rem;
  border: 1px solid rgba(126, 197, 255, 0.18);
  animation: spinReverse 12s linear infinite;
}

.spark {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 50%;
  background: rgba(190, 238, 255, 0.92);
  box-shadow: 0 0 18px rgba(126, 197, 255, 0.82);
  animation: twinkle 2.6s ease-in-out infinite;
  z-index: 2;
}

.spark-a {
  top: 18%;
  left: 18%;
}

.spark-b {
  top: 27%;
  right: 17%;
  animation-delay: 0.55s;
}

.spark-c {
  top: 54%;
  left: 15%;
  animation-delay: 1.1s;
}

.spark-d {
  bottom: 24%;
  right: 18%;
  animation-delay: 1.65s;
}

.signal-beam {
  right: -8%;
  top: 18%;
  width: 32%;
  height: 32%;
  border: 1px solid rgba(126, 197, 255, 0.18);
  border-left: none;
  border-bottom: none;
  border-radius: 0 22px 0 0;
  opacity: 0.8;
  box-shadow: 0 0 24px rgba(126, 197, 255, 0.08);
  z-index: 2;
}

.voice-meter {
  position: absolute;
  z-index: 8;
  backdrop-filter: blur(14px);
}

.voice-meter {
  left: 50%;
  bottom: 0.9rem;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  gap: 0.24rem;
  padding: 0.52rem 0.78rem;
  border-radius: 999px;
  background: rgba(8, 26, 45, 0.56);
  border: 1px solid rgba(126, 197, 255, 0.12);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 10px 20px rgba(2, 11, 24, 0.18);
}

.voice-meter span {
  width: 0.34rem;
  height: 0.5rem;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(155, 231, 255, 0.92), rgba(68, 126, 255, 0.7));
  animation: meter 1.15s ease-in-out infinite;
}

.voice-meter span:nth-child(2) {
  animation-delay: 0.12s;
}

.voice-meter span:nth-child(3) {
  animation-delay: 0.24s;
}

.voice-meter span:nth-child(4) {
  animation-delay: 0.36s;
}

.avatar-portrait {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  animation: portraitFloat 4.8s ease-in-out infinite;
}

.portrait-group {
  transform-origin: center 58%;
}

.eye {
  transform-origin: center;
  animation: blink 6.4s ease-in-out infinite;
}

.virtual-agent[data-state='listening'] .voice-meter span {
  background: linear-gradient(180deg, rgba(255, 231, 171, 0.96), rgba(248, 203, 113, 0.72));
}

.virtual-agent[data-state='speaking'] .body-aura,
.virtual-agent[data-state='speaking'] .chest-core {
  animation: auraPulse 1.6s ease-in-out infinite;
}

.virtual-agent[data-state='speaking'] .mouth-line,
.virtual-agent[data-state='speaking'] .lip-glow {
  animation: mouthTalk 0.9s ease-in-out infinite;
}

.virtual-agent[data-state='speaking'] .voice-meter span {
  animation-duration: 0.72s;
}

.virtual-agent[data-state='idle'] .voice-meter span {
  opacity: 0.28;
}

@media (max-width: 1320px) {
  .virtual-agent {
    min-height: auto;
  }

  .stage-shell {
    min-height: 24rem;
  }
}

@media (max-width: 760px) {
  .stage-shell {
    min-height: 20rem;
  }

  .voice-meter {
    bottom: 0.8rem;
  }
}

@keyframes portraitFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

@keyframes spin {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@keyframes spinReverse {
  from {
    transform: translate(-50%, -50%) rotate(360deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(0deg);
  }
}

@keyframes auraPulse {
  0%,
  100% {
    opacity: 0.88;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
}

@keyframes sweep {
  0%,
  100% {
    transform: translateY(-8%) rotate(-8deg);
    opacity: 0.2;
  }
  50% {
    transform: translateY(130%) rotate(-8deg);
    opacity: 0.55;
  }
}

@keyframes drift {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(12px, -8px, 0) scale(1.04);
  }
}

@keyframes blink {
  0%,
  45%,
  55%,
  100% {
    transform: scaleY(1);
  }
  48%,
  52% {
    transform: scaleY(0.18);
  }
}

@keyframes meter {
  0%,
  100% {
    height: 0.45rem;
  }
  40% {
    height: 1.58rem;
  }
  70% {
    height: 0.88rem;
  }
}

@keyframes mouthTalk {
  0%,
  100% {
    transform: scaleY(1);
    opacity: 0.75;
  }
  50% {
    transform: scaleY(1.35);
    opacity: 1;
  }
}

@keyframes twinkle {
  0%,
  100% {
    opacity: 0.35;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.18);
  }
}
</style>
