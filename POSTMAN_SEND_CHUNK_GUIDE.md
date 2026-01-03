# Postman Guide - Send Transcript Chunk

## 🎯 **Quick Steps**

### **1. Open Postman**
- Create new request or open existing

### **2. Set Method & URL**
- **Method:** `POST`
- **URL:** `https://meetpmap-production.up.railway.app/api/transcript`
  - Or for local: `http://localhost:8001/api/transcript`

### **3. Set Headers**
- Go to **"Headers"** tab
- Postman auto-adds `Content-Type: application/json` (or add it manually)

### **4. Set Body**
- Go to **"Body"** tab
- Select **"raw"**
- Select **"JSON"** from dropdown (right side)

### **5. Enter JSON**
Paste this JSON (modify as needed):

```json
{
  "text": "We need to implement user authentication system with login and registration functionality.",
  "start": 0.0,
  "end": 5.5,
  "speaker": "John",
  "chunk_id": "chunk_001",
  "user_id": "john_doe"
}
```

### **6. Click Send**
- Wait 10-30 seconds (first request may be slower)
- Check response

---

## 📋 **Complete Configuration**

### **Request Settings:**

| Setting | Value |
|---------|-------|
| **Method** | `POST` |
| **URL** | `https://meetpmap-production.up.railway.app/api/transcript` |
| **Headers** | `Content-Type: application/json` (auto-set) |
| **Body** | `raw` → `JSON` |

---

## 📝 **JSON Body Fields**

### **Required Fields:**
- `text` (string) - The transcript text
- `start` (number) - Start timestamp in seconds
- `end` (number) - End timestamp in seconds

### **Optional Fields:**
- `speaker` (string) - Speaker name
- `chunk_id` (string) - Unique chunk identifier
- `user_id` (string) - **User identifier (for multi-user isolation)**

---

## 📦 **Example JSON Bodies**

### **Example 1: Basic Chunk with user_id**
```json
{
  "text": "We need to implement user authentication system with login and registration functionality.",
  "start": 0.0,
  "end": 5.5,
  "user_id": "john_doe"
}
```

### **Example 2: Full Chunk with All Fields**
```json
{
  "text": "Let's discuss the quarterly budget. We have $50,000 allocated for marketing. I think we should invest in social media advertising and content creation.",
  "start": 10.0,
  "end": 15.2,
  "speaker": "Sarah",
  "chunk_id": "chunk_002",
  "user_id": "sarah_smith"
}
```

### **Example 3: Minimal (Only Required)**
```json
{
  "text": "The project deadline has been moved to next month. We need to adjust our timeline accordingly.",
  "start": 20.0,
  "end": 25.0,
  "user_id": "test_user"
}
```

---

## ✅ **Expected Response**

### **Success (200 OK):**
```json
{
  "status": "success",
  "nodes": [
    {
      "id": "node_1",
      "text": "Implement user authentication system",
      "type": "idea",
      "timestamp": 0.0,
      "confidence": 1.0,
      "metadata": {
        "user_id": "john_doe",
        "depth": 1,
        "parent_id": "root_john_doe",
        "cluster_id": 0,
        "cluster_color": "#FF6B6B"
      }
    }
  ],
  "edges": [
    {
      "from_node": "root_john_doe",
      "to_node": "node_1",
      "type": "root",
      "strength": 1.0
    }
  ]
}
```

### **Error (500):**
```json
{
  "status": "error",
  "message": "Error description here"
}
```

---

## 🧪 **Testing Multi-User**

### **Test User 1:**
```json
{
  "text": "User 1's idea about authentication",
  "start": 0.0,
  "end": 5.0,
  "user_id": "user_1"
}
```

### **Test User 2:**
```json
{
  "text": "User 2's idea about budget",
  "start": 0.0,
  "end": 5.0,
  "user_id": "user_2"
}
```

### **Then Get Each User's Graph:**

**User 1:**
```
GET https://meetpmap-production.up.railway.app/api/graph/state?user_id=user_1
```

**User 2:**
```
GET https://meetpmap-production.up.railway.app/api/graph/state?user_id=user_2
```

Each should only see their own nodes!

---

## 🐛 **Troubleshooting**

### **Error: "Connection refused"**
- **Cause:** Backend not running
- **Fix:** Start backend: `python main.py`

### **Error: "422 Unprocessable Entity"**
- **Cause:** Missing required fields or wrong JSON format
- **Fix:** Check JSON has `text`, `start`, `end` fields

### **Error: "500 Internal Server Error"**
- **Cause:** Backend error
- **Fix:** Check Railway logs for error details

### **Error: "Timeout"**
- **Cause:** First request takes longer (model loading)
- **Fix:** Wait 30-60 seconds, or check Railway logs

---

## 📸 **Visual Guide**

### **Postman Setup:**

1. **Method:** Dropdown → Select `POST`

2. **URL:** 
   ```
   https://meetpmap-production.up.railway.app/api/transcript
   ```

3. **Body Tab:**
   - Click **"Body"** tab
   - Select **"raw"** radio button
   - Select **"JSON"** from dropdown (top right)

4. **JSON:**
   ```json
   {
     "text": "Your transcript text here",
     "start": 0.0,
     "end": 5.0,
     "user_id": "your_user_id"
   }
   ```

5. **Send:**
   - Click blue **"Send"** button
   - Wait for response

---

## 💡 **Pro Tips**

### **1. Save Request**
- Click **"Save"** to save your request
- Create collection: "MeetMap API"

### **2. Use Variables**
- Set `base_url` variable: `https://meetpmap-production.up.railway.app`
- Use `{{base_url}}/api/transcript` in URL

### **3. Test Multiple Chunks**
- Send multiple chunks sequentially
- Each chunk creates new nodes
- Use different `chunk_id` for each

### **4. Check Graph State**
- After sending chunks, call:
  ```
  GET {{base_url}}/api/graph/state?user_id=your_user_id
  ```
- See all nodes created

---

## ✅ **Quick Checklist**

- [ ] Method: `POST`
- [ ] URL: `https://meetpmap-production.up.railway.app/api/transcript`
- [ ] Body: `raw` → `JSON`
- [ ] JSON includes: `text`, `start`, `end`, `user_id`
- [ ] Click **"Send"**
- [ ] Wait for response (10-30 seconds)

---

## 🎯 **Ready to Test!**

**Copy this JSON and test:**

```json
{
  "text": "We need to improve our customer support system. Let's add a chatbot and implement a ticketing system for better response times.",
  "start": 0.0,
  "end": 8.5,
  "speaker": "Alice",
  "chunk_id": "test_001",
  "user_id": "test_user"
}
```

**Good luck!** 🚀

