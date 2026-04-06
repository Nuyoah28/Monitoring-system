<template>
	<view class="main" :class="{ 'drawer-open': showSessionList, 'owner-app': isOwnerApp }" :style="{ minHeight: safeHeight + 'px', paddingTop: statusBarHeight + 'px', '--status-bar-height': statusBarHeight + 'px' }">
		<view class="header">
			<view class="topNav">
				<view class="back-btn" @tap="goBack">
					<u-icon name="arrow-left" color="#1a2a3a" size="34rpx"></u-icon>
				</view>
				<view class="choosen" @tap="toggleSessionList">
					<image class="session-tag" src="/static/messagelist.png"></image>
				</view>
			</view>
			<view class="header-title">
				<span>AI助手</span>
			</view>
			<view class="setting-btn" @tap="jump">
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
		<view class="body" :style="bodyStyle">
			<scroll-view :scroll-top="scrollTop" class="scroll" scroll-y @scroll="recordHeight" :style="{ height: scrollHeight + 'px' }">
				<view class="chat">
					<view id="msgbar" v-for="(item, index) in textList" :key="index" :class="index%2 === 1 ? 'left' : 'right'">
						<view class="avatar">
							<image :src="index % 2 === 0 ? '/static/AIuser.png' : '/static/ai.png' "></image>
						</view>
						<view class="msg">
							<rich-text v-if="index % 2 === 1" class="msg-rich" :nodes="mdToHtml(item)"></rich-text>
							<view v-else>{{ item }}</view>
						</view>
					</view>
					<view class="loading" v-show="isLoading">
						<view class="loadText">
							<span>智能生成中...</span>
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
			<view class="down" id="down">
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
import wsRequest from '@/api/websocket.js'
import { AI_HTTP_URL, AI_WS_URL } from '@/common/config.js'
import Vue from 'vue';
	import OwnerTabbar from '@/components/navigation/owner-tabbar.vue';
	export default {
		components: {
			OwnerTabbar,
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
				scrollHeight:0,
				count:0,
				websocket: null,
				cnt: 0,
				isLoading: false,
				// 语音
				agentBaseUrl: AI_HTTP_URL,
				isRecording: false,
				isTtsPlaying: false,
				recorderManager: null,
				innerAudioContext: null,
				showSessionList: false,
				sessions: [],
				currentSessionId: '',
				sessionLongPressLock: false,
			}
		},
		onShow() {
			const info = uni.getWindowInfo();
			this.safeHeight = info.safeArea.height;
			this.statusBarHeight = info.statusBarHeight || 20;
			this.loadSessionCache();
			if (!this.sessions.length) {
				this.startNewSession();
			} else {
				const defaultId = this.currentSessionId || this.sessions[0].id;
				this.switchSession(defaultId, false);
			}
			this.createWs();
		},
		beforeDestroy() {

		},
		computed: {
			isOwnerApp() {
				return uni.getStorageSync('appType') === 'owner';
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
			bodyStyle() {
				return {
					transform: this.showSessionList ? 'translateX(80%)' : 'translateX(0)',
				};
			},
		},
		methods:{
			goBack() {
				if (getCurrentPages().length > 1) {
					uni.navigateBack();
				} else {
					// Fallback to home if directly opened
					uni.switchTab({ url: '/pages/manage/controls/controls' });
				}
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
				this.sessions.unshift({
					id,
					title: '新会话',
					updatedAt: Date.now(),
					messages: [],
				});
				this.currentSessionId = id;
				this.textList = [];
				this.showSessionList = false;
				this.saveSessionCache();
			},
			switchSession(id, closePanel = true) {
				if (this.sessionLongPressLock) return;
				const target = this.sessions.find((item) => item.id === id);
				if (!target) return;
				this.currentSessionId = id;
				this.textList = Array.isArray(target.messages) ? [...target.messages] : [];
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
				const first = (session.messages[0] || '').replace(/\s+/g, ' ').trim();
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
				const first = (messages[0] || '').replace(/\s+/g, ' ').trim();
				const title = first ? (first.length > 12 ? first.slice(0, 12) + '...' : first) : '新会话';
				Vue.set(this.sessions, index, {
					...this.sessions[index],
					title,
					updatedAt: Date.now(),
					messages,
				});
				this.saveSessionCache();
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
				let token = uni.getStorageSync('token')
				// 关于ai对话部分的，如果没有需求先不用管这一部分
				// this.websocket = new wsRequest(`ws://8.152.219.117:10215/api/v1/gpt/ws/${token}`,5000) //服务器
				this.websocket = new wsRequest(`${AI_WS_URL}/api/v1/gpt/ws/${token}`,5000) // Python Agent
				// this.websocket = new wsRequest(`ws://localhost:10215/api/v1/gpt/ws/${token}`,5000) //本地
				// this.websocket = new wsRequest(`ws://192.168.3.135:5050/api/v1/gpt/ws/${token}`,5000) //Python Agent直接连接
				// this.websocket = new wsRequest(`ws://192.168.68.31:5050/api/v1/gpt/ws/${token}`,5000) //Python Agent直接连接
				this.websocket.getMessage(res => {
					// console.log('res=',res.data)
					// console.log('textList=',this.textList[this.textList.length-1])
					this.cnt ++;
					if (res.data === "[REPLACE]") {
						this.answerText = '';
						Vue.set(this.textList, this.textList.length - 1, '');
						return;
					}
					this.isLoading = false;
					if(res.data !== "[DONE]"){
						this.answerText += res.data;
					}
					Vue.set(this.textList , this.textList.length-1 , this.answerText)
					this.refreshCurrentSession();
					if(res.data === "[DONE]") {
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
			setSafeArea() {
				this.safeHeight = uni.getWindowInfo().safeArea.height;
				this.$nextTick(() => {
					const query = uni.createSelectorQuery().in(this);
					query.select('.body').boundingClientRect();
					query.select('.title').boundingClientRect();
					query.select('#down').boundingClientRect();
					query.exec((res) => {
						const body = res[0];
						const title = res[1];
						const down = res[2];
						if (body && down) {
							const titleH = (title && title.height) ? title.height : 50;
							this.scrollHeight = Math.max(200, (body.height || 0) - titleH - down.height);
						}
					});
				});
			},
			jump() {
			  uni.navigateTo({
			    url: "/pages/manage/personal/setting/setting",
			  });
			},
			send(){
				if(this.text == ""){
					uni.showToast({
						title: '请勿发送空消息',
						icon: 'none',
						duration: 1500
					})  
				}
				else {
					// console.log("输入的消息为：" + this.text);
					this.cnt = 0;
					this.answerText = "";
					this.textList.push(this.text);
					this.toBottom();
					this.count ++;
					this.getAnswer(this.text);
					this.text = "";
					// this.isDisabled = true;
					this.isLoading = true;
					this.refreshCurrentSession();
				}	
			},
			getAnswer(ask){
				// this.isLeft = 1;
				this.answerText = ""
				this.textList.push(this.answerText);
				this.toBottom();
				this.count ++ ;
				this.refreshCurrentSession();
				// 发送消息
				let data = ask;
				this.websocket.send(JSON.stringify(data));
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
					if (typeof rm.onStart === 'function') rm.onStart(() => { this.isRecording = true; });
					if (typeof rm.onStop === 'function') {
						rm.onStop((res) => {
							this.isRecording = false;
							if (res && res.tempFilePath) this.sendVoiceToAgent(res.tempFilePath);
							else uni.showToast({ title: '录音失败', icon: 'none' });
						});
					}
					if (typeof rm.onError === 'function') {
						rm.onError((err) => {
							this.isRecording = false;
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
				uni.uploadFile({
					url: this.agentBaseUrl + '/chat/voice',
					filePath: tempFilePath,
					name: 'audio',
					header: token ? { Authorization: 'Bearer ' + token } : {},
					formData: { return_tts: 'true' },
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
								return;
							}
							// 部分平台 res.data 已是对象，部分为字符串
							const raw = res.data;
							if (raw === undefined || raw === null || raw === '') {
								uni.showToast({ title: '无返回数据', icon: 'none' });
								this.isLoading = false;
								return;
							}
							const data = typeof raw === 'string' ? JSON.parse(raw) : (raw || {});
							if (data.code !== '00000' || !data.data) {
								uni.showToast({ title: data.message || '请求失败', icon: 'none' });
								this.isLoading = false;
								return;
							}
							const { question: recognized, answer } = data.data;
							this.textList.push(recognized || '(语音)');
							this.textList.push(answer || '');
							this.refreshCurrentSession();
							this.toBottom();
							if (answer && answer.trim()) this.requestTtsAndPlay(answer.trim());
						} catch (e) {
							uni.showToast({ title: '解析失败，请确认 Agent 已启动', icon: 'none' });
						}
						this.isLoading = false;
					},
					fail: () => {
						uni.showToast({ title: '网络异常', icon: 'none' });
						this.isLoading = false;
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
				const ctx = uni.createInnerAudioContext();
				this.innerAudioContext = ctx;
				ctx.obeysMuteSwitch = false;
				ctx.src = playUrl;
				ctx.onPlay(() => { this.isTtsPlaying = true; });
				ctx.onEnded(() => { this.isTtsPlaying = false; this.innerAudioContext = null; });
				ctx.onError(() => {
					this.isTtsPlaying = false;
					this.innerAudioContext = null;
					uni.showToast({ title: '语音播放失败', icon: 'none' });
				});
				ctx.play();
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
							uni.showToast({ title: res.data && res.data.message ? res.data.message : 'TTS 请求失败', icon: 'none' });
						}
					},
					fail: () => {
						uni.showToast({ title: '网络异常', icon: 'none' });
					}
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
			},
		},
		watch:{
			count: {
				handler() {
					// console.log("@count_handler");
					this.scrollTop = this.newTop;
				},
			},
		}
	}
</script>

<style lang="scss">
	.main {
		width: 100%;
		margin: 0 auto;
		position: absolute;
		bottom: 0;
		left: 0;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		align-items: center;
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

				.topNav {
					display: flex;
					align-items: center;
					gap: 16rpx;
					.back-btn {
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
					.choosen {
						position: relative;
						z-index: 1200;
						background: rgba(255, 255, 255, 0.7);
						border: 1px solid rgba(0, 122, 255, 0.15);
						padding: 10rpx;
						border-radius: 18rpx;
						box-shadow: 0 8rpx 20rpx rgba(0, 122, 255, 0.08);
						display: flex;
						align-items: center;
						justify-content: center;
						.session-tag {
							width: 44rpx;
							height: 44rpx;
							object-fit: contain;
						}
					}
				}
				.header-title {
					display: flex;
					align-items: center;
					justify-content: center;
					margin-top: 2rpx;
					span {
						color: #51678f;
						font-size: 40rpx;
						font-weight: 700;
						font-family: "Novecento wide", "半展开", "粗体";
						letter-spacing: 4rpx;
						transform: translateY(-2rpx);
					}
				}
				.setting-btn {
					width: 60rpx;
					height: 60rpx;
					background: transparent;
					border: none;
					border-radius: 50%;
					display: flex;
					justify-content: center;
					align-items: center;
					box-shadow: none;
					.setting-tag {
						width: 48rpx;
						height: 48rpx;
						object-fit: contain;
					}
				}
			}
			.session-drawer {
				position: fixed;
				left: 0;
				top: calc(100rpx + var(--status-bar-height, 0px));
				width: 100%;
				height: calc(100% - 100rpx - var(--status-bar-height, 0px));
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
				overflow: hidden;
			}
			.session-drawer.open .session-panel {
				transform: translateX(0);
			}
			.session-peek {
				width: 20%;
				height: 100%;
				background: linear-gradient(90deg, rgba(233, 242, 255, 0.06) 0%, rgba(233, 242, 255, 0.28) 45%, rgba(233, 242, 255, 0.56) 100%);
				backdrop-filter: blur(2px);
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
				flex-direction: column;
				gap: 8rpx;
				border-bottom: 1px solid rgba(0, 122, 255, 0.08);
				transition: background 0.2s ease;
			}
			.session-item:active {
				background: rgba(88, 147, 255, 0.1);
			}
			.session-item.active {
				background: linear-gradient(90deg, rgba(88, 147, 255, 0.16) 0%, rgba(88, 147, 255, 0.06) 100%);
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
				font-size: 22rpx;
				color: #7990b3;
			}
			.body {
				position: absolute;
				z-index: 10;
				bottom: 0;
				width: 100%;
				height: 93%;
				background: transparent;
				border-radius: 0;
				display: flex;
				flex-direction: column;
				align-items: center;
				justify-content: flex-start;
				box-shadow: none;
				transition: transform 260ms ease;
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
					gap: 10rpx;
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
					gap: 20rpx;
					padding: 12rpx 24rpx;
					background: rgba(255, 152, 0, 0.12);
					border-radius: 24rpx;
					width: 100%;
					max-width: 400rpx;
					box-sizing: border-box;
				}
				.tts-bar-text {
					font-size: 24rpx;
					color: #e65100;
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
</style>
