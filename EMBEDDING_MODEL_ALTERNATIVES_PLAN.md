# Embedding Model Alternatives - Research & Plan

## Current Setup
- **Model**: `all-MiniLM-L6-v2` (SentenceTransformer)
- **Embedding Dimension**: 384
- **Model Size**: ~80-90 MB (download + load)
- **Load Time**: 2-5 seconds on first use
- **Speed**: Fast inference (~10-50ms per embedding)
- **Quality**: Good semantic understanding, widely used

## Problem
- Slow backend startup (even with lazy loading, first request is slow)
- Model download on first run can take 10-30 seconds
- Memory footprint (~200-300MB in RAM when loaded)

## Research: Alternative Models

### Option 1: FastEmbed (Recommended for Speed)
**Library**: `fastembed` (by Qdrant)
- **Speed**: 50% faster than PyTorch Transformers
- **Size**: Smaller quantized models
- **Quality**: Better than OpenAI Ada-002, competitive with SentenceTransformers
- **Pros**:
  - Optimized for CPU inference
  - Quantized models (smaller, faster)
  - Easy API: `from fastembed import TextEmbedding`
- **Cons**:
  - Different library (need to change code)
  - May have different embedding dimensions (need to verify)
  - Less community adoption than SentenceTransformers

**Implementation**:
```python
from fastembed import TextEmbedding

# Initialize
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
# or "sentence-transformers/all-MiniLM-L6-v2" (faster wrapper)

# Usage
embeddings = list(embedding_model.embed(["text here"]))
```

### Option 2: Smaller SentenceTransformer Models
**Models to consider**:
- `all-MiniLM-L6-v2` (current) - 384 dim, ~80MB
- `all-MiniLM-L12-v2` - 384 dim, ~120MB (slower, better quality)
- `paraphrase-MiniLM-L3-v2` - 384 dim, ~60MB (smaller, faster)
- `all-mpnet-base-v2` - 768 dim, ~420MB (better quality, much slower)

**Best smaller option**: `paraphrase-MiniLM-L3-v2`
- Same 384 dimensions (no code changes needed!)
- ~25% smaller model
- ~20-30% faster inference
- Slightly lower quality but still very good

### Option 3: Quantized/ONNX Models
**Approach**: Convert SentenceTransformer to ONNX for faster inference
- **Speed**: 2-3x faster inference
- **Size**: Similar or slightly smaller
- **Pros**: Same API, just faster
- **Cons**: Requires conversion step, ONNX runtime dependency

**Implementation**:
```python
from sentence_transformers import SentenceTransformer
from optimum.onnxruntime import ORTModelForFeatureExtraction

# Convert to ONNX (one-time)
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('model_path')
# Convert using optimum library

# Load ONNX version
onnx_model = ORTModelForFeatureExtraction.from_pretrained('model_path', from_tf=False)
```

### Option 4: Model2Vec (Distilled Models)
**Approach**: Use pre-distilled smaller models
- **Speed**: Significantly faster
- **Size**: Much smaller
- **Quality**: Competitive with original
- **Cons**: Limited model availability, may need custom training

### Option 5: Keep Current + Optimize Loading
**Approach**: Keep `all-MiniLM-L6-v2` but optimize:
- Pre-download model on install
- Use model caching more aggressively
- Load in background thread
- Use quantized version if available

## Comparison Table

| Model | Size | Speed | Quality | Dim | Code Changes |
|-------|------|-------|---------|-----|--------------|
| **all-MiniLM-L6-v2** (current) | ~80MB | Fast | Good | 384 | None |
| **paraphrase-MiniLM-L3-v2** | ~60MB | Faster | Good | 384 | Minimal |
| **FastEmbed** | ~50MB | Fastest | Good | 384? | Medium |
| **ONNX all-MiniLM-L6-v2** | ~80MB | Fastest | Good | 384 | Medium |
| **all-MiniLM-L12-v2** | ~120MB | Slower | Better | 384 | None |

## Recommendations

### 🥇 Best Option: `paraphrase-MiniLM-L3-v2`
**Why**:
- Same 384 dimensions → **zero code changes needed**
- Smaller and faster than current
- Still excellent quality
- Easy drop-in replacement

**Implementation**:
```python
# Just change one line:
self._embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
```

### 🥈 Alternative: FastEmbed (if willing to change code)
**Why**:
- Fastest option
- Better performance benchmarks
- Smaller memory footprint
- Requires code changes but better long-term

**Implementation**:
```python
from fastembed import TextEmbedding

# In __init__ or property:
self._embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# In encode method:
embeddings = list(self._embedding_model.embed([text]))
embedding = embeddings[0].tolist()  # Convert to list
```

### 🥉 Keep Current + Optimize
**Why**:
- No risk, no code changes
- Current model works well
- Just optimize loading strategy

**Optimizations**:
1. Pre-download model in Docker/build step
2. Use persistent model cache
3. Background loading on startup
4. Add model loading progress indicator

## Code Changes Required

### For `paraphrase-MiniLM-L3-v2` (Easiest):
- **File**: `backend/services/meetmap_service.py`
- **Change**: Line 44, change model name
- **Testing**: Verify embeddings are still 384-dim (should be same)

### For FastEmbed (Medium):
- **File**: `backend/services/meetmap_service.py`
- **Changes**:
  1. Add `fastembed` to requirements.txt
  2. Change import
  3. Change initialization
  4. Change encode method
- **Testing**: Verify embedding dimensions match (384)

### For ONNX (Medium-Hard):
- **File**: `backend/services/meetmap_service.py`
- **Changes**:
  1. Add `optimum[onnxruntime]` to requirements.txt
  2. Convert model to ONNX (one-time script)
  3. Change model loading
- **Testing**: Verify embeddings match original

## Testing Plan

1. **Benchmark current model**:
   - Load time
   - Inference time per embedding
   - Memory usage
   - Quality (test with sample embeddings)

2. **Test alternative**:
   - Same benchmarks
   - Verify embedding dimensions match
   - Test similarity search still works
   - Verify clustering still works

3. **Quality check**:
   - Compare similarity scores on same text pairs
   - Test with real transcript chunks
   - Verify graph structure still makes sense

## Decision Matrix

Choose based on priority:

- **Speed is #1 priority** → FastEmbed
- **Minimal code changes** → `paraphrase-MiniLM-L3-v2`
- **Best quality** → Keep current or try L12
- **Production ready** → Keep current + optimize loading
- **Future-proof** → FastEmbed or ONNX

## Next Steps

1. ✅ Research complete
2. ⏳ User decision on priority
3. ⏳ Implement chosen option
4. ⏳ Benchmark and compare
5. ⏳ Test with real data
6. ⏳ Deploy if successful


