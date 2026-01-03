# Deployment Order - Multi-User Support

## 🎯 **Recommended Order**

### **Step 1: Add Frontend User ID Mechanism** ✅ (Do This First)
- Add simple `user_id` storage/retrieval
- Update Dashboard to use `user_id`
- Test locally

### **Step 2: Test Locally** ✅
- Run backend locally
- Run frontend locally
- Verify `user_id` is sent and filtered correctly

### **Step 3: Deploy to Railway** ✅
- Push all changes to GitHub
- Railway auto-deploys
- Test on production

---

## ✅ **What I Just Did**

I've updated `Dashboard.jsx` to:
1. **Get or create `user_id`** from localStorage
2. **Pass `user_id`** to `api.getGraphState(userId)`
3. **Re-fetch** when `userId` changes

**How it works:**
- On first visit, generates a unique `user_id`: `user_1234567890_abc123`
- Stores it in `localStorage` as `meetmap_user_id`
- Uses same `user_id` on future visits
- Passes `user_id` to all API calls

---

## 🧪 **Test Locally First**

### **1. Start Backend:**
```bash
cd backend
python main.py
```

### **2. Start Frontend:**
```bash
cd frontend
npm run dev
```

### **3. Test:**
- Open browser: `http://localhost:5173`
- Check console: Should see "Created new user ID: user_xxx"
- Check Network tab: API calls should include `?user_id=user_xxx`
- Send a transcript chunk (if you have UI for it)
- Verify only your nodes appear

### **4. Test Multi-User:**
- Open browser in **Incognito/Private mode**
- Should get a different `user_id`
- Send different transcript
- Verify nodes are isolated

---

## 🚀 **Then Deploy**

### **1. Commit Changes:**
```bash
git add .
git commit -m "Add multi-user support with user_id isolation"
git push origin main
```

### **2. Railway Auto-Deploys:**
- Railway detects push to `main`
- Auto-builds and deploys
- Takes 5-10 minutes

### **3. Test on Production:**
- Open your Railway URL
- Check console for `user_id`
- Verify API calls include `user_id`
- Test with multiple users (different browsers/devices)

---

## 📋 **What's Ready**

### **Backend:**
- ✅ Accepts `user_id` in requests
- ✅ Filters nodes by `user_id`
- ✅ Creates user-specific roots
- ✅ Backward compatible

### **Frontend:**
- ✅ Gets/stores `user_id` from localStorage
- ✅ Passes `user_id` to `getGraphState()`
- ✅ API methods accept `userId` parameter

### **Still Need:**
- ⚠️ Update any component that sends transcripts to pass `userId`
- ⚠️ Test locally first
- ⚠️ Then deploy

---

## 🔍 **Find Where Transcripts Are Sent**

If you have a component that sends transcripts, update it:

```javascript
// In your component that sends transcripts
import { api } from '../services/api'

const userId = localStorage.getItem('meetmap_user_id')
await api.processTranscript(chunk, userId)
```

---

## ✅ **Summary**

**Do This:**
1. ✅ **Frontend user_id mechanism** - DONE (just added)
2. ⚠️ **Test locally** - Do this now
3. ⚠️ **Deploy to Railway** - After testing

**Order:**
1. Test locally first (make sure it works)
2. Then deploy (Railway auto-deploys on push)

**Your frontend is ready!** Just test locally, then push to deploy! 🚀

