class websocketUtil {
	constructor(url, time) {
		this.is_open_socket = false //避免重复连接
		this.is_connecting = false
		this.manual_close = false
		this.url = url //地址
		this.data = null
		//心跳检测
		this.timeout= time //多少秒执行检测
		this.heartbeatInterval= null //检测服务器端是否还活着
		this.reconnectTimeOut= null //重连之后多久再次重连
		this.reconnectAttempts = 0
		this.maxReconnectAttempts = 3

		try {
			this.connectSocketInit()
		} catch (e) {
			console.log('catch');
			this.is_open_socket = false
			this.reconnect();
		}
	}

	// 进入这个页面的时候创建websocket连接【整个页面随时使用】
	connectSocketInit() {
		if (this.manual_close || this.is_open_socket || this.is_connecting) {
			return
		}
		this.is_connecting = true
		this.socketTask = uni.connectSocket({
			url: this.url,
			success:()=>{
				console.log("正准备建立websocket中...");
				// 返回实例
				return this.socketTask
			},
		});
		if (!this.socketTask || typeof this.socketTask.onOpen !== 'function') {
			console.warn('websocket connect failed: invalid socketTask', this.url)
			this.is_open_socket = false
			this.is_connecting = false
			this.reconnect();
			return
		}
		this.socketTask.onOpen((res) => {
			console.log("WebSocket连接正常！");
			clearTimeout(this.reconnectTimeOut)
			clearTimeout(this.heartbeatInterval)
			this.is_open_socket = true;
			this.is_connecting = false;
			this.reconnectAttempts = 0;
			// this.start();
			// 注：只有连接正常打开中 ，才能正常收到消息
			// this.socketTask.onMessage((res) => {
			// 	console.log(res.data)
			// });
		})
		this.socketTask.onClose(() => {
			console.log("已经被关闭了")
			this.is_open_socket = false;
			this.is_connecting = false;
			if (!this.manual_close) this.reconnect();
		})
		if (typeof this.socketTask.onError === 'function') {
			this.socketTask.onError((err) => {
				console.warn('websocket error', err)
				this.is_open_socket = false
				this.is_connecting = false
				this.reconnect();
			})
		}
	}
	
	//发送消息
	send(value){
		if (!this.socketTask || !this.is_open_socket) {
			console.warn('websocket not ready, skip send')
			return false
		}
		// 注：只有连接正常打开中 ，才能正常成功发送消息
		this.socketTask.send({
			data: value,
			async success() {
				console.log("消息发送成功");
			},
		});
		return true
	}
	//开启心跳检测
	start(){
		this.heartbeatInterval = setTimeout(()=>{
			this.data={value:"",method:""}
			console.log(this.data)
			this.send(JSON.stringify(this.data));
		},this.timeout)
	}
	//重新连接
	reconnect(){
		//停止发送心跳
		clearTimeout(this.heartbeatInterval)
		if (this.manual_close || this.is_open_socket || this.is_connecting) return
		if (this.reconnectAttempts >= this.maxReconnectAttempts) {
			console.warn('websocket reconnect stopped: max attempts reached', this.url)
			return
		}
		if (this.reconnectTimeOut) return
		//如果不是人为关闭的话，进行重连
		this.reconnectAttempts += 1
		this.reconnectTimeOut = setTimeout(()=>{
			this.reconnectTimeOut = null
			this.connectSocketInit();
		},3000)
	}
	//外部获取消息
	getMessage(callback) {
		if (!this.socketTask || typeof this.socketTask.onMessage !== 'function') return
		this.socketTask.onMessage((res) => {
			return callback(res)
		})
	}

	close() {
		this.manual_close = true
		this.is_open_socket = false
		this.is_connecting = false
		clearTimeout(this.heartbeatInterval)
		clearTimeout(this.reconnectTimeOut)
		this.heartbeatInterval = null
		this.reconnectTimeOut = null
		if (this.socketTask && typeof this.socketTask.close === 'function') {
			this.socketTask.close({})
		}
	}
 
}

module.exports = websocketUtil
