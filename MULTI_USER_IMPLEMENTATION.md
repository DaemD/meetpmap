# Multi-User Implementation Guide

## ✅ **What I've Implemented**

### **1. User Isolation in Backend**

**Added `user_id` support:**
- ✅ `TranscriptChunk` schema now includes optional `user_id` field
- ✅ Nodes store `user_id` in metadata
- ✅ Graph queries filter by `user_id`
- ✅ Each user gets their own root node

### **2. Updated Endpoints**

**`POST /api/transcript`:**
- Accepts `user_id` in request body (optional)
- If provided, nodes are isolated to that user
- If not provided, nodes are shared (backward compatible)

**`GET /api/graph/state`:**
- Accepts `user_id` as query parameter (optional)
- Returns only nodes for that user
- If not provided, returns all nodes (backward compatible)

### **3. Updated Frontend API**

**`api.processTranscript(chunk, userId)`:**
- Accepts optional `userId` parameter
- Adds `user_id` to chunk before sending

**`api.getGraphState(userId)`:**
- Accepts optional `userId` parameter
- Sends `user_id` as query parameter

---

## 🚀 **How to Use**

### **Option 1: Single User (Current Behavior)**

**No changes needed!** If you don't provide `user_id`, everything works as before (all nodes shared).

### **Option 2: Multi-User with User ID**

#### **Backend (Postman/API):**

**Send transcript with user_id:**
```json
{
  "text": "We need to implement user authentication",
  "start": 0.0,
  "end": 5.0,
  "user_id": "user_123"
}
```

**Get graph state for specific user:**
```
GET https://meetpmap-production.up.railway.app/api/graph/state?user_id=user_123
```

#### **Frontend:**

**Update Dashboard.jsx:**
```javascript
// Get user_id from localStorage, auth, or props
const userId = localStorage.getItem('userId') || 'user_123'

// Fetch graph state for this user
const response = await api.getGraphState(userId)

// Send transcript with user_id
await api.processTranscript(chunk, userId)
```

---

## 📋 **Implementation Details**

### **How User Isolation Works:**

1. **Node Creation:**
   - When `user_id` is provided, it's stored in node metadata
   - Each user gets their own root node: `root_{user_id}`

2. **Graph Queries:**
   - `get_all_nodes(user_id)` filters nodes by `user_id`
   - `find_globally_similar_nodes()` only searches within user's nodes
   - Each user's graph is completely isolated

3. **Root Node:**
   - Global root: `root` (for nodes without user_id)
   - User root: `root_{user_id}` (for nodes with user_id)
   - Created automatically on first node for that user

---

## 🔧 **Frontend Integration**

### **Step 1: Get User ID**

You can get `user_id` from:
- **localStorage**: `localStorage.getItem('userId')`
- **Auth token**: Decode JWT or session
- **URL parameter**: `?user_id=xxx`
- **Props**: Pass from parent component

### **Step 2: Update Dashboard**

```javascript
// frontend/src/components/Dashboard.jsx
import { useState, useEffect } from 'react'
import NodeMap from './NodeMap'
import { api } from '../services/api'
import './Dashboard.css'

export default function Dashboard() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  
  // Get user_id (you can change this logic)
  const userId = localStorage.getItem('userId') || null

  const fetchGraphState = async () => {
    try {
      const response = await api.getGraphState(userId)  // Pass userId
      if (response.status === 'success') {
        setNodes(response.nodes || [])
        setEdges(response.edges || [])
      }
    } catch (error) {
      console.error('Error fetching graph state:', error)
    }
  }

  useEffect(() => {
    fetchGraphState()
    const interval = setInterval(fetchGraphState, 2000)
    return () => clearInterval(interval)
  }, [userId])  // Re-fetch when userId changes

  return (
    <div className="dashboard">
      <NodeMap nodes={nodes} edges={edges} />
    </div>
  )
}
```

### **Step 3: Send Transcripts with User ID**

When sending transcript chunks:
```javascript
// In your component that sends transcripts
const userId = localStorage.getItem('userId') || 'user_123'
await api.processTranscript(chunk, userId)
```

---

## 🧪 **Testing**

### **Test Multi-User:**

1. **User 1:**
   ```json
   POST /api/transcript
   {
     "text": "User 1's idea",
     "start": 0.0,
     "end": 5.0,
     "user_id": "user_1"
   }
   ```

2. **User 2:**
   ```json
   POST /api/transcript
   {
     "text": "User 2's idea",
     "start": 0.0,
     "end": 5.0,
     "user_id": "user_2"
   }
   ```

3. **Get User 1's Graph:**
   ```
   GET /api/graph/state?user_id=user_1
   ```
   Should only return User 1's nodes

4. **Get User 2's Graph:**
   ```
   GET /api/graph/state?user_id=user_2
   ```
   Should only return User 2's nodes

---

## ✅ **Backward Compatibility**

**Everything is backward compatible!**

- ✅ If `user_id` is not provided, nodes are shared (old behavior)
- ✅ If `user_id` is provided, nodes are isolated (new behavior)
- ✅ Existing code works without changes

---

## 🎯 **Next Steps**

1. **Update Frontend:**
   - Get `user_id` from auth/localStorage
   - Pass `userId` to `api.getGraphState(userId)`
   - Pass `userId` to `api.processTranscript(chunk, userId)`

2. **Test:**
   - Send chunks with different `user_id` values
   - Verify each user only sees their own nodes

3. **Deploy:**
   - Push changes to GitHub
   - Railway auto-deploys
   - Test on production

---

## 📝 **Summary**

**What's Done:**
- ✅ Backend supports `user_id` filtering
- ✅ Each user gets isolated graph
- ✅ Frontend API updated to support `user_id`
- ✅ Backward compatible (works without `user_id`)

**What You Need to Do:**
- ⚠️ Update frontend to get and pass `user_id`
- ⚠️ Test with multiple users
- ⚠️ Deploy to Railway

**Your multi-user system is ready!** 🎉

