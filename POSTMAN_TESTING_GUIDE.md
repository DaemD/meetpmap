# Postman Testing Guide - Railway Backend

## 🎯 **Your Railway URL**

```
https://meetpmap-production.up.railway.app
```

---

## 📋 **Postman Setup**

### **Step 1: Create New Request**

1. Open Postman
2. Click **"New"** → **"HTTP Request"**
3. Or click **"+"** to create new tab

### **Step 2: Configure Request**

**Method:** `POST`  
**URL:** `https://meetpmap-production.up.railway.app/api/transcript`

**Important:** Use `https://` (not `http://`)

---

## 📦 **Request Body (JSON)**

### **Step 3: Set Request Body**

1. Click **"Body"** tab
2. Select **"raw"**
3. Select **"JSON"** from dropdown (right side)

### **Step 4: Enter JSON**

**Required Fields:**
- `text` (string) - The transcript text
- `start` (number) - Start timestamp in seconds
- `end` (number) - End timestamp in seconds

**Optional Fields:**
- `speaker` (string) - Speaker name
- `chunk_id` (string) - Unique chunk identifier

---

## 📝 **Example JSON**

### **Example 1: Basic Transcript**

```json
{
  "text": "We need to implement a new feature for user authentication. This will include login, registration, and password reset functionality.",
  "start": 0.0,
  "end": 5.5,
  "speaker": "John",
  "chunk_id": "chunk_001"
}
```

### **Example 2: Meeting Discussion**

```json
{
  "text": "Let's discuss the quarterly budget. We have $50,000 allocated for marketing. I think we should invest in social media advertising and content creation.",
  "start": 10.0,
  "end": 15.2,
  "speaker": "Sarah",
  "chunk_id": "chunk_002"
}
```

### **Example 3: Minimal (Only Required Fields)**

```json
{
  "text": "The project deadline has been moved to next month. We need to adjust our timeline accordingly.",
  "start": 20.0,
  "end": 25.0
}
```

---

## 🚀 **Send Request**

### **Step 5: Send**

1. Click **"Send"** button
2. Wait for response (may take 10-30 seconds first time)

---

## ✅ **Expected Response**

### **Success Response (200 OK):**

```json
{
  "status": "success",
  "nodes": [
    {
      "id": "node_123",
      "text": "Implement user authentication feature",
      "type": "idea",
      "timestamp": 0.0,
      "confidence": 1.0,
      "metadata": {
        "depth": 1,
        "parent_id": "root",
        "cluster_id": 0,
        "cluster_color": "#FF6B6B"
      }
    }
  ],
  "edges": [
    {
      "from_node": "root",
      "to_node": "node_123",
      "type": "root",
      "strength": 1.0,
      "metadata": {
        "relationship": "parent_child"
      }
    }
  ]
}
```

### **Error Response (500):**

```json
{
  "status": "error",
  "message": "Error description here"
}
```

---

## 🧪 **Test Other Endpoints**

### **1. Health Check**

**Method:** `GET`  
**URL:** `https://meetpmap-production.up.railway.app/health`

**Expected:**
```json
{
  "status": "healthy"
}
```

### **2. Root Endpoint**

**Method:** `GET`  
**URL:** `https://meetpmap-production.up.railway.app/`

**Expected:**
```json
{
  "message": "MeetMap Prototype API",
  "status": "running"
}
```

### **3. Get Graph State**

**Method:** `GET`  
**URL:** `https://meetpmap-production.up.railway.app/api/graph/state`

**Expected:**
```json
{
  "status": "success",
  "nodes": [...],
  "edges": [...]
}
```

---

## 📋 **Complete Postman Configuration**

### **Request Settings:**

| Setting | Value |
|---------|-------|
| **Method** | `POST` |
| **URL** | `https://meetpmap-production.up.railway.app/api/transcript` |
| **Headers** | Auto-set by Postman (Content-Type: application/json) |
| **Body** | `raw` → `JSON` |

### **Headers (Auto-Set):**

Postman automatically sets:
```
Content-Type: application/json
```

**You don't need to add headers manually!**

---

## 🐛 **Troubleshooting**

### **Error: "Connection refused"**
- **Cause:** Service not running
- **Fix:** Check Railway dashboard - service should be "Active"

### **Error: "SSL/TLS error"**
- **Cause:** Using `http://` instead of `https://`
- **Fix:** Use `https://meetpmap-production.up.railway.app`

### **Error: "404 Not Found"**
- **Cause:** Wrong endpoint path
- **Fix:** Use `/api/transcript` (not `/api/transcript/`)

### **Error: "422 Unprocessable Entity"**
- **Cause:** Missing required fields or wrong JSON format
- **Fix:** Check JSON has `text`, `start`, `end` fields

### **Error: "500 Internal Server Error"**
- **Cause:** Backend error (check Railway logs)
- **Fix:** Check Railway deployment logs for error details

### **Error: "Timeout"**
- **Cause:** First request takes longer (model loading)
- **Fix:** Wait 30-60 seconds, or check Railway logs

---

## 💡 **Pro Tips**

### **1. Save Request**
- Click **"Save"** to save your request
- Create a collection: "MeetMap API Tests"

### **2. Use Variables**
- Set `base_url` variable: `https://meetpmap-production.up.railway.app`
- Use `{{base_url}}/api/transcript` in URL

### **3. Test Multiple Chunks**
- Send multiple transcript chunks sequentially
- Each chunk creates new nodes in the graph
- Use different `chunk_id` for each

### **4. Check Graph State**
- After sending chunks, call `/api/graph/state`
- See all nodes and edges created

---

## 📝 **Quick Reference**

### **Endpoint:**
```
POST https://meetpmap-production.up.railway.app/api/transcript
```

### **Minimal JSON:**
```json
{
  "text": "Your transcript text here",
  "start": 0.0,
  "end": 5.0
}
```

### **Full JSON:**
```json
{
  "text": "Your transcript text here",
  "start": 0.0,
  "end": 5.0,
  "speaker": "John",
  "chunk_id": "chunk_001"
}
```

---

## ✅ **Step-by-Step Checklist**

- [ ] Open Postman
- [ ] Create new POST request
- [ ] Set URL: `https://meetpmap-production.up.railway.app/api/transcript`
- [ ] Go to Body tab
- [ ] Select "raw" and "JSON"
- [ ] Paste JSON with `text`, `start`, `end`
- [ ] Click "Send"
- [ ] Wait for response (10-30 seconds)
- [ ] Check response for `status: "success"`

---

## 🎯 **Ready to Test!**

**Your URL:** `https://meetpmap-production.up.railway.app`  
**Endpoint:** `/api/transcript`  
**Method:** `POST`  
**Body:** JSON with `text`, `start`, `end`

**Copy this JSON and test:**
```json
{
  "text": "We need to improve our customer support system. Let's add a chatbot and implement a ticketing system for better response times.",
  "start": 0.0,
  "end": 8.5,
  "speaker": "Alice",
  "chunk_id": "test_001"
}
```

**Good luck!** 🚀

