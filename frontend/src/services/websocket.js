export class WebSocketService {
  constructor() {
    this.socket = null
    this.listeners = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }

  connect() {
    const wsUrl = 'ws://localhost:8001/ws'
    this.socket = new WebSocket(wsUrl)

    this.socket.onopen = () => {
      console.log('Connected to WebSocket')
      this.reconnectAttempts = 0
      this.emit('connect', {})
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type || 'message'
        // For new_nodes, pass the entire data object
        if (type === 'new_nodes') {
          this.emit(type, data.data || data)
        } else {
          this.emit(type, data.data || data)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.emit('error', error)
    }

    this.socket.onclose = () => {
      console.log('Disconnected from WebSocket')
      this.emit('disconnect', {})
      
      // Attempt to reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        setTimeout(() => {
          console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
          this.connect()
        }, 1000 * this.reconnectAttempts)
      }
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
  }

  sendTranscriptChunk(chunk) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'transcript_chunk',
        data: chunk
      }))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data))
    }
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN
  }
}

