# Railway Deployment Check ✅

## Will It Work? **YES, with a few considerations**

Your backend is **mostly ready** for Railway. Here's what's good and what needs attention:

---

## ✅ What's Already Correct

### 1. **Port Configuration** ✓
```python
port = int(os.getenv("PORT", 8001))
uvicorn.run(app, host="0.0.0.0", port=port)
```
- ✅ Uses `PORT` environment variable (Railway sets this automatically)
- ✅ Host is `0.0.0.0` (correct for Railway)
- ✅ Default port is fine (Railway will override it)

### 2. **Railway Configuration** ✓
```json
{
  "rootDirectory": "backend",
  "startCommand": "python main.py"
}
```
- ✅ Root directory is set correctly
- ✅ Start command is correct
- ✅ Procfile exists as backup

### 3. **Dependencies** ✓
- ✅ All dependencies in `requirements.txt`
- ✅ Model is eager loaded (good for Railway)

### 4. **CORS Configuration** ✓
```python
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)
```
- ✅ Supports production frontend URL via environment variable

---

## ⚠️ Potential Issues & Solutions

### Issue 1: Memory Constraints (Free Tier)

**Problem**: 
- Railway free tier: **512 MB RAM**
- Your dependencies:
  - `torch` (~500MB)
  - `sentence-transformers` (~100MB)
  - Model: `all-MiniLM-L6-v2` (~80MB)
  - FastAPI + other dependencies (~50MB)
  - **Total: ~730MB** (might exceed free tier)

**Solution**:
1. **Try free tier first** - it might work if Railway allocates more
2. **Upgrade to Hobby ($5/month)** - 1GB RAM (recommended)
3. **Optimize model** - Already using `all-MiniLM-L6-v2` (smallest good model)

**Status**: Should work on free tier, but might be tight. Hobby tier is safer.

---

### Issue 2: Build Time

**Problem**: 
- Large dependencies (`torch`, `sentence-transformers`) take 5-10 minutes to build
- This is normal, not an error

**Solution**: 
- ✅ Just wait - Railway will show build progress
- ✅ First build is slowest, subsequent builds are faster (caching)

---

### Issue 3: Environment Variables

**Required Variables**:
1. `OPENAI_API_KEY` - **MUST SET** (your API key)
2. `FRONTEND_URL` - **SET IF** frontend is deployed (e.g., `https://your-frontend.vercel.app`)
3. `PORT` - **AUTO-SET** by Railway (don't set manually)

**How to Set**:
1. Go to Railway project
2. Click on your service
3. Go to **"Variables"** tab
4. Add:
   - `OPENAI_API_KEY` = `sk-...` (your key)
   - `FRONTEND_URL` = `https://your-frontend-url.com` (if deployed)

---

### Issue 4: Startup Time

**Problem**: 
- Model loading takes 10-30 seconds (as you saw in logs)
- Railway might timeout if startup takes > 60 seconds

**Solution**:
- ✅ Your model is eager loaded (loads at startup)
- ✅ Railway allows up to 60 seconds for startup
- ✅ Should be fine, but monitor logs

---

## 🚀 Deployment Steps

### Step 1: Connect GitHub
1. Go to [Railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Select your repo: `DaemD/meetpmap`
5. Railway auto-detects `railway.json`

### Step 2: Configure Service
Railway should auto-detect:
- **Root Directory**: `backend` ✓
- **Start Command**: `python main.py` ✓
- **Build**: Auto-detected from `requirements.txt` ✓

**Verify**:
- Go to **Settings** → **Service**
- Check **Root Directory** = `backend`
- Check **Start Command** = `python main.py`

### Step 3: Add Environment Variables
1. Go to **Variables** tab
2. Add:
   ```
   OPENAI_API_KEY = sk-your-actual-key-here
   FRONTEND_URL = https://your-frontend-url.com (optional)
   ```

### Step 4: Deploy
1. Railway will auto-deploy on first connect
2. Watch the **Deployments** tab for progress
3. Build will take 5-10 minutes (first time)
4. Check **Logs** tab for startup progress

---

## 🧪 Testing After Deployment

### 1. Check Health Endpoint
```bash
curl https://your-service.railway.app/health
```
Expected: `{"status": "healthy"}`

### 2. Check Root Endpoint
```bash
curl https://your-service.railway.app/
```
Expected: `{"message": "MeetMap Prototype API", "status": "running"}`

### 3. Test Graph State
```bash
curl https://your-service.railway.app/api/graph/state
```
Expected: `{"status": "success", "nodes": [...], "edges": [...]}`

### 4. Update Frontend API URL
In `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'https://your-service.railway.app'
```

---

## 📊 Expected Behavior

### ✅ What Will Work:
- Server starts on Railway-provided port
- Model loads at startup (10-30 seconds)
- API endpoints respond correctly
- CORS works with frontend (if `FRONTEND_URL` is set)
- Auto-deploy on git push to `main`

### ⚠️ What to Monitor:
- **Memory usage** - Check Railway metrics
- **Startup time** - Should be < 60 seconds
- **Build time** - 5-10 minutes is normal
- **Cold starts** - Free tier spins down after inactivity

---

## 🔧 Troubleshooting

### Problem: "Out of Memory"
**Solution**: Upgrade to Hobby tier ($5/month) for 1GB RAM

### Problem: "Build Failed"
**Solution**: 
- Check logs for specific error
- Verify `requirements.txt` is correct
- Check Python version (Railway auto-detects)

### Problem: "Service Not Responding"
**Solution**:
- Check logs for startup errors
- Verify `OPENAI_API_KEY` is set
- Check if model loading completed

### Problem: "CORS Error"
**Solution**:
- Set `FRONTEND_URL` environment variable
- Include protocol: `https://your-frontend.com` (not just domain)

---

## 💰 Pricing Recommendation

### Free Tier (Try First):
- ✅ 512 MB RAM
- ✅ $5 free credit/month
- ⚠️ Might be tight for your model
- ⚠️ Spins down after inactivity

### Hobby Tier ($5/month) - **Recommended**:
- ✅ 1 GB RAM (comfortable for your model)
- ✅ Always-on (no spin-down)
- ✅ Better for production

**Start with free tier, upgrade if needed.**

---

## ✅ Final Checklist

Before deploying:
- [ ] Code pushed to GitHub `main` branch
- [ ] `railway.json` exists in repo root
- [ ] `backend/requirements.txt` is up to date
- [ ] `OPENAI_API_KEY` ready to add
- [ ] `FRONTEND_URL` ready (if frontend deployed)

After deploying:
- [ ] Service shows "Active" status
- [ ] `/health` endpoint returns 200
- [ ] Logs show model loaded successfully
- [ ] Test API endpoints work
- [ ] Frontend can connect (if deployed)

---

## 🎯 Bottom Line

**YES, it will work on Railway!**

Your code is well-configured. The main considerations are:
1. **Memory** - Free tier might be tight, Hobby tier is safer
2. **Build time** - 5-10 minutes is normal (first time)
3. **Environment variables** - Must set `OPENAI_API_KEY`

**Recommendation**: Deploy to free tier first, monitor memory usage, upgrade to Hobby if needed.

---

## 🚀 Quick Start

1. Go to [railway.app](https://railway.app)
2. New Project → GitHub → Select `meetpmap`
3. Add `OPENAI_API_KEY` in Variables
4. Wait for build (5-10 min)
5. Test `/health` endpoint
6. Done! ✅

**It should work!** 🎉

