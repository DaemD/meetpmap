import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import './App.css'

function App() {
  const [userId, setUserId] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // Get userId from your service
    // TODO: Replace this with your actual service call
    const fetchUserId = async () => {
      try {
        // Option 1: Get from URL parameter (for testing)
        const params = new URLSearchParams(window.location.search)
        const urlUserId = params.get('user_id')
        
        if (urlUserId) {
          setUserId(urlUserId)
          setLoading(false)
          return
        }
        
        // Option 2: Get from your auth service API
        // Uncomment and modify based on your service:
        // const response = await fetch('https://your-auth-service.com/api/current-user')
        // const user = await response.json()
        // setUserId(user.id)
        
        // Option 3: Get from localStorage (if your service stores it)
        const storedUserId = localStorage.getItem('user_id') || 
                            localStorage.getItem('auth_user_id') ||
                            localStorage.getItem('current_user_id')
        
        if (storedUserId) {
          setUserId(storedUserId)
        } else {
          console.warn('No userId found. Please provide userId via URL (?user_id=xxx) or your auth service.')
        }
      } catch (error) {
        console.error('Error fetching userId:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchUserId()
  }, [])
  
  if (loading) {
    return (
      <div className="App" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    )
  }
  
  if (!userId) {
    return (
      <div className="App" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <h2>No user ID found</h2>
        <p>Please provide userId via:</p>
        <ul style={{ textAlign: 'left' }}>
          <li>URL parameter: <code>?user_id=your_user_id</code></li>
          <li>Or configure your auth service to provide userId</li>
        </ul>
      </div>
    )
  }
  
  return (
    <div className="App">
      <Dashboard userId={userId} />
    </div>
  )
}

export default App

