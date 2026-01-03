# Railway Setup - Step by Step Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Sign Up on Railway

1. Go to **[railway.app](https://railway.app)**
2. Click **"Start a New Project"** or **"Login"**
3. Sign up with **GitHub** (recommended - one-click connection)
4. Authorize Railway to access your GitHub

---

### Step 2: Create New Project

1. In Railway dashboard, click **"New Project"** (top right)
2. Select **"Deploy from GitHub repo"**
3. If first time, click **"Configure GitHub App"** and authorize
4. Search for your repository: `meetpmap` or `milesweb`
5. Click on your repository to select it
6. Railway will create a new project and start detecting your app

---

### Step 3: Configure Service Settings

Railway should auto-detect Python, but you need to set the root directory:

1. Click on your **service** (the box that appeared)
2. Go to **Settings** tab (top right)
3. Scroll to **"Service Settings"**
4. Find **"Root Directory"** field
5. Enter: `backend`
6. Click **"Save"**

**Why?** Your backend code is in the `backend/` folder, not the root.

---

### Step 4: Add Environment Variables

1. In your service, click **"Variables"** tab
2. Click **"New Variable"** or **"Raw Editor"**
3. Add your OpenAI API key:

   **Key**: `OPENAI_API_KEY`  
   **Value**: `sk-proj-your-actual-api-key-here`

4. Click **"Add"** or **"Save"**

**Note**: `PORT` is automatically set by Railway (you don't need to add it)

---

### Step 5: Verify Configuration

Check that `railway.json` exists in your repo root (it should - we created it):

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

This tells Railway:
- ✅ Use `backend/` as root directory
- ✅ Start command: `python main.py`
- ✅ Auto-restart on failure

---

### Step 6: Deploy!

Railway automatically starts building when you:
1. Connect the repo (already done)
2. Set root directory (Step 3)
3. Add environment variables (Step 4)

**Watch the deployment:**
- Click **"Deployments"** tab
- You'll see build logs in real-time
- First deployment takes **5-10 minutes** (downloading ML models)

---

### Step 7: Get Your URL

Once deployment completes:

1. Go to **Settings** tab
2. Scroll to **"Domains"** section
3. You'll see your Railway URL: `https://your-app-name.up.railway.app`
4. Or click **"Generate Domain"** to create a custom name

**Test it:**
```bash
curl https://your-app-name.up.railway.app/health
```

Should return: `{"status":"healthy"}`

---

## 📋 Configuration Checklist

Before deploying, verify:

- [ ] ✅ Repository connected to Railway
- [ ] ✅ Root Directory set to `backend`
- [ ] ✅ `OPENAI_API_KEY` environment variable added
- [ ] ✅ `railway.json` exists in repo root
- [ ] ✅ Code pushed to GitHub `main` branch

---

## 🔄 Auto-Deploy Setup

Railway automatically deploys when you push to GitHub:

1. **Make changes locally**
2. **Commit and push:**
   ```bash
   git add .
   git commit -m "Update code"
   git push origin main
   ```
3. **Railway detects push** → Starts new deployment
4. **Check "Deployments" tab** → See build progress
5. **Deployment completes** → Changes are live (~2-5 minutes)

---

## 🎯 Branch Configuration (Optional)

**Default**: Railway deploys from `main` branch

**To change branch:**
1. Go to **Settings** → **Service Settings**
2. Under **"Source"**, find **"Branch"** dropdown
3. Select your branch:
   - `main` (production)
   - `develop` (staging)
   - Or **"All branches"** (deploy from any branch)

---

## 📊 Monitor Your Deployment

### View Logs
1. Click **"Deployments"** tab
2. Click on a deployment
3. See real-time build logs
4. See runtime logs (after deployment)

### Check Status
- **Building** → Installing dependencies
- **Deploying** → Starting your app
- **Active** → Running successfully
- **Failed** → Check logs for errors

---

## 🐛 Troubleshooting

### Issue: Build Fails

**Check:**
1. **Root Directory** is set to `backend`
2. **Environment variables** are set correctly
3. **Build logs** for specific errors

**Common errors:**
- "Module not found" → Check `requirements.txt`
- "Port already in use" → Railway handles this automatically
- "Out of memory" → Free tier has 512MB limit

### Issue: Service Won't Start

**Check:**
1. **Start Command** is correct: `python main.py`
2. **Logs** show any Python errors
3. **Environment variables** are set

### Issue: Auto-Deploy Not Working

**Check:**
1. **GitHub webhook** is connected (Settings → Source)
2. **Branch** is set correctly
3. **You're pushing to the correct branch**

---

## 💰 Free Tier Limits

**Railway Free Tier:**
- ✅ 500 hours/month
- ✅ 512MB RAM
- ✅ 1GB disk
- ✅ 100GB bandwidth/month
- ✅ Always-on (no spin-down!)

**If you exceed:**
- Upgrade to **Hobby** plan ($5/month)
- Or monitor usage in dashboard

---

## ✅ Quick Commands Reference

```bash
# Push code to trigger auto-deploy
git add .
git commit -m "Your commit message"
git push origin main

# Test your Railway API
curl https://your-app.up.railway.app/health

# Check deployment status
# → Go to Railway dashboard → Deployments tab
```

---

## 🎉 You're Done!

Your backend is now:
- ✅ Deployed on Railway
- ✅ Auto-deploying on every push
- ✅ Always-on (no cold starts!)
- ✅ Accessible at `https://your-app.up.railway.app`

**Next Steps:**
1. Test your API endpoints
2. Update frontend to use Railway URL
3. Monitor usage in Railway dashboard

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway) - Community support
- [Railway Status](https://status.railway.app) - Service status

---

**Need help?** Check Railway logs or their Discord community!


