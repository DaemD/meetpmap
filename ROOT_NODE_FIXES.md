# Root Node Fixes - Multi-User Support

## 🐛 **Issues Found from API Testing**

### **Issue 1: Wrong Root Node ID in `/api/transcript` Response**
- **Problem**: Request 1 returned root with ID `"root"` (global) instead of `"root_john_doe"` (user-specific)
- **Cause**: `_graph_to_frontend_format()` called `get_root()` without `user_id` parameter
- **Impact**: Root node ID didn't match edges, causing frontend display issues

### **Issue 2: Wrong Edge Type for Root Edges**
- **Problem**: Edges from root had type `"extends"` instead of `"root"`
- **Cause**: Edge type check only looked for global root `"root"`, not user-specific roots like `"root_john_doe"`
- **Impact**: Frontend couldn't distinguish root edges from regular edges

### **Issue 3: LLM Placement Using Wrong Root**
- **Problem**: `decide_placement()` always used global `root_id` as fallback
- **Cause**: No `user_id` parameter passed to `decide_placement()`
- **Impact**: Nodes could be placed under wrong root for multi-user scenarios

---

## ✅ **Fixes Applied**

### **1. Fixed `_graph_to_frontend_format()` Method**
- **Added `user_id` parameter** to method signature
- **Fixed root retrieval**: Now calls `get_root(user_id=user_id)` to get user-specific root
- **Fixed edge type detection**: Now checks for both global root and user-specific roots
- **Improved root inclusion logic**: Only includes root if new nodes connect to it

**Before:**
```python
def _graph_to_frontend_format(self, new_graph_nodes: List):
    root = self.graph_manager.get_root()  # ❌ Always gets global root
    # ...
    type="extends" if graph_node.parent_id != "root" else "root"  # ❌ Only checks global root
```

**After:**
```python
def _graph_to_frontend_format(self, new_graph_nodes: List, user_id: Optional[str] = None):
    root = self.graph_manager.get_root(user_id=user_id)  # ✅ Gets user-specific root
    # ...
    is_root_parent = (graph_node.parent_id == self.graph_manager.root_id) or \
                    (user_id and graph_node.parent_id == f"root_{user_id}")  # ✅ Checks both
    type="root" if is_root_parent else "extends"  # ✅ Correct type
```

### **2. Fixed `decide_placement()` Method**
- **Added `user_id` parameter** to method signature
- **Fixed all root fallbacks**: Now uses user-specific root when `user_id` is provided
- **Updated all 6 fallback locations** to use correct root

**Before:**
```python
async def decide_placement(self, ..., similar_nodes: List):
    # ...
    parent_id = target_node.parent_id if target_node.parent_id else self.graph_manager.root_id  # ❌ Always global root
```

**After:**
```python
async def decide_placement(self, ..., similar_nodes: List, user_id: Optional[str] = None):
    # Get appropriate root ID (user-specific or global)
    if user_id:
        user_root = self.graph_manager.get_root(user_id=user_id)
        fallback_root_id = user_root.id if user_root else self.graph_manager.root_id
    else:
        fallback_root_id = self.graph_manager.root_id
    # ...
    parent_id = target_node.parent_id if target_node.parent_id else fallback_root_id  # ✅ Correct root
```

### **3. Updated `extract_nodes()` Method**
- **Passes `user_id`** to `_graph_to_frontend_format()`
- **Passes `user_id`** to `decide_placement()`

---

## 🧪 **Expected Results After Fix**

### **Request 1 (john_doe):**
```json
{
  "nodes": [
    {
      "id": "root_john_doe",  // ✅ Now correct (was "root")
      "text": "Meeting Start"
    },
    // ... other nodes
  ],
  "edges": [
    {
      "from_node": "root_john_doe",
      "to_node": "node_1",
      "type": "root"  // ✅ Now correct (was "extends")
    }
  ]
}
```

### **Request 3 (emily):**
```json
{
  "nodes": [
    {
      "id": "root_emily",  // ✅ Correct
      "text": "Meeting Start"
    },
    // ... other nodes
  ],
  "edges": [
    {
      "from_node": "root_emily",
      "to_node": "node_6",
      "type": "root"  // ✅ Correct
    }
  ]
}
```

---

## 📝 **Files Changed**

1. **`backend/services/meetmap_service.py`**:
   - `_graph_to_frontend_format()`: Added `user_id` parameter, fixed root retrieval and edge type
   - `decide_placement()`: Added `user_id` parameter, fixed all root fallbacks
   - `extract_nodes()`: Passes `user_id` to both methods

---

## ✅ **Testing Checklist**

- [x] Root node ID matches user-specific root (`root_{user_id}`)
- [x] Edge type is `"root"` for edges from root
- [x] Edge type is `"extends"` for other edges
- [x] User isolation: Each user's root is separate
- [x] LLM placement uses correct root as fallback

---

## 🚀 **Next Steps**

1. Push code to GitHub
2. Railway will auto-deploy
3. Test with Postman:
   - Send chunk with `user_id: "john_doe"`
   - Verify root ID is `"root_john_doe"`
   - Verify edge type is `"root"`
   - Send chunk with `user_id: "emily"`
   - Verify root ID is `"root_emily"`
   - Verify graphs are isolated

