# Quick Deploy Guide 🚀

## TL;DR - Deploy in 5 Minutes

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Deploy on Railway (Easiest)

1. Go to [railway.app](https://railway.app) → Sign up with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Select your `milesweb` repository
4. **Settings** → Set **Root Directory** to `backend`
5. **Variables** → Add `OPENAI_API_KEY=your_key_here`
6. Wait ~5-10 minutes for first build
7. Get your URL: `https://your-app.up.railway.app`

### Step 3: Test It
```bash
curl https://your-app.up.railway.app/health
# Should return: {"status":"healthy"}
```

### Step 4: Auto-Deploy is ON! ✅

Every time you push to GitHub:
```bash
git push origin main
```
Railway automatically rebuilds and deploys in ~2-5 minutes.

---

## What I Created For You

✅ **railway.json** - Railway configuration  
✅ **backend/Procfile** - Process file for Railway/Heroku  
✅ **render.yaml** - Render.com configuration  
✅ **backend/Dockerfile** - Docker configuration (for Fly.io)  
✅ **backend/.dockerignore** - Docker ignore file  
✅ **DEPLOYMENT_GUIDE.md** - Full detailed guide  
✅ **Updated CORS** - Now supports production frontend URL  

---

## Environment Variables Needed

Set these in your hosting platform:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `PORT` | Server port (auto-set by platform) | `8000` |
| `FRONTEND_URL` | Your frontend URL (optional) | `https://your-frontend.com` |

---

## Platform Comparison

| Platform | Setup Time | Free Tier | Best For |
|----------|------------|-----------|----------|
| **Railway** ⭐ | 5 min | ✅ 500hrs/mo | **Start here** |
| Render | 5 min | ✅ (spins down) | Budget |
| Fly.io | 10 min | ✅ 3 VMs | Global |
| DigitalOcean | 5 min | ❌ $5/mo | Production |

---

## Troubleshooting

**Build fails?**
- Check logs in platform dashboard
- Ensure `OPENAI_API_KEY` is set
- First build takes 5-10 min (downloading ML models)

**Auto-deploy not working?**
- Check GitHub webhook in platform settings
- Verify you're pushing to `main` branch
- Check build logs for errors

**CORS errors?**
- Add `FRONTEND_URL` environment variable
- Or update `allowed_origins` in `backend/main.py`

---

## Next Steps

1. ✅ Deploy backend (Railway recommended)
2. ✅ Get production URL
3. ✅ Update frontend to use production backend
4. ✅ Deploy frontend (Vercel/Netlify)
5. ✅ Test end-to-end

---

**Full guide**: See `DEPLOYMENT_GUIDE.md` for detailed instructions.

