# Frontend Update Guide - Railway Backend

## ✅ **What I Updated**

### **File: `frontend/src/services/api.js`**

**Changed from:**
```javascript
const API_BASE_URL = 'http://localhost:8001'
```

**Changed to:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://meetpmap-production.up.railway.app'
```

---

## 🎯 **What This Means**

### **Production (Default):**
- Frontend will use: `https://meetpmap-production.up.railway.app`
- Works when frontend is deployed or running locally

### **Development (Optional):**
- If you want to use local backend, create `.env.local`:
  ```
  VITE_API_URL=http://localhost:8001
  ```
- Otherwise, it uses Railway URL by default

---

## 🚀 **How to Use**

### **Option 1: Use Railway (Recommended)**
**No action needed!** The frontend is already configured to use Railway.

Just:
1. Run your frontend: `npm run dev`
2. It will connect to Railway backend automatically

### **Option 2: Use Local Backend (Development)**
If you want to test with local backend:

1. Create `frontend/.env.local`:
   ```
   VITE_API_URL=http://localhost:8001
   ```

2. Restart frontend dev server

---

## ✅ **What's Working Now**

### **Frontend → Railway Backend:**
- ✅ API calls go to: `https://meetpmap-production.up.railway.app`
- ✅ All endpoints work: `/api/transcript`, `/api/graph/state`, etc.
- ✅ CORS is configured (localhost is allowed)

---

## 🧪 **Test It**

### **1. Start Frontend:**
```bash
cd frontend
npm run dev
```

### **2. Open Browser:**
- Go to: `http://localhost:5173` (or `http://localhost:3000`)
- Frontend should connect to Railway backend

### **3. Check Network Tab:**
- Open browser DevTools → Network tab
- Send a transcript chunk
- You should see requests to: `https://meetpmap-production.up.railway.app/api/transcript`

---

## 🔧 **CORS Configuration**

Your Railway backend already allows:
- ✅ `http://localhost:3000`
- ✅ `http://localhost:5173`
- ✅ Your Railway frontend URL (if you add `FRONTEND_URL` env var)

**No CORS issues!** ✅

---

## 📋 **Summary**

**What changed:**
- ✅ Frontend API URL updated to Railway
- ✅ Uses environment variable for flexibility
- ✅ Defaults to Railway (production-ready)

**What you need to do:**
- ✅ **Nothing!** Just run your frontend
- ✅ It will automatically use Railway backend

**Optional:**
- Create `.env.local` if you want to use local backend for development

---

## 🎉 **You're All Set!**

**Frontend is ready to use Railway backend!** 🚀

Just run:
```bash
cd frontend
npm run dev
```

And your frontend will connect to `https://meetpmap-production.up.railway.app` automatically!

