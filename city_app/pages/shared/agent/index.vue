<template>
	<view class="main" :class="{ 'owner-app': isOwnerApp }" :style="{ minHeight: safeHeight + 'px', height: safeHeight + 'px', paddingTop: statusBarHeight + 'px', '--status-bar-height': statusBarHeight + 'px' }">
		<view class="header" id="ai-header">
			<view class="topNav">
				<view class="back-btn" @tap="goBack">
					<u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
				</view>
				<view class="choosen" @tap="toggleSessionList">
					<image class="session-tag" src="/static/messagelist.png"></image>
				</view>
			</view>
		<view class="header-title">
				<text>{{ isOwnerApp ? '社区助手' : 'AI助手' }}</text>
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
						<view class="session-content">
							<view class="session-name">{{ getSessionTitle(item) }}</view>
							<view class="session-time">{{ formatSessionTime(item.updatedAt) }}</view>
						</view>
						<view class="session-delete" @tap.stop="onSessionLongPress(item.id)">删除</view>
					</view>
				</scroll-view>
			</view>
			<view class="session-peek" @tap="showSessionList = false"></view>
		</view>
		<view class="body" id="ai-body" :class="{ 'chat-open': showChatPanel }" :style="bodyStyle">
			<view class="agent-fallback-card" v-if="visualFallback">
					<view class="fallback-avatar">助</view>
					<view class="fallback-title">社区助手已就绪</view>
					<view class="fallback-sub">当前使用简化模式，仍可继续对话</view>
				</view>
				<virtual-agent-card v-else :state="agentState" :status-text="agentStatusText" :subtitle="agentStatusSubText" :fit-scale="0.88" @tap="handleAgentTap" @failed="handleVisualFailed" />
				<view class="assistant-dock">
					<view class="assistant-dock-title">{{ isOwnerApp ? '社区助手' : 'AI助手' }}</view>
					<view class="assistant-chip-row">
						<view class="assistant-chip">提醒</view>
						<view class="assistant-chip">环境</view>
						<view class="assistant-chip">停车</view>
						<view class="assistant-chip">事项</view>
					</view>
				</view>

			<view class="floating-dialog" v-if="latestUserText || latestAssistantText">
				<view class="floating-bubble user-bubble" v-if="latestUserText">
					<text>{{ latestUserText }}</text>
				</view>
				<view class="floating-bubble assistant-bubble" v-if="latestAssistantText">
					<text>{{ latestAssistantText }}</text>
				</view>
			</view>

			<view class="chat-toggle" @tap="toggleChatPanel">
				<text>{{ showChatPanel ? '收起对话' : '对话记录' }}</text>
			</view>
			<view class="chat-mask" v-if="showChatPanel" @tap="showChatPanel = false"></view>
			<view class="chat-panel" :class="{ open: showChatPanel }" @tap.stop>
				<view class="chat-panel-head">
					<text class="chat-panel-title">对话记录</text>
					<text class="chat-panel-close" @tap="showChatPanel = false">收起</text>
				</view>
				<scroll-view :scroll-top="scrollTop" class="scroll chat-scroll" scroll-y @scroll="recordHeight" :style="{ height: scrollHeight + 'px' }">
					<view class="chat">
						<view id="msgbar" v-for="(item, index) in textList" :key="index" :class="getMessageRole(item, index) === 'assistant' ? 'left' : 'right'">
							<view class="avatar">
								<image :src="getMessageRole(item, index) === 'assistant' ? '/static/ai.png' : '/static/AIuser.png' "></image>
							</view>
							<view class="msg">
								<rich-text v-if="getMessageRole(item, index) === 'assistant'" class="msg-rich" :nodes="mdToHtml(getMessageText(item))"></rich-text>
								<view v-else>{{ getMessageText(item) }}</view>
							</view>
						</view>
						<view class="loading" v-show="isLoading">
							<view class="loadText">
								<text>智能生成中...</text>
							</view>
							<view class="spinner">
								<view></view>
								<view></view>
								<view></view>
								<view></view>
								<view></view>
								<view></view>
							</view>
						</view>
					</view>
				</scroll-view>
			</view>
			<view class="down" id="ai-down">
				<view class="input-wrap">
					<input class="input-inner" type="text" v-model="text" placeholder="输入问题，或点击麦克风对话" :disabled="isLoading" />
					<view class="btn-voice" :class="{ recording: isRecording }" @click="voiceClickHandler" :style="{ opacity: isLoading ? 0.6 : 1 }">
						<text class="btn-voice-text">{{ isRecording ? '停止' : '🎤' }}</text>
					</view>
					<view class="btn-send" :class="{ disabled: isDisabled }" @click="!isDisabled && send()">
						<text class="btn-send-text">发送</text>
					</view>
				</view>
				<view class="voice-tip" v-if="isRecording || isVoiceProcessing">{{ isVoiceProcessing ? '语音已发送，正在识别，请稍等' : '正在聆听，再次点击即可发送' }}</view>
				<view class="tts-bar" v-if="isTtsPlaying">
					<text class="tts-bar-text">正在为你播报</text>
					<view class="btn-stop-tts" @click.stop="stopTtsPlayback">停止播放</view>
				</view>
			</view>
		</view>
		<owner-tabbar v-if="isOwnerApp" current="ai" />
	</view>
</template>

<script>
import wsRequest from '@/api/websocket.js'
import { AI_HTTP_URL, AI_WS_URL } from '@/common/config.js'
import Vue from 'vue';
	import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';
	import VirtualAgentCard from '@/components/VirtualAgentCard.vue';

	const AI_WELCOME_MESSAGE = '你好，我是社区助手。你可以问我社区提醒、环境数据、停车服务和日常事项，我会尽量用简单清楚的方式帮你说明。';

	export default {
		components: {
			OwnerTabbar,
			VirtualAgentCard,
		},
		data() {
			return {
				isDisabled:false,
				safeHeight:0,
				statusBarHeight:0,
				text: "",
				answerText: "",
				textList:[],
				scrollTop:0,
				newTop:0,
				scrollHeight:420,
				count:0,
				websocket: null,
				cnt: 0,
				isLoading: false,
				// 语音
				agentBaseUrl: AI_HTTP_URL,
				isRecording: false,
				isVoiceProcessing: false,
				isTtsPlaying: false,
				voiceRecordStartAt: 0,
				recorderManager: null,
				innerAudioContext: null,
				ttsDownloadTask: null,
				ttsPlaybackToken: 0,
				showSessionList: false,
				showChatPanel: false,
				visualFallback: false,
				visualFallbackTimer: null,
				sessions: [],
				currentSessionId: '',
				sessionLongPressLock: false,
			}
		},
		onShow() {
			const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
			const safeAreaHeight = info && info.safeArea && info.safeArea.height
				? info.safeArea.height
				: (info.windowHeight || info.screenHeight || 0);
			this.safeHeight = safeAreaHeight;
			this.statusBarHeight = (info && info.statusBarHeight) || 20;
				this.scrollHeight = Math.max(260, safeAreaHeight - this.statusBarHeight - (this.isOwnerApp ? 210 : 150) - 140);
				this.$nextTick(() => {
					this.refreshScrollViewport(true);
				});
			this.loadSessionCache();
			if (!this.sessions.length) {
				this.startNewSession();
			} else {
				const defaultId = this.currentSessionId || this.sessions[0].id;
				this.switchSession(defaultId, false);
			}
			try {
				this.createWs();
			} catch (e) {
				this.isLoading = false;
			}
			this.scheduleVisualFallback();
		},
		onReady() {
			this.$nextTick(() => {
				this.refreshScrollViewport(true);
			});
		},
			onHide() {
				this.stopAllVoiceAndTts();
				this.closeWs();
				this.clearVisualFallbackTimer();
			},
			onUnload() {
				this.stopAllVoiceAndTts();
				this.closeWs();
				this.clearVisualFallbackTimer();
			},
			beforeDestroy() {
				this.stopAllVoiceAndTts();
				this.closeWs();
				this.clearVisualFallbackTimer();
			},
	computed: {
		isOwnerApp() {
			return uni.getStorageSync('appType') === 'owner';
		},
		sessionCacheKey() {
			const appType = uni.getStorageSync('appType') || 'manage';
			const userId = uni.getStorageSync('userId') || 'anonymous';
			return `aiSessionCache:${appType}:${userId}`;
		},
		voiceClickHandler() {
			const self = this;
				return function() {
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
			latestUserText() {
				if (this.isRecording) return '正在聆听...';
				if (this.isVoiceProcessing) return '语音已收到，正在整理...';
				for (let i = this.textList.length - 1; i >= 0; i -= 1) {
					const item = this.textList[i];
					if (this.getMessageRole(item, i) === 'user') {
						const text = this.getMessageText(item).replace(/\s+/g, ' ').trim();
						if (text) return this.trimFloatingText(text, 42);
					}
				}
				return '';
			},
			latestAssistantText() {
				const text = this.getLatestAssistantContent();
				if (text) return this.trimFloatingText(text, 62);
				if (this.isVoiceProcessing) return '请稍等，我正在识别语音';
				if (this.isLoading || this.isDisabled) return '正在思考，请稍等';
				return '';
			},
			bodyStyle() {
				return {};
			},
			agentState() {
				if (this.isTtsPlaying) return 'speaking';
				if (this.isRecording) return 'listening';
				if (this.isLoading || this.isDisabled) return 'thinking';
				return 'idle';
			},
			agentStatusText() {
				const map = {
					idle: '随时待命',
					listening: '我在听',
					thinking: '正在思考',
					speaking: '为你播报',
				};
				return map[this.agentState] || map.idle;
			},
			agentStatusSubText() {
				const map = {
					idle: '可以询问报警、巡检、环境与车位信息',
					listening: '说完后再次点击麦克风即可发送',
					thinking: '正在整理社区数据与建议',
					speaking: '正在用语音为你说明结果',
				};
				return map[this.agentState] || map.idle;
			},
		},
		methods:{
			goBack() {
				if (getCurrentPages().length > 1) {
					uni.navigateBack();
				} else {
					this.goHomeByAppType();
				}
			},
			goHomeByAppType() {
				if (this.isOwnerApp) {
					uni.reLaunch({ url: '/pages/owner/home/index' });
					return;
				}
				uni.reLaunch({ url: '/pages/manage/controls/controls' });
			},
    loadSessionCache() {
      try {
        const cache = uni.getStorageSync(this.sessionCacheKey);
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
        uni.setStorageSync(this.sessionCacheKey, {
          sessions: this.sessions,
          currentSessionId: this.currentSessionId,
        });
				} catch (e) {}
			},
			toggleSessionList() {
				this.showSessionList = !this.showSessionList;
				if (this.showSessionList) this.showChatPanel = false;
			},
			toggleChatPanel() {
				this.showChatPanel = !this.showChatPanel;
				if (this.showChatPanel) {
					this.showSessionList = false;
					this.refreshScrollViewport(true);
				}
			},
			handleAgentTap() {
				if (this.isRecording) {
					uni.showToast({ title: '我在听，请继续说', icon: 'none' });
					return;
				}
				if (this.isLoading) {
					uni.showToast({ title: '正在思考，请稍等', icon: 'none' });
					return;
				}
				if (this.isTtsPlaying) {
					uni.showToast({ title: '正在为你播报', icon: 'none' });
					return;
				}
				uni.showToast({ title: '有什么可以帮你？', icon: 'none' });
			},
			handleVisualFailed() {
				this.visualFallback = true;
				this.clearVisualFallbackTimer();
			},
			stopAllVoiceAndTts() {
				this.ttsPlaybackToken += 1;
				if (this.ttsDownloadTask && typeof this.ttsDownloadTask.abort === 'function') {
					try { this.ttsDownloadTask.abort(); } catch (e) {}
				}
				this.ttsDownloadTask = null;
				if (this.innerAudioContext) {
					try {
						if (typeof this.innerAudioContext.stop === 'function') this.innerAudioContext.stop();
						if (typeof this.innerAudioContext.destroy === 'function') this.innerAudioContext.destroy();
					} catch (e) {}
					this.innerAudioContext = null;
				}
				if (this.recorderManager && typeof this.recorderManager.stop === 'function') {
					try { this.recorderManager.stop(); } catch (e) {}
				}
				this.recorderManager = null;
				this.voiceRecordStartAt = 0;
				this.isRecording = false;
				this.isVoiceProcessing = false;
				this.isTtsPlaying = false;
			},
			scheduleVisualFallback() {
				this.clearVisualFallbackTimer();
				this.visualFallback = false;
				this.visualFallbackTimer = setTimeout(() => {
					this.visualFallback = true;
				}, 2600);
			},
			clearVisualFallbackTimer() {
				if (this.visualFallbackTimer) {
					clearTimeout(this.visualFallbackTimer);
					this.visualFallbackTimer = null;
				}
			},
			startNewSession() {
				const id = String(Date.now());
				this.sessions.unshift({
					id,
					title: '新会话',
					updatedAt: Date.now(),
					messages: [this.createWelcomeMessage()],
				});
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
					}
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
				if (!session || !Array.isArray(session.messages) || !session.messages.length) return session && session.title ? session.title : '新会话';
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
				Vue.set(this.sessions, index, {
					...this.sessions[index],
					title,
					updatedAt: Date.now(),
					messages,
				});
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
			trimFloatingText(text, limit) {
				return text.length > limit ? text.slice(0, limit) + '...' : text;
			},
			getLatestAssistantContent() {
				for (let i = this.textList.length - 1; i >= 0; i -= 1) {
					const item = this.textList[i];
					if (this.getMessageRole(item, i) === 'assistant' && item.type !== 'welcome') {
						const text = this.getMessageText(item).replace(/\s+/g, ' ').trim();
						if (text) return text;
					}
				}
				return '';
			},
			// 将 Markdown 转为富文本可用的 HTML，去掉符号并保留排版
			mdToHtml(str) {
				if (str == null || typeof str !== 'string') return ''
				let s = str
				// 先转义 HTML
				s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
				// 代码块 ```...```（多行）
				s = s.replace(/```[\s\S]*?```/g, (m) => {
					const text = m.replace(/^```\n?|```$/g, '').trim()
					return '<div class="md-code-block">' + text + '</div>'
				})
				// 行内代码 `...`
				s = s.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
				// ### 标题
				s = s.replace(/^###\s+(.+)$/gm, '<div class="md-h3">$1</div>')
				s = s.replace(/^##\s+(.+)$/gm, '<div class="md-h2">$1</div>')
				s = s.replace(/^#\s+(.+)$/gm, '<div class="md-h1">$1</div>')
				// **粗体** __粗体__
				s = s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
				s = s.replace(/__(.+?)__/g, '<b>$1</b>')
				// *斜体* _斜体_
				s = s.replace(/\*([^*]+)\*/g, '<i>$1</i>')
				s = s.replace(/_([^_]+)_/g, '<i>$1</i>')
				// 换行
				s = s.replace(/\n/g, '<br/>')
				return s
			},
			createWs() {
				if (!wsRequest) {
					console.warn('[AIPage] wsRequest not available');
					return;
				}
				let token = uni.getStorageSync('token')
				if (!token) {
					console.warn('[AIPage] token missing, skip websocket');
					return;
				}
				if (this.websocket && (this.websocket.is_open_socket || this.websocket.is_connecting)) return;
				this.closeWs();
				this.websocket = new wsRequest(`${AI_WS_URL}/api/v1/gpt/ws/${token}`,5000) // Python Agent
				if (!this.websocket || typeof this.websocket.getMessage !== 'function') {
					console.warn('[AIPage] websocket instance invalid', this.websocket);
					return;
				}
				this.websocket.getMessage(res => {
					const payload = typeof res.data === 'string' ? res.data.trim() : res.data;
					if (payload === 'ping' || payload === 'pong' || payload === '') return;
					// console.log('res=',res.data)
					// console.log('textList=',this.textList[this.textList.length-1])
					this.cnt ++;
					if (payload === "[REPLACE]") {
						this.answerText = '';
						Vue.set(this.textList, this.textList.length - 1, { role: 'assistant', content: '' });
						return;
					}
					this.isLoading = false;
					if(payload !== "[DONE]"){
						this.answerText += payload;
					}
					Vue.set(this.textList , this.textList.length-1 , { role: 'assistant', content: this.answerText })
					this.refreshCurrentSession();
					if(payload === "[DONE]") {
						this.isDisabled = false;
						// 文字回复也播放语音（与 Web 端体验一致）
						if (this.answerText && this.answerText.trim()) {
							this.requestTtsAndPlay(this.answerText.trim());
						}
					}
					if (this.cnt == 12) {
						this.toBottom();
						this.cnt = 0;
					}
				})
			},
			closeWs() {
				if (this.websocket && typeof this.websocket.close === 'function') {
					this.websocket.close();
				}
				this.websocket = null;
				this.isLoading = false;
				this.isVoiceProcessing = false;
				this.isDisabled = false;
				this.clearVisualFallbackTimer();
			},
			refreshScrollViewport(scrollToBottom = false) {
				const info = typeof uni.getWindowInfo === 'function' ? uni.getWindowInfo() : uni.getSystemInfoSync();
				const safeAreaHeight = info && info.safeArea && info.safeArea.height
					? info.safeArea.height
					: (info.windowHeight || info.screenHeight || 0);
				this.safeHeight = safeAreaHeight;
				this.$nextTick(() => {
					const query = uni.createSelectorQuery().in(this);
					query.select('#ai-body').boundingClientRect();
					query.select('#ai-down').boundingClientRect();
					query.exec((res) => {
						const body = res[0];
						const down = res[1];
						if (body && down) {
							this.scrollHeight = Math.max(260, Math.floor((body.height || 0) - (down.height || 0) - 140));
						} else {
							this.scrollHeight = Math.max(260, this.safeHeight - this.statusBarHeight - (this.isOwnerApp ? 210 : 150) - 140);
						}
						if (scrollToBottom) {
							this.$nextTick(() => this.toBottom());
						}
					});
				});
			},
			send(){
				const ask = (this.text || '').trim();
				if(ask == ""){
					uni.showToast({
						title: '请勿发送空消息',
						icon: 'none',
						duration: 1500
					})  
				}
				else if (!this.websocket || !this.websocket.is_open_socket) {
					uni.showToast({
						title: '助手正在准备，请稍后再试',
						icon: 'none',
						duration: 1500
					})
				}
				else {
					// console.log("输入的消息为：" + this.text);
					this.cnt = 0;
					this.answerText = "";
					this.textList.push({ role: 'user', content: ask });
					this.toBottom();
					this.count ++;
					const sent = this.getAnswer(ask);
					if (!sent) {
						this.textList.pop();
						uni.showToast({
							title: '助手正在准备，请稍后再试',
							icon: 'none',
							duration: 1500
						});
						return;
					}
					this.text = "";
					// this.isDisabled = true;
					this.isLoading = true;
					this.isDisabled = true;
					this.refreshCurrentSession();
				}	
			},
			getClientTime() {
				const now = new Date();
				const pad = (num) => String(num).padStart(2, '0');
				return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
			},
			getAnswer(ask){
				if (!this.websocket || typeof this.websocket.send !== 'function' || !this.websocket.is_open_socket) {
					this.isLoading = false;
					return false;
				}
				// this.isLeft = 1;
				this.answerText = ""
				const sent = this.websocket.send(JSON.stringify({ question: ask, client_time: this.getClientTime() }));
				if (!sent) {
					this.isLoading = false;
					return false;
				}
				this.textList.push({ role: 'assistant', content: this.answerText });
				this.toBottom();
				this.count ++ ;
				this.refreshCurrentSession();
				return true;
			},
			recordHeight(e) {
				this.newTop = e.detail.scrollTop;
			},
			toBottom() {
				this.$nextTick(() => {
					this.query = uni.createSelectorQuery().in(this);
					this.query
					.selectAll("#msgbar")
					.boundingClientRect((data) => {
						// console.log(data);
						const elements = Array.from(data);
						// console.log("elements");
						// console.log(elements);
						if (!elements.length) return;
						let index = elements.length - 1;
						this.scrollTop = elements[index].bottom - elements[0].bottom;
					})
					.exec();
					this.query = null;
				});
			},
			// 语音输入（安全包装，避免 handler 为 undefined 报错）
			onVoiceClick() {
				try {
					if (this.isRecording) {
						this.stopVoiceRecordAndSend();
					} else {
						this.startVoiceRecord();
					}
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
							success: () => { this.doStartRecord(); },
							fail: () => {
								uni.showModal({
									title: '需要麦克风权限',
									content: '请在设置中允许使用麦克风，用于语音输入',
									confirmText: '去设置',
									success: (res) => {
										if (res.confirm && typeof uni.openSetting === 'function') uni.openSetting();
									}
								});
							}
						});
					} else {
						this.doStartRecord();
					}
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
					if (typeof rm.onStart === 'function') rm.onStart(() => {
						this.voiceRecordStartAt = Date.now();
						this.isRecording = true;
					});
					if (typeof rm.onStop === 'function') {
						rm.onStop((res) => {
							this.isRecording = false;
							const duration = this.voiceRecordStartAt ? Date.now() - this.voiceRecordStartAt : 0;
							this.voiceRecordStartAt = 0;
							if (duration && duration < 800) {
								uni.showToast({ title: '说话时间太短，请重新录音', icon: 'none' });
								return;
							}
							if (res && res.tempFilePath) this.sendVoiceToAgent(res.tempFilePath);
							else uni.showToast({ title: '录音失败', icon: 'none' });
						});
					}
					if (typeof rm.onError === 'function') {
						rm.onError((err) => {
							this.isRecording = false;
							this.voiceRecordStartAt = 0;
							const msg = (err && err.errMsg) ? err.errMsg : '录音错误';
							if (msg.indexOf('auth') !== -1 || msg.indexOf('权限') !== -1) {
								uni.showModal({
									title: '麦克风权限未开启',
									content: '请到系统设置中允许本应用使用麦克风',
									confirmText: '去设置',
									success: (res) => { if (res.confirm && typeof uni.openSetting === 'function') uni.openSetting(); }
								});
							} else {
								uni.showToast({ title: '录音错误', icon: 'none' });
							}
						});
					}
					// 先用最简参数启动，兼容各平台（部分不支持 format: 'wav'）
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
				this.isVoiceProcessing = true;
				uni.uploadFile({
					url: this.agentBaseUrl + '/chat/voice',
					filePath: tempFilePath,
					name: 'audio',
					header: token ? { Authorization: 'Bearer ' + token } : {},
					formData: { return_tts: 'true', client_time: this.getClientTime() },
					success: (res) => {
						try {
							if (res.statusCode && res.statusCode !== 200) {
								let msg = '服务异常 ' + (res.statusCode || '');
								try {
									const raw = res.data;
									const data = typeof raw === 'string' ? JSON.parse(raw) : (raw || {});
									if (data.message) msg = data.message;
								} catch (e) {}
								uni.showToast({ title: msg, icon: 'none' });
								this.isLoading = false;
								this.isVoiceProcessing = false;
								return;
							}
							// 部分平台 res.data 已是对象，部分为字符串
							const raw = res.data;
							if (raw === undefined || raw === null || raw === '') {
								uni.showToast({ title: '无返回数据', icon: 'none' });
								this.isLoading = false;
								this.isVoiceProcessing = false;
								return;
							}
							const data = typeof raw === 'string' ? JSON.parse(raw) : (raw || {});
							if (data.code !== '00000' || !data.data) {
								uni.showToast({ title: data.message || '请求失败', icon: 'none' });
								this.isLoading = false;
								this.isVoiceProcessing = false;
								return;
							}
							const { question: recognized, answer } = data.data;
							this.textList.push({ role: 'user', content: recognized || '(语音)' });
							this.textList.push({ role: 'assistant', content: answer || '' });
							this.refreshCurrentSession();
							this.refreshScrollViewport(true);
							if (answer && answer.trim()) this.requestTtsAndPlay(answer.trim());
						} catch (e) {
							uni.showToast({ title: '语音结果暂时不可用，请稍后再试', icon: 'none' });
						}
						this.isLoading = false;
						this.isVoiceProcessing = false;
					},
					fail: () => {
						uni.showToast({ title: '网络异常', icon: 'none' });
						this.isLoading = false;
						this.isVoiceProcessing = false;
					}
				});
			},
			// 使用可播放的 URL 播放（兼容各平台）
			playTtsByPlayUrl(playUrl) {
				if (!playUrl) return;
				this.stopTtsPlayback();
				if (typeof uni.createInnerAudioContext !== 'function') {
					uni.showToast({ title: '当前环境不支持语音播放', icon: 'none' });
					return;
				}
				const playbackToken = this.ttsPlaybackToken + 1;
				this.ttsPlaybackToken = playbackToken;
				this.isTtsPlaying = true;
				this.refreshScrollViewport(true);
				const startPlayback = (src) => {
					if (playbackToken !== this.ttsPlaybackToken || !src) return;
					const ctx = uni.createInnerAudioContext();
					this.innerAudioContext = ctx;
					ctx.obeysMuteSwitch = false;
					ctx.src = src;
					ctx.onPlay(() => {
						this.isTtsPlaying = true;
						this.refreshScrollViewport(true);
					});
					ctx.onEnded(() => {
						if (this.innerAudioContext === ctx) this.innerAudioContext = null;
						if (typeof ctx.destroy === 'function') ctx.destroy();
						if (playbackToken === this.ttsPlaybackToken) this.isTtsPlaying = false;
						this.refreshScrollViewport(true);
					});
					ctx.onError(() => {
						if (this.innerAudioContext === ctx) this.innerAudioContext = null;
						if (typeof ctx.destroy === 'function') ctx.destroy();
						if (playbackToken === this.ttsPlaybackToken) this.isTtsPlaying = false;
						this.refreshScrollViewport(true);
						uni.showToast({ title: '语音播放失败', icon: 'none' });
					});
					ctx.play();
				};
				if (typeof uni.downloadFile !== 'function') {
					startPlayback(playUrl);
					return;
				}
				this.ttsDownloadTask = uni.downloadFile({
					url: playUrl,
					success: (res) => {
						this.ttsDownloadTask = null;
						if (playbackToken !== this.ttsPlaybackToken) return;
						if (res.statusCode === 200 && res.tempFilePath) {
							startPlayback(res.tempFilePath);
						} else {
							this.isTtsPlaying = false;
							this.refreshScrollViewport(true);
							uni.showToast({ title: '语音播放暂时不可用', icon: 'none' });
						}
					},
					fail: () => {
						this.ttsDownloadTask = null;
						if (playbackToken !== this.ttsPlaybackToken) return;
						this.isTtsPlaying = false;
						this.refreshScrollViewport(true);
						uni.showToast({ title: '语音下载失败', icon: 'none' });
					},
				});
			},
			// 请求 TTS 并播放：POST 提交全文，用返回的短 URL 播放，避免 GET 长度限制导致念不完
			requestTtsAndPlay(text) {
				if (!text || !this.agentBaseUrl) return;
				const token = uni.getStorageSync('token') || '';
				uni.request({
					url: this.agentBaseUrl + '/tts/audio',
					method: 'POST',
					header: {
						'Content-Type': 'application/json',
						...(token ? { Authorization: 'Bearer ' + token } : {})
					},
					data: { text: text },
					success: (res) => {
						if (res.statusCode === 200 && res.data && res.data.code === '00000' && res.data.data && res.data.data.play_url) {
							this.playTtsByPlayUrl(res.data.data.play_url);
						} else {
							uni.showToast({ title: res.data && res.data.message ? res.data.message : '语音播放暂时不可用', icon: 'none' });
						}
					},
					fail: () => {
						uni.showToast({ title: '网络异常', icon: 'none' });
					}
				});
			},
			stopTtsPlayback() {
				this.ttsPlaybackToken += 1;
				if (this.ttsDownloadTask && typeof this.ttsDownloadTask.abort === 'function') {
					try { this.ttsDownloadTask.abort(); } catch (e) {}
				}
				this.ttsDownloadTask = null;
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
		watch:{
			count: {
				handler() {
					// console.log("@count_handler");
					this.scrollTop = this.newTop;
				},
			},
			isRecording() {
				this.refreshScrollViewport(true);
			},
			isVoiceProcessing() {
				this.refreshScrollViewport(true);
			},
			isTtsPlaying() {
				this.refreshScrollViewport(true);
			},
		}
	}
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
		min-height: 100vh;
		background:
			radial-gradient(1200rpx 520rpx at 12% -5%, rgba(89, 171, 255, 0.3) 0%, rgba(89, 171, 255, 0) 70%),
			radial-gradient(1000rpx 460rpx at 92% 8%, rgba(0, 210, 255, 0.2) 0%, rgba(0, 210, 255, 0) 72%),
			linear-gradient(180deg, #deedfb 0%, #ebf5ff 46%, #f4f9ff 100%);
		// justify-content: center;
		// .inner {
		// 	border: 2px solid blue;
		// 	width: 95%;
		// 	display: flex;
		// 	flex-direction: column;
		//  justify-content: space-around;
			.header {
				position: fixed;
				left: 24rpx;
				right: 24rpx;
				top: calc(var(--status-bar-height, 0px) + 28rpx);
				z-index: 1200;
				display: flex;
				justify-content: space-between;
				align-items: center;
				min-height: 74rpx;
				pointer-events: none;

				.topNav {
					display: flex;
					align-items: center;
					gap: 14rpx;
					pointer-events: auto;
					.back-btn,
					.choosen {
						width: 66rpx;
						height: 66rpx;
						border-radius: 22rpx;
						background: rgba(255, 255, 255, 0.72);
						border: 1px solid rgba(126, 187, 255, 0.28);
						box-shadow: 0 12rpx 30rpx rgba(8, 31, 75, 0.14);
						display: flex;
						align-items: center;
						justify-content: center;
						backdrop-filter: blur(8px);
						box-sizing: border-box;
					}
					.choosen {
						padding: 10rpx;
						.session-tag {
							width: 42rpx;
							height: 42rpx;
							object-fit: contain;
						}
					}
				}
				.header-title {
					position: absolute;
					left: 50%;
					transform: translateX(-50%);
					display: flex;
					align-items: center;
					justify-content: center;
					padding: 10rpx 22rpx;
					border-radius: 999rpx;
					background: rgba(7, 27, 54, 0.34);
					border: 1px solid rgba(139, 219, 255, 0.16);
					backdrop-filter: blur(8px);
					text {
						color: rgba(232, 245, 255, 0.92);
						font-size: 26rpx;
						font-weight: 700;
						letter-spacing: 2rpx;
					}
				}
				.setting-btn {
					width: 66rpx;
					height: 66rpx;
					border-radius: 22rpx;
					background: rgba(255, 255, 255, 0.72);
					border: 1px solid rgba(126, 187, 255, 0.28);
					box-shadow: 0 12rpx 30rpx rgba(8, 31, 75, 0.14);
					display: flex;
					justify-content: center;
					align-items: center;
					backdrop-filter: blur(8px);
					pointer-events: auto;
					.setting-tag {
						width: 42rpx;
						height: 42rpx;
						object-fit: contain;
					}
				}
			}
			.session-drawer {
				position: fixed;
				left: 0;
				top: 0;
				width: 100%;
				height: 100%;
				z-index: 1150;
				display: flex;
				pointer-events: none;
			}
			.session-drawer.open {
				pointer-events: auto;
			}
			.session-panel {
				width: 78%;
				max-width: 620rpx;
				height: 100%;
				padding-top: calc(var(--status-bar-height, 0px) + 96rpx);
				background: rgba(245, 250, 255, 0.96);
				border-right: 1px solid rgba(38, 108, 232, 0.18);
				box-shadow: 18rpx 0 46rpx rgba(6, 24, 60, 0.22);
				display: flex;
				flex-direction: column;
				transform: translateX(-100%);
				transition: transform 260ms ease;
				overflow: hidden;
				box-sizing: border-box;
				backdrop-filter: blur(12px);
			}
			.session-drawer.open .session-panel {
				transform: translateX(0);
			}
			.session-peek {
				flex: 1;
				height: 100%;
				background: rgba(3, 13, 30, 0.26);
				opacity: 0;
				transition: opacity 260ms ease;
			}
			.session-drawer.open .session-peek {
				opacity: 1;
			}
			.session-panel-head {
				height: 86rpx;
				padding: 0 24rpx;
				display: flex;
				align-items: center;
				justify-content: space-between;
				border-bottom: 1px solid rgba(0, 122, 255, 0.12);
				background: linear-gradient(180deg, rgba(230, 241, 255, 0.95) 0%, rgba(240, 247, 255, 0.98) 100%);
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
				min-height: 180rpx;
			}
			.session-item {
				padding: 18rpx 24rpx;
				display: flex;
				align-items: center;
				justify-content: space-between;
				gap: 18rpx;
				border-bottom: 1px solid rgba(0, 122, 255, 0.08);
				transition: background 0.2s ease;
			}
			.session-item:active {
				background: rgba(88, 147, 255, 0.1);
			}
			.session-item.active {
				background: linear-gradient(90deg, rgba(88, 147, 255, 0.16) 0%, rgba(88, 147, 255, 0.06) 100%);
			}
			.session-content {
				flex: 1;
				min-width: 0;
			}
			.session-name {
				font-size: 28rpx;
				font-weight: 600;
				color: #243a5e;
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
			}
			.session-time {
				margin-top: 8rpx;
				font-size: 22rpx;
				color: #7990b3;
			}
			.session-delete {
				flex-shrink: 0;
				padding: 8rpx 18rpx;
				border-radius: 999rpx;
				font-size: 22rpx;
				font-weight: 700;
				color: #d84d4d;
				background: rgba(216, 77, 77, 0.1);
				border: 1px solid rgba(216, 77, 77, 0.16);
			}
			.body {
				position: absolute;
				left: 0;
				right: 0;
				top: 0;
				bottom: 0;
				z-index: 10;
				width: 100%;
				overflow: hidden;
				background: transparent;
				border-radius: 0;
				display: flex;
				flex-direction: column;
				align-items: center;
				justify-content: flex-start;
				box-shadow: none;
				.scroll {
					flex: 1;
					min-height: 0;
					width: 100%;
					box-sizing: border-box;
					overflow: hidden;
					.chat {
						background: transparent;
						display: flex;
						flex-direction: column;
						align-items: center;
						justify-content: flex-start;
						padding: 6rpx 0 12rpx;
						///////LEFT//////
						.left {
							width: 95%;
							margin-bottom: 18rpx;
							display: flex;
							flex-direction: row;
							align-items: flex-start;
							.avatar {
								width: 100rpx;
								height: 100rpx;
								background-color: #fff;
								border-radius: 50%;
								box-shadow: 0 10rpx 24rpx rgba(0, 40, 100, 0.12);
								image {
									width: 100%;
									height: 100%;
									border-radius: 50%;
								}
							}
							.msg {
								margin-top: 15rpx;
								max-width: 70%;
								background: rgba(255, 255, 255, 0.9);
								margin-left: 20rpx;
								box-sizing: border-box;
								padding: 16rpx 20rpx;
								border-radius: 24rpx;
								border: 1px solid rgba(0, 122, 255, 0.12);
								box-shadow: 0 8rpx 20rpx rgba(14, 52, 110, 0.08);
								view {
									word-break:break-all;
									word-wrap:break-word;
									color: #22395d;
								}
								.msg-rich {
									word-break: break-all;
									word-wrap: break-word;
									font-size: 28rpx;
									line-height: 1.5;
									color: #333;
								}
								.md-inline-code, .md-code-block {
									background: #f5f5f5;
									padding: 4rpx 8rpx;
									border-radius: 6rpx;
									font-size: 24rpx;
								}
								.md-h1 { font-size: 36rpx; font-weight: 700; margin: 8rpx 0; }
								.md-h2 { font-size: 32rpx; font-weight: 700; margin: 6rpx 0; }
								.md-h3 { font-size: 30rpx; font-weight: 600; margin: 4rpx 0; }
							}
						}
						//////RIGHT/////
						.right {
							width: 95%;
							margin-bottom: 18rpx;
							display: flex;
							flex-direction: row-reverse;
							align-items: flex-start;
							.avatar {
								width: 100rpx;
								height: 100rpx;
								background-color: #fff;
								border-radius: 50%;
								box-shadow: 0 10rpx 24rpx rgba(0, 40, 100, 0.12);
								image {
									width: 100%;
									height: 100%;
									border-radius: 50%;
								}
							}
							.msg {
								margin-top: 15rpx;
								max-width: 70%;
								background: linear-gradient(135deg, #3f78ff 0%, #5b9cff 100%);
								margin-right: 20rpx;
								box-sizing: border-box;
								padding: 16rpx 20rpx;
								border-radius: 24rpx;
								box-shadow: 0 10rpx 24rpx rgba(32, 87, 185, 0.24);
								view {
									word-break:break-all;
									word-wrap:break-word;
									color: #ffffff;
								}
								.msg-rich {
									word-break: break-all;
									word-wrap: break-word;
									font-size: 28rpx;
									line-height: 1.5;
									color: #333;
								}
								.md-inline-code, .md-code-block {
									background: #f5f5f5;
									padding: 4rpx 8rpx;
									border-radius: 6rpx;
									font-size: 24rpx;
								}
								.md-h1 { font-size: 36rpx; font-weight: 700; margin: 8rpx 0; }
								.md-h2 { font-size: 32rpx; font-weight: 700; margin: 6rpx 0; }
								.md-h3 { font-size: 30rpx; font-weight: 600; margin: 4rpx 0; }
							}
						}
					}
				}
				.down {
					width: 100%;
					flex-shrink: 0;
					padding: 16rpx 24rpx 24rpx;
					background: linear-gradient(180deg, rgba(225, 236, 255, 0.9) 0%, rgba(214, 228, 255, 0.98) 100%);
					border-top: 1px solid rgba(0, 122, 255, 0.12);
					display: flex;
					flex-direction: column;
					align-items: center;
					box-sizing: border-box;
				}
				.voice-tip,
				.tts-bar {
					margin-top: 10rpx;
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
					border: 1px solid rgba(0, 122, 255, 0.14);
					box-shadow: 0 10rpx 26rpx rgba(21, 69, 140, 0.12);
				}
				.input-inner {
					flex: 1;
					min-width: 0;
					height: 100%;
					font-size: 28rpx;
					color: #333;
					background: transparent;
				}
				.input-inner::placeholder {
					color: #b0b8d4;
				}
				.btn-voice {
					width: 72rpx;
					height: 72rpx;
					min-width: 72rpx;
					border-radius: 50%;
					background-color: #e6eeff;
					display: flex;
					justify-content: center;
					align-items: center;
					margin-left: 12rpx;
					flex-shrink: 0;
				}
				.btn-voice:active {
					opacity: 0.9;
				}
				.btn-voice.recording {
					width: 100rpx;
					min-width: 100rpx;
					height: 72rpx;
					border-radius: 36rpx;
					background-color: #f56c6c;
				}
				.btn-voice-text {
					white-space: nowrap;
					font-size: 36rpx;
					font-weight: 600;
					color: #5a6ab8;
				}
				.btn-voice.recording .btn-voice-text {
					color: #fff;
					font-size: 28rpx;
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
					flex-shrink: 0;
				}
				.btn-send:active {
					opacity: 0.9;
				}
				.btn-send.disabled {
					opacity: 0.5;
				}
				.btn-send-text {
					color: #fff;
					font-size: 30rpx;
					font-weight: 600;
				}
				.voice-tip {
					font-size: 24rpx;
					color: #5f759a;
				}
				.tts-bar {
					display: flex;
					align-items: center;
					justify-content: center;
					padding: 12rpx 24rpx;
					background: rgba(255, 152, 0, 0.12);
					border-radius: 24rpx;
					width: 100%;
					max-width: 400rpx;
					box-sizing: border-box;
				}
				.tts-bar-text {
					margin-right: 20rpx;
				}
				.tts-bar-text {
					font-size: 24rpx;
					color: #e65100;
				}
				.agent-fallback-card {
					position: absolute;
					left: 50%;
					top: calc(var(--status-bar-height, 0px) + 150rpx);
					transform: translateX(-50%);
					z-index: 7;
					width: 72%;
					max-width: 640rpx;
					padding: 28rpx 24rpx;
					border-radius: 30rpx;
					background: rgba(7, 27, 54, 0.36);
					border: 1px solid rgba(139, 219, 255, 0.18);
					box-shadow: 0 16rpx 40rpx rgba(0, 13, 38, 0.18);
					backdrop-filter: blur(10px);
					display: flex;
					flex-direction: column;
					align-items: center;
					text-align: center;
				}
				.fallback-avatar {
					width: 92rpx;
					height: 92rpx;
					border-radius: 30rpx;
					background: linear-gradient(135deg, #4ea8ff 0%, #6d7cff 100%);
					box-shadow: 0 12rpx 30rpx rgba(78, 168, 255, 0.28);
					display: flex;
					align-items: center;
					justify-content: center;
					color: #fff;
					font-size: 34rpx;
					font-weight: 900;
				}
				.fallback-title {
					margin-top: 18rpx;
					color: #e8f5ff;
					font-size: 32rpx;
					font-weight: 800;
				}
				.fallback-sub {
					margin-top: 10rpx;
					color: rgba(232, 245, 255, 0.84);
					font-size: 23rpx;
					line-height: 1.5;
				}
				.btn-stop-tts {
					padding: 10rpx 28rpx;
					font-size: 26rpx;
					font-weight: 600;
					background-color: #f57c00;
					color: #fff;
					border-radius: 24rpx;
				}
			}
		// }
	}
	.main.owner-app {
		.body {
			.down {
				padding-bottom: calc(130rpx + env(safe-area-inset-bottom));
			}
		}
	}
	.loading {
		// border: 2px solid red;
		position: fixed;
		bottom: 12%;
		// width: 50%;
		display: flex;
		flex-direction: row-reverse;
		.loadText {
			margin-left: 25rpx;
		}
		.spinner {
				width: 40rpx;
				height: 40rpx;
				animation: spinner-y0fdc1 2s infinite ease;
				transform-style: preserve-3d;
			}

			.spinner > view {
				background-color: rgba(0,77,255,0.2);
				height: 100%;
				position: absolute;
				width: 100%;
				border: 2px solid #004dff;
			}

			.spinner view:nth-of-type(1) {
			transform: translateZ(-21.5rpx) rotateY(180deg);
			}

			.spinner view:nth-of-type(2) {
			transform: rotateY(-270deg) translateX(50%);
			transform-origin: top right;
			}

			.spinner view:nth-of-type(3) {
			transform: rotateY(270deg) translateX(-50%);
			transform-origin: center left;
			}

			.spinner view:nth-of-type(4) {
			transform: rotateX(90deg) translateY(-50%);
			transform-origin: top center;
			}

			.spinner view:nth-of-type(5) {
			transform: rotateX(-90deg) translateY(50%);
			transform-origin: bottom center;
			}

			.spinner view:nth-of-type(6) {
			transform: translateZ(21.5rpx);
			}

			@keyframes spinner-y0fdc1 {
			0% {
			transform: rotate(45deg) rotateX(-25deg) rotateY(25deg);
			}

			50% {
			transform: rotate(45deg) rotateX(-385deg) rotateY(25deg);
			}

			100% {
			transform: rotate(45deg) rotateX(-385deg) rotateY(385deg);
			}
			}

	}
	.floating-dialog {
		position: absolute;
		left: 24rpx;
		right: 24rpx;
		bottom: 244rpx;
		z-index: 28;
		pointer-events: none;
	}
	.floating-bubble {
		max-width: 58%;
		padding: 18rpx 22rpx;
		border-radius: 28rpx;
		box-shadow: 0 14rpx 36rpx rgba(8, 31, 75, 0.16);
	}
	.floating-bubble text {
		font-size: 25rpx;
		line-height: 1.42;
	}
	.user-bubble {
		margin-left: auto;
		margin-bottom: 18rpx;
		border-bottom-right-radius: 8rpx;
		background: linear-gradient(135deg, rgba(64, 123, 255, 0.94) 0%, rgba(91, 156, 255, 0.94) 100%);
	}
	.user-bubble text {
		color: #fff;
	}
	.assistant-bubble {
		margin-right: auto;
		border-bottom-left-radius: 8rpx;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(126, 187, 255, 0.28);
	}
	.assistant-bubble text {
		color: #1f3760;
	}
	.chat-toggle {
		position: absolute;
		right: 32rpx;
		bottom: 396rpx;
		z-index: 35;
		height: 64rpx;
		line-height: 64rpx;
		padding: 0 24rpx;
		border-radius: 999rpx;
		background: rgba(255, 255, 255, 0.88);
		border: 1px solid rgba(126, 187, 255, 0.3);
		box-shadow: 0 12rpx 30rpx rgba(8, 31, 75, 0.14);
	}
	.chat-toggle text {
		color: #245cbd;
		font-size: 24rpx;
		font-weight: 700;
	}
	.chat-mask {
		position: absolute;
		inset: 0;
		z-index: 38;
		background: rgba(3, 13, 30, 0.28);
	}
	.chat-panel {
		position: absolute;
		left: 22rpx;
		right: 22rpx;
		bottom: 144rpx;
		z-index: 42;
		border-radius: 34rpx 34rpx 0 0;
		overflow: hidden;
		background: rgba(243, 248, 255, 0.96);
		border: 1px solid rgba(126, 187, 255, 0.28);
		box-shadow: 0 -18rpx 46rpx rgba(5, 25, 70, 0.22);
		transform: translateY(calc(100% + 170rpx));
		transition: transform 260ms ease;
	}
	.chat-panel.open {
		transform: translateY(0);
	}
	.chat-panel-head {
		height: 82rpx;
		padding: 0 26rpx;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid rgba(0, 122, 255, 0.1);
	}
	.chat-panel-title {
		color: #1f3760;
		font-size: 30rpx;
		font-weight: 800;
	}
	.chat-panel-close {
		color: #3572d8;
		font-size: 25rpx;
		font-weight: 700;
	}
	.chat-scroll .chat {
		padding: 18rpx 0 24rpx;
	}
	.chat-panel .loading {
		position: relative;
		bottom: auto;
		margin-top: 8rpx;
	}
	.main .body .down {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 50;
		width: 100%;
		padding: 18rpx 24rpx 26rpx;
		background: linear-gradient(180deg, rgba(7, 21, 45, 0) 0%, rgba(7, 21, 45, 0.72) 28%, rgba(6, 19, 40, 0.92) 100%);
		border-top: 0;
	}
	.main .body .input-wrap {
		max-width: 700rpx;
		height: 92rpx;
		background-color: rgba(255, 255, 255, 0.96);
		border-radius: 46rpx;
		border: 1px solid rgba(126, 187, 255, 0.24);
		box-shadow: 0 16rpx 42rpx rgba(0, 12, 42, 0.2);
	}
	.main .body .voice-tip,
	.main .body .tts-bar {
		margin-top: 12rpx;
		color: rgba(232, 245, 255, 0.9);
		font-size: 24rpx;
	}
	.main .body .tts-bar {
		background: transparent;
		padding: 0;
	}
	.main .body .tts-bar-text {
		color: rgba(232, 245, 255, 0.9);
	}
	.main .body .btn-stop-tts {
		padding: 8rpx 22rpx;
		border-radius: 999rpx;
		color: #fff;
		font-size: 24rpx;
		background: rgba(255, 152, 0, 0.86);
	}
</style>
