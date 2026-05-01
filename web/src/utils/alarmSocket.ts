import { webSocketBaseUrl } from '@/config/config'

export interface AlarmSocketMessage {
  type?: string
  message?: string
  data?: any
  [key: string]: any
}

interface AlarmSocketOptions {
  userId: number | string
  onAlarm: (message: AlarmSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (event: Event) => void
}

const HEARTBEAT_INTERVAL_MS = 30000
const RECONNECT_DELAY_MS = 5000

export class AlarmSocketClient {
  private socket: WebSocket | null = null
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private closedByUser = false
  private readonly options: AlarmSocketOptions

  constructor(options: AlarmSocketOptions) {
    this.options = options
  }

  connect() {
    if (!this.options.userId) return
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    this.closedByUser = false
    const url = `${webSocketBaseUrl}/ws/alarm/${this.options.userId}`

    try {
      this.socket = new WebSocket(url)
    } catch (event) {
      this.scheduleReconnect()
      return
    }

    this.socket.onopen = () => {
      this.options.onOpen?.()
      this.startHeartbeat()
    }

    this.socket.onmessage = (event) => {
      if (event.data === 'pong' || event.data === 'ping') return
      try {
        const payload = JSON.parse(event.data)
        if (payload?.type === 'NEW_ALARM') {
          this.options.onAlarm(payload)
        }
      } catch (error) {
        console.warn('[AlarmSocket] 消息解析失败:', error)
      }
    }

    this.socket.onerror = (event) => {
      this.options.onError?.(event)
    }

    this.socket.onclose = () => {
      this.stopHeartbeat()
      this.options.onClose?.()
      if (!this.closedByUser) {
        this.scheduleReconnect()
      }
    }
  }

  close() {
    this.closedByUser = true
    this.clearReconnect()
    this.stopHeartbeat()
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send('ping')
      }
    }, HEARTBEAT_INTERVAL_MS)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer !== null) {
      window.clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null || this.closedByUser) return
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, RECONNECT_DELAY_MS)
  }

  private clearReconnect() {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}
