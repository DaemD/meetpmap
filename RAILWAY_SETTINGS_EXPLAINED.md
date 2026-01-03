# Railway Settings Explained - Complete Guide

## 📋 Your Current Settings Analysis

### ✅ **Source**
- **Source Repo**: `DaemD/meetpmap` ✅ Correct
- **Disconnect**: Don't click this (keeps GitHub connection)

### ⚠️ **Root Directory** (NEEDS FIX)
- **Current**: Not set (or empty)
- **Should be**: `backend`
- **Why**: Your `main.py` is in the `backend/` folder

### ✅ **Branch**
- **Current**: `main` ✅ Correct
- **Auto-deploy**: Enabled ✅ Correct

### ✅ **Networking**
- **Public Networking**: Enabled ✅ Correct
- **Generate Domain**: Click this to get your URL!

### ⚠️ **Build Settings** (NEEDS FIX)
- **Builder**: `Railpack` ✅ Correct (or NIXPACKS)
- **Build Command**: `python main.py` ❌ **WRONG!**
  - This is a START command, not a BUILD command
  - Should be: `pip install -r requirements.txt` (or leave empty for auto)

### ⚠️ **Deploy Settings** (NEEDS FIX)
- **Start Command**: `npm run start` ❌ **WRONG!**
  - This is for Node.js, not Python
  - Should be: `python main.py`

### ⚠️ **Watch Paths** (OPTIONAL)
- **Current**: `/backend/**` ✅ Good (only redeploys when backend changes)

### ✅ **Resource Limits**
- **CPU**: 8 vCPU (your plan limit)
- **Memory**: 8 GB (your plan limit)
- **For your app**: 1-2 GB RAM is enough, but 8 GB is fine

### ✅ **Restart Policy**
- **On Failure**: ✅ Correct
- **Max restart retries**: 10 ✅ Correct

---

## 🔧 What You Need to Fix

### **1. Root Directory** (CRITICAL)

**Current**: Not set  
**Should be**: `backend`

**How to fix**:
1. Click **"Add Root Directory"**
2. Enter: `backend`
3. Save

**Why**: Railway needs to know your Python code is in the `backend/` folder, not the root.

---

### **2. Build Command** (CRITICAL)

**Current**: `python main.py` ❌  
**Should be**: `pip install -r requirements.txt` (or leave empty

**How to fix**:
1. In **"Custom Build Command"** section
2. Change from: `python main.py`
3. To: `pip install -r requirements.txt`
4. Or: Leave empty (Railway auto-detects Python and installs requirements.txt)

**Why**: Build command installs dependencies. Start command runs your app.

---

### **3. Start Command** (CRITICAL)

**Current**: `npm run start` ❌  
**Should be**: `python main.py`

**How to fix**:
1. In **"Custom Start Command"** section
2. Change from: `npm run start`
3. To: `python main.py`
4. Save

**Why**: You're running a Python FastAPI app, not Node.js.

---

## 📝 Complete Configuration Guide

### **Source Section**
```
Source Repo: DaemD/meetpmap ✅
Branch: main ✅
Wait for CI: Optional (leave unchecked unless you have GitHub Actions)
```

### **Root Directory** ⚠️ FIX THIS
```
Add Root Directory: backend
```
**Action**: Click "Add Root Directory" → Enter `backend` → Save

### **Networking**
```
Public Networking: ✅ Enabled
Generate Domain: Click this button to get your URL!
```

### **Build Section** ⚠️ FIX THIS
```
Builder: Railpack (or NIXPACKS) ✅
Custom Build Command: pip install -r requirements.txt
```
**OR** leave empty - Railway auto-detects Python and installs from `requirements.txt`

### **Deploy Section** ⚠️ FIX THIS
```
Custom Start Command: python main.py
```

### **Watch Paths** (Optional)
```
/backend/**
```
This means: Only redeploy when files in `backend/` folder change. Good for monorepos!

### **Resource Limits**
```
CPU: 1-2 vCPU (enough for your app)
Memory: 1-2 GB (enough for your app)
```
You have 8 GB available, but 1-2 GB is sufficient. You can reduce to save resources.

### **Restart Policy**
```
On Failure: ✅ Enabled
Max restart retries: 10 ✅
```

---

## 🎯 Step-by-Step Fix Instructions

### Step 1: Set Root Directory
1. Find **"Add Root Directory"** button
2. Click it
3. Enter: `backend`
4. Save

### Step 2: Fix Build Command
1. Find **"Custom Build Command"** section
2. Change: `python main.py` → `pip install -r requirements.txt`
3. **OR** delete it (leave empty) - Railway will auto-detect
4. Save

### Step 3: Fix Start Command
1. Find **"Custom Start Command"** section
2. Change: `npm run start` → `python main.py`
3. Save

### Step 4: Generate Domain
1. Find **"Generate Domain"** button in Networking section
2. Click it
3. Copy your URL: `https://xxx.up.railway.app`

### Step 5: Add Environment Variable
1. Go to **"Variables"** tab (not shown in your screenshot, but it's there)
2. Add: `OPENAI_API_KEY` = `sk-proj-your-actual-api-key-here`

---

## ✅ Correct Configuration Summary

| Setting | Current | Should Be | Status |
|---------|---------|-----------|--------|
| **Root Directory** | Not set | `backend` | ⚠️ FIX |
| **Build Command** | `python main.py` | `pip install -r requirements.txt` (or empty) | ⚠️ FIX |
| **Start Command** | `npm run start` | `python main.py` | ⚠️ FIX |
| **Branch** | `main` | `main` | ✅ OK |
| **Public Networking** | Enabled | Enabled | ✅ OK |
| **Restart Policy** | On Failure | On Failure | ✅ OK |
| **Watch Paths** | `/backend/**` | `/backend/**` | ✅ OK |

---

## 🚨 Critical Fixes Needed

### **Priority 1: Root Directory**
Without this, Railway won't find your `main.py` file!

### **Priority 2: Start Command**
Without this, Railway will try to run Node.js instead of Python!

### **Priority 3: Build Command**
Without this, dependencies won't install!

---

## 💡 Pro Tips

### **1. Use railway.json Instead**
Your `railway.json` file already has the correct settings! Railway should auto-detect it. If it's not working:
- Make sure `railway.json` is in repo root
- Railway should use it automatically
- You can override in UI if needed

### **2. Watch Paths Optimization**
Your `/backend/**` watch path is good! This means:
- Changes to `frontend/` won't trigger redeploy
- Only `backend/` changes trigger redeploy
- Saves build time

### **3. Resource Limits**
You can reduce to save resources:
- **CPU**: 1 vCPU (enough for your app)
- **Memory**: 2 GB (enough for your app + model)

### **4. Healthcheck Path**
Add this for better monitoring:
```
Healthcheck Path: /health
```
Railway will check this endpoint before marking deployment as successful.

---

## 🎯 Quick Action Items

**Do these 3 things NOW:**

1. ✅ **Add Root Directory**: `backend`
2. ✅ **Fix Start Command**: `python main.py`
3. ✅ **Fix Build Command**: `pip install -r requirements.txt` (or leave empty)

**Then:**
4. ✅ **Generate Domain** (get your URL)
5. ✅ **Add Environment Variable**: `OPENAI_API_KEY`
6. ✅ **Deploy!**

---

## 📊 After Fixes

Once you fix these settings, Railway will:
1. ✅ Build from `backend/` directory
2. ✅ Install dependencies from `requirements.txt`
3. ✅ Start your app with `python main.py`
4. ✅ Auto-restart on failure
5. ✅ Give you a public URL

**Your deployment will work!** 🚀

