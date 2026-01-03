# User Isolation Confirmation

## ✅ **YES - Each User Will Only See Their Own Graph**

**IF** both conditions are met:
1. ✅ Users send chunks with their own `user_id`
2. ✅ Frontend requests graph state with `user_id`

---

## 🔍 **How It Works**

### **Scenario: Two Users**

#### **User 1 (john_doe):**
```javascript
// Sends chunk
POST /api/transcript
{
  "text": "We need authentication",
  "user_id": "john_doe"  // ← User 1's ID
}

// Requests graph
GET /api/graph/state?user_id=john_doe  // ← User 1's ID
```

**Backend creates:**
- `root_john_doe` (user-specific root)
- `node_1` (metadata: `{"user_id": "john_doe"}`)
- `node_2` (metadata: `{"user_id": "john_doe"}`)

**Backend returns:**
- Only nodes where `metadata["user_id"] == "john_doe"`
- Only `root_john_doe` and john_doe's nodes

**Frontend displays:** Only john_doe's graph ✅

---

#### **User 2 (jane_doe):**
```javascript
// Sends chunk
POST /api/transcript
{
  "text": "Let's discuss budget",
  "user_id": "jane_doe"  // ← User 2's ID
}

// Requests graph
GET /api/graph/state?user_id=jane_doe  // ← User 2's ID
```

**Backend creates:**
- `root_jane_doe` (user-specific root)
- `node_3` (metadata: `{"user_id": "jane_doe"}`)
- `node_4` (metadata: `{"user_id": "jane_doe"}`)

**Backend returns:**
- Only nodes where `metadata["user_id"] == "jane_doe"`
- Only `root_jane_doe` and jane_doe's nodes

**Frontend displays:** Only jane_doe's graph ✅

---

## 🔒 **Isolation Guarantees**

### **1. Node Creation:**
- ✅ User 1's chunks → Creates nodes with `user_id: "john_doe"`
- ✅ User 2's chunks → Creates nodes with `user_id: "jane_doe"`
- ✅ Nodes are **tagged** with user_id in metadata

### **2. Similar Node Search:**
- ✅ User 1 searches → Only searches john_doe's nodes
- ✅ User 2 searches → Only searches jane_doe's nodes
- ✅ **No cross-user matching**

### **3. Graph Retrieval:**
- ✅ `GET /api/graph/state?user_id=john_doe` → Only john_doe's nodes
- ✅ `GET /api/graph/state?user_id=jane_doe` → Only jane_doe's nodes
- ✅ **Filtered by user_id**

### **4. Root Nodes:**
- ✅ User 1 gets: `root_john_doe`
- ✅ User 2 gets: `root_jane_doe`
- ✅ **Separate roots per user**

---

## ⚠️ **Important: Frontend Must Send user_id**

### **Current Frontend Implementation:**

**Dashboard.jsx:**
```javascript
export default function Dashboard({ userId }) {
  // userId must be passed as prop from your service
  
  const fetchGraphState = async () => {
    const response = await api.getGraphState(userId)  // ← Passes userId
    // ...
  }
}
```

**TranscriptInput.jsx:**
```javascript
export default function TranscriptInput({ userId, ... }) {
  const response = await api.processTranscript(chunk, userId)  // ← Passes userId
}
```

**API Service:**
```javascript
async getGraphState(userId = null) {
  const params = userId ? { user_id: userId } : {}
  const response = await axios.get(`${API_BASE_URL}/api/graph/state`, { params })
  // Sends: GET /api/graph/state?user_id=john_doe
}

async processTranscript(chunk, userId = null) {
  const chunkWithUser = userId ? { ...chunk, user_id: userId } : chunk
  const response = await axios.post(`${API_BASE_URL}/api/transcript`, chunkWithUser)
  // Sends: POST /api/transcript with user_id in body
}
```

---

## ✅ **What You Need to Do**

### **1. Get userId from Your Service:**
```javascript
// In your parent component/service
const userId = getUserIdFromYourAuthService()  // Your function

<Dashboard userId={userId} />
<TranscriptInput userId={userId} />
```

### **2. Ensure userId is Always Sent:**
- ✅ When sending chunks: Include `user_id` in request body
- ✅ When fetching graph: Include `user_id` as query parameter

---

## 🧪 **Test Isolation**

### **Test 1: User 1**
```javascript
// Send chunk
POST /api/transcript
{ "text": "User 1 idea", "user_id": "user1" }

// Get graph
GET /api/graph/state?user_id=user1
```
**Expected:** Only user1's nodes

### **Test 2: User 2**
```javascript
// Send chunk
POST /api/transcript
{ "text": "User 2 idea", "user_id": "user2" }

// Get graph
GET /api/graph/state?user_id=user2
```
**Expected:** Only user2's nodes

### **Test 3: Verify Isolation**
```javascript
// User 1 requests graph
GET /api/graph/state?user_id=user1
// Should NOT see user2's nodes

// User 2 requests graph
GET /api/graph/state?user_id=user2
// Should NOT see user1's nodes
```

---

## 📊 **Backend Storage (All Users Together)**

```python
self.nodes = {
    # User 1's nodes
    "root_user1": {metadata: {"user_id": "user1"}},
    "node_1": {metadata: {"user_id": "user1"}},
    "node_2": {metadata: {"user_id": "user1"}},
    
    # User 2's nodes
    "root_user2": {metadata: {"user_id": "user2"}},
    "node_3": {metadata: {"user_id": "user2"}},
    "node_4": {metadata: {"user_id": "user2"}},
}
```

**But filtering ensures:**
- User 1 only sees: `root_user1`, `node_1`, `node_2`
- User 2 only sees: `root_user2`, `node_3`, `node_4`

---

## ✅ **Summary**

**Question:** Will each user only see their own graph?

**Answer:** **YES!** ✅

**Requirements:**
1. ✅ Each user sends chunks with their own `user_id`
2. ✅ Frontend passes `userId` to Dashboard and TranscriptInput
3. ✅ Frontend requests graph with `user_id` parameter

**How it works:**
- Backend stores all nodes together (tagged with `user_id`)
- Backend filters by `user_id` on retrieval
- Each user gets isolated graph view
- No cross-user data leakage

**Your implementation is correct!** 🎉

