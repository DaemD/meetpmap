"""
Graph Manager - Manages the semantic idea-evolution graph
Uses adjacency list-based directed graph structure
"""

from typing import Dict, Optional, List, Any
import time
import numpy as np
from models.schemas import GraphNode


class GraphManager:
    """Manages the semantic idea-evolution graph"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}  # node_id -> GraphNode
        self.root_id: Optional[str] = None
        
        # Single threshold for all similarity checks
        self.SIMILARITY_THRESHOLD = 0.75
        
        # TOP_K for global search (will be dynamic based on graph size)
        self.TOP_K_DEFAULT = 5
        
        # Color palette for clusters (20 distinct colors)
        self.CLUSTER_COLORS = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
            "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52BE80",
            "#EC7063", "#5DADE2", "#F1948A", "#82E0AA", "#F4D03F",
            "#AED6F1", "#F9E79F", "#A9DFBF", "#F5B7B1", "#D7BDE2"
        ]
        
        # Threshold-based incremental clustering
        # Cluster similarity threshold (lower than placement threshold for broader grouping)
        self.CLUSTER_SIMILARITY_THRESHOLD = 0.65  # Nodes with similarity >= this join same cluster
        
        # Store cluster centroids: cluster_id -> centroid_embedding
        self.cluster_centroids: Dict[int, List[float]] = {}
        
        # Store cluster members: cluster_id -> [node_ids]
        self.cluster_members: Dict[int, List[str]] = {}
        
        # Track next available cluster ID
        self.next_cluster_id = 0
        
        self._initialize_root()
    
    def _initialize_root(self, user_id: Optional[str] = None):
        """Create root node at graph initialization, optionally for a specific user"""
        if user_id:
            root_id = f"root_{user_id}"
        else:
            root_id = "root"
        
        # Create a generic placeholder embedding (zero vector or small random)
        # In practice, this could be a generic "meeting start" embedding
        placeholder_embedding = [0.0] * 384  # Default size for all-MiniLM-L6-v2
        
        root_metadata = {"is_root": True}
        if user_id:
            root_metadata["user_id"] = user_id
        
        root_node = GraphNode(
            id=root_id,
            embedding=placeholder_embedding,
            summary="Meeting Start",
            parent_id=None,
            children_ids=[],
            depth=0,
            last_updated=time.time(),
            metadata=root_metadata
        )
        
        self.nodes[root_id] = root_node
        if not user_id:
            self.root_id = root_id
        print(f"🌳 Graph initialized with root node: {root_id}" + (f" (user: {user_id})" if user_id else ""))
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
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
    
    def get_children(self, node_id: str) -> List[GraphNode]:
        """Get all children of a node"""
        node = self.get_node(node_id)
        if not node:
            return []
        return [self.nodes[child_id] for child_id in node.children_ids if child_id in self.nodes]
    
    def add_node(
        self,
        node_id: str,
        embedding: List[float],
        summary: str,
        parent_id: str,
        metadata: dict = None
    ) -> GraphNode:
        """
        Add a new node to the graph
        
        Args:
            node_id: Unique identifier
            embedding: Vector representation
            summary: Text description
            parent_id: Parent node ID
            metadata: Additional data
        """
        parent = self.get_node(parent_id)
        if not parent:
            raise ValueError(f"Parent node {parent_id} does not exist")
        
        # Calculate depth
        depth = parent.depth + 1
        
        # Create node
        node = GraphNode(
            id=node_id,
            embedding=embedding,
            summary=summary,
            parent_id=parent_id,
            children_ids=[],
            depth=depth,
            last_updated=time.time(),
            metadata=metadata or {}
        )
        
        # Add to graph
        self.nodes[node_id] = node
        
        # Update parent's children list
        if node_id not in parent.children_ids:
            parent.children_ids.append(node_id)
        
        print(f"  ✓ Added node: {node_id} (depth={depth}, parent={parent_id})")
        
        # Incrementally assign node to cluster (threshold-based)
        self._assign_to_cluster(node_id, embedding)
        
        return node
    
    def _assign_to_cluster(self, node_id: str, embedding: List[float]):
        """
        Incrementally assign a new node to an existing cluster or create a new one
        Uses threshold-based approach: if similarity to any centroid >= threshold, join that cluster
        Otherwise, create a new cluster
        
        Args:
            node_id: ID of the node to assign
            embedding: Embedding vector of the node
        """
        node = self.nodes.get(node_id)
        if not node:
            return
        
        # If no clusters exist yet, create first cluster
        if len(self.cluster_centroids) == 0:
            cluster_id = 0
            self.cluster_centroids[cluster_id] = embedding.copy()
            self.cluster_members[cluster_id] = [node_id]
            node.metadata["cluster_id"] = cluster_id
            self.next_cluster_id = 1
            print(f"  🎨 Created cluster {cluster_id} with node {node_id}")
            return
        
        # Find best matching cluster
        best_cluster_id = None
        best_similarity = -1.0
        
        for cluster_id, centroid in self.cluster_centroids.items():
            similarity = self.cosine_similarity(embedding, centroid)
            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster_id = cluster_id
        
        # Check if similarity meets threshold
        if best_similarity >= self.CLUSTER_SIMILARITY_THRESHOLD:
            # Assign to existing cluster
            cluster_id = best_cluster_id
            self.cluster_members[cluster_id].append(node_id)
            node.metadata["cluster_id"] = cluster_id
            
            # Update centroid (running average)
            self._update_centroid(cluster_id, embedding)
            
            print(f"  🎨 Assigned node {node_id} to cluster {cluster_id} (similarity: {best_similarity:.3f})")
        else:
            # Create new cluster
            cluster_id = self.next_cluster_id
            self.cluster_centroids[cluster_id] = embedding.copy()
            self.cluster_members[cluster_id] = [node_id]
            node.metadata["cluster_id"] = cluster_id
            self.next_cluster_id += 1
            
            print(f"  🎨 Created new cluster {cluster_id} for node {node_id} (best similarity: {best_similarity:.3f} < {self.CLUSTER_SIMILARITY_THRESHOLD})")
    
    def _update_centroid(self, cluster_id: int, new_embedding: List[float]):
        """
        Update cluster centroid using running average
        New centroid = (old_centroid * (n-1) + new_embedding) / n
        
        Args:
            cluster_id: ID of the cluster to update
            new_embedding: Embedding of the newly added node
        """
        if cluster_id not in self.cluster_centroids:
            return
        
        old_centroid = np.array(self.cluster_centroids[cluster_id])
        new_embedding_np = np.array(new_embedding)
        
        n = len(self.cluster_members[cluster_id])
        
        # Running average: new_centroid = (old * (n-1) + new) / n
        new_centroid = (old_centroid * (n - 1) + new_embedding_np) / n
        
        self.cluster_centroids[cluster_id] = new_centroid.tolist()
    
    def get_cluster_color(self, cluster_id: int) -> str:
        """
        Get color for a cluster ID
        
        Args:
            cluster_id: Cluster ID (0-based)
        
        Returns:
            Hex color code
        """
        if cluster_id is None:
            return "#CCCCCC"  # Default gray
        return self.CLUSTER_COLORS[cluster_id % len(self.CLUSTER_COLORS)]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_best_match(
        self,
        candidate_embedding: List[float],
        node_embeddings: List[tuple[str, List[float]]],
        threshold: Optional[float] = None
    ) -> tuple[Optional[str], float, bool]:
        """
        Find best matching node from a list of candidates
        
        Returns:
            (node_id, similarity, is_match)
            is_match: True if similarity >= threshold, False otherwise
        """
        if threshold is None:
            threshold = self.SIMILARITY_THRESHOLD
        
        if not node_embeddings:
            return None, 0.0, False
        
        best_id = None
        best_similarity = -1.0
        
        for node_id, node_embedding in node_embeddings:
            similarity = self.cosine_similarity(candidate_embedding, node_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_id = node_id
        
        is_match = best_similarity >= threshold
        return best_id, best_similarity, is_match
    
    def get_all_nodes(self, user_id: Optional[str] = None) -> List[GraphNode]:
        """Get all nodes in the graph, optionally filtered by user_id"""
        if user_id is None:
            return list(self.nodes.values())
        # Filter nodes by user_id in metadata
        return [node for node in self.nodes.values() 
                if node.metadata.get("user_id") == user_id or 
                (node.id == self.root_id and node.metadata.get("user_id") == user_id) or
                (node.id == self.root_id and user_id is None)]
    
    def get_all_nodes_except_root(self, user_id: Optional[str] = None) -> List[GraphNode]:
        """Get all nodes except root (for global search), optionally filtered by user_id"""
        if user_id is None:
            return [node for node in self.nodes.values() if node.id != self.root_id]
        # Filter nodes by user_id, excluding root
        return [node for node in self.nodes.values() 
                if node.id != self.root_id and node.metadata.get("user_id") == user_id]
    
    def get_all_edges(self) -> List[dict]:
        """
        Get all edges in the graph (from parent-child relationships)
        
        Returns:
            List of edge dictionaries with from_node, to_node, type, strength, metadata
        """
        edges = []
        for node in self.nodes.values():
            if node.parent_id:
                edge = {
                    "from_node": node.parent_id,
                    "to_node": node.id,
                    "type": "extends" if node.parent_id != self.root_id else "root",
                    "strength": 1.0,
                    "metadata": {
                        "relationship": "parent_child"
                    }
                }
                edges.append(edge)
        return edges
    
    def get_recent_chunk_nodes(self, num_chunks: int = 5) -> List[tuple[str, List[GraphNode]]]:
        """
        Get nodes from the most recent N chunks, grouped by chunk_id
        
        Args:
            num_chunks: Number of recent chunks to retrieve (default: 5)
        
        Returns:
            List of (chunk_id, [nodes]) tuples, ordered by chunk timestamp (oldest first)
            chunk_id will be "unknown" if not set in metadata
        """
        # Get all nodes except root
        all_nodes = [node for node in self.nodes.values() if node.id != self.root_id]
        
        # Group nodes by chunk_id (use "unknown" as fallback)
        nodes_by_chunk: dict[str, List[GraphNode]] = {}
        chunk_timestamps: dict[str, float] = {}
        
        for node in all_nodes:
            chunk_id = node.metadata.get("chunk_id") or "unknown"
            
            if chunk_id not in nodes_by_chunk:
                nodes_by_chunk[chunk_id] = []
            nodes_by_chunk[chunk_id].append(node)
            
            # Track earliest timestamp for each chunk
            chunk_timestamp = node.metadata.get("timestamp", 0.0)
            if chunk_id not in chunk_timestamps or chunk_timestamp < chunk_timestamps[chunk_id]:
                chunk_timestamps[chunk_id] = chunk_timestamp
        
        # Sort chunks by timestamp (oldest first) and take most recent N
        sorted_chunks = sorted(
            chunk_timestamps.items(),
            key=lambda x: x[1],
            reverse=False  # Oldest first (chronological order)
        )
        
        # Get the most recent N chunks
        recent_chunks = sorted_chunks[-num_chunks:] if len(sorted_chunks) > num_chunks else sorted_chunks
        
        # Return chunks with their nodes, in chronological order
        result = []
        for chunk_id, _ in recent_chunks:
            # Sort nodes within chunk by timestamp
            chunk_nodes = sorted(
                nodes_by_chunk[chunk_id],
                key=lambda n: n.metadata.get("timestamp", 0.0)
            )
            result.append((chunk_id, chunk_nodes))
        
        return result
    
    def get_node_path(self, node_id: str) -> List[str]:
        """Get path from root to node (for LLM context)"""
        path = []
        current = self.get_node(node_id)
        while current and current.parent_id:
            path.insert(0, current.id)
            current = self.get_node(current.parent_id)
        return path
    
    def find_globally_similar_nodes(
        self,
        candidate_embedding: List[float],
        exclude_node_id: Optional[str] = None,
        filter_by_threshold: bool = False,
        user_id: Optional[str] = None
    ) -> List[tuple[str, float, GraphNode]]:
        """
        Find top-K most similar nodes in entire graph
        
        Args:
            candidate_embedding: Embedding to compare against
            exclude_node_id: Node ID to exclude from search
            filter_by_threshold: If True, only return nodes >= SIMILARITY_THRESHOLD
            user_id: Optional user ID to filter nodes by user
        
        Returns:
            List of (node_id, similarity, node) tuples, sorted by similarity descending
        """
        all_nodes = self.get_all_nodes_except_root(user_id=user_id)
        if exclude_node_id:
            all_nodes = [n for n in all_nodes if n.id != exclude_node_id]
        
        if not all_nodes:
            return []
        
        # Dynamic TOP_K: use min of default or available nodes
        available_count = len(all_nodes)
        top_k = min(self.TOP_K_DEFAULT, available_count)
        
        similarities = []
        for node in all_nodes:
            similarity = self.cosine_similarity(candidate_embedding, node.embedding)
            if not filter_by_threshold or similarity >= self.SIMILARITY_THRESHOLD:
                similarities.append((node.id, similarity, node))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-K (or all if fewer than K)
        return similarities[:top_k]
    
    def get_downward_paths(self, node_id: str) -> dict:
        """
        Get all paths from node to its last children (leaf nodes)
        Uses DFS to find all paths to leaf nodes
        
        Returns:
            {
                "paths": [[node_id, child_id, ...], ...],
                "all_nodes_in_paths": [node_ids],
                "last_children": [node_ids]
            }
        """
        def find_leaf_paths(current_id, current_path):
            current_node = self.get_node(current_id)
            if not current_node:
                return []
            
            current_path = current_path + [current_id]
            
            # If leaf node (no children), return this path
            if not current_node.children_ids:
                return [current_path]
            
            # Otherwise, continue DFS
            all_paths = []
            for child_id in current_node.children_ids:
                child_paths = find_leaf_paths(child_id, current_path)
                all_paths.extend(child_paths)
            
            return all_paths
        
        all_paths = find_leaf_paths(node_id, [])
        
        # Get all unique nodes in all paths
        all_nodes = set()
        for path in all_paths:
            all_nodes.update(path)
        
        # Get last children (leaf nodes)
        last_children = [path[-1] for path in all_paths]
        
        return {
            "paths": all_paths,
            "all_nodes_in_paths": list(all_nodes),
            "last_children": list(set(last_children))
        }
    
    def get_path_to_root(self, node_id: str) -> dict:
        """
        Get path from node to root (backtracking)
        
        Returns:
            {
                "path": [root_id, ..., node_id],
                "all_nodes": [node_ids]
            }
        """
        path = []
        current = self.get_node(node_id)
        
        # Backtrack to root
        while current:
            path.insert(0, current.id)
            if current.parent_id:
                current = self.get_node(current.parent_id)
            else:
                break
        
        return {
            "path": path,
            "all_nodes": path
        }
    
    def calculate_maturity(self, node_id: str) -> dict:
        """
        Calculate maturity score for a node
        
        Returns:
            {
                "score": float (0-100),
                "breakdown": {
                    "depth_score": float,
                    "children_score": float,
                    "descendants_score": float
                }
            }
        """
        node = self.get_node(node_id)
        if not node:
            return {"score": 0, "breakdown": {}}
        
        # Count all descendants
        def count_descendants(node_id):
            node = self.get_node(node_id)
            if not node:
                return 0
            count = len(node.children_ids)
            for child_id in node.children_ids:
                count += count_descendants(child_id)
            return count
        
        descendants = count_descendants(node_id)
        
        # Weighted formula
        depth_score = min(node.depth * 10, 50)  # Max 50 points
        children_score = min(len(node.children_ids) * 5, 30)  # Max 30 points
        descendants_score = min(descendants * 2, 20)  # Max 20 points
        
        maturity = depth_score + children_score + descendants_score
        maturity = min(maturity, 100)  # Cap at 100
        
        return {
            "score": round(maturity, 1),
            "breakdown": {
                "depth_score": round(depth_score, 1),
                "children_score": round(children_score, 1),
                "descendants_score": round(descendants_score, 1)
            }
        }
    
    def calculate_influence(self, node_id: str) -> dict:
        """
        Calculate influence score for a node
        
        Returns:
            {
                "score": int (total nodes influenced),
                "direct": int (direct children),
                "indirect": int (all descendants)
            }
        """
        node = self.get_node(node_id)
        if not node:
            return {"score": 0, "direct": 0, "indirect": 0}
        
        # Count all descendants (direct + indirect)
        def count_all_descendants(node_id):
            node = self.get_node(node_id)
            if not node:
                return 0
            total = len(node.children_ids)  # Direct children
            
            # Recursively count descendants
            for child_id in node.children_ids:
                total += count_all_descendants(child_id)
            
            return total
        
        direct = len(node.children_ids)
        indirect = count_all_descendants(node_id) - direct
        total = direct + indirect
        
        return {
            "score": total,
            "direct": direct,
            "indirect": indirect
        }
    
    def reset(self):
        """Reset graph (for new meeting)"""
        self.nodes = {}
        self.root_id = None
        self.cluster_centroids = {}
        self.cluster_members = {}
        self.next_cluster_id = 0
        self._initialize_root()
        print("🔄 Graph reset")

