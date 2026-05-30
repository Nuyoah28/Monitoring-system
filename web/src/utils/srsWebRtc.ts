export interface SrsWebRtcPlayer {
  close: () => void
}

interface SrsRtcAnswer {
  code: number
  sdp?: string
  server?: string
  sessionid?: string
  msg?: string
}

const DEFAULT_RTC_API = 'http://123.56.248.17:1985/rtc/v1/play/'

export const isSrsWebRtcUrl = (url?: string | null) => (
  Boolean(url && /^webrtc:\/\//i.test(url.trim()))
)

const buildRtcRequest = (url: string) => {
  const parsed = new URL(url)
  const api = parsed.searchParams.get('api') || DEFAULT_RTC_API
  const eip = parsed.searchParams.get('eip') || parsed.hostname
  const streamUrl = `webrtc://${parsed.host}${parsed.pathname}?eip=${encodeURIComponent(eip)}`
  const apiUrl = api.includes('?') ? api : `${api}?eip=${encodeURIComponent(eip)}`

  return { apiUrl, streamUrl }
}

export const createSrsWebRtcPlayer = async (
  videoEl: HTMLVideoElement,
  url: string,
): Promise<SrsWebRtcPlayer> => {
  const { apiUrl, streamUrl } = buildRtcRequest(url)
  const pc = new RTCPeerConnection({ iceServers: [] })
  const fallbackStream = new MediaStream()
  let closed = false

  pc.addTransceiver('audio', { direction: 'recvonly' })
  pc.addTransceiver('video', { direction: 'recvonly' })

  pc.ontrack = (event) => {
    const stream = event.streams[0]
    if (stream) {
      if (videoEl.srcObject !== stream) videoEl.srcObject = stream
    } else {
      if (!fallbackStream.getTracks().some(track => track.id === event.track.id)) {
        fallbackStream.addTrack(event.track)
      }
      if (videoEl.srcObject !== fallbackStream) videoEl.srcObject = fallbackStream
    }
    videoEl.play().catch(() => {})
  }
  pc.oniceconnectionstatechange = () => {
    console.info('SRS WebRTC ICE state:', pc.iceConnectionState)
  }
  pc.onconnectionstatechange = () => {
    console.info('SRS WebRTC connection state:', pc.connectionState)
  }

  try {
    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api: apiUrl,
        tid: Math.random().toString(16).slice(2),
        streamurl: streamUrl,
        clientip: null,
        sdp: offer.sdp,
      }),
    })
    const answer = await response.json() as SrsRtcAnswer
    if (!response.ok || answer.code !== 0 || !answer.sdp) {
      pc.close()
      throw new Error(answer.msg || `SRS WebRTC play failed: ${response.status}`)
    }

    await pc.setRemoteDescription({ type: 'answer', sdp: answer.sdp })
  } catch (error) {
    pc.close()
    fallbackStream.getTracks().forEach(track => track.stop())
    if (videoEl.srcObject === fallbackStream) videoEl.srcObject = null
    throw error
  }

  return {
    close: () => {
      if (closed) return
      closed = true
      pc.ontrack = null
      pc.oniceconnectionstatechange = null
      pc.onconnectionstatechange = null
      pc.close()
      fallbackStream.getTracks().forEach(track => track.stop())
      videoEl.srcObject = null
    },
  }
}
