import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import { WebSocketService } from './services/websocket'
import './App.css'

function App() {
  const [wsService] = useState(() => new WebSocketService())

  useEffect(() => {
    wsService.connect()
    return () => {
      wsService.disconnect()
    }
  }, [])

  return (
    <div className="App">
      <Dashboard wsService={wsService} />
    </div>
  )
}

export default App

