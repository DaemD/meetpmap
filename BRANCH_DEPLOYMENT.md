# Branch Deployment Guide
## Deploying from Any Branch (Not Just Main)

---

## 🎯 Quick Answer

**No, you don't need to push to `main`!** All platforms let you configure which branch triggers deployments.

---

## Platform-Specific Branch Configuration

### Railway

**Default**: `main` branch

**Change Branch**:
1. Go to your project → **Settings** → **Service Settings**
2. Under **Source**, find **Branch** dropdown
3. Select your branch:
   - `main` (production)
   - `develop` (staging)
   - `feature/xyz` (feature branch)
   - Or **"All branches"** to deploy from any branch

**Multiple Environments**:
- Create separate Railway services for different branches
- Service 1: `main` → Production
- Service 2: `develop` → Staging
- Service 3: `feature/*` → Preview deployments

---

### Render

**Default**: `main` branch

**Change Branch**:
1. Go to your service → **Settings**
2. Scroll to **Build & Deploy**
3. Under **Branch**, select your branch
4. Or enable **"Auto-Deploy"** for specific branches

**Branch Rules**:
- Production: `main`
- Preview: Any other branch (creates preview URL)

---

### Fly.io

**Default**: `main` branch

**Change Branch**:
1. In `fly.toml`, add:
```toml
[build]
  branch = "develop"  # or your branch name
```

2. Or use Fly CLI:
```bash
fly deploy --branch develop
```

**Multiple Apps**:
- Create separate Fly apps for different branches
- `meetmap-prod` → `main` branch
- `meetmap-staging` → `develop` branch

---

### DigitalOcean App Platform

**Default**: `main` branch

**Change Branch**:
1. Go to **Settings** → **App Spec**
2. Edit `branch` field:
```yaml
name: meetmap-backend
branch: develop  # Change this
```

---

## 🎯 Common Branch Strategies

### Strategy 1: Single Branch (Simple)

**Use**: `main` branch only
- Push to `main` → Auto-deploys to production
- Simple, but no staging environment

**Setup**: Default configuration (no changes needed)

---

### Strategy 2: Main + Develop (Recommended)

**Use**: Two branches
- `main` → Production deployment
- `develop` → Staging/testing deployment

**Setup**:
1. Create two services on your platform:
   - **Production**: Connected to `main` branch
   - **Staging**: Connected to `develop` branch
2. Workflow:
   ```bash
   # Work on develop branch
   git checkout develop
   git add .
   git commit -m "New feature"
   git push origin develop
   # → Auto-deploys to staging
   
   # When ready, merge to main
   git checkout main
   git merge develop
   git push origin main
   # → Auto-deploys to production
   ```

---

### Strategy 3: All Branches (Preview Deployments)

**Use**: Deploy from any branch
- `main` → Production
- `develop` → Staging
- `feature/xyz` → Preview URL (for testing)

**Setup**:
- Railway: Set branch to **"All branches"**
- Render: Enable **"Auto-Deploy"** for all branches
- Each branch gets its own preview URL

**Example**:
```bash
# Create feature branch
git checkout -b feature/new-api
git push origin feature/new-api
# → Gets preview URL: https://feature-new-api.up.railway.app
```

---

## 🔧 How to Set Up Multi-Branch Deployment

### Example: Railway (Two Environments)

1. **Create Production Service**:
   - New Project → Connect GitHub
   - Branch: `main`
   - Name: `meetmap-prod`
   - URL: `https://meetmap-prod.up.railway.app`

2. **Create Staging Service**:
   - New Service → Connect same GitHub repo
   - Branch: `develop`
   - Name: `meetmap-staging`
   - URL: `https://meetmap-staging.up.railway.app`

3. **Different Environment Variables** (if needed):
   - Production: `OPENAI_API_KEY=prod_key`
   - Staging: `OPENAI_API_KEY=test_key`

---

## 📋 Workflow Examples

### Example 1: Feature Branch Testing

```bash
# Create feature branch
git checkout -b feature/add-clustering
# ... make changes ...
git add .
git commit -m "Add clustering feature"
git push origin feature/add-clustering

# Platform creates preview deployment
# Test at: https://feature-add-clustering.up.railway.app

# When done, merge to develop
git checkout develop
git merge feature/add-clustering
git push origin develop
# → Deploys to staging
```

### Example 2: Hotfix to Production

```bash
# Fix urgent bug
git checkout main
git checkout -b hotfix/critical-bug
# ... fix bug ...
git add .
git commit -m "Fix critical bug"
git push origin hotfix/critical-bug

# Test preview, then merge to main
git checkout main
git merge hotfix/critical-bug
git push origin main
# → Auto-deploys to production
```

---

## ⚠️ Important Notes

1. **Branch Protection**: Consider protecting `main` branch on GitHub
   - Require pull requests
   - Require reviews
   - Prevent direct pushes

2. **Environment Variables**: Can be different per branch/service
   - Production: Real API keys
   - Staging: Test API keys
   - Preview: Shared test keys

3. **Database/State**: 
   - Production and staging should have separate databases
   - Preview deployments can share staging database

4. **Cost**: 
   - Multiple services = multiple deployments
   - Railway free tier: 500 hours/month total (across all services)
   - Preview deployments count toward usage

---

## 🎯 Recommended Setup for Your Project

**For Development/Testing**:
```
main branch → Production (railway.app/meetmap-prod)
develop branch → Staging (railway.app/meetmap-staging)
```

**Workflow**:
1. Work on `develop` branch
2. Test on staging URL
3. When ready, merge `develop` → `main`
4. Production auto-updates

**Commands**:
```bash
# Daily work
git checkout develop
# ... make changes ...
git push origin develop  # → Deploys to staging

# Release to production
git checkout main
git merge develop
git push origin main  # → Deploys to production
```

---

## ✅ Summary

- ✅ **You can deploy from ANY branch**
- ✅ **Default is `main`, but easily changeable**
- ✅ **Multiple branches = multiple environments**
- ✅ **Preview deployments for feature branches**
- ✅ **Configure in platform settings (usually under "Branch")**

**No need to always push to `main`!** Use whatever branch strategy fits your workflow.


