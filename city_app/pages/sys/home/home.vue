<template>
	<view class="main" :style="{ height: safeHeight + 'px' }">
		<view class="header">
			<view class="topNav">
				<view class="choosen">
					<span>
						<h2>智慧助手</h2>
					</span>
				</view>
			</view>
			<view class="setting" @click="jump">
				<image src="../../../static/edb8e6b3-f7e0-4778-bdc4-691d6e4f1511.png" mode="aspectFit" alt=""></image>
			</view>
		</view>
		<view class="body">
			<view class="title">
				<span>AI助手</span>
			</view>
			<scroll-view :scroll-top="scrollTop" class="scroll" scroll-y @scroll="recordHeight" :style="{ height: scrollHeight + 'px' }">
				<view class="chat">
					<view id="msgbar" v-for="(item, index) in textList" :key="index" :class="index%2 === 1 ? 'left' : 'right'">
						<view class="avatar">
							<image :src="index % 2 === 0 ? '../../../static/AIuser.png' : '../../../static/ai.png' "></image>
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
	</view>
</template>

<script>
import wsRequest from '../../../api/websocket.js'
import Vue from 'vue';
	export default {
		data() {
			return {
				isDisabled:false,
				safeHeight:0,
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
				agentBaseUrl: 'http://192.168.1.8:5050',
				isRecording: false,
				isTtsPlaying: false,
				recorderManager: null,
				innerAudioContext: null,
			}
		},
		onShow() {
			this.setSafeArea();
			this.createWs();
		},
		beforeDestroy() {

		},
		computed: {
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
			}
		},
		methods:{
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
				this.websocket = new wsRequest(`ws://192.168.1.8:5050/api/v1/gpt/ws/${token}`,5000) // Python Agent
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
			    url: "/pages/sys/personal/setting/setting",
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
				}	
			},
			getAnswer(ask){
				// this.isLeft = 1;
				this.answerText = ""
				this.textList.push(this.answerText);
				this.toBottom();
				this.count ++ ;
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
		// border: 2px solid red;
		width: 100%;
		margin: 0 auto;
		position: absolute;
		bottom: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		// justify-content: center;
		// .inner {
		// 	border: 2px solid blue;
		// 	width: 95%;
		// 	display: flex;
		// 	flex-direction: column;
		//  justify-content: space-around;
			.header {
				// border: 2px solid red;
				width: 95%;
				display: flex;
				justify-content: space-between;
				align-items: center;
				margin-bottom: 3%;
				padding: 0 5rpx;
				padding-bottom: 0;
				box-sizing: border-box;
				height: 80rpx;
				.topNav {
					// border: 2px solid red;
					width: 445rpx;
					display: flex;
					justify-content: space-between;
					.choosen {
						display: flex;
						justify-content: center;
						align-items: flex-end;
						span {
							font-size: 40rpx;
							position: relative;
						}
						h2::after {
							content: "";
							position: absolute;
							width: 100%;
							height: 28%;
							left: 0;
							bottom: 2px;
							background: #9eb3ff;
							z-index: -1;
							border-radius: 5rpx;
							font-size: 80rpx;
						}
					}
				}
				.setting {
					// border: 2px solid red;
					width: 30px;
					height: 30px;
					image {
						width: 100%;
						height: 100%;
					}
				}
			}
			.body {
				position: absolute;
				bottom: 0;
				width: 100%;
				height: 93%;
				background-color: #E9EEFF;
				border-radius: 50rpx 50rpx 0 0rpx;
				display: flex;
				flex-direction: column;
				align-items: center;
				justify-content: flex-start;
				.title {
					width: 80%;
					height: 7%;
					border: 2px solid #8891b5;
					border-top: 0;
					border-left: 0;
					border-right: 0;
					display: flex;
					justify-content:center;
					align-items: center;
					margin-bottom: 20rpx;
					span {
						color: #747EA1;
						font-size: 40rpx;
						font-weight: 700;
						font-family: "Novecento wide", "半展开", "粗体";
					}
				}
				.scroll {
					flex: 1;
					min-height: 0;
					width: 100%;
					box-sizing: border-box;
					overflow: hidden;
					.chat {
						// width: 98%;
						// height: 79%;	
						background-color: #E9EEFF;
						// border: 2px solid red;
						display: flex;
						flex-direction: column;
						align-items: center;
						justify-content: flex-start;
						///////LEFT//////
						.left {
							
							width: 95%;
							// height: 10%;
							// border: 2px solid green;
							margin-bottom: 15rpx;
							display: flex;
							flex-direction: row;
							align-items: flex-start;
							.avatar {
								width: 100rpx;
								height: 100rpx;
								background-color: #fff;
								border-radius: 50%;
								image {
									width: 100%;
									height: 100%;
									border-radius: 50%;
								}
							}
							.msg {
								// width: 70%;
								margin-top: 15rpx;
								max-width: 70%;
								// height: 80%;
								background-color: white;
								margin-left: 20rpx;
								box-sizing: border-box;
								padding: 5px 10px;
								border-radius: 20rpx;
								view {
									// width: 96%;
									word-break:break-all;
									word-wrap:break-word;
									// border: 2px solid red;
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
							// height: 10%;
							// border: 2px solid green;
							margin-bottom: 15rpx;
							display: flex;
							flex-direction: row-reverse;
							align-items: flex-start;
							.avatar {
								width: 100rpx;
								height: 100rpx;
								background-color: #fff;
								border-radius: 50%;
								image {
									width: 100%;
									height: 100%;
									border-radius: 50%;
								}
							}
							.msg {
								// width: 70%;
								margin-top: 15rpx;
								max-width: 70%;
								// height: 80%;
								background-color: white;
								margin-right: 20rpx;
								box-sizing: border-box;
								padding: 5px 10px;
								border-radius: 20rpx;
								view {
									// width: 96%;
									word-break:break-all;
									word-wrap:break-word;
									// border: 2px solid red;
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
					background-color: #DDE4FF;
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
					background-color: #fff;
					border-radius: 44rpx;
					overflow: hidden;
					padding: 0 8rpx 0 28rpx;
					box-sizing: border-box;
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
					background-color: #E0E6FF;
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
					background-color: #5a6ab8;
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
					color: #747EA1;
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
