# Render Deployment - Step by Step

## Quick Setup Guide

### Step 1: Sign Up
1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (recommended)

### Step 2: Create Web Service
1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. Connect your GitHub repository:
   - Click **"Connect account"** if not connected
   - Search for `milesweb` or `meetpmap` repository
   - Click **"Connect"**

### Step 3: Configure Service

**Option A: Using render.yaml (Automatic - Recommended)**

If you have `render.yaml` in your repo root (which you do!), Render will auto-detect it:
- ✅ Service name: `meetmap-backend`
- ✅ Root directory: `backend`
- ✅ Build command: `pip install -r requirements.txt`
- ✅ Start command: `python main.py`

**Option B: Manual Configuration**

If auto-detection doesn't work, configure manually:

1. **Name**: `meetmap-backend`
2. **Environment**: `Python 3`
3. **Region**: Choose closest to you
4. **Branch**: `main` (or your branch)
5. **Root Directory**: `backend`
6. **Build Command**: `pip install -r requirements.txt`
7. **Start Command**: `python main.py`

### Step 4: Set Environment Variables

1. Scroll down to **"Environment Variables"** section
2. Click **"Add Environment Variable"**
3. Add:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-...`)
4. Click **"Save Changes"**

**Note**: `PORT` is automatically set by Render (you don't need to add it)

### Step 5: Choose Plan

- **Free**: Spins down after 15 minutes of inactivity (first request after spin-down takes ~30s)
- **Starter ($7/mo)**: Always on, better for production

For testing, **Free** is fine. For production, consider **Starter**.

### Step 6: Deploy!

1. Click **"Create Web Service"** at the bottom
2. Render will:
   - Clone your repository
   - Install dependencies (`pip install -r requirements.txt`)
   - Download ML models (first time takes 5-10 minutes)
   - Start your FastAPI server
3. Watch the **"Logs"** tab for progress

### Step 7: Get Your URL

Once deployed, you'll get a URL like:
```
https://meetmap-backend.onrender.com
```

Test it:
```bash
curl https://meetmap-backend.onrender.com/health
```

Should return: `{"status":"healthy"}`

---

## Auto-Deploy Setup

Render automatically deploys when you push to the connected branch:

1. **Default**: Deploys from `main` branch
2. **To change branch**: 
   - Go to **Settings** → **Build & Deploy**
   - Under **Branch**, select your branch
3. **Every `git push`** → Render rebuilds and redeploys

---

## Important Notes

### Free Tier Limitations

- **Spins down after 15min inactivity**
- First request after spin-down: ~30 seconds (cold start)
- Subsequent requests: Fast
- **Solution**: Use Starter plan ($7/mo) for always-on

### Build Time

- **First deployment**: 5-10 minutes (downloading ML models)
- **Subsequent deployments**: 2-5 minutes (cached dependencies)

### Memory Limits

- Free tier: 512MB RAM
- Your app uses ~200-300MB (with ML models)
- Should work fine on free tier

### Logs

- View logs in **"Logs"** tab
- Real-time build and runtime logs
- Useful for debugging

---

## Troubleshooting

### Issue: Build Fails - "Out of Memory"

**Solution**: 
- Free tier has 512MB limit
- Your ML models might be too large
- Try using smaller model: `paraphrase-MiniLM-L3-v2`

### Issue: Service Keeps Spinning Down

**Solution**:
- Free tier spins down after 15min inactivity
- Upgrade to Starter plan ($7/mo) for always-on
- Or use a service like UptimeRobot to ping your service every 10 minutes

### Issue: Auto-Deploy Not Working

**Solution**:
1. Check **Settings** → **Build & Deploy** → **Branch**
2. Verify GitHub webhook is connected
3. Check **"Events"** tab for deployment triggers

### Issue: CORS Errors

**Solution**:
1. Add `FRONTEND_URL` environment variable in Render
2. Or update `allowed_origins` in `backend/main.py`

### Issue: Model Download Times Out

**Solution**:
- First build takes time (downloading ~80MB model)
- Be patient, check logs
- If fails, try pre-downloading in Dockerfile (see DEPLOYMENT_GUIDE.md)

---

## Quick Commands Reference

```bash
# Push code to trigger auto-deploy
git add .
git commit -m "Update code"
git push origin main

# Check deployment status
# → Go to Render dashboard → Your service → "Events" tab

# View logs
# → Render dashboard → Your service → "Logs" tab

# Test your API
curl https://meetmap-backend.onrender.com/health
```

---

## Next Steps After Deployment

1. ✅ Get your Render URL: `https://meetmap-backend.onrender.com`
2. ✅ Test health endpoint
3. ✅ Update frontend to use Render URL
4. ✅ Test end-to-end
5. ✅ Set up custom domain (optional, in Settings)

---

## Cost Comparison

| Plan | Price | Always On | Best For |
|------|-------|-----------|----------|
| **Free** | $0 | ❌ (spins down) | Testing/Development |
| **Starter** | $7/mo | ✅ Yes | Production |
| **Standard** | $25/mo | ✅ Yes | High traffic |

**Recommendation**: Start with **Free** for testing, upgrade to **Starter** for production.

---

## Summary

✅ **render.yaml** is already in your repo (auto-configures everything)  
✅ **Sign up** → **New Web Service** → **Connect GitHub**  
✅ **Add `OPENAI_API_KEY`** environment variable  
✅ **Deploy!** (takes 5-10 min first time)  
✅ **Auto-deploys** on every `git push`  

Your API will be live at: `https://meetmap-backend.onrender.com`


