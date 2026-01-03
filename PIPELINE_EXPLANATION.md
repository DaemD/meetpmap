# Complete Pipeline Explanation - Multi-User Flow

## 🎯 **Starting Point: User Sends Chunk with user_id**

### **Step 1: Frontend/Client Sends Request**

**Request:**
```javascript
POST https://meetpmap-production.up.railway.app/api/transcript

Body:
{
  "text": "We need to implement user authentication system",
  "start": 0.0,
  "end": 5.5,
  "speaker": "John",
  "chunk_id": "chunk_001",
  "user_id": "john_doe"  // ← User ID from your service
}
```

**What happens:**
- Your frontend/service gets `user_id` from your auth system
- Sends chunk with `user_id` in request body
- Backend receives the request

---

## 📥 **Step 2: Backend Receives Request**

### **Location:** `backend/main.py` - `POST /api/transcript`

```python
@app.post("/api/transcript")
async def process_transcript_chunk(chunk: dict):
    transcript_chunk = TranscriptChunk(**chunk)  # Validates and parses
    # transcript_chunk.user_id = "john_doe"
    
    nodes, edges = await meetmap_service.extract_nodes(transcript_chunk)
    # Returns nodes and edges for this user
```

**What happens:**
1. FastAPI receives POST request
2. Validates request body against `TranscriptChunk` schema
3. Creates `TranscriptChunk` object with `user_id` field
4. Passes to `MeetMapService.extract_nodes()`

---

## 🔄 **Step 3: MeetMapService Processes Chunk**

### **Location:** `backend/services/meetmap_service.py` - `extract_nodes()`

### **3.1: Extract Ideas (GPT)**

```python
idea_descriptions = await self._extract_ideas(chunk)
# Returns: ["Implement user authentication system", "Add login functionality"]
```

**What happens:**
- Sends chunk text to GPT-4o-mini
- GPT extracts ideas (no graph decisions)
- Returns list of idea descriptions
- **Note:** `user_id` is not used here (GPT doesn't need it)

---

### **3.2: Generate Embeddings**

```python
for idea_text in idea_descriptions:
    embedding = self.embedding_model.encode(idea_text).tolist()
    # embedding = [0.123, -0.456, 0.789, ...] (384 dimensions)
```

**What happens:**
- For each idea, generates vector embedding
- Uses `all-MiniLM-L6-v2` model (384 dimensions)
- **Note:** `user_id` not used here (embedding is semantic, not user-specific)

---

### **3.3: Global Search for Similar Nodes**

```python
similar_nodes = self.graph_manager.find_globally_similar_nodes(
    candidate_embedding=embedding,
    exclude_node_id=None,
    filter_by_threshold=False,
    user_id=chunk.user_id  # ← FILTER BY USER ID
)
```

**What happens:**
1. Calls `graph_manager.find_globally_similar_nodes(user_id="john_doe")`
2. **GraphManager filters nodes:**
   ```python
   all_nodes = self.get_all_nodes_except_root(user_id="john_doe")
   # Only gets nodes where metadata["user_id"] == "john_doe"
   ```
3. Compares embedding with **only john_doe's nodes**
4. Returns top-K most similar nodes (e.g., top 5)
5. **Result:** Only finds similar nodes within john_doe's graph

**Why this matters:**
- User A's nodes won't match User B's nodes
- Each user has isolated semantic search
- Prevents cross-user node connections

---

### **3.4: LLM Decides Placement**

```python
if similar_nodes:
    parent_id = await self.decide_placement(
        candidate_summary=idea_text,
        candidate_embedding=embedding,
        similar_nodes=similar_nodes  # Only john_doe's nodes
    )
else:
    # No nodes found - place under user-specific root
    user_root = self.graph_manager.get_root(user_id="john_doe")
    if not user_root:
        # Create user-specific root: "root_john_doe"
        self.graph_manager._initialize_root(user_id="john_doe")
    parent_id = user_root.id  # "root_john_doe"
```

**What happens:**
1. If similar nodes found: LLM decides which node to place under
2. If no nodes found: Places under user-specific root
3. **User-specific root:**
   - First time: Creates `root_john_doe`
   - Stores `user_id` in root metadata
   - Each user gets their own root node

---

### **3.5: Create Node in Graph**

```python
node_metadata = {
    "chunk_id": chunk.chunk_id,
    "timestamp": chunk.start,
    "end_time": chunk.end,
    "speaker": chunk.speaker,
    "user_id": "john_doe"  # ← STORE USER ID IN METADATA
}

graph_node = self.graph_manager.add_node(
    node_id="node_1",
    embedding=embedding,
    summary=idea_text,
    parent_id=parent_id,  # "root_john_doe" or another node
    metadata=node_metadata  # Contains user_id
)
```

**What happens:**
1. Creates new `GraphNode` object
2. **Stores `user_id` in node metadata**
3. Adds node to graph structure
4. Updates parent's children list
5. Assigns node to cluster (threshold-based clustering)

**Node structure:**
```python
GraphNode(
    id="node_1",
    embedding=[0.123, -0.456, ...],
    summary="Implement user authentication system",
    parent_id="root_john_doe",
    children_ids=[],
    depth=1,
    metadata={
        "user_id": "john_doe",  # ← KEY: User isolation
        "chunk_id": "chunk_001",
        "timestamp": 0.0,
        "cluster_id": 0
    }
)
```

---

## 🗄️ **Step 4: GraphManager Stores Node**

### **Location:** `backend/services/graph_manager.py` - `add_node()`

```python
def add_node(self, node_id, embedding, summary, parent_id, metadata):
    # metadata contains user_id
    
    node = GraphNode(
        id=node_id,
        embedding=embedding,
        summary=summary,
        parent_id=parent_id,
        metadata=metadata  # Contains user_id
    )
    
    self.nodes[node_id] = node  # Store in graph
    # All nodes stored in same dictionary, but filtered by user_id
```

**What happens:**
1. Node stored in `self.nodes` dictionary
2. **All users' nodes in same dictionary** (not separate graphs)
3. **Filtering happens on retrieval** (not storage)
4. Node metadata contains `user_id` for filtering

**Storage structure:**
```python
self.nodes = {
    "root": GraphNode(metadata={"is_root": True}),
    "root_john_doe": GraphNode(metadata={"user_id": "john_doe", "is_root": True}),
    "root_jane_doe": GraphNode(metadata={"user_id": "jane_doe", "is_root": True}),
    "node_1": GraphNode(metadata={"user_id": "john_doe"}),
    "node_2": GraphNode(metadata={"user_id": "john_doe"}),
    "node_3": GraphNode(metadata={"user_id": "jane_doe"}),
    # All nodes in same dictionary, but tagged with user_id
}
```

---

## 📤 **Step 5: Return Nodes to Frontend**

### **Location:** `backend/main.py` - `POST /api/transcript` (return)

```python
return {
    "status": "success",
    "nodes": [node.model_dump() for node in nodes],
    "edges": [edge.model_dump() for edge in edges]
}
```

**What happens:**
- Returns newly created nodes
- Nodes include `user_id` in metadata
- Frontend receives response

---

## 🔍 **Step 6: Frontend Requests Graph State**

### **Request:**
```javascript
GET https://meetpmap-production.up.railway.app/api/graph/state?user_id=john_doe
```

### **Location:** `backend/main.py` - `GET /api/graph/state`

```python
@app.get("/api/graph/state")
async def get_graph_state(user_id: Optional[str] = Query(None)):
    graph_manager = meetmap_service.graph_manager
    
    # FILTER BY USER ID
    all_graph_nodes = graph_manager.get_all_nodes(user_id=user_id)
    # Only returns nodes where metadata["user_id"] == "john_doe"
    
    root = graph_manager.get_root(user_id=user_id)
    # Returns "root_john_doe" (user-specific root)
```

**What happens:**
1. Frontend sends `user_id` as query parameter
2. Backend calls `get_all_nodes(user_id="john_doe")`
3. **GraphManager filters:**
   ```python
   def get_all_nodes(self, user_id=None):
       if user_id is None:
           return list(self.nodes.values())  # All nodes
       
       # Filter by user_id
       return [node for node in self.nodes.values() 
               if node.metadata.get("user_id") == user_id]
   ```
4. Returns only john_doe's nodes
5. Returns john_doe's root node (`root_john_doe`)

**Response:**
```json
{
  "status": "success",
  "nodes": [
    {
      "id": "root_john_doe",
      "text": "Meeting Start",
      "metadata": {"user_id": "john_doe", "is_root": true}
    },
    {
      "id": "node_1",
      "text": "Implement user authentication system",
      "metadata": {"user_id": "john_doe", "cluster_id": 0}
    }
  ],
  "edges": [
    {"from_node": "root_john_doe", "to_node": "node_1"}
  ]
}
```

---

## 🔄 **Complete Flow Diagram**

```
1. User sends chunk with user_id="john_doe"
   ↓
2. Backend receives: POST /api/transcript
   ↓
3. MeetMapService.extract_nodes(chunk)
   ├─ Extract ideas (GPT) - no user_id needed
   ├─ Generate embeddings - no user_id needed
   ├─ Search similar nodes - FILTERED by user_id="john_doe"
   ├─ LLM placement - only considers john_doe's nodes
   └─ Create node - STORES user_id in metadata
   ↓
4. GraphManager.add_node()
   └─ Stores node with metadata["user_id"] = "john_doe"
   ↓
5. Return nodes to frontend
   ↓
6. Frontend requests: GET /api/graph/state?user_id=john_doe
   ↓
7. Backend filters: get_all_nodes(user_id="john_doe")
   └─ Returns only john_doe's nodes
   ↓
8. Frontend displays john_doe's graph
```

---

## 🔑 **Key Points: User Isolation**

### **1. Storage:**
- **All nodes stored together** in `self.nodes` dictionary
- **Tagged with `user_id`** in metadata
- Not separate graphs per user

### **2. Filtering:**
- **Happens on retrieval**, not storage
- `get_all_nodes(user_id)` filters by metadata
- `find_globally_similar_nodes(user_id)` only searches user's nodes

### **3. Root Nodes:**
- **Global root:** `root` (for nodes without user_id)
- **User root:** `root_{user_id}` (e.g., `root_john_doe`)
- Created automatically on first node

### **4. Clustering:**
- Clusters are **per-user** (filtered by user_id)
- User A's clusters don't affect User B's clusters
- Each user has isolated color coding

---

## 📊 **Example: Two Users**

### **User 1 (john_doe) sends chunk:**
```
Chunk: "We need to implement authentication"
user_id: "john_doe"
```

**Backend creates:**
- Root: `root_john_doe`
- Node: `node_1` (metadata: `{"user_id": "john_doe"}`)

### **User 2 (jane_doe) sends chunk:**
```
Chunk: "Let's discuss the budget"
user_id: "jane_doe"
```

**Backend creates:**
- Root: `root_jane_doe`
- Node: `node_2` (metadata: `{"user_id": "jane_doe"}`)

### **Storage:**
```python
self.nodes = {
    "root_john_doe": {...},
    "node_1": {metadata: {"user_id": "john_doe"}},
    "root_jane_doe": {...},
    "node_2": {metadata: {"user_id": "jane_doe"}}
}
```

### **User 1 requests graph:**
```
GET /api/graph/state?user_id=john_doe
```
**Returns:** Only `root_john_doe` and `node_1`

### **User 2 requests graph:**
```
GET /api/graph/state?user_id=jane_doe
```
**Returns:** Only `root_jane_doe` and `node_2`

---

## ✅ **Summary**

**Pipeline Flow:**
1. User sends chunk with `user_id` → Backend receives
2. Extract ideas (GPT) → Generate embeddings
3. **Search similar nodes (filtered by `user_id`)**
4. **LLM placement (only user's nodes)**
5. **Create node (store `user_id` in metadata)**
6. **Store in graph (tagged with `user_id`)**
7. Frontend requests graph → **Filter by `user_id`**
8. Return only user's nodes

**User Isolation:**
- ✅ Nodes tagged with `user_id` in metadata
- ✅ Filtering happens on retrieval
- ✅ Each user has own root node
- ✅ Semantic search is per-user
- ✅ Clustering is per-user

**Your multi-user pipeline is working!** 🎉

