<template>
  <view class="video-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <view class="header">
      <view class="back" @tap="goBack"><u-icon name="arrow-left" size="34rpx" color="#2c3e50" /></view>
      <view class="title">{{ name || '监控视频' }}</view>
      <view class="placeholder"></view>
    </view>

    <view class="player-wrap" style="min-height: 480rpx;">
      <!-- #ifdef APP-PLUS || MP-WEIXIN -->
      <video
        v-if="playerVisible"
        :src="playUrl || video"
        :autoplay="true"
        :controls="true"
        :show-fullscreen-btn="true"
        :show-center-play-btn="false"
        :muted="true"
        object-fit="contain"
        class="player"
        style="width: 100%; height: 480rpx; display: block;"
        @play="onPlayerEvent('playing', $event)"
        @error="onPlayerEvent('error', $event)"
        @waiting="onPlayerEvent('waiting', $event)"
        @loadedmetadata="onPlayerEvent('loadedmetadata', $event)"
      ></video>
      <view class="player-overlay" v-if="playerStatus !== 'playing'">
        <view v-if="playerStatus !== 'playing'" class="player-state">
          <view class="state-title">{{ playerStatusText }}</view>
          <view class="state-url">当前地址：{{ playUrl || video || '未获取到视频地址' }}</view>
          <view v-if="streamProbeText" class="state-url">{{ streamProbeText }}</view>
          <view v-if="playerMessage" class="state-message">{{ playerMessage }}</view>
          <view v-if="streamCandidates.length > 1" class="state-url">
            候选 {{ currentStreamIndex + 1 }}/{{ streamCandidates.length }}
          </view>
        </view>
      </view>
      <!-- #endif -->
      <!-- #ifdef H5 -->
      <video
        v-if="playerVisible"
        :src="playUrl || video"
        :autoplay="true"
        :controls="true"
        :show-fullscreen-btn="true"
        class="player"
      ></video>
      <!-- #endif -->
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      statusBarHeight: 0,
      name: '',
      video: '',
      playUrl: '',
      streamCandidates: [],
      currentStreamIndex: 0,
      playerStatus: 'loading',
      playerMessage: '',
      streamProbeText: '',
      stallTimer: null,
      candidateTimer: null,
      playbackSeq: 0,
      playerVisible: true,
      pageActive: false,
    };
  },
  computed: {
    playerStatusText() {
      const textMap = {
        loading: '正在连接实时画面',
        ready: '播放器已就绪，正在拉流',
        playing: '实时画面播放中',
        loadedmetadata: '已读取视频信息，正在出画面',
        waiting: '正在缓冲实时画面',
        error: '实时画面加载失败',
      };
      return textMap[this.playerStatus] || '正在连接实时画面';
    },
    isHls() {
      return /\.m3u8($|[?#])/i.test(String(this.playUrl || this.video || ''));
    },
    isLive() {
      const currentUrl = this.playUrl || this.video;
      if (!currentUrl) return false;
      const url = String(currentUrl).toLowerCase();
      return url.includes('.flv') || url.startsWith('rtmp://');
    },
  },
  onLoad(query) {
    const info = uni.getWindowInfo();
    this.statusBarHeight = info.statusBarHeight || 20;
    this.name = decodeURIComponent(query.name || '');
    this.video = decodeURIComponent(query.video || '');
    this.streamCandidates = this.buildStreamCandidates(this.video);
    this.currentStreamIndex = 0;
    this.playUrl = this.streamCandidates[0] || this.video;
  },
  onReady() {
    this.pageActive = true;
    this.startPlaybackWatch();
  },
  onShow() {
    this.pageActive = true;
    if (!this.playerVisible) {
      this.playerVisible = true;
      this.startPlaybackWatch();
    }
  },
  onHide() {
    this.pageActive = false;
    this.playerVisible = false;
    this.clearPlaybackTimers();
  },
  onUnload() {
    this.pageActive = false;
    this.playerVisible = false;
    this.playbackSeq += 1;
    this.clearPlaybackTimers();
  },
  methods: {
    goBack() {
      uni.navigateBack();
    },
    onPlayerEvent(status, event) {
      if (!this.pageActive) return;
      this.playerStatus = status;
      this.playerMessage = this.formatEventDetail(event);
      if (status === 'playing' || status === 'loadedmetadata') {
        this.clearStallTimer();
      } else if (status === 'error') {
        this.scheduleNextCandidate('播放器报错，准备尝试备用地址');
      }
      console.log('[monitor-video]', status, this.playerMessage);
    },
    formatEventDetail(event) {
      if (!event) return '';
      const detail = event.detail || event;
      if (typeof detail === 'string') return detail;
      try {
        return JSON.stringify(detail);
      } catch (error) {
        return String(detail);
      }
    },
    buildStreamCandidates(url) {
      const value = String(url || '').trim();
      if (!value) return [];
      const candidates = [value];
      if (/\/raw\.flv($|[?#])/i.test(value)) {
        candidates.push(value.replace(/\/raw\.flv($|[?#].*)/i, '/raw.m3u8'));
        candidates.push(value.replace(/^http:\/\//i, 'rtmp://').replace(/:8080\/live\/raw\.flv($|[?#].*)/i, ':1935/live/raw'));
      }
      if (/\/raw\.m3u8($|[?#])/i.test(value)) {
        candidates.push(value.replace(/\/raw\.m3u8($|[?#].*)/i, '/raw.flv'));
        candidates.push(value.replace(/^http:\/\//i, 'rtmp://').replace(/:8080\/live\/raw\.m3u8($|[?#].*)/i, ':1935/live/raw'));
      }
      return [...new Set(candidates)];
    },
    async startPlaybackWatch() {
      const seq = ++this.playbackSeq;
      if (!this.pageActive) return;
      this.clearStallTimer();
      this.playerStatus = 'loading';
      this.playerMessage = '';
      await this.probeCurrentStream();
      if (seq !== this.playbackSeq || !this.pageActive) return;
      this.playerStatus = 'ready';
      this.playerMessage = this.playUrl;
      this.stallTimer = setTimeout(() => {
        if (seq !== this.playbackSeq || !this.pageActive) return;
        this.scheduleNextCandidate('8 秒内没有收到播放回调，准备尝试备用地址');
      }, 8000);
    },
    async probeCurrentStream() {
      if (!this.playUrl || !/^https?:\/\//i.test(this.playUrl)) {
        this.streamProbeText = '当前协议无法用 HTTP 探测';
        return;
      }
      if (!/\.m3u8($|[?#])/i.test(this.playUrl)) {
        this.streamProbeText = '备用 HTTP 流直接交给播放器尝试';
        return;
      }
      this.streamProbeText = '正在探测直播地址...';
      try {
        const res = await uni.request({
          url: this.playUrl,
          method: 'GET',
          timeout: 5000,
        });
        const response = Array.isArray(res) ? res[1] : res;
        if (!response) {
          this.streamProbeText = 'HTTP 探测没有返回响应';
          return;
        }
        const body = typeof response.data === 'string' ? response.data : JSON.stringify(response.data || '');
        const preview = body.replace(/\s+/g, ' ').slice(0, 80);
        this.streamProbeText = `HTTP ${response.statusCode || '-'}，响应 ${body.length || 0} 字节 ${preview ? `：${preview}` : ''}`;
      } catch (error) {
        this.streamProbeText = `HTTP 探测失败：${error && error.errMsg ? error.errMsg : String(error)}`;
      }
    },
    scheduleNextCandidate(reason) {
      if (!this.pageActive) return;
      this.clearStallTimer();
      if (this.currentStreamIndex >= this.streamCandidates.length - 1) {
        this.playerStatus = 'error';
        this.playerMessage = `${reason}，已尝试全部地址仍未播放`;
        return;
      }
      this.playerStatus = 'waiting';
      this.playerMessage = reason;
      this.clearCandidateTimer();
      const seq = this.playbackSeq;
      this.candidateTimer = setTimeout(() => {
        if (seq !== this.playbackSeq || !this.pageActive) return;
        this.currentStreamIndex += 1;
        this.playUrl = this.streamCandidates[this.currentStreamIndex];
        this.candidateTimer = null;
        this.startPlaybackWatch();
      }, 600);
    },
    clearStallTimer() {
      if (this.stallTimer) {
        clearTimeout(this.stallTimer);
        this.stallTimer = null;
      }
    },
    clearCandidateTimer() {
      if (this.candidateTimer) {
        clearTimeout(this.candidateTimer);
        this.candidateTimer = null;
      }
    },
    clearPlaybackTimers() {
      this.clearStallTimer();
      this.clearCandidateTimer();
    },
  },
};
</script>

<style scoped lang="scss">
.video-page {
  min-height: 100vh;
  background: #eef5fd;
  padding: 0 20rpx 30rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8rpx 0 16rpx;
}

.back, .placeholder {
  width: 52rpx;
  height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back {
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(205, 225, 246, 0.9);
  box-shadow: 0 10rpx 22rpx rgba(3, 20, 39, 0.16);
}

.title {
  font-size: 32rpx;
  color: #eaf7ff;
  font-weight: 700;
}

.player-wrap {
  border-radius: 20rpx;
  overflow: hidden;
  background: #000;
  position: relative;
}

.player {
  width: 100%;
  height: 480rpx;
}

.player-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28rpx;
  box-sizing: border-box;
  color: #dbeafe;
  text-align: center;
  pointer-events: none;
  background: rgba(0, 0, 0, 0.72);
}

.player-state {
  width: 100%;
}

.state-title {
  font-size: 28rpx;
  font-weight: 800;
}

.state-url,
.state-message {
  max-width: 100%;
  margin-top: 14rpx;
  font-size: 20rpx;
  line-height: 1.45;
  color: #93c5fd;
  word-break: break-all;
}

.state-message {
  color: #fca5a5;
}
</style>
