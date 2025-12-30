# Context-Aware Idea Extraction - Planning Document

## Problem Statement

**Current Flow:**
```
Chunk 1 → GPT (no context) → Extract ideas → Create nodes
Chunk 2 → GPT (no context) → Extract ideas → Create nodes  
Chunk 3 → GPT (no context) → Extract ideas → Create nodes
```

**Issues:**
- GPT has no knowledge of what came before
- Might extract unimportant ideas
- Misses connections to previous ideas
- Creates redundant nodes
- No understanding of conversation flow

---

## Solution 1: Cumulative Summaries (Your Proposal)

### Approach
```
Chunk 1 → GPT → Extract ideas → Summarize chunk 1
Chunk 2 + Summary(1) → GPT → Extract ideas → Summarize chunk 2
Chunk 3 + Summary(1+2) → GPT → Extract ideas → Summarize chunk 3
```

### Implementation
- Maintain a running summary of all previous chunks
- Each new chunk is sent with cumulative summary
- GPT can see what's already been discussed

### Pros ✅
- Simple to implement
- GPT has full conversation context
- Can identify continuations/refinements
- Can filter out less important ideas
- Relatively low token cost (summaries are compact)

### Cons ❌
- Summaries might lose important details
- Could bias GPT towards existing topics
- Summary quality degrades over time (compression loss)
- Need to manage summary length (token limits)

### Token Cost Estimate
- Chunk 1: ~500 tokens (chunk only)
- Chunk 2: ~500 (chunk) + ~200 (summary) = ~700 tokens
- Chunk 3: ~500 (chunk) + ~400 (cumulative summary) = ~900 tokens
- Chunk N: ~500 + ~(N-1)*200 tokens
- **Total for 10 chunks: ~14,000 tokens** (reasonable)

---

## Solution 2: Sliding Window Context

### Approach
```
Keep last N chunks in full (not summarized)
Chunk 1 → Extract ideas
Chunk 2 + Chunk 1 (full) → Extract ideas
Chunk 3 + Chunk 2 + Chunk 1 (full) → Extract ideas
Chunk 4 + Chunk 3 + Chunk 2 (drop Chunk 1) → Extract ideas
```

### Pros ✅
- No information loss (full context)
- More accurate than summaries
- Can see exact wording, not just summaries

### Cons ❌
- Higher token cost (full chunks, not summaries)
- Window size limited by token budget
- Older context still gets dropped

### Token Cost Estimate
- If each chunk ~500 tokens, window of 3:
  - Chunk 1: ~500 tokens
  - Chunk 2: ~1,000 tokens (chunk + previous)
  - Chunk 3+: ~1,500 tokens (chunk + 2 previous)
- **Total for 10 chunks: ~13,500 tokens** (similar to summaries)

---

## Solution 3: Graph-Aware Extraction (Hybrid)

### Approach
```
Chunk N → GPT with:
1. Current chunk text
2. Summary of recent chunks (last 2-3)
3. Current graph structure (node summaries + relationships)
```

### Pros ✅
- GPT knows what nodes already exist
- Can explicitly identify continuations/refinements
- Can suggest which existing nodes to connect to
- Most contextually aware

### Cons ❌
- Most complex to implement
- Highest token cost
- Need to format graph structure for GPT
- Graph structure might be large

### Token Cost Estimate
- Chunk: ~500 tokens
- Recent summaries: ~400 tokens
- Graph structure (10 nodes): ~1,000 tokens
- **Per chunk: ~1,900 tokens**
- **Total for 10 chunks: ~19,000 tokens** (higher but manageable)

---

## Solution 4: Two-Stage Extraction

### Approach
```
Stage 1: Extract ALL potential ideas (current approach, no context)
Stage 2: Filter/Rank with context (GPT with summaries + graph)
```

### Pros ✅
- Doesn't miss ideas in Stage 1
- Context used for filtering/ranking only
- Can be more selective

### Cons ❌
- Two GPT calls per chunk (2x cost)
- More complex pipeline
- Slower processing

---

## Recommendation: **Solution 1 (Cumulative Summaries) + Graph Context**

### Why This Hybrid?
1. **Cumulative summaries** provide conversation flow context
2. **Graph structure** (lightweight) provides existing node context
3. **Balanced cost** - summaries are compact, graph structure is small
4. **Best accuracy** - GPT knows both conversation history AND existing nodes

### Implementation Plan

#### Step 1: Add Summary Storage
```python
class MeetMapService:
    def __init__(self):
        # ... existing code ...
        self.chunk_summaries: List[str] = []  # Store summaries of processed chunks
        self.cumulative_summary: str = ""  # Running cumulative summary
```

#### Step 2: Summarize Each Chunk After Processing
```python
async def _summarize_chunk(self, chunk: TranscriptChunk, extracted_ideas: List[str]) -> str:
    """Create a concise summary of the chunk and ideas extracted"""
    prompt = f"""Summarize this conversation chunk and the key ideas discussed.

Chunk: "{chunk.text}"

Ideas extracted: {extracted_ideas}

Create a concise summary (2-3 sentences) that captures:
- Main topic discussed
- Key points raised
- Any decisions or actions mentioned

Summary:"""
    
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content.strip()
```

#### Step 3: Update Extraction Prompt with Context
```python
async def _extract_ideas(self, chunk: TranscriptChunk) -> List[str]:
    # Build context string
    context_parts = []
    
    # Add cumulative summary
    if self.cumulative_summary:
        context_parts.append(f"Previous conversation summary:\n{self.cumulative_summary}")
    
    # Add lightweight graph context (existing node summaries)
    existing_nodes = self.graph_manager.get_all_nodes_except_root()
    if existing_nodes:
        node_summaries = [f"- {node.summary}" for node in existing_nodes[-10:]]  # Last 10 nodes
        context_parts.append(f"Existing ideas in conversation:\n" + "\n".join(node_summaries))
    
    context_str = "\n\n".join(context_parts) if context_parts else ""
    
    prompt = f"""You are analyzing a conversation transcript chunk.

{context_str}

Current chunk: "{chunk.text}"

Your task:
1. Extract distinct ideas, decisions, actions, or proposals from this chunk
2. Consider if any ideas are continuations or refinements of existing ideas mentioned above
3. Focus on important ideas that add value to the conversation
4. Skip minor comments or unimportant details

Extract each distinct idea as a short, self-contained summary (1-2 sentences max).

Return JSON:
{{
  "ideas": [
    "idea description 1",
    "idea description 2"
  ]
}}"""
```

#### Step 4: Update Processing Flow
```python
async def extract_nodes(self, chunk: TranscriptChunk):
    # Step 1: Extract ideas (with context)
    idea_descriptions = await self._extract_ideas(chunk)
    
    # Step 2-4: Generate embeddings, traverse, place nodes
    # ... existing code ...
    
    # Step 5: Summarize chunk and update cumulative summary
    if idea_descriptions:
        chunk_summary = await self._summarize_chunk(chunk, idea_descriptions)
        self.chunk_summaries.append(chunk_summary)
        self.cumulative_summary = self._update_cumulative_summary(chunk_summary)
    
    # Step 6: Convert to frontend format
    return nodes, edges
```

#### Step 5: Manage Cumulative Summary Length
```python
def _update_cumulative_summary(self, new_summary: str) -> str:
    """Update cumulative summary, keeping it concise"""
    if not self.cumulative_summary:
        return new_summary
    
    # Option 1: Simple concatenation (grows linearly)
    updated = f"{self.cumulative_summary}\n\n{new_summary}"
    
    # Option 2: Re-summarize if too long (better, but costs tokens)
    if len(updated.split()) > 200:  # ~400 tokens
        # Re-summarize to keep it compact
        prompt = f"""Summarize these conversation summaries into one concise summary:

{self.cumulative_summary}

{new_summary}

Create a single concise summary (3-4 sentences) that captures the main topics and progression."""
        response = self.client.chat.completions.create(...)
        return response.choices[0].message.content.strip()
    
    return updated
```

---

## Alternative: Lightweight Graph Context Only

If token cost is a concern, we can skip cumulative summaries and just use graph context:

```python
# Only send existing node summaries (last 10-15 nodes)
existing_nodes = self.graph_manager.get_all_nodes_except_root()
node_summaries = [f"- {node.summary}" for node in existing_nodes[-15:]]

prompt = f"""Existing ideas in this conversation:
{chr(10).join(node_summaries)}

New chunk: "{chunk.text}"

Extract ideas, considering if they relate to existing ideas above."""
```

**Pros:** Lower cost, still provides context  
**Cons:** Less conversation flow awareness

---

## Decision Matrix

| Solution | Token Cost | Accuracy | Complexity | Recommendation |
|----------|-----------|----------|------------|----------------|
| Cumulative Summaries | Medium | High | Low | ✅ **Best balance** |
| Sliding Window | Medium | Very High | Low | ✅ Good alternative |
| Graph-Aware Hybrid | Higher | Very High | Medium | ✅ Best accuracy |
| Two-Stage | High | Very High | High | ❌ Too complex |
| Graph Only | Low | Medium | Low | ✅ Good if cost-sensitive |

---

## Final Recommendation

**Implement Solution 1 (Cumulative Summaries) with optional Graph Context:**

1. **Start with Cumulative Summaries only** (simpler, good results)
2. **Add lightweight graph context** (last 10 node summaries) if needed
3. **Monitor token usage** and adjust summary length management
4. **Consider re-summarizing** cumulative summary every 5-10 chunks to prevent bloat

This gives you:
- ✅ Conversation flow awareness
- ✅ Ability to identify continuations
- ✅ Reasonable token cost
- ✅ Simple implementation
- ✅ Can add graph context later if needed

---

## Next Steps

1. Add summary storage to `MeetMapService`
2. Implement `_summarize_chunk()` method
3. Update `_extract_ideas()` to include cumulative summary
4. Add cumulative summary management (length limits)
5. Test with multiple chunks to verify context awareness
6. Monitor token usage and adjust as needed

