# Backend Deployment Guide
## Auto-Deploy from GitHub on Every Push

This guide covers hosting your FastAPI backend with automatic deployments when you push code to GitHub.

---

## 🎯 Requirements

Your backend needs:
- ✅ Python 3.9+
- ✅ Environment variables (`OPENAI_API_KEY`, `PORT`)
- ✅ Heavy ML dependencies (torch, sentence-transformers ~80MB model)
- ✅ FastAPI + Uvicorn server
- ✅ Auto-restart on code changes

---

## 🚀 Option 1: Railway (Recommended - Easiest)

**Why Railway?**
- ✅ **Free tier available** (500 hours/month)
- ✅ **Auto-deploy from GitHub** (just connect repo)
- ✅ **Handles heavy dependencies** (torch, transformers)
- ✅ **Easy environment variables**
- ✅ **Automatic HTTPS**
- ✅ **No configuration files needed** (but we'll add some for optimization)

### Setup Steps

#### 1. Prepare Your Repository

Make sure your GitHub repo has:
```
milesweb/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
└── README.md
```

#### 2. Create Railway Configuration Files

**Create `railway.json` in project root:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Create `Procfile` in `backend/` directory:**
```
web: python main.py
```

**Create `runtime.txt` in `backend/` directory (optional, for specific Python version):**
```
python-3.11
```

#### 3. Update `main.py` for Production

Railway will set `PORT` environment variable. Your code already handles this:
```python
port = int(os.getenv("PORT", 8001))
```

But update CORS to allow your frontend domain:
```python
# In main.py, update CORS origins
allow_origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "https://your-frontend-domain.com"  # Add your frontend URL
]
```

#### 4. Deploy on Railway

1. **Go to [railway.app](https://railway.app)**
2. **Sign up** (use GitHub account)
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository**
6. **Railway auto-detects Python** and starts building

#### 5. Configure Environment Variables

In Railway dashboard:
1. Go to your project → **Variables** tab
2. Add:
   ```
   OPENAI_API_KEY=your_key_here
   PORT=8000  # Railway sets this automatically, but you can override
   ```

#### 6. Set Root Directory (Important!)

Railway needs to know your backend is in a subdirectory:

1. Go to **Settings** → **Service Settings**
2. Under **Root Directory**, set: `backend`
3. Or in `railway.json`, add:
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "rootDirectory": "backend",
    "startCommand": "python main.py"
  }
}
```

#### 7. Deploy!

- Railway automatically deploys on every `git push`
- Check **Deployments** tab for logs
- Your API will be at: `https://your-app-name.up.railway.app`

#### 8. Configure Branch (Optional)

**By default**, Railway deploys from `main` branch. To change this:

1. Go to **Settings** → **Service Settings**
2. Under **Source**, find **Branch**
3. Select your branch (e.g., `develop`, `staging`, `production`)
4. Or set to **"All branches"** to deploy from any branch

**Branch Options**:
- `main` - Production (default)
- `develop` - Development/staging
- `feature/*` - Feature branches (for testing)
- `All branches` - Deploy from any branch push

#### 9. Monitor Deployments

- Railway shows build logs in real-time
- First deployment takes ~5-10 minutes (downloading ML models)
- Subsequent deployments are faster (cached dependencies)

---

## 🚀 Option 2: Render (Alternative)

**Why Render?**
- ✅ Free tier (spins down after 15min inactivity)
- ✅ Auto-deploy from GitHub
- ✅ Good for Python apps

### Setup Steps

#### 1. Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: meetmap-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python main.py
    envVars:
      - key: OPENAI_API_KEY
        sync: false  # You'll set this in dashboard
      - key: PORT
        value: 8000
```

#### 2. Deploy on Render

1. Go to [render.com](https://render.com)
2. **New** → **Web Service**
3. **Connect GitHub** → Select repo
4. **Settings**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. **Add Environment Variables**:
   - `OPENAI_API_KEY`
6. **Deploy!**

**Note**: Free tier spins down after inactivity. First request after spin-down takes ~30s.

---

## 🚀 Option 3: Fly.io (Good for Global)

**Why Fly.io?**
- ✅ Free tier (3 VMs)
- ✅ Global edge deployment
- ✅ Good Docker support

### Setup Steps

#### 1. Create `Dockerfile` in `backend/`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
```

#### 2. Create `.dockerignore` in `backend/`:

```
__pycache__
*.pyc
venv/
.env
*.log
```

#### 3. Install Fly CLI and Deploy

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize (in backend/ directory)
cd backend
fly launch

# Set secrets
fly secrets set OPENAI_API_KEY=your_key_here

# Deploy
fly deploy
```

**Auto-deploy**: Connect GitHub repo in Fly.io dashboard → **Settings** → **GitHub Integration**

---

## 🚀 Option 4: DigitalOcean App Platform

**Why DigitalOcean?**
- ✅ $5/month starter plan
- ✅ Auto-deploy from GitHub
- ✅ Reliable and fast

### Setup Steps

1. Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. **Apps** → **Create App** → **GitHub**
3. Select repository
4. **Configure**:
   - **Type**: Web Service
   - **Source Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python main.py`
5. **Add Environment Variables**: `OPENAI_API_KEY`
6. **Deploy!**

---

## 📋 Comparison Table

| Platform | Free Tier | Auto-Deploy | Build Time | Best For |
|---------|-----------|-------------|------------|----------|
| **Railway** | ✅ 500hrs/mo | ✅ Yes | ~5-10min | **Easiest setup** |
| **Render** | ✅ (spins down) | ✅ Yes | ~5-8min | Budget-friendly |
| **Fly.io** | ✅ 3 VMs | ✅ Yes | ~3-5min | Global edge |
| **DigitalOcean** | ❌ $5/mo | ✅ Yes | ~4-6min | Production |

**Recommendation**: Start with **Railway** (easiest), then move to **DigitalOcean** for production.

---

## 🔧 Production Optimizations

### 1. Update CORS for Production

In `backend/main.py`:
```python
import os

# Get frontend URL from environment
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        FRONTEND_URL,  # Your production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Add Health Check Endpoint

Your `/health` endpoint is perfect for monitoring:
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "meetmap-backend",
        "version": "1.0.0"
    }
```

### 3. Optimize Model Loading

Consider lazy loading for faster startup (but slower first request):
```python
# In meetmap_service.py
@property
def embedding_model(self):
    if self._embedding_model is None:
        self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return self._embedding_model
```

### 4. Add Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

---

## 🐛 Troubleshooting

### Issue: Build Fails - "Out of Memory"

**Solution**: Railway/Render free tiers have memory limits. Options:
1. Use smaller model: `paraphrase-MiniLM-L3-v2` (faster, smaller)
2. Upgrade to paid tier
3. Use lazy loading (load model on first request)

### Issue: Model Download Times Out

**Solution**: Pre-download model in Dockerfile:
```dockerfile
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Issue: Port Already in Use

**Solution**: Your code already handles this:
```python
port = int(os.getenv("PORT", 8001))
```
Platforms set `PORT` automatically. If issues, check platform logs.

### Issue: Dependencies Install Slowly

**Solution**: Use `requirements.txt` with pinned versions (you already have this).

### Issue: Auto-Deploy Not Working

**Solution**:
1. Check GitHub webhook in platform dashboard
2. Verify repository connection
3. Check build logs for errors
4. Verify the correct branch is selected (Settings → Branch)
5. If using a different branch, make sure it's configured in platform settings

---

## 📝 Quick Start Checklist

### For Railway (Recommended):

- [ ] Push code to GitHub
- [ ] Create Railway account
- [ ] Connect GitHub repo
- [ ] Set root directory to `backend`
- [ ] Add `OPENAI_API_KEY` environment variable
- [ ] Wait for first deployment (~5-10 min)
- [ ] Test API: `https://your-app.up.railway.app/health`
- [ ] Update frontend API URL to Railway URL
- [ ] Push code → Auto-deploys! 🎉

---

## 🔄 Workflow After Setup

1. **Make code changes locally**
2. **Test locally**: `python backend/main.py`
3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin main
   ```
4. **Platform auto-deploys** (check dashboard for status)
5. **Test production API** (usually ready in 2-5 minutes)

---

## 🎯 Next Steps

1. **Set up Railway** (follow Option 1)
2. **Get your production URL**: `https://your-app.up.railway.app`
3. **Update frontend** to use production backend URL
4. **Test end-to-end**
5. **Set up custom domain** (optional, in Railway settings)

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Fly.io Docs](https://fly.io/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Questions?** Check platform logs or their support docs. Most platforms have excellent documentation and support.

