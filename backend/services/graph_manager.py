"""
Graph Manager - Manages the semantic idea-evolution graph
Uses adjacency list-based directed graph structure
"""

from typing import Dict, Optional, List
import time
import numpy as np
from models.schemas import GraphNode


class GraphManager:
    """Manages the semantic idea-evolution graph"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}  # node_id -> GraphNode
        self.root_id: Optional[str] = None
        self._initialize_root()
    
    def _initialize_root(self):
        """Create root node at graph initialization"""
        root_id = "root"
        
        # Create a generic placeholder embedding (zero vector or small random)
        # In practice, this could be a generic "meeting start" embedding
        placeholder_embedding = [0.0] * 384  # Default size for all-MiniLM-L6-v2
        
        root_node = GraphNode(
            id=root_id,
            embedding=placeholder_embedding,
            summary="Meeting Start",
            parent_id=None,
            children_ids=[],
            depth=0,
            last_updated=time.time(),
            metadata={"is_root": True}
        )
        
        self.nodes[root_id] = root_node
        self.root_id = root_id
        print(f"🌳 Graph initialized with root node: {root_id}")
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def get_root(self) -> GraphNode:
        """Get root node"""
        return self.nodes[self.root_id]
    
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
        return node
    
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
        high_threshold: float = 0.75,
        medium_threshold: float = 0.60
    ) -> tuple[Optional[str], float, str]:
        """
        Find best matching node from a list of candidates
        
        Returns:
            (node_id, similarity, match_type)
            match_type: "high" | "medium" | "none"
        """
        if not node_embeddings:
            return None, 0.0, "none"
        
        best_id = None
        best_similarity = -1.0
        
        for node_id, node_embedding in node_embeddings:
            similarity = self.cosine_similarity(candidate_embedding, node_embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_id = node_id
        
        # Determine match type
        if best_similarity >= high_threshold:
            match_type = "high"
        elif best_similarity >= medium_threshold:
            match_type = "medium"
        else:
            match_type = "none"
        
        return best_id, best_similarity, match_type
    
    def traverse_and_place(
        self,
        candidate_embedding: List[float],
        candidate_summary: str,
        high_threshold: float = 0.75,
        medium_threshold: float = 0.60
    ) -> str:
        """
        Traverse graph from root to find best placement location
        Returns the parent_id where the candidate should be placed
        """
        traverse_start = time.time()
        current_node_id = self.root_id
        max_depth = 10  # Prevent infinite loops
        depth = 0
        total_children_compared = 0
        
        while depth < max_depth:
            level_start = time.time()
            current_node = self.get_node(current_node_id)
            if not current_node:
                break
            
            # Get children
            get_children_start = time.time()
            children = self.get_children(current_node_id)
            get_children_elapsed = time.time() - get_children_start
            
            if not children:
                # No children, place here
                elapsed = time.time() - traverse_start
                print(f"      → Traversal stopped at {current_node_id} (no children) - depth {depth}, total: {elapsed:.3f}s")
                return current_node_id
            
            # Compare with children
            compare_start = time.time()
            child_embeddings = [(child.id, child.embedding) for child in children]
            total_children_compared += len(child_embeddings)
            
            best_id, similarity, match_type = self.find_best_match(
                candidate_embedding,
                child_embeddings,
                high_threshold,
                medium_threshold
            )
            compare_elapsed = time.time() - compare_start
            level_elapsed = time.time() - level_start
            
            if match_type == "high":
                # High similarity - descend into this child
                print(f"      → Depth {depth}: High similarity ({similarity:.3f}) with {best_id} (compared {len(child_embeddings)} children in {compare_elapsed:.3f}s), descending...")
                current_node_id = best_id
                depth += 1
            elif match_type == "medium":
                # Medium similarity - could branch, but for now descend (can be refined)
                print(f"      → Depth {depth}: Medium similarity ({similarity:.3f}) with {best_id} (compared {len(child_embeddings)} children in {compare_elapsed:.3f}s), descending...")
                current_node_id = best_id
                depth += 1
            else:
                # No good match - place here
                elapsed = time.time() - traverse_start
                print(f"      → Depth {depth}: Low similarity ({similarity:.3f}), placing at {current_node_id} (compared {len(child_embeddings)} children in {compare_elapsed:.3f}s, total: {elapsed:.3f}s)")
                return current_node_id
        
        # Reached max depth or no more children
        elapsed = time.time() - traverse_start
        print(f"      → Traversal complete at max depth, placing at {current_node_id} (total: {elapsed:.3f}s, compared {total_children_compared} nodes)")
        return current_node_id
    
    def get_all_nodes(self) -> List[GraphNode]:
        """Get all nodes in the graph"""
        return list(self.nodes.values())
    
    def reset(self):
        """Reset graph (for new meeting)"""
        self.nodes = {}
        self.root_id = None
        self._initialize_root()
        print("🔄 Graph reset")

