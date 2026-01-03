# Railway Build Issue Fix

## 🚨 Problem

When you click deploy, Railway runs:
```
python main.py
```

**This is WRONG!** This is trying to **start** your app during the **build** phase, before dependencies are installed.

---

## ✅ Solution

Railway needs to:
1. **Build phase**: Install dependencies (`pip install -r requirements.txt`)
2. **Start phase**: Run your app (`python main.py`)

---

## 🔧 Fix 1: Update railway.json

I've updated your `railway.json` to explicitly set the build command:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "rootDirectory": "backend",
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Changes:**
- ✅ Added `buildCommand: "pip install -r requirements.txt"` to build section
- ✅ Kept `startCommand: "python main.py"` in deploy section

---

## 🔧 Fix 2: Update Railway UI Settings

If Railway UI is overriding `railway.json`, fix it manually:

### In Railway Dashboard:

1. **Build Command** (Custom Build Command section):
   - Change from: `python main.py`
   - To: `pip install -r requirements.txt`
   - **OR** leave empty (Railway will auto-detect)

2. **Start Command** (Custom Start Command section):
   - Should be: `python main.py`
   - If it's `npm run start`, change it to `python main.py`

---

## 📋 What Should Happen

### **Build Phase** (5-10 minutes):
```
pip install -r requirements.txt
```
- Installs FastAPI, PyTorch, transformers, etc.
- Downloads ~730 MB of dependencies
- Creates the environment

### **Start Phase** (after build):
```
python main.py
```
- Runs your FastAPI app
- Loads the embedding model
- Starts the server

---

## 🧪 Test After Fix

1. **Push updated railway.json**:
   ```bash
   git add railway.json
   git commit -m "Fix Railway build command"
   git push origin main
   ```

2. **Railway will auto-deploy** (or click Deploy)

3. **Check logs** - You should see:
   - Build phase: Installing packages
   - Start phase: Starting FastAPI server

---

## 🐛 If It Still Fails

### Check Railway Logs:
1. Go to Railway dashboard
2. Click on your service
3. Go to **"Deployments"** tab
4. Click on latest deployment
5. Check **"Build Logs"** and **"Deploy Logs"**

### Common Issues:

**Issue**: "Module not found"
- **Cause**: Dependencies not installed
- **Fix**: Make sure build command is `pip install -r requirements.txt`

**Issue**: "Command not found: python"
- **Cause**: Python not detected
- **Fix**: Railway should auto-detect Python, but check root directory is `backend`

**Issue**: "Port already in use"
- **Cause**: Multiple instances running
- **Fix**: Railway handles this automatically

---

## ✅ Summary

**Problem**: Railway runs `python main.py` during build (wrong phase)

**Fix**: 
1. ✅ Updated `railway.json` with explicit build command
2. ⚠️ Update Railway UI settings if they override the file

**Result**: 
- Build phase installs dependencies
- Start phase runs your app
- Everything works! 🎉

---

## 🚀 Next Steps

1. ✅ `railway.json` is updated
2. ⚠️ Push to GitHub: `git push origin main`
3. ⚠️ Check Railway UI settings match
4. ⚠️ Deploy and check logs

**Your build should work now!** ✅

