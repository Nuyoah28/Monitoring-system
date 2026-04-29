<template>
  <view class="main" :style="{ minHeight: safeHeight + 'px', height: safeHeight + 'px', paddingTop: statusBarHeight + 'px' }">
    <view class="header">
      <view class="top-nav">
        <view class="back-btn" @tap="goBack">
          <u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
        </view>
        <view class="list-btn" @tap="toggleSessionList">
          <image class="session-tag" src="/static/messagelist.png"></image>
        </view>
      </view>
      <text class="header-title">AI助手</text>
      <view class="setting-btn" @tap="jumpSetting">
        <image class="setting-tag" src="/static/settings.png"></image>
      </view>
    </view>

    <view class="session-drawer" :class="{ open: showSessionList }" @touchmove.stop.prevent>
      <view class="session-panel" @click.stop>
        <view class="session-panel-head">
          <text class="session-panel-title">消息列表</text>
          <view class="session-new" @tap="startNewSession">新建会话</view>
        </view>
        <scroll-view class="session-scroll" scroll-y>
          <view
            class="session-item"
            :class="item.id === currentSessionId ? 'active' : ''"
            v-for="item in sortedSessions"
            :key="item.id"
            @tap="switchSession(item.id)"
            @longpress.stop="onSessionLongPress(item.id)"
            @longtap.stop="onSessionLongPress(item.id)"
          >
            <view class="session-name">{{ getSessionTitle(item) }}</view>
            <view class="session-time">{{ formatSessionTime(item.updatedAt) }}</view>
          </view>
        </scroll-view>
      </view>
      <view class="session-peek" @tap="showSessionList = false"></view>
    </view>

    <view class="body" id="ai-body" :style="bodyStyle">
      <scroll-view :scroll-top="scrollTop" class="scroll" scroll-y @scroll="recordHeight" :style="{ height: scrollHeight + 'px' }">
        <view class="chat">
          <view id="msgbar" v-for="(item, index) in textList" :key="index" :class="getMessageRole(item, index) === 'assistant' ? 'left' : 'right'">
            <view class="avatar">
              <image :src="getMessageRole(item, index) === 'assistant' ? '/static/ai.png' : '/static/AIuser.png'"></image>
            </view>
            <view class="msg">
              <rich-text v-if="getMessageRole(item, index) === 'assistant'" class="msg-rich" :nodes="mdToHtml(getMessageText(item))"></rich-text>
              <view v-else>{{ getMessageText(item) }}</view>
            </view>
          </view>
          <view class="loading" v-show="isLoading">
            <view class="load-text"><text>智能生成中...</text></view>
          </view>
        </view>
      </scroll-view>

      <view class="down" id="ai-down">
        <view class="input-wrap">
          <input class="input-inner" type="text" v-model="text" placeholder="输入或点击麦克风说话" :disabled="isLoading" />
          <view class="btn-voice" :class="{ recording: isRecording }" @click="voiceClickHandler" :style="{ opacity: isLoading ? 0.6 : 1 }">
            <text class="btn-voice-text">{{ isRecording ? '停止' : '🎤' }}</text>
          </view>
          <view class="btn-send" :class="{ disabled: isDisabled }" @click="!isDisabled && send()">
            <text class="btn-send-text">发送</text>
          </view>
        </view>
        <view class="voice-tip" v-if="isRecording">正在录音，再次点击停止并发送</view>
        <view class="tts-bar" v-if="isTtsPlaying">
          <text class="tts-bar-text">语音播放中</text>
          <view class="btn-stop-tts" @click.stop="stopTtsPlayback">停止播放</view>
        </view>
      </view>
    </view>

    <owner-tabbar v-if="isOwnerApp" current="ai" />
  </view>
</template>

<script>
import wsRequest from '@/api/websocket.js';
import { AI_HTTP_URL, AI_WS_URL } from '@/common/config.js';
import Vue from 'vue';
import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';

const AI_WELCOME_MESSAGE = '你好，我是社区智眼 AI 助手。你可以问我报警处置、监控巡检、环境数据、车位检测相关的问题，我会尽量用简单清楚的方式帮你分析。';

export default {
  components: { OwnerTabbar },
  data() {
    return {
      isDisabled: false,
      safeHeight: 0,
      statusBarHeight: 0,
      text: '',
      answerText: '',
      textList: [],
      scrollTop: 0,
      newTop: 0,
      scrollHeight: 420,
      count: 0,
      websocket: null,
      cnt: 0,
      isLoading: false,
      agentBaseUrl: AI_HTTP_URL,
      isRecording: false,
      isTtsPlaying: false,
      recorderManager: null,
      innerAudioContext: null,
      showSessionList: false,
      sessions: [],
      currentSessionId: '',
      sessionLongPressLock: false,
    };
  },
  computed: {
    isOwnerApp() {
      return uni.getStorageSync('appType') === 'owner';
    },
    voiceClickHandler() {
      const self = this;
      return function () {
        try {
          if (self.isRecording) self.stopVoiceRecordAndSend();
          else self.startVoiceRecord();
        } catch (e) {
          uni.showToast({ title: '语音功能异常', icon: 'none' });
        }
      };
    },
    sortedSessions() {
      return [...this.sessions].sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
    },
    bodyStyle() {
      return {
        transform: this.showSessionList ? 'translateX(80%)' : 'translateX(0)',
      };
    },
  },
  onShow() {
    this.initLayout();
    this.loadSessionCache();
    if (!this.sessions.length) this.startNewSession();
    else this.switchSession(this.currentSessionId || this.sessions[0].id, false);
    this.createWs();
    this.$nextTick(() => {
      this.refreshScrollViewport(true);
    });
  },
  onReady() {
    this.$nextTick(() => {
      this.refreshScrollViewport(true);
    });
  },
  onHide() {
    this.closeWs();
  },
  onUnload() {
    this.closeWs();
  },
  methods: {
    initLayout() {
      const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
      const safeAreaHeight = info && info.safeArea && info.safeArea.height ? info.safeArea.height : info.windowHeight || info.screenHeight || 720;
      this.safeHeight = safeAreaHeight;
      this.statusBarHeight = (info && info.statusBarHeight) || 20;
      const header = 108;
      const input = this.isOwnerApp ? 180 : 128;
      this.scrollHeight = Math.max(260, safeAreaHeight - this.statusBarHeight - header - input);
    },
    refreshScrollViewport(scrollToBottom = false) {
      const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
      const safeAreaHeight = info && info.safeArea && info.safeArea.height ? info.safeArea.height : info.windowHeight || info.screenHeight || 720;
      this.safeHeight = safeAreaHeight;
      this.statusBarHeight = (info && info.statusBarHeight) || 20;
      this.$nextTick(() => {
        const query = uni.createSelectorQuery().in(this);
        query.select('#ai-body').boundingClientRect();
        query.select('#ai-down').boundingClientRect();
        query.exec((res) => {
          const body = res && res[0] ? res[0] : null;
          const down = res && res[1] ? res[1] : null;
          const baseHeight = body && body.height ? body.height : this.safeHeight - this.statusBarHeight - 108;
          const downHeight = down && down.height ? down.height : (this.isOwnerApp ? 180 : 128);
          this.scrollHeight = Math.max(220, Math.floor(baseHeight - downHeight));
          if (scrollToBottom) {
            this.$nextTick(() => this.toBottom());
          }
        });
      });
    },
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack();
        return;
      }
      if (this.isOwnerApp) {
        uni.reLaunch({ url: '/pages/owner/home/index' });
        return;
      }
      uni.switchTab({ url: '/pages/manage/controls/controls' });
    },
    loadSessionCache() {
      try {
        const cache = uni.getStorageSync('aiSessionCache');
        if (!cache) return;
        const parsed = typeof cache === 'string' ? JSON.parse(cache) : cache;
        if (parsed && Array.isArray(parsed.sessions)) {
          this.sessions = parsed.sessions;
          this.currentSessionId = parsed.currentSessionId || '';
        }
      } catch (e) {}
    },
    saveSessionCache() {
      try {
        uni.setStorageSync('aiSessionCache', {
          sessions: this.sessions,
          currentSessionId: this.currentSessionId,
        });
      } catch (e) {}
    },
    toggleSessionList() {
      this.showSessionList = !this.showSessionList;
    },
    startNewSession() {
      const id = String(Date.now());
      this.sessions.unshift({ id, title: '新会话', updatedAt: Date.now(), messages: [this.createWelcomeMessage()] });
      this.currentSessionId = id;
      this.textList = [this.createWelcomeMessage()];
      this.showSessionList = false;
      this.saveSessionCache();
      this.$nextTick(() => this.toBottom());
    },
    switchSession(id, closePanel = true) {
      if (this.sessionLongPressLock) return;
      const target = this.sessions.find((item) => item.id === id);
      if (!target) return;
      this.currentSessionId = id;
      const messages = Array.isArray(target.messages) ? [...target.messages] : [];
      this.textList = messages.length ? messages : [this.createWelcomeMessage()];
      if (!messages.length) target.messages = [...this.textList];
      if (closePanel) this.showSessionList = false;
      this.$nextTick(() => this.toBottom());
      this.saveSessionCache();
    },
    onSessionLongPress(id) {
      this.sessionLongPressLock = true;
      setTimeout(() => {
        this.sessionLongPressLock = false;
      }, 260);
      uni.showModal({
        title: '删除会话',
        content: '确认删除该聊天会话吗？',
        confirmColor: '#e15656',
        success: (res) => {
          if (res.confirm) this.deleteSession(id);
        },
      });
    },
    deleteSession(id) {
      const index = this.sessions.findIndex((item) => item.id === id);
      if (index < 0) return;
      const removedIsCurrent = this.sessions[index].id === this.currentSessionId;
      this.sessions.splice(index, 1);
      if (!this.sessions.length) {
        this.startNewSession();
        return;
      }
      if (removedIsCurrent) {
        const next = this.sortedSessions[0];
        if (next) this.switchSession(next.id, false);
      }
      this.saveSessionCache();
    },
    getSessionTitle(session) {
      if (!session || !Array.isArray(session.messages) || !session.messages.length) return (session && session.title) || '新会话';
      const firstUserMessage = session.messages.find((item, index) => this.getMessageRole(item, index) === 'user');
      const first = this.getMessageText(firstUserMessage).replace(/\s+/g, ' ').trim();
      if (!first) return session.title || '新会话';
      return first.length > 12 ? first.slice(0, 12) + '...' : first;
    },
    formatSessionTime(ts) {
      if (!ts) return '';
      const date = new Date(ts);
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const d = String(date.getDate()).padStart(2, '0');
      const h = String(date.getHours()).padStart(2, '0');
      const min = String(date.getMinutes()).padStart(2, '0');
      return `${m}-${d} ${h}:${min}`;
    },
    refreshCurrentSession() {
      const index = this.sessions.findIndex((item) => item.id === this.currentSessionId);
      if (index < 0) return;
      const messages = [...this.textList];
      const firstUserMessage = messages.find((item, msgIndex) => this.getMessageRole(item, msgIndex) === 'user');
      const first = this.getMessageText(firstUserMessage).replace(/\s+/g, ' ').trim();
      const title = first ? (first.length > 12 ? first.slice(0, 12) + '...' : first) : '新会话';
      Vue.set(this.sessions, index, { ...this.sessions[index], title, updatedAt: Date.now(), messages });
      this.saveSessionCache();
    },
    createWelcomeMessage() {
      return {
        role: 'assistant',
        type: 'welcome',
        content: AI_WELCOME_MESSAGE,
      };
    },
    getMessageText(item) {
      if (item == null) return '';
      if (typeof item === 'object') return String(item.content || item.text || '');
      return String(item);
    },
    getMessageRole(item, index) {
      if (item && typeof item === 'object' && item.role) return item.role;
      return index % 2 === 1 ? 'assistant' : 'user';
    },
    mdToHtml(str) {
      if (str == null || typeof str !== 'string') return '';
      let s = str;
      s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
      s = s.replace(/```[\s\S]*?```/g, (m) => {
        const text = m.replace(/^```\n?|```$/g, '').trim();
        return '<div class="md-code-block">' + text + '</div>';
      });
      s = s.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');
      s = s.replace(/^###\s+(.+)$/gm, '<div class="md-h3">$1</div>');
      s = s.replace(/^##\s+(.+)$/gm, '<div class="md-h2">$1</div>');
      s = s.replace(/^#\s+(.+)$/gm, '<div class="md-h1">$1</div>');
      s = s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/__(.+?)__/g, '<b>$1</b>');
      s = s.replace(/\*([^*]+)\*/g, '<i>$1</i>').replace(/_([^_]+)_/g, '<i>$1</i>');
      s = s.replace(/\n/g, '<br/>');
      return s;
    },
    createWs() {
      const token = uni.getStorageSync('token');
      if (!token) return;
      if (this.websocket && (this.websocket.is_open_socket || this.websocket.is_connecting)) return;
      this.closeWs();
      try {
        this.websocket = new wsRequest(`${AI_WS_URL}/api/v1/gpt/ws/${token}`, 5000);
      } catch (e) {
        return;
      }
      if (!this.websocket || typeof this.websocket.getMessage !== 'function') return;
      this.websocket.getMessage((res) => {
        const payload = typeof res.data === 'string' ? res.data.trim() : res.data;
        if (payload === 'ping' || payload === 'pong' || payload === '') return;
        this.cnt += 1;
        if (payload === '[REPLACE]') {
          this.answerText = '';
          Vue.set(this.textList, this.textList.length - 1, { role: 'assistant', content: '' });
          return;
        }
        this.isLoading = false;
        if (payload !== '[DONE]') this.answerText += payload;
        Vue.set(this.textList, this.textList.length - 1, { role: 'assistant', content: this.answerText });
        this.refreshCurrentSession();
        if (payload === '[DONE]') {
          this.isDisabled = false;
          if (this.answerText && this.answerText.trim()) this.requestTtsAndPlay(this.answerText.trim());
        }
        if (this.cnt >= 12) {
          this.toBottom();
          this.cnt = 0;
        }
      });
    },
    closeWs() {
      if (this.websocket && typeof this.websocket.close === 'function') {
        this.websocket.close();
      }
      this.websocket = null;
      this.isLoading = false;
      this.isDisabled = false;
    },
    jumpSetting() {
      if (this.isOwnerApp) {
        uni.reLaunch({ url: '/pages/owner/personal/index' });
        return;
      }
      uni.navigateTo({ url: '/pages/manage/personal/setting/setting' });
    },
    send() {
      const ask = (this.text || '').trim();
      if (!ask) {
        uni.showToast({ title: '请勿发送空消息', icon: 'none', duration: 1500 });
        return;
      }
      if (!this.websocket || !this.websocket.is_open_socket) {
        uni.showToast({ title: 'AI连接未就绪，请稍后再试', icon: 'none' });
        return;
      }
      this.cnt = 0;
      this.answerText = '';
      this.textList.push({ role: 'user', content: ask });
      this.toBottom();
      this.count += 1;
      const sent = this.getAnswer(ask);
      if (!sent) {
        this.textList.pop();
        uni.showToast({ title: 'AI连接未就绪，请稍后再试', icon: 'none' });
        return;
      }
      this.text = '';
      this.isLoading = true;
      this.isDisabled = true;
      this.refreshCurrentSession();
    },
    getAnswer(ask) {
      if (!this.websocket || typeof this.websocket.send !== 'function' || !this.websocket.is_open_socket) {
        this.isLoading = false;
        return false;
      }
      this.answerText = '';
      const sent = this.websocket.send(JSON.stringify(ask));
      if (!sent) {
        this.isLoading = false;
        return false;
      }
      this.textList.push({ role: 'assistant', content: this.answerText });
      this.toBottom();
      this.count += 1;
      this.refreshCurrentSession();
      return true;
    },
    recordHeight(e) {
      this.newTop = e.detail.scrollTop;
    },
    toBottom() {
      this.$nextTick(() => {
        const query = uni.createSelectorQuery().in(this);
        query
          .selectAll('#msgbar')
          .boundingClientRect((data) => {
            const elements = Array.from(data || []);
            if (!elements.length) return;
            this.scrollTop = elements[elements.length - 1].bottom - elements[0].bottom;
          })
          .exec();
      });
    },
    onVoiceClick() {
      try {
        if (this.isRecording) this.stopVoiceRecordAndSend();
        else this.startVoiceRecord();
      } catch (e) {
        uni.showToast({ title: '语音功能异常', icon: 'none' });
      }
    },
    toggleVoice() {
      this.onVoiceClick();
    },
    startVoiceRecord() {
      try {
        if (typeof uni.authorize === 'function') {
          uni.authorize({
            scope: 'scope.record',
            success: () => this.doStartRecord(),
            fail: () => {
              uni.showModal({
                title: '需要麦克风权限',
                content: '请在设置中允许使用麦克风，用于语音输入',
                confirmText: '去设置',
                success: (res) => {
                  if (res.confirm && typeof uni.openSetting === 'function') uni.openSetting();
                },
              });
            },
          });
        } else this.doStartRecord();
      } catch (e) {
        uni.showToast({ title: '录音不可用', icon: 'none' });
      }
    },
    doStartRecord() {
      try {
        if (typeof uni.getRecorderManager !== 'function') {
          uni.showToast({ title: '当前环境不支持录音', icon: 'none' });
          return;
        }
        const rm = uni.getRecorderManager();
        if (!rm || typeof rm.start !== 'function') {
          uni.showToast({ title: '当前环境不支持录音', icon: 'none' });
          return;
        }
        this.recorderManager = rm;
        if (typeof rm.onStart === 'function') rm.onStart(() => (this.isRecording = true));
        if (typeof rm.onStop === 'function') rm.onStop((res) => {
          this.isRecording = false;
          if (res && res.tempFilePath) this.sendVoiceToAgent(res.tempFilePath);
          else uni.showToast({ title: '录音失败', icon: 'none' });
        });
        if (typeof rm.onError === 'function') rm.onError(() => {
          this.isRecording = false;
          uni.showToast({ title: '录音错误', icon: 'none' });
        });
        try {
          rm.start({ duration: 60000, format: 'wav', sampleRate: 16000, numberOfChannels: 1 });
        } catch (e) {
          rm.start({ duration: 60000 });
        }
      } catch (e) {
        uni.showToast({ title: '录音不可用，请使用 App 或小程序', icon: 'none' });
      }
    },
    stopVoiceRecordAndSend() {
      if (this.recorderManager) {
        this.recorderManager.stop();
        this.recorderManager = null;
      }
    },
    sendVoiceToAgent(tempFilePath) {
      const token = uni.getStorageSync('token') || '';
      this.isLoading = true;
      uni.uploadFile({
        url: this.agentBaseUrl + '/chat/voice',
        filePath: tempFilePath,
        name: 'audio',
        header: token ? { Authorization: 'Bearer ' + token } : {},
        formData: { return_tts: 'true' },
        success: (res) => {
          try {
            if (res.statusCode && res.statusCode !== 200) {
              uni.showToast({ title: '服务异常 ' + (res.statusCode || ''), icon: 'none' });
              this.isLoading = false;
              return;
            }
            const raw = res.data;
            const data = typeof raw === 'string' ? JSON.parse(raw || '{}') : raw || {};
            if (data.code !== '00000' || !data.data) {
              uni.showToast({ title: data.message || '请求失败', icon: 'none' });
              this.isLoading = false;
              return;
            }
            const { question: recognized, answer } = data.data;
            this.textList.push({ role: 'user', content: recognized || '(语音)' });
            this.textList.push({ role: 'assistant', content: answer || '' });
            this.refreshCurrentSession();
            this.refreshScrollViewport(true);
            if (answer && answer.trim()) this.requestTtsAndPlay(answer.trim());
          } catch (e) {
            uni.showToast({ title: '解析失败，请确认 Agent 已启动', icon: 'none' });
          }
          this.isLoading = false;
        },
        fail: () => {
          uni.showToast({ title: '网络异常', icon: 'none' });
          this.isLoading = false;
        },
      });
    },
    playTtsByPlayUrl(playUrl) {
      if (!playUrl) return;
      this.stopTtsPlayback();
      if (typeof uni.createInnerAudioContext !== 'function') {
        uni.showToast({ title: '当前环境不支持语音播放', icon: 'none' });
        return;
      }
      const ctx = uni.createInnerAudioContext();
      this.innerAudioContext = ctx;
      ctx.obeysMuteSwitch = false;
      ctx.src = playUrl;
      ctx.onPlay(() => {
        this.isTtsPlaying = true;
        this.refreshScrollViewport(true);
      });
      ctx.onEnded(() => {
        this.isTtsPlaying = false;
        this.innerAudioContext = null;
        this.refreshScrollViewport(true);
      });
      ctx.onError(() => {
        this.isTtsPlaying = false;
        this.innerAudioContext = null;
        this.refreshScrollViewport(true);
        uni.showToast({ title: '语音播放失败', icon: 'none' });
      });
      ctx.play();
    },
    requestTtsAndPlay(text) {
      if (!text || !this.agentBaseUrl) return;
      const token = uni.getStorageSync('token') || '';
      uni.request({
        url: this.agentBaseUrl + '/tts/audio',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: 'Bearer ' + token } : {}),
        },
        data: { text },
        success: (res) => {
          if (res.statusCode === 200 && res.data && res.data.code === '00000' && res.data.data && res.data.data.play_url) {
            this.playTtsByPlayUrl(res.data.data.play_url);
          }
        },
      });
    },
    stopTtsPlayback() {
      if (this.innerAudioContext) {
        try {
          if (typeof this.innerAudioContext.stop === 'function') this.innerAudioContext.stop();
          if (typeof this.innerAudioContext.destroy === 'function') this.innerAudioContext.destroy();
        } catch (e) {}
        this.innerAudioContext = null;
      }
      this.isTtsPlaying = false;
      this.refreshScrollViewport(true);
    },
  },
  watch: {
    count: {
      handler() {
        this.scrollTop = this.newTop;
      },
    },
    isRecording() {
      this.refreshScrollViewport(true);
    },
    isTtsPlaying() {
      this.refreshScrollViewport(true);
    },
  },
};
</script>

<style lang="scss">
.main {
  width: 100%;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  background:
    radial-gradient(1200rpx 520rpx at 12% -5%, rgba(89, 171, 255, 0.3) 0%, rgba(89, 171, 255, 0) 70%),
    radial-gradient(1000rpx 460rpx at 92% 8%, rgba(0, 210, 255, 0.2) 0%, rgba(0, 210, 255, 0) 72%),
    linear-gradient(180deg, #deedfb 0%, #ebf5ff 46%, #f4f9ff 100%);
}

.header {
  position: relative;
  z-index: 20;
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40rpx;
  box-sizing: border-box;
  height: 100rpx;
  margin-bottom: 8rpx;
}

.top-nav {
  display: flex;
  align-items: center;
}

.back-btn,
.list-btn {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 122, 255, 0.15);
  width: 66rpx;
  height: 66rpx;
  border-radius: 18rpx;
  box-shadow: 0 8rpx 20rpx rgba(0, 122, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-btn {
  margin-left: 16rpx;
  z-index: 1200;
  padding: 10rpx;
  box-sizing: border-box;
}

.session-tag {
  width: 44rpx;
  height: 44rpx;
  object-fit: contain;
}

.header-title {
  color: #51678f;
  font-size: 40rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
}

.setting-btn {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  justify-content: center;
  align-items: center;
}

.setting-tag {
  width: 48rpx;
  height: 48rpx;
  object-fit: contain;
}

.session-drawer {
  position: fixed;
  left: 0;
  top: calc(100rpx + env(safe-area-inset-top));
  width: 100%;
  height: calc(100% - 100rpx - env(safe-area-inset-top));
  z-index: 1100;
  display: flex;
  pointer-events: none;
}

.session-drawer.open {
  pointer-events: auto;
}

.session-panel {
  width: 80%;
  height: 100%;
  background: rgba(245, 250, 255, 0.98);
  border-right: 1px solid rgba(38, 108, 232, 0.18);
  box-shadow: 12rpx 0 30rpx rgba(16, 60, 130, 0.16);
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 260ms ease;
}

.session-drawer.open .session-panel {
  transform: translateX(0);
}

.session-peek {
  width: 20%;
  height: 100%;
}

.session-panel-head {
  height: 86rpx;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(0, 122, 255, 0.12);
}

.session-panel-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #1f3760;
}

.session-new {
  height: 54rpx;
  line-height: 54rpx;
  padding: 0 18rpx;
  border-radius: 27rpx;
  font-size: 24rpx;
  font-weight: 600;
  color: #215fca;
  background: rgba(86, 144, 255, 0.16);
}

.session-scroll {
  flex: 1;
}

.session-item {
  padding: 18rpx 24rpx;
  border-bottom: 1px solid rgba(0, 122, 255, 0.08);
}

.session-item.active {
  background: linear-gradient(90deg, rgba(88, 147, 255, 0.16) 0%, rgba(88, 147, 255, 0.06) 100%);
}

.session-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #243a5e;
}

.session-time {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #7990b3;
}

.body {
  position: relative;
  z-index: 10;
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 260ms ease;
}

.scroll {
  width: 100%;
  flex: 1;
  min-height: 0;
}

.chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6rpx 0 12rpx;
}

.left,
.right {
  width: 95%;
  margin-bottom: 18rpx;
  display: flex;
  align-items: flex-start;
}

.right {
  flex-direction: row-reverse;
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  background-color: #fff;
  border-radius: 50%;
}

.avatar image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.msg {
  margin-top: 15rpx;
  max-width: 70%;
  box-sizing: border-box;
  padding: 16rpx 20rpx;
  border-radius: 24rpx;
}

.left .msg {
  background: rgba(255, 255, 255, 0.9);
  margin-left: 20rpx;
}

.right .msg {
  background: linear-gradient(135deg, #3f78ff 0%, #5b9cff 100%);
  margin-right: 20rpx;
}

.msg view,
.msg-rich {
  word-break: break-all;
  word-wrap: break-word;
}

.right .msg view {
  color: #fff;
}

.loading {
  margin-top: 8rpx;
}

.load-text text {
  color: #5f759a;
  font-size: 24rpx;
}

.down {
  width: 100%;
  flex-shrink: 0;
  margin-top: auto;
  padding: 16rpx 24rpx 24rpx;
  border-top: 1px solid rgba(0, 122, 255, 0.12);
  box-sizing: border-box;
}

.input-wrap {
  width: 93%;
  max-width: 680rpx;
  height: 88rpx;
  display: flex;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 44rpx;
  overflow: hidden;
  padding: 0 8rpx 0 28rpx;
  box-sizing: border-box;
  margin: 0 auto;
}

.input-inner {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
}

.btn-voice {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background-color: #e6eeff;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-left: 12rpx;
}

.btn-voice.recording {
  width: 100rpx;
  border-radius: 36rpx;
  background-color: #f56c6c;
}

.btn-send {
  height: 72rpx;
  min-width: 120rpx;
  padding: 0 28rpx;
  margin-left: 12rpx;
  border-radius: 36rpx;
  background: linear-gradient(90deg, #2f73ff 0%, #4d8dff 100%);
  display: flex;
  justify-content: center;
  align-items: center;
}

.btn-send-text,
.btn-voice-text {
  color: #fff;
  font-size: 28rpx;
}

.voice-tip,
.tts-bar {
  margin-top: 10rpx;
  text-align: center;
}

.tts-bar-text {
  margin-right: 16rpx;
}

.main.owner-app .down {
  padding-bottom: calc(130rpx + env(safe-area-inset-bottom));
}
</style>
