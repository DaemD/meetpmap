# Graph-Based Features Planning

## Overview
Since we're using a graph structure, we can leverage graph algorithms to provide powerful insights about idea evolution, relationships, and conversation flow.

---

## Feature Categories

### 1. **Idea Maturity & Evolution**

#### 1.1 Maturity Score
**What it shows:** How developed/mature an idea is

**Graph Techniques:**
- **Depth analysis**: Deeper nodes = more refined
- **Descendant count**: More children = more explored
- **Branching factor**: More branches = more mature discussion
- **Time-based metrics**: Older nodes with activity = mature

**Algorithm:**
```python
def calculate_maturity(node):
    depth_weight = node.depth * 0.2
    children_weight = len(node.children_ids) * 0.3
    descendants_weight = count_all_descendants(node) * 0.3
    time_weight = (current_time - node.last_updated) * 0.2
    return depth_weight + children_weight + descendants_weight + time_weight
```

**Usefulness:** ⭐⭐⭐⭐⭐
- Users can see which ideas are fully developed vs. just mentioned
- Helps identify "dead ends" (ideas with no children)
- Shows which topics got the most discussion

---

#### 1.2 Idea Lifecycle Stage
**What it shows:** Is this idea new, developing, mature, or resolved?

**Graph Techniques:**
- **BFS from root**: Distance from root = how early in conversation
- **DFS to count descendants**: Total reach of idea
- **In-degree/Out-degree**: How connected the idea is

**Algorithm:**
```python
def get_lifecycle_stage(node):
    if len(node.children_ids) == 0:
        return "new"  # No exploration yet
    elif count_descendants(node) < 3:
        return "developing"  # Some discussion
    elif count_descendants(node) >= 3 and node.depth > 2:
        return "mature"  # Well explored
    else:
        return "resolved"  # Deep with many branches
```

**Usefulness:** ⭐⭐⭐⭐
- Quick visual indicator of idea status
- Helps prioritize what to focus on

---

### 2. **Influence & Impact Analysis**

#### 2.1 Idea Influence Score
**What it shows:** Which ideas influenced the most other ideas

**Graph Techniques:**
- **Out-degree centrality**: Number of direct children
- **Descendant count**: Total nodes influenced (direct + indirect)
- **PageRank-like algorithm**: Ideas that influence important ideas are more influential

**Algorithm:**
```python
def calculate_influence(node):
    # Direct influence (children)
    direct = len(node.children_ids)
    
    # Indirect influence (all descendants)
    indirect = count_all_descendants(node)
    
    # Weighted by depth (deeper influence = more important)
    depth_bonus = node.depth * 0.1
    
    return direct * 2 + indirect + depth_bonus
```

**Usefulness:** ⭐⭐⭐⭐⭐
- Shows which ideas were most impactful
- Identifies key decision points
- Helps understand conversation flow

---

#### 2.2 Impact Propagation
**What it shows:** How an idea's influence spreads through the graph

**Graph Techniques:**
- **BFS from node**: Find all reachable nodes
- **Path analysis**: Show paths from idea to all affected nodes
- **Dependency graph**: Which ideas depend on this one

**Algorithm:**
```python
def get_impact_propagation(node):
    # BFS to find all descendants
    affected_nodes = []
    queue = [node.id]
    visited = set()
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        current_node = get_node(current)
        affected_nodes.append(current_node)
        
        # Add children to queue
        for child_id in current_node.children_ids:
            queue.append(child_id)
    
    return affected_nodes
```

**Usefulness:** ⭐⭐⭐⭐
- Visualize how one idea led to many others
- See the "ripple effect" of decisions
- Understand idea dependencies

---

### 3. **Path & Journey Analysis**

#### 3.1 "How Did We Get Here?"
**What it shows:** Path from root to any node (idea genealogy)

**Graph Techniques:**
- **DFS/BFS path finding**: Find path from root to target
- **Backtracking**: Trace parent chain
- **Path visualization**: Show the journey

**Algorithm:**
```python
def get_path_to_node(target_node_id):
    path = []
    current = get_node(target_node_id)
    
    # Backtrack to root
    while current and current.parent_id:
        path.insert(0, current)
        current = get_node(current.parent_id)
    
    path.insert(0, get_root())
    return path
```

**Usefulness:** ⭐⭐⭐⭐⭐
- Understand how a decision was reached
- See the conversation flow that led to an idea
- Trace idea evolution

---

#### 3.2 Common Ancestors
**What it shows:** What ideas led to multiple different outcomes

**Graph Techniques:**
- **Lowest Common Ancestor (LCA)**: Find shared parent of multiple nodes
- **Intersection of paths**: Find where paths converge

**Algorithm:**
```python
def find_common_ancestors(node_ids):
    # Get paths for all nodes
    paths = [get_path_to_node(nid) for nid in node_ids]
    
    # Find common nodes in all paths
    common = set(paths[0])
    for path in paths[1:]:
        common = common.intersection(set(path))
    
    # Return deepest common ancestor
    return max(common, key=lambda n: n.depth)
```

**Usefulness:** ⭐⭐⭐
- Find shared origins of different ideas
- Understand branching points

---

#### 3.3 Decision Paths
**What it shows:** All possible paths from an idea to its outcomes

**Graph Techniques:**
- **DFS to find all paths**: Enumerate all paths from source to targets
- **Path enumeration**: Show all ways an idea evolved

**Algorithm:**
```python
def find_all_paths(source_id, target_id):
    paths = []
    
    def dfs(current, target, path):
        if current == target:
            paths.append(path[:])
            return
        
        current_node = get_node(current)
        for child_id in current_node.children_ids:
            path.append(child_id)
            dfs(child_id, target, path)
            path.pop()
    
    dfs(source_id, target_id, [source_id])
    return paths
```

**Usefulness:** ⭐⭐⭐
- See all ways an idea could evolve
- Understand alternative paths not taken

---

### 4. **Graph Structure Analysis**

#### 4.1 Branching Factor
**What it shows:** Which ideas split into many directions

**Graph Techniques:**
- **Out-degree**: Count of direct children
- **Branching ratio**: Children / depth ratio

**Algorithm:**
```python
def get_branching_factor(node):
    return len(node.children_ids) / max(node.depth, 1)
```

**Usefulness:** ⭐⭐⭐⭐
- Identify topics with many sub-topics
- Find "hub" ideas that connect many concepts

---

#### 4.2 Convergence Points
**What it shows:** Where multiple ideas merge or converge

**Graph Techniques:**
- **In-degree analysis**: Nodes with many parents (not possible in tree, but can find nodes that are referenced)
- **Common descendants**: Ideas that lead to same outcomes
- **Clustering**: Find nodes that are semantically similar and close

**Algorithm:**
```python
def find_convergence_points():
    # Find nodes that are referenced by many paths
    convergence = {}
    
    for node in all_nodes:
        # Count how many different paths lead to this node's descendants
        paths_to_descendants = count_unique_paths_to_descendants(node)
        if paths_to_descendants > 2:
            convergence[node.id] = paths_to_descendants
    
    return sorted(convergence.items(), key=lambda x: x[1], reverse=True)
```

**Usefulness:** ⭐⭐⭐
- Find where ideas come together
- Identify synthesis points

---

#### 4.3 Graph Density
**What it shows:** How connected the conversation is

**Graph Techniques:**
- **Edge-to-node ratio**: More edges = more connected
- **Average degree**: Average connections per node
- **Clustering coefficient**: How tightly connected neighbors are

**Algorithm:**
```python
def calculate_graph_density():
    nodes = len(all_nodes)
    edges = sum(len(n.children_ids) for n in all_nodes)
    
    # For directed graph
    max_edges = nodes * (nodes - 1)
    density = edges / max_edges if max_edges > 0 else 0
    
    return density
```

**Usefulness:** ⭐⭐
- Overall conversation structure metric
- Less useful for individual users

---

### 5. **Centrality & Importance**

#### 5.1 Central Nodes
**What it shows:** Most important/central ideas in the conversation

**Graph Techniques:**
- **Betweenness centrality**: Nodes on many shortest paths
- **Closeness centrality**: Average distance to all other nodes
- **Eigenvector centrality**: Connected to other important nodes

**Algorithm:**
```python
def calculate_betweenness_centrality(node):
    centrality = 0
    
    # For each pair of nodes, count paths through this node
    for source in all_nodes:
        for target in all_nodes:
            if source == target or source == node or target == node:
                continue
            
            paths = find_all_paths(source.id, target.id)
            paths_through_node = [p for p in paths if node.id in p]
            
            if paths:
                centrality += len(paths_through_node) / len(paths)
    
    return centrality
```

**Usefulness:** ⭐⭐⭐⭐
- Identify key ideas that connect everything
- Find "bridge" concepts

---

#### 5.2 Hub Nodes
**What it shows:** Ideas that connect to many other ideas

**Graph Techniques:**
- **Degree centrality**: High out-degree = hub
- **Weighted degree**: Consider importance of connections

**Algorithm:**
```python
def find_hub_nodes():
    hubs = []
    for node in all_nodes:
        # Direct connections
        degree = len(node.children_ids)
        
        # Weighted by depth (deeper = more important)
        weighted_degree = degree * (1 + node.depth * 0.1)
        
        if weighted_degree > threshold:
            hubs.append((node, weighted_degree))
    
    return sorted(hubs, key=lambda x: x[1], reverse=True)
```

**Usefulness:** ⭐⭐⭐⭐
- Find main topics
- Identify conversation themes

---

### 6. **Time-Based Analysis**

#### 6.1 Idea Timeline
**What it shows:** Chronological view of idea creation

**Graph Techniques:**
- **Topological sort by timestamp**: Order nodes by creation time
- **Time-weighted graph**: Consider when ideas were created

**Algorithm:**
```python
def get_timeline():
    nodes_by_time = sorted(
        all_nodes,
        key=lambda n: n.metadata.get('timestamp', 0)
    )
    return nodes_by_time
```

**Usefulness:** ⭐⭐⭐⭐
- See conversation progression over time
- Understand temporal flow

---

#### 6.2 Idea Velocity
**What it shows:** How quickly ideas are being generated/explored

**Graph Techniques:**
- **Time intervals**: Time between node creations
- **Rate of change**: Nodes created per time unit

**Algorithm:**
```python
def calculate_idea_velocity():
    timestamps = [n.metadata.get('timestamp', 0) for n in all_nodes]
    timestamps.sort()
    
    if len(timestamps) < 2:
        return 0
    
    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    avg_interval = sum(intervals) / len(intervals)
    
    # Velocity = nodes per minute (inverse of interval)
    velocity = 60 / avg_interval if avg_interval > 0 else 0
    return velocity
```

**Usefulness:** ⭐⭐⭐
- See conversation pace
- Identify fast vs. slow discussion periods

---

### 7. **Clustering & Grouping**

#### 7.1 Semantic Clusters (Already Planned)
**What it shows:** Groups of related ideas (using K-means on embeddings)

**Graph Techniques:**
- **K-means clustering**: Group by embedding similarity
- **Graph clustering**: Find connected components with high internal similarity

**Usefulness:** ⭐⭐⭐⭐⭐
- Visual grouping of related ideas
- Color-coding for easy identification

---

#### 7.2 Topic Islands
**What it shows:** Isolated sub-graphs (separate topics)

**Graph Techniques:**
- **Connected components**: Find disconnected sub-graphs
- **DFS to find components**: Identify separate discussion threads

**Algorithm:**
```python
def find_topic_islands():
    visited = set()
    islands = []
    
    for node in all_nodes:
        if node.id in visited:
            continue
        
        # DFS to find all connected nodes
        component = []
        stack = [node.id]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            
            current_node = get_node(current)
            # Add parent and children
            if current_node.parent_id:
                stack.append(current_node.parent_id)
            stack.extend(current_node.children_ids)
        
        if len(component) > 1:
            islands.append(component)
    
    return islands
```

**Usefulness:** ⭐⭐⭐
- Identify separate discussion topics
- Find disconnected ideas

---

### 8. **Search & Discovery**

#### 8.1 Find Related Ideas
**What it shows:** Ideas similar to a given idea

**Graph Techniques:**
- **Semantic search**: Use embeddings (already have this)
- **Graph neighbors**: Find nearby nodes in graph structure
- **Combined similarity**: Semantic + structural similarity

**Algorithm:**
```python
def find_related_ideas(node_id, semantic_weight=0.7, structural_weight=0.3):
    node = get_node(node_id)
    
    # Semantic similarity (already have)
    semantic_similar = find_globally_similar_nodes(node.embedding)
    
    # Structural similarity (graph distance)
    structural_similar = []
    for other_node in all_nodes:
        if other_node.id == node_id:
            continue
        
        # Graph distance (shortest path)
        distance = shortest_path_length(node_id, other_node.id)
        structural_similar.append((other_node, distance))
    
    # Combine scores
    combined = []
    for sem_node, sem_score in semantic_similar:
        struct_score = 1 / (1 + shortest_path_length(node_id, sem_node.id))
        combined_score = semantic_weight * sem_score + structural_weight * struct_score
        combined.append((sem_node, combined_score))
    
    return sorted(combined, key=lambda x: x[1], reverse=True)
```

**Usefulness:** ⭐⭐⭐⭐⭐
- Discover related ideas
- Find connections user might miss

---

#### 8.2 Shortest Path Between Ideas
**What it shows:** How two ideas are connected

**Graph Techniques:**
- **BFS shortest path**: Find minimum path between nodes
- **Dijkstra's algorithm**: If edges have weights

**Algorithm:**
```python
def shortest_path(source_id, target_id):
    # BFS to find shortest path
    queue = [(source_id, [source_id])]
    visited = set()
    
    while queue:
        current, path = queue.pop(0)
        
        if current == target_id:
            return path
        
        if current in visited:
            continue
        visited.add(current)
        
        current_node = get_node(current)
        # Check children
        for child_id in current_node.children_ids:
            queue.append((child_id, path + [child_id]))
        
        # Check parent
        if current_node.parent_id:
            queue.append((current_node.parent_id, path + [current_node.parent_id]))
    
    return None  # No path found
```

**Usefulness:** ⭐⭐⭐⭐
- See how ideas connect
- Understand relationships

---

### 9. **Visualization Enhancements**

#### 9.1 Node Size by Importance
**What it shows:** Larger nodes = more important

**Graph Techniques:**
- Use centrality scores or influence scores
- Scale node size proportionally

**Usefulness:** ⭐⭐⭐⭐
- Quick visual identification of key ideas

---

#### 9.2 Edge Thickness by Relationship Strength
**What it shows:** Thicker edges = stronger relationship

**Graph Techniques:**
- Use similarity scores
- Consider number of shared descendants

**Usefulness:** ⭐⭐⭐
- Visual indication of connection strength

---

#### 9.3 Layout by Depth
**What it shows:** Hierarchical layout showing idea depth

**Graph Techniques:**
- Use node depth for Y-coordinate
- Use breadth for X-coordinate

**Usefulness:** ⭐⭐⭐⭐
- Clear hierarchy visualization
- Easy to see idea evolution

---

## Implementation Priority

### High Priority (Most Useful):
1. ✅ **Idea Maturity Score** - Very useful for users
2. ✅ **"How Did We Get Here?" Path** - Core feature
3. ✅ **Idea Influence Score** - Shows impact
4. ✅ **Shortest Path Between Ideas** - Discovery feature
5. ✅ **Find Related Ideas** - Discovery feature

### Medium Priority:
6. **Idea Lifecycle Stage** - Quick status indicator
7. **Impact Propagation** - Visualize influence spread
8. **Hub Nodes** - Find main topics
9. **Branching Factor** - Identify split points
10. **Idea Timeline** - Temporal view

### Low Priority (Nice to Have):
11. **Common Ancestors** - Less commonly needed
12. **Decision Paths** - Alternative paths
13. **Convergence Points** - Synthesis analysis
14. **Graph Density** - Overall metric
15. **Idea Velocity** - Pace analysis

---

## Data Structures Needed

### Additional Node Metadata:
```python
class GraphNode:
    # Existing fields...
    
    # New computed fields:
    maturity_score: float = 0.0
    influence_score: float = 0.0
    lifecycle_stage: str = "new"  # new, developing, mature, resolved
    centrality_score: float = 0.0
    branching_factor: float = 0.0
    descendant_count: int = 0
```

### Graph Analysis Service:
```python
class GraphAnalysisService:
    def calculate_maturity_scores(self) -> Dict[str, float]
    def calculate_influence_scores(self) -> Dict[str, float]
    def get_path_to_node(self, node_id: str) -> List[GraphNode]
    def shortest_path(self, source_id: str, target_id: str) -> List[str]
    def find_hub_nodes(self, top_k: int = 10) -> List[GraphNode]
    def find_related_ideas(self, node_id: str, top_k: int = 5) -> List[tuple]
    def get_timeline(self) -> List[GraphNode]
```

---

## API Endpoints to Add

```python
# GET /api/graph/analysis/maturity
# Returns: {node_id: maturity_score}

# GET /api/graph/analysis/influence
# Returns: {node_id: influence_score}

# GET /api/graph/path/{node_id}
# Returns: [node_ids] path from root to node

# GET /api/graph/path/{source_id}/{target_id}
# Returns: [node_ids] shortest path between nodes

# GET /api/graph/related/{node_id}?top_k=5
# Returns: [related nodes with scores]

# GET /api/graph/hubs?top_k=10
# Returns: [hub nodes]

# GET /api/graph/timeline
# Returns: [nodes] sorted by timestamp
```

---

## Frontend Features

### Node Tooltips:
- Show maturity score
- Show influence score
- Show lifecycle stage
- Show descendant count

### Context Menu:
- "Show path from root"
- "Find related ideas"
- "Show impact propagation"
- "Find shortest path to..."

### Sidebar Panels:
- **Analytics Panel**: Show top influential ideas, most mature ideas, hub nodes
- **Path Viewer**: Visualize path from root to selected node
- **Timeline View**: Chronological view of ideas

---

## Next Steps

1. **Start with High Priority features:**
   - Implement maturity score calculation
   - Implement path finding (root to node)
   - Implement influence score
   - Add API endpoints

2. **Add to frontend:**
   - Show scores in node tooltips
   - Add path visualization
   - Add related ideas panel

3. **Iterate based on user feedback**

