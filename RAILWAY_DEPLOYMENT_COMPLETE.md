# Railway Deployment - Complete Configuration Guide

## ✅ Your Railway Configuration Files

### 1. `railway.json` (Already exists ✅)

Located in repo root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "rootDirectory": "backend",
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**This is correct!** Railway will:
- Use NIXPACKS to auto-detect Python
- Build from `backend/` directory
- Run `python main.py` to start
- Auto-restart on failure

---

### 2. `backend/Procfile` (Already exists ✅)

```
web: python main.py
```

**This is correct!** Backup start command for Railway.

---

### 3. `backend/requirements.txt` (Already exists ✅)

Your dependencies are listed. Railway will install them automatically.

---

## 🚀 Step-by-Step Railway Deployment

### Step 1: Push Code to GitHub

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

---

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Sign up / Log in (use GitHub account)
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Authorize Railway to access your GitHub
6. Select repository: `DaemD/meetpmap`
7. Click **"Deploy Now"**

---

### Step 3: Railway Auto-Detects Configuration

Railway will automatically:
- ✅ Detect `railway.json`
- ✅ Set root directory to `backend`
- ✅ Use start command: `python main.py`
- ✅ Start building your service

**You don't need to configure anything manually!**

---

### Step 4: Add Environment Variables

While the build is running:

1. Go to your service in Railway dashboard
2. Click **"Variables"** tab
3. Click **"New Variable"**
4. Add these variables:

#### Required:
```
OPENAI_API_KEY = sk-proj-your-actual-api-key-here
```

#### Optional (if frontend is deployed):
```
FRONTEND_URL = https://your-frontend-url.com
```

**Note**: `PORT` is automatically set by Railway (don't add it manually)

---

### Step 5: Wait for Build (5-10 minutes)

Railway will:
1. Install Python dependencies
2. Download PyTorch, transformers, etc. (~730 MB)
3. Build container
4. Deploy service

**Watch the logs** to see progress!

---

### Step 6: Get Your URL

After deployment succeeds:

1. Go to **"Settings"** tab
2. Scroll to **"Domains"** section
3. Copy your URL: `https://xxx.up.railway.app`

Or find it in the service overview at the top.

---

### Step 7: Test Your Deployment

Open in browser:
```
https://your-service.up.railway.app/health
```

Expected response:
```json
{"status": "healthy"}
```

---

## 📋 Railway Configuration Summary

### What Railway Uses:

| Setting | Value | Source |
|---------|-------|--------|
| **Root Directory** | `backend` | `railway.json` |
| **Start Command** | `python main.py` | `railway.json` |
| **Build System** | NIXPACKS | `railway.json` |
| **Python Version** | Auto-detected | NIXPACKS |
| **Dependencies** | `requirements.txt` | Auto-installed |
| **Port** | Auto-set | Railway (env var) |

---

## 🔧 Optional: Optimize Build (CPU-Only PyTorch)

To reduce build size from ~730 MB to ~500 MB, you can add a build command.

### Option 1: Update `railway.json` (Recommended)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt"
  },
  "deploy": {
    "rootDirectory": "backend",
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Note**: This is optional. Your current config works fine, just takes longer to build.

---

## 📝 Environment Variables Checklist

### Required:
- [x] `OPENAI_API_KEY` - Your OpenAI API key

### Optional:
- [ ] `FRONTEND_URL` - If frontend is deployed (for CORS)

### Auto-Set by Railway:
- [x] `PORT` - Don't set manually
- [x] `RAILWAY_ENVIRONMENT` - Auto-set
- [x] `RAILWAY_PROJECT_ID` - Auto-set

---

## 🧪 Testing After Deployment

### 1. Health Check
```bash
curl https://your-service.up.railway.app/health
```

### 2. Root Endpoint
```bash
curl https://your-service.up.railway.app/
```

### 3. Graph State
```bash
curl https://your-service.up.railway.app/api/graph/state
```

### 4. Test from Frontend

Update `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'https://your-service.up.railway.app'
```

---

## 🔄 Auto-Deployment

Railway automatically deploys when you:
- Push to `main` branch
- Merge a pull request to `main`

**The URL stays the same** - only the code updates!

---

## 🐛 Troubleshooting

### Build Fails
- Check Railway logs for error messages
- Verify `requirements.txt` is correct
- Ensure Python version is compatible

### Service Won't Start
- Check logs for startup errors
- Verify `OPENAI_API_KEY` is set
- Check if model loading completes (takes 10-30 seconds)

### Out of Memory
- Upgrade to Hobby tier ($5/month) for 1GB RAM
- Free tier (512 MB) might be tight

### CORS Errors
- Add `FRONTEND_URL` environment variable
- Include full URL with `https://`

---

## 📊 Current Configuration Status

✅ **railway.json** - Correct
✅ **Procfile** - Correct  
✅ **requirements.txt** - Ready
✅ **main.py** - Uses PORT env var correctly
✅ **CORS** - Configured for production

**Everything is ready to deploy!** 🚀

---

## 🎯 Quick Deploy Checklist

Before deploying:
- [ ] Code pushed to GitHub `main` branch
- [ ] `railway.json` exists in repo root
- [ ] `backend/requirements.txt` is up to date
- [ ] `OPENAI_API_KEY` ready to add

During deployment:
- [ ] Create Railway project
- [ ] Connect GitHub repo
- [ ] Add `OPENAI_API_KEY` environment variable
- [ ] Wait for build (5-10 min)
- [ ] Copy Railway URL

After deployment:
- [ ] Test `/health` endpoint
- [ ] Test `/api/graph/state` endpoint
- [ ] Update frontend API URL
- [ ] Test frontend connection

---

## ✅ You're Ready!

Your Railway configuration is complete. Just:
1. Push to GitHub
2. Deploy on Railway
3. Add environment variables
4. Get your URL
5. Update frontend

**That's it!** 🎉

