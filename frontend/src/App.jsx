import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [meetingId, setMeetingId] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Get meeting_id from URL parameter
    const fetchMeetingId = async () => {
      try {
        // Get from URL parameter (required)
        const params = new URLSearchParams(window.location.search)
        const urlMeetingId = params.get('meeting_id')
        
        if (urlMeetingId) {
          setMeetingId(urlMeetingId)
          setLoading(false)
          return
        }
        
        // Fallback: Check localStorage
        const storedMeetingId = localStorage.getItem('meeting_id')
        
        if (storedMeetingId) {
          setMeetingId(storedMeetingId)
        } else {
          console.warn('No meeting_id found. Please provide meeting_id via URL (?meeting_id=xxx)')
        }
      } catch (error) {
        console.error('Error fetching meeting_id:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchMeetingId()
  }, [])
  
  if (loading) {
    return (
      <div className="App" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    )
  }
  
  if (!meetingId) {
    return (
      <div className="App" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <h2>No meeting ID found</h2>
        <p>Please provide meeting_id via:</p>
        <ul style={{ textAlign: 'left' }}>
          <li>URL parameter: <code>?meeting_id=your_meeting_id</code></li>
          <li>Example: <code>?meeting_id=meeting_07507e7bb202</code></li>
        </ul>
      </div>
    )
  }
  
  return (
    <div className="App">
      <Dashboard meetingId={meetingId} />
    </div>
  )
}

export default App

