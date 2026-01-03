# Product Requirements Document (PRD)
## MeetMap: Transcript-to-Graph Pipeline

**Version:** 1.0  
**Date:** January 2025  
**Status:** Production

---

## 1. Executive Summary

### 1.1 Purpose
This PRD documents the complete pipeline that transforms conversation transcript chunks into a semantic idea-evolution graph. The system extracts ideas from text, generates vector embeddings, performs semantic similarity search, uses LLM-based placement decisions, and dynamically clusters nodes for visual color-coding.

### 1.2 Key Features
- **Real-time Processing**: Streams transcript chunks as they arrive
- **Semantic Understanding**: Uses vector embeddings for similarity matching
- **Intelligent Placement**: LLM decides parent-child relationships based on conversational flow
- **Dynamic Clustering**: Threshold-based incremental clustering for color-coding
- **Context-Aware**: Considers recent conversation history for better extraction

---

## 2. Pipeline Overview

### 2.1 High-Level Flow

```
Transcript Chunk (Input)
    ↓
[STEP 1] GPT Idea Extraction
    ↓
[STEP 2] Embedding Generation
    ↓
[STEP 3] Global Similarity Search
    ↓
[STEP 4] LLM Placement Decision
    ↓
[STEP 5] Node Creation & Clustering
    ↓
[STEP 6] Frontend Format Conversion
    ↓
Nodes & Edges (Output)
```

### 2.2 Pipeline Stages

| Stage | Component | Purpose | Output |
|-------|-----------|---------|--------|
| **Step 1** | GPT-4o-mini | Extract distinct ideas from chunk | List of idea descriptions |
| **Step 2** | SentenceTransformer | Generate vector embeddings | 384-dim embedding vectors |
| **Step 3** | GraphManager | Find similar nodes globally | Top-K similar nodes |
| **Step 4** | GPT-4o-mini | Decide parent placement | `parent_id` |
| **Step 5** | GraphManager | Add node + assign cluster | GraphNode with cluster_id |
| **Step 6** | MeetMapService | Convert to frontend format | NodeData[] + EdgeData[] |

---

## 3. Detailed Pipeline Stages

### 3.1 STEP 1: GPT Idea Extraction

#### 3.1.1 Purpose
Extract distinct, self-contained ideas from a transcript chunk. GPT's **only role** is extraction—no graph decisions.

#### 3.1.2 Input
- `TranscriptChunk`:
  ```python
  {
    "chunk_id": str,
    "text": str,           # Raw transcript text
    "start": float,         # Timestamp
    "end": float,
    "speaker": str          # Optional
  }
  ```

#### 3.1.3 Process

1. **Context Gathering**:
   - Retrieve nodes from most recent 5 chunks
   - Build context string: `"Chunk X: - idea1\n- idea2\n..."`
   - Purpose: Help GPT understand conversation flow

2. **GPT Prompt Construction**:
   ```
   System: "You are an expert at extracting clear, concise ideas..."
   
   User Prompt:
   - Recent conversation context (last 5 chunks)
   - Current chunk text
   - Instructions:
     * Extract distinct ideas (1-2 sentences max)
     * Focus on: new ideas, decisions, actions, proposals
     * Consider context but extract naturally
     * NO graph structure decisions
     * NO parent-child relationships
   ```

3. **API Call**:
   - Model: `gpt-4o-mini`
   - Temperature: `0.3` (deterministic)
   - Max tokens: `500`
   - Response format: JSON `{"ideas": ["idea1", "idea2", ...]}`

4. **Response Parsing**:
   - Handle markdown code blocks (```json)
   - Extract `ideas` array
   - Filter empty strings
   - Return: `List[str]`

#### 3.1.4 Output
```python
[
  "We should implement user authentication",
  "Consider using OAuth2 for SSO",
  "Need to add rate limiting"
]
```

#### 3.1.5 Error Handling
- API failure → Return empty list `[]`
- Invalid JSON → Parse error logged, return `[]`
- No ideas extracted → Continue pipeline (empty result)

#### 3.1.6 Performance
- **Expected time**: 0.5-2.0 seconds per chunk
- **Factors**: Chunk length, context size, API latency

---

### 3.2 STEP 2: Embedding Generation

#### 3.2.1 Purpose
Convert idea text into 384-dimensional vector embeddings for semantic similarity comparison.

#### 3.2.2 Input
- Idea text: `str` (from Step 1)

#### 3.2.3 Process

1. **Model Loading**:
   - Model: `all-MiniLM-L6-v2` (SentenceTransformer)
   - Loaded at service initialization (eager loading)
   - Dimension: 384
   - Size: ~80MB

2. **Encoding**:
   ```python
   embedding = embedding_model.encode(idea_text).tolist()
   ```
   - Input: String
   - Output: `List[float]` (384 elements)
   - Normalized: Yes (L2 normalized by default)

#### 3.2.4 Output
```python
[0.123, -0.456, 0.789, ..., 0.234]  # 384 floats
```

#### 3.2.5 Performance
- **Expected time**: 0.01-0.05 seconds per idea
- **Bottleneck**: Model inference (CPU/GPU)

---

### 3.3 STEP 3: Global Similarity Search

#### 3.3.1 Purpose
Find the top-K most semantically similar nodes in the entire graph using cosine similarity.

#### 3.3.2 Input
- `candidate_embedding`: `List[float]` (384-dim)
- Graph state: All existing nodes (except root)

#### 3.3.3 Process

1. **Node Collection**:
   ```python
   all_nodes = graph_manager.get_all_nodes_except_root()
   ```
   - Excludes root node (placeholder)
   - Returns: `List[GraphNode]`

2. **Similarity Calculation**:
   For each existing node:
   ```python
   similarity = cosine_similarity(candidate_embedding, node.embedding)
   ```
   - Formula: `dot(a, b) / (||a|| * ||b||)`
   - Range: `[-1, 1]` (typically `[0, 1]` for normalized vectors)
   - Higher = more similar

3. **Top-K Selection**:
   - Sort by similarity (descending)
   - Take top `K = min(5, available_nodes)`
   - No threshold filtering (get top-K regardless)

4. **Result Format**:
   ```python
   [
     (node_id, similarity_score, GraphNode),
     (node_id, similarity_score, GraphNode),
     ...
   ]
   ```

#### 3.3.4 Output
```python
[
  ("node_5", 0.87, GraphNode(...)),
  ("node_2", 0.82, GraphNode(...)),
  ("node_8", 0.79, GraphNode(...)),
  ...
]
```

#### 3.3.5 Performance
- **Time complexity**: O(n) where n = number of nodes
- **Expected time**: 0.001-0.01 seconds (for <1000 nodes)
- **Bottleneck**: Linear scan (no indexing yet)

#### 3.3.6 Future Optimization
- Vector database (Pinecone, Weaviate, Qdrant)
- Approximate nearest neighbor (ANN) search
- O(log n) or O(1) lookup instead of O(n)

---

### 3.4 STEP 4: LLM Placement Decision

#### 3.4.1 Purpose
Use LLM to decide where to place the new node in the graph based on conversational flow and semantic relationships.

#### 3.4.2 Input
- `candidate_summary`: `str` (idea text)
- `candidate_embedding`: `List[float]` (not used in prompt, but available)
- `similar_nodes`: `List[(node_id, similarity, GraphNode)]` (from Step 3)

#### 3.4.3 Process

1. **Context Building**:
   For each similar node:
   - Node ID, text, similarity score
   - Depth in graph
   - Path from root: `"root → node_1 → node_2"`
   - Parent ID

2. **GPT Prompt Construction**:
   ```
   System: "You are an expert at understanding conversational flow..."
   
   User Prompt:
   - New idea: "{candidate_summary}"
   - Similar existing nodes (with paths, depths, similarities)
   - Decision types:
     * "continuation": Deepens/elaborates existing idea → CHILD of target
     * "branch": Different direction, same parent → SIBLING of target
     * "resolution": Answers/resolves target → CHILD of target
   - Rules:
     * For "continuation"/"resolution": parent_id = target_node_id
     * For "branch": parent_id = target_node_id's parent
   ```

3. **API Call**:
   - Model: `gpt-4o-mini`
   - Temperature: `0.3`
   - Max tokens: `300`
   - Response: JSON `{decision, target_node_id, parent_id, reasoning}`

4. **Validation & Enforcement**:
   ```python
   if decision == "continuation" or "resolution":
       parent_id = target_node_id  # Force child placement
   elif decision == "branch":
       parent_id = target_node.parent_id  # Force sibling placement
   ```
   - Validates `target_node_id` exists in similar_nodes
   - Validates `parent_id` exists in graph
   - Fallback: Use root if invalid

#### 3.4.4 Output
```python
parent_id: str  # e.g., "node_5" or "root"
```

#### 3.4.5 Decision Types

| Type | Meaning | Placement | Example |
|------|---------|-----------|---------|
| **continuation** | Deepens/elaborates | Child of target | "Add rate limiting" → child of "Implement auth" |
| **branch** | Different direction | Sibling of target | "Add dark mode" → sibling of "Add auth" |
| **resolution** | Answers/resolves | Child of target | "Use OAuth2" → child of "How to auth?" |

#### 3.4.6 Error Handling
- Invalid `target_node_id` → Use first similar node
- Invalid `parent_id` → Use target's parent or root
- API failure → Use most similar node's parent

#### 3.4.7 Performance
- **Expected time**: 0.5-2.0 seconds
- **Factors**: Number of similar nodes, API latency

---

### 3.5 STEP 5: Node Creation & Clustering

#### 3.5.1 Purpose
Add node to graph structure and assign it to a color cluster using threshold-based incremental clustering.

#### 3.5.2 Input
- `node_id`: `str` (e.g., "node_10")
- `embedding`: `List[float]` (384-dim)
- `summary`: `str` (idea text)
- `parent_id`: `str` (from Step 4)
- `metadata`: `dict` (chunk_id, timestamp, speaker)

#### 3.5.3 Process

**A. Node Creation**:

1. **Validate Parent**:
   ```python
   parent = graph_manager.get_node(parent_id)
   if not parent:
       raise ValueError("Parent does not exist")
   ```

2. **Calculate Depth**:
   ```python
   depth = parent.depth + 1
   ```

3. **Create GraphNode**:
   ```python
   node = GraphNode(
       id=node_id,
       embedding=embedding,
       summary=summary,
       parent_id=parent_id,
       children_ids=[],
       depth=depth,
       last_updated=time.time(),
       metadata={...}
   )
   ```

4. **Update Graph**:
   - Add to `graph_manager.nodes[node_id]`
   - Append `node_id` to `parent.children_ids`

**B. Cluster Assignment**:

1. **Check Existing Clusters**:
   - If no clusters exist → Create cluster 0

2. **Find Best Cluster**:
   ```python
   for cluster_id, centroid in cluster_centroids.items():
       similarity = cosine_similarity(embedding, centroid)
       if similarity > best_similarity:
           best_similarity = similarity
           best_cluster_id = cluster_id
   ```

3. **Threshold Check**:
   ```python
   if best_similarity >= CLUSTER_SIMILARITY_THRESHOLD (0.65):
       # Assign to existing cluster
       cluster_members[cluster_id].append(node_id)
       node.metadata["cluster_id"] = cluster_id
       _update_centroid(cluster_id, embedding)  # Running average
   else:
       # Create new cluster
       cluster_id = next_cluster_id
       cluster_centroids[cluster_id] = embedding.copy()
       cluster_members[cluster_id] = [node_id]
       node.metadata["cluster_id"] = cluster_id
       next_cluster_id += 1
   ```

4. **Centroid Update** (if assigned to existing):
   ```python
   # Running average: new_centroid = (old * (n-1) + new) / n
   new_centroid = (old_centroid * (n - 1) + new_embedding) / n
   ```

#### 3.5.4 Output
- `GraphNode` with `metadata["cluster_id"]` set

#### 3.5.5 Clustering Details

**Threshold-Based Incremental Clustering**:
- **Similarity threshold**: `0.65` (cosine similarity)
- **Dynamic K**: Clusters created on-the-fly
- **Centroid update**: Running average (no full recomputation)
- **Color assignment**: `CLUSTER_COLORS[cluster_id % 20]`

**Why This Approach**:
- ✅ Streaming data (nodes arrive one at a time)
- ✅ Unknown number of topics
- ✅ Real-time color assignment
- ✅ No expensive re-clustering

**vs K-means**:
- ❌ K-means requires fixed K upfront
- ❌ K-means needs all data at once
- ❌ K-means requires full recomputation

#### 3.5.6 Performance
- **Node creation**: O(1) - constant time
- **Cluster assignment**: O(k) where k = number of clusters
- **Expected time**: <0.001 seconds

---

### 3.6 STEP 6: Frontend Format Conversion

#### 3.6.1 Purpose
Convert internal `GraphNode` objects to frontend-compatible `NodeData` and `EdgeData` formats.

#### 3.6.2 Input
- `new_graph_nodes`: `List[GraphNode]` (nodes created in this chunk)

#### 3.6.3 Process

1. **Root Node Inclusion** (first chunk only):
   ```python
   if not root_sent and len(new_graph_nodes) > 0:
       root_node_data = NodeData(
           id="root",
           text="Meeting Start",
           type="idea",
           metadata={"is_root": True, ...}
       )
       nodes.append(root_node_data)
       root_sent = True
   ```

2. **Convert GraphNodes to NodeData**:
   ```python
   for graph_node in new_graph_nodes:
       cluster_id = graph_node.metadata.get("cluster_id")
       cluster_color = graph_manager.get_cluster_color(cluster_id)
       
       node_data = NodeData(
           id=graph_node.id,
           text=graph_node.summary,
           type="idea",
           timestamp=graph_node.metadata.get("timestamp"),
           metadata={
               "depth": graph_node.depth,
               "parent_id": graph_node.parent_id,
               "children_count": len(graph_node.children_ids),
               "cluster_id": cluster_id,
               "cluster_color": cluster_color,
               ...
           }
       )
       nodes.append(node_data)
   ```

3. **Create Edges**:
   ```python
   if graph_node.parent_id:
       edge = EdgeData(
           from_node=graph_node.parent_id,
           to_node=graph_node.id,
           type="extends" if parent != "root" else "root",
           strength=1.0,
           metadata={"relationship": "parent_child"}
       )
       edges.append(edge)
   ```

#### 3.6.4 Output
```python
(
    [NodeData, NodeData, ...],  # List of nodes
    [EdgeData, EdgeData, ...]   # List of edges
)
```

#### 3.6.5 Data Structures

**NodeData**:
```python
{
    "id": str,
    "text": str,
    "type": str,  # "idea"
    "timestamp": float,
    "confidence": float,
    "metadata": {
        "depth": int,
        "parent_id": str,
        "children_count": int,
        "cluster_id": int,
        "cluster_color": str,  # Hex color
        "chunk_id": str,
        "speaker": str,
        ...
    }
}
```

**EdgeData**:
```python
{
    "from_node": str,
    "to_node": str,
    "type": str,  # "root" or "extends"
    "strength": float,
    "metadata": {
        "relationship": "parent_child"
    }
}
```

---

## 4. Data Structures

### 4.1 GraphNode (Internal)

```python
class GraphNode:
    id: str
    embedding: List[float]  # 384-dim
    summary: str
    parent_id: Optional[str]
    children_ids: List[str]
    depth: int
    last_updated: float
    metadata: dict  # cluster_id, chunk_id, timestamp, speaker, ...
```

### 4.2 Graph Structure

```python
class GraphManager:
    nodes: Dict[str, GraphNode]  # node_id -> GraphNode
    root_id: str  # "root"
    
    # Clustering state
    cluster_centroids: Dict[int, List[float]]  # cluster_id -> centroid
    cluster_members: Dict[int, List[str]]      # cluster_id -> [node_ids]
    next_cluster_id: int
    CLUSTER_SIMILARITY_THRESHOLD: float = 0.65
    CLUSTER_COLORS: List[str]  # 20 colors
```

---

## 5. API Endpoints

### 5.1 POST `/api/transcript`

**Purpose**: Process a transcript chunk and return new nodes/edges

**Request**:
```json
{
  "chunk_id": "chunk_1",
  "text": "We should implement user authentication...",
  "start": 0.0,
  "end": 5.2,
  "speaker": "Alice"
}
```

**Response**:
```json
{
  "status": "success",
  "nodes": [
    {
      "id": "node_1",
      "text": "We should implement user authentication",
      "type": "idea",
      "metadata": {
        "cluster_id": 0,
        "cluster_color": "#FF6B6B",
        "depth": 1,
        ...
      }
    }
  ],
  "edges": [
    {
      "from_node": "root",
      "to_node": "node_1",
      "type": "root"
    }
  ]
}
```

### 5.2 GET `/api/graph/state`

**Purpose**: Get complete graph state (all nodes and edges)

**Response**: Same format as POST, but includes all nodes/edges

---

## 6. Performance Characteristics

### 6.1 Pipeline Timing (Per Chunk)

| Stage | Expected Time | Bottleneck |
|-------|---------------|------------|
| Step 1: GPT Extraction | 0.5-2.0s | API latency |
| Step 2: Embedding | 0.01-0.05s | Model inference |
| Step 3: Similarity Search | 0.001-0.01s | Linear scan (O(n)) |
| Step 4: LLM Placement | 0.5-2.0s | API latency |
| Step 5: Node Creation | <0.001s | In-memory ops |
| Step 6: Conversion | <0.001s | Data transformation |
| **Total** | **1.0-4.0s** | **API calls** |

### 6.2 Scalability

**Current Limitations**:
- Linear similarity search: O(n) per node
- No vector database indexing
- In-memory graph (not persisted)

**Scaling Considerations**:
- **<100 nodes**: Fast (<0.01s search)
- **100-1000 nodes**: Acceptable (<0.1s search)
- **>1000 nodes**: Needs optimization (vector DB)

### 6.3 Memory Usage

- **Embedding model**: ~80MB (loaded once)
- **Per node**: ~1-2KB (embedding + metadata)
- **1000 nodes**: ~1-2MB
- **Total (typical)**: <100MB

---

## 7. Error Handling & Edge Cases

### 7.1 Error Scenarios

| Scenario | Handling | Fallback |
|----------|----------|----------|
| GPT API failure | Log error, return `[]` | Skip chunk |
| Invalid JSON response | Parse error logged | Return `[]` |
| No ideas extracted | Continue pipeline | Empty result |
| No similar nodes found | Place under root | `parent_id = "root"` |
| Invalid parent_id | Validate & fix | Use root |
| Embedding model error | Exception logged | Skip node |

### 7.2 Edge Cases

1. **Empty chunk**: Returns `[]` nodes, `[]` edges
2. **First chunk**: Creates root node + first real node
3. **Very similar ideas**: Both get same cluster_id
4. **Completely new topic**: Creates new cluster
5. **Graph reset**: Clears all nodes, resets clusters

---

## 8. Configuration & Parameters

### 8.1 Thresholds

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `SIMILARITY_THRESHOLD` | 0.75 | Placement similarity (not used in search) |
| `CLUSTER_SIMILARITY_THRESHOLD` | 0.65 | Cluster assignment threshold |
| `TOP_K_DEFAULT` | 5 | Number of similar nodes for LLM |

### 8.2 Models

| Component | Model | Version |
|-----------|-------|---------|
| Idea Extraction | GPT | `gpt-4o-mini` |
| Placement Decision | GPT | `gpt-4o-mini` |
| Embeddings | SentenceTransformer | `all-MiniLM-L6-v2` |

### 8.3 Context Windows

| Context | Size | Purpose |
|---------|------|---------|
| Recent chunks | 5 | GPT idea extraction context |
| Similar nodes | Top-K (5) | LLM placement context |

---

## 9. Future Improvements

### 9.1 Short-Term (Next Sprint)

1. **Vector Database Integration**
   - Replace linear search with ANN search
   - Options: Pinecone, Weaviate, Qdrant
   - Expected: 10-100x faster similarity search

2. **Smaller Embedding Model**
   - Switch to `paraphrase-MiniLM-L3-v2`
   - 25% faster loading, same dimensions
   - Trade-off: Slightly lower quality

3. **Batch Processing**
   - Process multiple ideas in parallel
   - Reduce total pipeline time

### 9.2 Medium-Term (Next Quarter)

1. **Graph Persistence**
   - Save graph to database (PostgreSQL/Neo4j)
   - Support multiple meetings
   - Graph versioning

2. **Advanced Clustering**
   - Hierarchical clustering
   - Cluster merging/splitting
   - Dynamic threshold adjustment

3. **Performance Monitoring**
   - Track pipeline timings
   - Alert on slow chunks
   - Dashboard for metrics

### 9.3 Long-Term (Future)

1. **Multi-Modal Support**
   - Audio embeddings
   - Image/slide analysis
   - Video transcription

2. **Graph Analytics**
   - Topic evolution over time
   - Influence propagation
   - Decision tree visualization

3. **Real-Time Collaboration**
   - Multiple users viewing same graph
   - Live updates via WebSocket
   - Conflict resolution

---

## 10. Testing & Validation

### 10.1 Unit Tests

- [ ] GPT extraction parsing
- [ ] Embedding generation
- [ ] Cosine similarity calculation
- [ ] Cluster assignment logic
- [ ] Node creation & parent updates

### 10.2 Integration Tests

- [ ] Full pipeline with mock GPT
- [ ] Graph state persistence
- [ ] Error handling scenarios
- [ ] Edge case handling

### 10.3 Performance Tests

- [ ] Pipeline timing (target: <4s per chunk)
- [ ] Memory usage (target: <100MB for 1000 nodes)
- [ ] Scalability (100, 1000, 10000 nodes)

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **Chunk** | A segment of transcript text with timestamps |
| **Idea** | A distinct concept extracted from a chunk |
| **Embedding** | 384-dimensional vector representation of text |
| **Similarity** | Cosine similarity between embeddings (0-1) |
| **Cluster** | Group of semantically similar nodes (same color) |
| **Centroid** | Average embedding of all nodes in a cluster |
| **Parent** | Node that this node extends/continues |
| **Child** | Node that extends/continues this node |
| **Depth** | Distance from root node (root = 0) |
| **Continuation** | Idea that deepens/elaborates another |
| **Branch** | Idea that takes conversation in new direction |
| **Resolution** | Idea that answers/resolves another |

---

## 12. Appendix

### 12.1 Example Pipeline Execution

**Input Chunk**:
```json
{
  "chunk_id": "chunk_1",
  "text": "We need to add user authentication. Let's use OAuth2 for SSO.",
  "start": 0.0,
  "end": 3.5
}
```

**Step 1 Output**:
```json
[
  "We need to add user authentication",
  "Let's use OAuth2 for SSO"
]
```

**Step 2 Output** (for first idea):
```python
[0.123, -0.456, ..., 0.789]  # 384 floats
```

**Step 3 Output**:
```python
[("node_5", 0.87, GraphNode(...)), ...]  # Top-K similar
```

**Step 4 Output**:
```python
"node_5"  # parent_id
```

**Step 5 Output**:
```python
GraphNode(
    id="node_10",
    cluster_id=2,
    parent_id="node_5",
    ...
)
```

**Step 6 Output**:
```json
{
  "nodes": [
    {
      "id": "node_10",
      "text": "We need to add user authentication",
      "metadata": {
        "cluster_id": 2,
        "cluster_color": "#45B7D1"
      }
    }
  ],
  "edges": [
    {
      "from_node": "node_5",
      "to_node": "node_10"
    }
  ]
}
```

---

**Document End**


