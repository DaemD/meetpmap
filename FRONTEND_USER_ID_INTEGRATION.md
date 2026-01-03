# Frontend User ID Integration Guide

## ❓ **The Problem**

When you go to `localhost:3000`, the frontend doesn't know which `user_id` to use because:
- Dashboard requires `userId` as a prop
- No one is providing it yet
- Your service needs to provide it

---

## 🔧 **Solution: Get userId from Your Service**

You need to get `userId` from your auth/service and pass it to Dashboard. Here are the options:

---

## **Option 1: Get from URL Parameter** (Quick Test)

### **Update App.jsx:**

```javascript
import { useSearchParams } from 'react-router-dom'
import Dashboard from './components/Dashboard'

function App() {
  const [searchParams] = useSearchParams()
  const userId = searchParams.get('user_id') || null
  
  return <Dashboard userId={userId} />
}
```

**Usage:**
- `http://localhost:3000?user_id=john_doe`
- Frontend gets `userId` from URL

---

## **Option 2: Get from Your Auth Service** (Recommended)

### **Update App.jsx:**

```javascript
import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'

function App() {
  const [userId, setUserId] = useState(null)
  
  useEffect(() => {
    // Get userId from your auth service
    const getUserId = async () => {
      // Option A: From your auth API
      const response = await fetch('https://your-auth-service.com/current-user')
      const user = await response.json()
      setUserId(user.id)
      
      // Option B: From localStorage (if your service stores it)
      // const storedUserId = localStorage.getItem('auth_user_id')
      // setUserId(storedUserId)
      
      // Option C: From JWT token
      // const token = localStorage.getItem('auth_token')
      // const decoded = jwt.decode(token)
      // setUserId(decoded.user_id)
    }
    
    getUserId()
  }, [])
  
  if (!userId) {
    return <div>Loading...</div>
  }
  
  return <Dashboard userId={userId} />
}
```

---

## **Option 3: Get from Window/Global** (If Your Service Sets It)

### **If your service sets a global variable:**

```javascript
// Your service sets: window.currentUserId = "john_doe"

function App() {
  const userId = window.currentUserId || null
  
  return <Dashboard userId={userId} />
}
```

---

## **Option 4: Mock for Testing** (Development Only)

### **For testing without your service:**

```javascript
function App() {
  // Mock userId for testing
  const userId = 'test_user_123'  // Replace with your service call
  
  return <Dashboard userId={userId} />
}
```

---

## 📋 **Current Setup**

### **Your App.jsx probably looks like:**

```javascript
import Dashboard from './components/Dashboard'

function App() {
  return <Dashboard />  // ❌ No userId provided
}
```

### **Should be:**

```javascript
import Dashboard from './components/Dashboard'

function App() {
  const userId = getUserIdFromYourService()  // ✅ Get from your service
  
  return <Dashboard userId={userId} />
}
```

---

## 🔍 **How to Find Your Service**

### **Check where your auth/user service is:**

1. **Check localStorage:**
   ```javascript
   const userId = localStorage.getItem('user_id')
   // or
   const userId = localStorage.getItem('auth_user_id')
   ```

2. **Check sessionStorage:**
   ```javascript
   const userId = sessionStorage.getItem('user_id')
   ```

3. **Check your auth service:**
   ```javascript
   import { getCurrentUser } from './services/auth'
   const user = getCurrentUser()
   const userId = user.id
   ```

4. **Check URL/token:**
   ```javascript
   // If userId is in URL
   const params = new URLSearchParams(window.location.search)
   const userId = params.get('user_id')
   ```

---

## ✅ **Recommended Implementation**

### **Update App.jsx:**

```javascript
import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'

function App() {
  const [userId, setUserId] = useState(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    // TODO: Replace with your actual service call
    const fetchUserId = async () => {
      try {
        // Example: Get from your auth service
        // const response = await fetch('/api/auth/current-user')
        // const user = await response.json()
        // setUserId(user.id)
        
        // For now, get from localStorage (if your service stores it there)
        const storedUserId = localStorage.getItem('user_id') || 
                            localStorage.getItem('auth_user_id') ||
                            localStorage.getItem('current_user_id')
        
        if (storedUserId) {
          setUserId(storedUserId)
        } else {
          console.warn('No userId found. Please set it in your auth service.')
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
    return <div>Loading...</div>
  }
  
  if (!userId) {
    return (
      <div>
        <h2>No user ID found</h2>
        <p>Please ensure your auth service provides a user_id</p>
      </div>
    )
  }
  
  return <Dashboard userId={userId} />
}

export default App
```

---

## 🧪 **Quick Test: URL Parameter**

### **For immediate testing, use URL parameter:**

```javascript
// App.jsx
function App() {
  const params = new URLSearchParams(window.location.search)
  const userId = params.get('user_id') || 'test_user'  // Fallback for testing
  
  return <Dashboard userId={userId} />
}
```

**Then visit:**
- `http://localhost:3000?user_id=john_doe`
- `http://localhost:3000?user_id=jane_doe`

---

## 📝 **Summary**

**Current Issue:**
- Dashboard requires `userId` prop
- App.jsx doesn't provide it
- Frontend doesn't know which user

**Solution:**
1. Get `userId` from your auth/service in App.jsx
2. Pass it to Dashboard: `<Dashboard userId={userId} />`
3. Dashboard will use it for all API calls

**Where to get userId:**
- Your auth service API
- localStorage (if your service stores it)
- URL parameter (for testing)
- JWT token (if you decode it)

**I can help you integrate it once you tell me how your service provides the userId!** 🚀

