# Railway Settings - Quick Reference

## 🔧 Build Command

### **What it does:**
Runs during the **build phase** to install dependencies and prepare your app.

### **For your Python backend:**
```
pip install -r requirements.txt
```

**OR** leave it **empty** - Railway will auto-detect Python and run this automatically.

### **Current (Wrong):**
```
python main.py  ❌
```
This is a START command, not a BUILD command!

### **Correct:**
```
pip install -r requirements.txt  ✅
```
**OR** leave empty (Railway auto-detects)

---

## 👀 Watch Paths

### **What it does:**
Tells Railway which files/folders to watch for changes. Only redeploys when those paths change.

### **For your setup:**
```
/backend/**
```

### **What this means:**
- ✅ Redeploy when files in `backend/` folder change
- ❌ Don't redeploy when `frontend/` changes
- ❌ Don't redeploy when root files change (unless in backend/)

### **Examples:**
```
/backend/**           → Watch entire backend folder ✅ (your current setting)
/backend/**/*.py     → Only watch Python files
/backend/main.py     → Only watch main.py
/**                  → Watch everything (not recommended)
```

### **Your current setting is PERFECT:**
```
/backend/**
```
This means Railway only redeploys when you change backend code, not frontend. Saves build time! ✅

---

## 🚀 Custom Start Command

### **What it does:**
Runs when your service **starts** (after build completes). This is what actually runs your app.

### **For your Python FastAPI backend:**
```
python main.py
```

### **Current (Wrong):**
```
npm run start  ❌
```
This is for Node.js, not Python!

### **Correct:**
```
python main.py  ✅
```

### **What happens:**
1. Build phase: `pip install -r requirements.txt` (installs dependencies)
2. Start phase: `python main.py` (runs your FastAPI app)

---

## 🌍 Regions

### **What it does:**
Chooses which geographic region to deploy your service in.

### **Your current:**
```
US West (California, USA)
```

### **Available regions:**
- **US West (California)** - Closest to US West Coast
- **US East (Virginia)** - Closest to US East Coast
- **EU West (Ireland)** - Closest to Europe
- **Asia Pacific (Singapore)** - Closest to Asia
- **Asia Pacific (Mumbai)** - Closest to India

### **Which to choose:**
- **If your users are in US**: US West or US East ✅
- **If your users are in Europe**: EU West
- **If your users are in Asia**: Singapore or Mumbai
- **If unsure**: US West (good default) ✅

### **Your current setting is fine:**
```
US West (California, USA)  ✅
```
Good for US users and general use.

### **Note:**
- You can only deploy to **1 region** on free/hobby plans
- **Multi-region** requires Pro plan ($20/month)

---

## 📋 Complete Configuration Summary

### **Build Command:**
```
pip install -r requirements.txt
```
**OR** leave empty (Railway auto-detects)

### **Watch Paths:**
```
/backend/**
```
✅ Perfect as-is! Only redeploys on backend changes.

### **Custom Start Command:**
```
python main.py
```
⚠️ **FIX THIS** - Change from `npm run start`

### **Regions:**
```
US West (California, USA)
```
✅ Perfect as-is! Good default location.

---

## 🎯 Quick Action Items

### **Must Fix:**
1. **Build Command**: `pip install -r requirements.txt` (or leave empty)
2. **Start Command**: `python main.py`

### **Already Correct:**
1. **Watch Paths**: `/backend/**` ✅
2. **Regions**: US West ✅

---

## 💡 Pro Tips

### **Build Command:**
- **Leave empty** if you want Railway to auto-detect
- **Set explicitly** if you want control: `pip install -r requirements.txt`
- **Never use** `python main.py` here (that's for starting, not building)

### **Watch Paths:**
- Use `/backend/**` to only redeploy on backend changes
- Saves build time and resources
- Perfect for monorepos (frontend + backend in same repo)

### **Start Command:**
- This is what **runs your app**
- Must match your actual start command
- For Python: `python main.py`
- For Node.js: `npm start` or `node server.js`

### **Regions:**
- Choose closest to your users for lower latency
- US West is good default
- Can't change easily after deployment (creates new service)

---

## ✅ Final Configuration

```
Build Command:     pip install -r requirements.txt  (or empty)
Watch Paths:       /backend/**                       ✅
Start Command:     python main.py                   ⚠️ FIX
Regions:           US West (California)              ✅
```

**Fix the Start Command and you're good to go!** 🚀

