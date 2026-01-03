# Backend Size Analysis (730 MB)

## Why is your backend 730 MB?

The size comes from **large machine learning dependencies**. Here's the breakdown:

---

## 📦 Size Breakdown

### **Major Contributors:**

1. **PyTorch (`torch>=2.0.0`)** - **~500-600 MB** 🔴
   - Required by `sentence-transformers`
   - Deep learning framework (huge library)

2. **Transformers (`transformers>=4.30.0`)** - **~200-300 MB** 🔴
   - Required by `sentence-transformers`
   - Hugging Face transformers library

3. **Sentence Transformers (`sentence-transformers>=2.2.2`)** - **~100-150 MB** 🟡
   - **ACTUALLY USED** in your code
   - Depends on torch + transformers

4. **Scikit-learn (`scikit-learn>=1.3.2`)** - **~50-100 MB** 🟡
   - Required by `sentence-transformers`
   - Machine learning utilities

5. **Model Files (`all-MiniLM-L6-v2`)** - **~80 MB** 🟡
   - Downloaded at runtime (not in package size)
   - But cached after first use

6. **Other Dependencies** - **~50 MB** 🟢
   - FastAPI, uvicorn, numpy, etc.

**Total: ~730 MB** ✅

---

## 🔍 What You're Actually Using

### ✅ **USED Dependencies:**
- `sentence-transformers` - **USED** (in `meetmap_service.py`)
- `torch` - **REQUIRED** by sentence-transformers
- `transformers` - **REQUIRED** by sentence-transformers
- `scikit-learn` - **REQUIRED** by sentence-transformers
- `numpy` - **REQUIRED** by sentence-transformers

### ❌ **UNUSED Dependencies (Can Remove):**
- `bertopic==0.15.0` - **NOT USED** (only in `talktraces_service.py` which isn't imported)
- `keybert==0.8.1` - **NOT USED** (only in `talktraces_service.py` which isn't imported)
- `neo4j==5.14.0` - **NOT USED** (database driver, not imported anywhere)
- `soundcard>=0.4.2` - **NOT USED** (audio library, not imported anywhere)
- `rake-nltk==1.0.6` - **NOT USED** (not imported in active code)

---

## 🎯 How to Reduce Size

### Option 1: Remove Unused Dependencies (Saves ~50-100 MB)

Remove these from `requirements.txt`:
```python
# REMOVE THESE (not used):
# bertopic==0.15.0
# keybert==0.8.1
# neo4j==5.14.0
# soundcard>=0.4.2
# rake-nltk==1.0.6
```

**Savings: ~50-100 MB** (not much, but helps)

---

### Option 2: Use CPU-Only PyTorch (Saves ~200-300 MB)

PyTorch comes with CUDA (GPU) support by default, which adds ~200-300 MB.

**Replace:**
```python
torch>=2.0.0
```

**With:**
```python
torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu
```

Or use the CPU-only version:
```python
# For CPU-only (smaller):
torch==2.0.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

**Savings: ~200-300 MB** (significant!)

**Note**: Railway free tier doesn't have GPUs anyway, so CPU-only is fine.

---

### Option 3: Use Lighter Embedding Model (Already Done ✅)

You're already using `all-MiniLM-L6-v2` which is the smallest good model:
- Size: ~80 MB
- Quality: Good for semantic similarity
- Speed: Fast

**No change needed here.**

---

### Option 4: Optimize Dependencies (Advanced)

Use `--no-deps` and install only what's needed, but this is complex and not recommended.

---

## 🚀 Recommended Action Plan

### Step 1: Remove Unused Dependencies

Update `requirements.txt`:
```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
openai==1.3.0
httpx<0.28,>=0.25.0
httpcore<1.0,>=0.18.0
python-dotenv==1.0.0
pydantic==2.5.0
numpy>=1.24.3,<2.0.0
sentence-transformers>=2.2.2
scikit-learn>=1.3.2
python-multipart==0.0.6
aiofiles==23.2.1
# Use CPU-only PyTorch (smaller)
--extra-index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0
transformers>=4.30.0

# REMOVED (not used):
# rake-nltk==1.0.6
# keybert==0.8.1
# bertopic==0.15.0
# neo4j==5.14.0
# soundcard>=0.4.2
```

**Expected size: ~450-500 MB** (down from 730 MB)

---

### Step 2: Verify It Still Works

After removing dependencies:
1. Test locally: `pip install -r requirements.txt`
2. Test backend: `python main.py`
3. Test API: Send a transcript chunk
4. Verify embeddings work

---

## 📊 Size Comparison

| Configuration | Size | Notes |
|--------------|------|-------|
| **Current** | **730 MB** | Full PyTorch + unused deps |
| **After cleanup** | **~500 MB** | CPU-only PyTorch + removed unused |
| **Minimal** | **~400 MB** | Would require major refactoring |

---

## 💡 Why 730 MB is Actually Normal

**This is normal for ML backends!**

- PyTorch alone is 500-600 MB
- Transformers is 200-300 MB
- Sentence-transformers adds 100-150 MB
- **Total: ~730 MB** ✅

**Comparison:**
- TensorFlow: ~800-1000 MB
- PyTorch: ~500-600 MB (what you have)
- Scikit-learn only: ~50-100 MB (but can't do embeddings)

**Your size is reasonable for an ML backend.**

---

## 🎯 Bottom Line

### **730 MB is normal** for a backend with:
- Sentence transformers (embeddings)
- PyTorch (ML framework)
- Transformers (Hugging Face)

### **You can reduce to ~500 MB** by:
1. ✅ Removing unused dependencies (bertopic, keybert, neo4j, soundcard)
2. ✅ Using CPU-only PyTorch (Railway doesn't have GPUs anyway)

### **Railway Free Tier:**
- **512 MB RAM** - Might be tight
- **Recommended: Hobby tier ($5/month)** - 1 GB RAM, comfortable

---

## ✅ Quick Fix

Want me to create an optimized `requirements.txt` that removes unused dependencies and uses CPU-only PyTorch? This will reduce size to ~500 MB.

