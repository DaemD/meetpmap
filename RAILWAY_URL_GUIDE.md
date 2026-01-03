# Railway Deployment: What Happens & URL Guide

## 🚀 What Happens When You Deploy on Railway

### Step-by-Step Process:

1. **Connect GitHub Repo**
   - Railway connects to your `DaemD/meetpmap` repo
   - Detects `railway.json` configuration
   - Starts first deployment

2. **Build Phase** (5-10 minutes first time)
   - Railway creates a build environment
   - Installs Python dependencies from `requirements.txt`
   - Downloads PyTorch, transformers, sentence-transformers (~730 MB)
   - Creates a container image

3. **Deploy Phase** (1-2 minutes)
   - Railway starts your service
   - Runs: `python main.py` (from `backend/` directory)
   - Railway sets `PORT` environment variable automatically
   - Your app listens on `0.0.0.0:PORT` (Railway's port)

4. **Service Goes Live**
   - Railway assigns a public URL
   - Your backend is accessible from the internet
   - Auto-deploys on every git push to `main` branch

---

## 🌐 How the URL Changes

### **Before Deployment (Local):**
```
Backend URL: http://localhost:8001
Frontend URL: http://localhost:3000 or http://localhost:5173
```

### **After Deployment (Railway):**
```
Backend URL: https://your-service-name.up.railway.app
Frontend URL: (still local, or your frontend hosting URL)
```

---

## 📍 Railway URL Structure

Railway gives you a URL in this format:

```
https://[service-name].up.railway.app
```

### Example URLs:
- `https://meetmap-backend.up.railway.app`
- `https://meetmap-api.up.railway.app`
- `https://meetpmap-production.up.railway.app`

**The exact URL depends on:**
- Your service name (you choose this)
- Railway's domain (always `*.up.railway.app`)

---

## 🔍 How to Find Your Railway URL

### Method 1: Railway Dashboard
1. Go to [railway.app](https://railway.app)
2. Click on your project
3. Click on your service
4. Go to **"Settings"** tab
5. Look for **"Domains"** section
6. You'll see: `https://your-service.up.railway.app`

### Method 2: Railway CLI
```bash
railway domain
```

### Method 3: Service Overview
- The URL is shown at the top of your service page
- Also in the **"Deployments"** tab after successful deploy

---

## 🔧 What You Need to Update

### 1. **Backend (No Changes Needed)** ✅

Your backend code is already correct:
```python
# backend/main.py
port = int(os.getenv("PORT", 8001))  # Railway sets PORT automatically
uvicorn.run(app, host="0.0.0.0", port=port)  # Listens on all interfaces
```

**Railway automatically:**
- Sets `PORT` environment variable
- Routes traffic to your service
- Provides HTTPS (SSL) automatically

### 2. **Frontend (Must Update)** ⚠️

You need to update `frontend/src/services/api.js`:

**Current (Local):**
```javascript
const API_BASE_URL = 'http://localhost:8001'
```

**After Railway Deployment:**
```javascript
// Option 1: Hardcode Railway URL
const API_BASE_URL = 'https://your-service-name.up.railway.app'

// Option 2: Use environment variable (recommended)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
```

---

## 📝 Step-by-Step: Update Frontend

### Step 1: Get Your Railway URL
1. Deploy on Railway
2. Copy your Railway URL: `https://your-service.up.railway.app`

### Step 2: Update Frontend Code

**Option A: Hardcode (Quick Test)**
```javascript
// frontend/src/services/api.js
const API_BASE_URL = 'https://your-service-name.up.railway.app'
```

**Option B: Environment Variable (Production)**
```javascript
// frontend/src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'
```

Then create `frontend/.env.production`:
```
VITE_API_URL=https://your-service-name.up.railway.app
```

And `frontend/.env.local` (for local development):
```
VITE_API_URL=http://localhost:8001
```

### Step 3: Rebuild Frontend
```bash
cd frontend
npm run build
```

---

## 🔐 CORS Configuration

Your backend already handles CORS correctly:

```python
# backend/main.py
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)
```

**After deploying frontend, add to Railway environment variables:**
```
FRONTEND_URL=https://your-frontend-url.com
```

This allows your frontend to make API calls to Railway backend.

---

## 🧪 Testing Your Railway Deployment

### 1. Health Check
```bash
curl https://your-service.up.railway.app/health
```
Expected: `{"status": "healthy"}`

### 2. Root Endpoint
```bash
curl https://your-service.up.railway.app/
```
Expected: `{"message": "MeetMap Prototype API", "status": "running"}`

### 3. Graph State
```bash
curl https://your-service.up.railway.app/api/graph/state
```
Expected: `{"status": "success", "nodes": [...], "edges": [...]}`

### 4. Test from Browser
Open: `https://your-service.up.railway.app/health`

---

## 🔄 Auto-Deployment

### How It Works:
1. **Push to GitHub** → Railway detects changes
2. **Auto-build** → Railway rebuilds your service
3. **Auto-deploy** → Railway deploys new version
4. **URL stays the same** → Your URL doesn't change

**The URL is permanent** - it only changes if you:
- Delete and recreate the service
- Change the service name

---

## 📊 URL Comparison

| Environment | Backend URL | Frontend URL | Notes |
|------------|-------------|--------------|-------|
| **Local** | `http://localhost:8001` | `http://localhost:3000` | Development |
| **Railway** | `https://xxx.up.railway.app` | `http://localhost:3000` | Backend on Railway, frontend local |
| **Production** | `https://xxx.up.railway.app` | `https://your-frontend.com` | Both deployed |

---

## 🎯 Quick Checklist

### Before Deployment:
- [ ] Code pushed to GitHub `main` branch
- [ ] `railway.json` exists in repo root
- [ ] `OPENAI_API_KEY` ready to add

### After Deployment:
- [ ] Copy Railway URL from dashboard
- [ ] Update `frontend/src/services/api.js` with Railway URL
- [ ] Test `/health` endpoint
- [ ] Test `/api/graph/state` endpoint
- [ ] Update frontend and test locally
- [ ] Add `FRONTEND_URL` to Railway env vars (if frontend deployed)

---

## 💡 Pro Tips

### 1. **Custom Domain (Optional)**
Railway allows custom domains:
- Go to **Settings** → **Domains**
- Add your custom domain: `api.yourdomain.com`
- Railway provides DNS instructions

### 2. **Environment-Specific URLs**
Use environment variables in frontend:
```javascript
const API_BASE_URL = 
  import.meta.env.MODE === 'production'
    ? 'https://your-service.up.railway.app'
    : 'http://localhost:8001'
```

### 3. **Multiple Environments**
- **Development**: `http://localhost:8001`
- **Staging**: `https://meetmap-staging.up.railway.app`
- **Production**: `https://meetmap-production.up.railway.app`

---

## 🚨 Common Issues

### Issue: "CORS Error"
**Solution**: Add `FRONTEND_URL` to Railway environment variables

### Issue: "Connection Refused"
**Solution**: 
- Check Railway service is running (green status)
- Verify URL is correct (HTTPS, not HTTP)
- Check Railway logs for errors

### Issue: "404 Not Found"
**Solution**:
- Verify endpoint path: `/api/graph/state` (not `/api/graph/state/`)
- Check Railway logs for routing errors

---

## ✅ Summary

**What Happens:**
1. Railway builds your backend (5-10 min)
2. Railway deploys your service (1-2 min)
3. Railway assigns a URL: `https://xxx.up.railway.app`
4. Your backend is live and accessible

**URL Changes:**
- **Local**: `http://localhost:8001`
- **Railway**: `https://your-service.up.railway.app`
- **URL is permanent** (doesn't change on redeploy)

**What You Need to Do:**
1. Deploy on Railway
2. Copy your Railway URL
3. Update `frontend/src/services/api.js` with Railway URL
4. Test endpoints
5. Done! ✅

---

**Your backend will work exactly the same, just accessible from the internet!** 🌐

