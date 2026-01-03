# Changes Explanation - Multi-User Support

## 📋 **Summary of Changes**

I implemented **user isolation** so each user has their own separate graph. Here's what changed:

---

## 🔧 **Backend Changes**

### **1. Schema Changes** (`backend/models/schemas.py`)

**Added `user_id` field to `TranscriptChunk`:**

```python
class TranscriptChunk(BaseModel):
    speaker: Optional[str] = None
    start: float
    end: float
    text: str
    chunk_id: Optional[str] = None
    user_id: Optional[str] = None  # ← NEW: User identifier for multi-user support
```

**What this does:**
- Allows transcript chunks to include a `user_id`
- Optional field (backward compatible)
- If provided, nodes are isolated to that user

---

### **2. GraphManager Changes** (`backend/services/graph_manager.py`)

#### **A. Updated `get_all_nodes()` method:**

**Before:**
```python
def get_all_nodes(self) -> List[GraphNode]:
    """Get all nodes in the graph"""
    return list(self.nodes.values())
```

**After:**
```python
def get_all_nodes(self, user_id: Optional[str] = None) -> List[GraphNode]:
    """Get all nodes in the graph, optionally filtered by user_id"""
    if user_id is None:
        return list(self.nodes.values())
    # Filter nodes by user_id in metadata
    return [node for node in self.nodes.values() 
            if node.metadata.get("user_id") == user_id or 
            (node.id == self.root_id and node.metadata.get("user_id") == user_id) or
            (node.id == self.root_id and user_id is None)]
```

**What this does:**
- If `user_id` is provided, returns only nodes for that user
- If `user_id` is None, returns all nodes (backward compatible)

---

#### **B. Updated `get_all_nodes_except_root()` method:**

**Before:**
```python
def get_all_nodes_except_root(self) -> List[GraphNode]:
    """Get all nodes except root (for global search)"""
    return [node for node in self.nodes.values() if node.id != self.root_id]
```

**After:**
```python
def get_all_nodes_except_root(self, user_id: Optional[str] = None) -> List[GraphNode]:
    """Get all nodes except root (for global search), optionally filtered by user_id"""
    if user_id is None:
        return [node for node in self.nodes.values() if node.id != self.root_id]
    # Filter nodes by user_id, excluding root
    return [node for node in self.nodes.values() 
            if node.id != self.root_id and node.metadata.get("user_id") == user_id]
```

**What this does:**
- Filters nodes by `user_id` when searching for similar nodes
- Ensures users only see similar nodes from their own graph

---

#### **C. Updated `get_root()` method:**

**Before:**
```python
def get_root(self) -> GraphNode:
    """Get root node"""
    return self.nodes[self.root_id]
```

**After:**
```python
def get_root(self, user_id: Optional[str] = None) -> Optional[GraphNode]:
    """Get root node, optionally for a specific user"""
    if user_id is None:
        return self.nodes.get(self.root_id)
    # For user-specific root, check if root has user_id or create user-specific root
    root = self.nodes.get(self.root_id)
    if root and root.metadata.get("user_id") == user_id:
        return root
    # If no user-specific root exists, return None (will be created on first node)
    return None
```

**What this does:**
- Returns user-specific root if `user_id` provided
- Returns global root if `user_id` is None

---

#### **D. Updated `_initialize_root()` method:**

**Before:**
```python
def _initialize_root(self):
    """Create root node at graph initialization"""
    root_id = "root"
    # ... creates root with id "root"
```

**After:**
```python
def _initialize_root(self, user_id: Optional[str] = None):
    """Create root node at graph initialization, optionally for a specific user"""
    if user_id:
        root_id = f"root_{user_id}"  # ← User-specific root ID
    else:
        root_id = "root"  # ← Global root ID
    
    root_metadata = {"is_root": True}
    if user_id:
        root_metadata["user_id"] = user_id  # ← Store user_id in root metadata
    # ... creates root with user_id in metadata
```

**What this does:**
- Creates user-specific root: `root_{user_id}` (e.g., `root_user_123`)
- Creates global root: `root` (if no user_id)
- Stores `user_id` in root metadata

---

#### **E. Updated `find_globally_similar_nodes()` method:**

**Before:**
```python
def find_globally_similar_nodes(
    self,
    candidate_embedding: List[float],
    exclude_node_id: Optional[str] = None,
    filter_by_threshold: bool = False
) -> List[tuple[str, float, GraphNode]]:
    all_nodes = self.get_all_nodes_except_root()
```

**After:**
```python
def find_globally_similar_nodes(
    self,
    candidate_embedding: List[float],
    exclude_node_id: Optional[str] = None,
    filter_by_threshold: bool = False,
    user_id: Optional[str] = None  # ← NEW parameter
) -> List[tuple[str, float, GraphNode]]:
    all_nodes = self.get_all_nodes_except_root(user_id=user_id)  # ← Filter by user_id
```

**What this does:**
- When searching for similar nodes, only searches within the user's graph
- Prevents cross-user node matching

---

### **3. MeetMapService Changes** (`backend/services/meetmap_service.py`)

#### **A. Store `user_id` in node metadata:**

**Before:**
```python
graph_node = self.graph_manager.add_node(
    node_id=node_id,
    embedding=embedding,
    summary=idea_text,
    parent_id=parent_id,
    metadata={
        "chunk_id": chunk.chunk_id,
        "timestamp": chunk.start,
        "end_time": chunk.end,
        "speaker": chunk.speaker
    }
)
```

**After:**
```python
# Include user_id in metadata if provided
node_metadata = {
    "chunk_id": chunk.chunk_id,
    "timestamp": chunk.start,
    "end_time": chunk.end,
    "speaker": chunk.speaker
}
if chunk.user_id:
    node_metadata["user_id"] = chunk.user_id  # ← Store user_id

graph_node = self.graph_manager.add_node(
    node_id=node_id,
    embedding=embedding,
    summary=idea_text,
    parent_id=parent_id,
    metadata=node_metadata
)
```

**What this does:**
- Stores `user_id` in node metadata when creating nodes
- Allows filtering nodes by `user_id` later

---

#### **B. Filter similar node search by `user_id`:**

**Before:**
```python
similar_nodes = self.graph_manager.find_globally_similar_nodes(
    candidate_embedding=embedding,
    exclude_node_id=None,
    filter_by_threshold=False
)
```

**After:**
```python
similar_nodes = self.graph_manager.find_globally_similar_nodes(
    candidate_embedding=embedding,
    exclude_node_id=None,
    filter_by_threshold=False,
    user_id=chunk.user_id  # ← Filter by user_id
)
```

**What this does:**
- Only searches for similar nodes within the user's graph
- Prevents matching nodes from other users

---

#### **C. Create user-specific root if needed:**

**Before:**
```python
else:
    # No nodes in graph (only root exists) - place under root
    parent_id = self.graph_manager.root_id
    print(f"No existing nodes found, placing under root")
```

**After:**
```python
else:
    # No nodes in graph - place under user-specific root
    if chunk.user_id:
        # Get or create user-specific root
        user_root = self.graph_manager.get_root(user_id=chunk.user_id)
        if not user_root:
            # Create user-specific root
            self.graph_manager._initialize_root(user_id=chunk.user_id)
            user_root = self.graph_manager.get_root(user_id=chunk.user_id)
        parent_id = user_root.id if user_root else self.graph_manager.root_id
    else:
        parent_id = self.graph_manager.root_id
    print(f"No existing nodes found, placing under root: {parent_id}")
```

**What this does:**
- Creates user-specific root (`root_{user_id}`) if it doesn't exist
- Places first node under user-specific root
- Falls back to global root if no `user_id`

---

### **4. API Endpoint Changes** (`backend/main.py`)

#### **A. Added imports:**

**Added:**
```python
from fastapi import FastAPI, Query  # ← Added Query
from typing import Optional  # ← Added Optional
```

**What this does:**
- Enables query parameter handling
- Type hints for optional parameters

---

#### **B. Updated `POST /api/transcript` endpoint:**

**Before:**
```python
@app.post("/api/transcript")
async def process_transcript_chunk(chunk: dict):
    transcript_chunk = TranscriptChunk(**chunk)
    # ... process chunk
```

**After:**
```python
@app.post("/api/transcript")
async def process_transcript_chunk(chunk: dict):
    transcript_chunk = TranscriptChunk(**chunk)
    # Note: user_id is optional - if not provided, nodes are shared
    # If user_id is provided, nodes are isolated per user
    # ... process chunk (user_id is automatically handled in service)
```

**What this does:**
- Accepts `user_id` in request body (optional)
- If provided, nodes are isolated to that user
- If not provided, nodes are shared (backward compatible)

---

#### **C. Updated `GET /api/graph/state` endpoint:**

**Before:**
```python
@app.get("/api/graph/state")
async def get_graph_state():
    graph_manager = meetmap_service.graph_manager
    all_graph_nodes = graph_manager.get_all_nodes()
    # ... return all nodes
```

**After:**
```python
@app.get("/api/graph/state")
async def get_graph_state(user_id: Optional[str] = Query(None, description="Filter nodes by user ID")):
    graph_manager = meetmap_service.graph_manager
    all_graph_nodes = graph_manager.get_all_nodes(user_id=user_id)  # ← Filter by user_id
    # ... return filtered nodes
```

**What this does:**
- Accepts `user_id` as query parameter: `/api/graph/state?user_id=user_123`
- Returns only nodes for that user
- If `user_id` not provided, returns all nodes (backward compatible)

---

#### **D. Updated root node handling in `get_graph_state`:**

**Before:**
```python
root = graph_manager.get_root()
root_node_data = NodeData(...)
nodes.append(root_node_data)
```

**After:**
```python
root = graph_manager.get_root(user_id=user_id)  # ← Get user-specific root
if root:  # ← Check if root exists
    root_node_data = NodeData(...)
    nodes.append(root_node_data)
```

**What this does:**
- Gets user-specific root if `user_id` provided
- Gets global root if `user_id` not provided
- Only includes root if it exists

---

## 📊 **Summary of All Changes**

| File | Change | Purpose |
|------|--------|---------|
| `models/schemas.py` | Added `user_id` to `TranscriptChunk` | Allow user identification |
| `services/graph_manager.py` | Updated `get_all_nodes()` to filter by `user_id` | Filter nodes by user |
| `services/graph_manager.py` | Updated `get_all_nodes_except_root()` to filter by `user_id` | Filter search by user |
| `services/graph_manager.py` | Updated `get_root()` to accept `user_id` | Get user-specific root |
| `services/graph_manager.py` | Updated `_initialize_root()` to create user-specific roots | Create `root_{user_id}` |
| `services/graph_manager.py` | Updated `find_globally_similar_nodes()` to filter by `user_id` | Search only user's nodes |
| `services/meetmap_service.py` | Store `user_id` in node metadata | Tag nodes with user |
| `services/meetmap_service.py` | Filter similar node search by `user_id` | Isolate node matching |
| `services/meetmap_service.py` | Create user-specific root on first node | Initialize user graph |
| `main.py` | Added `Query` and `Optional` imports | Enable query params |
| `main.py` | Updated `POST /api/transcript` to accept `user_id` | Accept user in request |
| `main.py` | Updated `GET /api/graph/state` to filter by `user_id` | Filter response by user |

---

## ✅ **What This Achieves**

### **Before (Single User):**
- All users share the same graph
- All nodes visible to everyone
- No isolation

### **After (Multi-User):**
- Each user has isolated graph
- Nodes filtered by `user_id`
- Each user gets their own root node
- Backward compatible (works without `user_id`)

---

## 🎯 **How It Works**

1. **User sends transcript with `user_id`:**
   ```json
   {
     "text": "...",
     "user_id": "user_123"
   }
   ```

2. **Backend stores `user_id` in node metadata:**
   ```python
   metadata = {
     "user_id": "user_123",
     "chunk_id": "...",
     ...
   }
   ```

3. **Backend creates user-specific root:**
   - Root ID: `root_user_123`
   - Stores `user_id` in root metadata

4. **Backend filters queries by `user_id`:**
   - `get_all_nodes(user_id="user_123")` → only user_123's nodes
   - `find_globally_similar_nodes(user_id="user_123")` → only searches user_123's nodes

5. **Frontend requests graph with `user_id`:**
   ```
   GET /api/graph/state?user_id=user_123
   ```
   → Returns only user_123's nodes

---

## 🔄 **Backward Compatibility**

**All changes are backward compatible:**

- ✅ If `user_id` is **not provided**: Works exactly as before (all nodes shared)
- ✅ If `user_id` is **provided**: Nodes are isolated per user
- ✅ Existing code works without changes
- ✅ No breaking changes

---

## 📝 **Files Changed**

1. ✅ `backend/models/schemas.py` - Added `user_id` field
2. ✅ `backend/services/graph_manager.py` - Added user filtering
3. ✅ `backend/services/meetmap_service.py` - Store and filter by `user_id`
4. ✅ `backend/main.py` - Updated API endpoints

**Total: 4 backend files modified**

---

**That's all the backend changes!** Everything is backward compatible and ready to use. 🎉

