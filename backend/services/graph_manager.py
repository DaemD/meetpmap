"""
Graph Manager - Manages the semantic idea-evolution graph
Uses PostgreSQL database for persistent storage
All operations are async and require meeting_id for meeting-based isolation
"""

from typing import Dict, Optional, List, Any
import time
import numpy as np
import json
from models.schemas import GraphNode
from services.database import db


class GraphManager:
    """Manages the semantic idea-evolution graph using PostgreSQL"""
    
    def __init__(self):
        # No in-memory storage - everything in database
        self.root_id: Optional[str] = None  # Global root (for backward compatibility)
        
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
    
    def _record_to_graph_node(self, record) -> GraphNode:
        """Convert database record to GraphNode object"""
        if not record:
            return None
        
        # Parse JSONB fields
        embedding = json.loads(record['embedding']) if isinstance(record['embedding'], str) else record['embedding']
        metadata = json.loads(record['metadata']) if isinstance(record['metadata'], str) else record['metadata']
        
        # Get children from database (parent_id = this node's id)
        # We'll load children_ids when needed, not stored in node
        
        return GraphNode(
            id=record['id'],
            embedding=embedding,
            summary=record['summary'],
            parent_id=record['parent_id'],
            children_ids=[],  # Will be loaded separately when needed
            depth=record['depth'],
            last_updated=record['last_updated'].timestamp() if hasattr(record['last_updated'], 'timestamp') else record['last_updated'],
            metadata=metadata or {}
        )
    
    async def _get_children_ids(self, node_id: str, meeting_id: str) -> List[str]:
        """Get children IDs for a node from database"""
        children = await db.get_children(node_id, meeting_id)
        return [child['id'] for child in children]
    
    async def _initialize_root(self, meeting_id: str):
        """Create root node in database for a specific meeting"""
        root_id = f"root_meeting_{meeting_id}"
        
        # Check if root already exists
        existing_root = await db.get_node(root_id, meeting_id)
        if existing_root:
            print(f"[*] Root node already exists: {root_id} (meeting: {meeting_id})")
            return
        
        # Create a generic placeholder embedding (zero vector)
        placeholder_embedding = [0.0] * 384  # Default size for all-MiniLM-L6-v2
        
        root_metadata = {"is_root": True, "meeting_id": meeting_id}
        
        # Save root to database
        await db.save_node(
            node_id=root_id,
            meeting_id=meeting_id,
            embedding=placeholder_embedding,
            summary="Meeting Start",
            parent_id=None,
            depth=0,
            metadata=root_metadata
        )
        
        print(f"[*] Graph initialized with root node: {root_id} (meeting: {meeting_id})")
    
    async def get_node(self, node_id: str, meeting_id: str) -> Optional[GraphNode]:
        """Get node by ID from database"""
        record = await db.get_node(node_id, meeting_id)
        if not record:
            return None
        
        node = self._record_to_graph_node(record)
        if node:
            # Load children_ids
            node.children_ids = await self._get_children_ids(node_id, meeting_id)
        return node
    
    async def get_root(self, meeting_id: str) -> Optional[GraphNode]:
        """Get root node from database for a specific meeting"""
        if meeting_id is None:
            raise ValueError("meeting_id is required")
        
        meeting_root_id = f"root_meeting_{meeting_id}"
        record = await db.get_root_node(meeting_id)
        
        if not record:
            # Root doesn't exist, create it
            await self._initialize_root(meeting_id)
            record = await db.get_root_node(meeting_id)
        
        if record:
            node = self._record_to_graph_node(record)
            if node:
                node.children_ids = await self._get_children_ids(node.id, meeting_id)
            return node
        return None
    
    async def get_children(self, node_id: str, meeting_id: str) -> List[GraphNode]:
        """Get all children of a node from database"""
        children_records = await db.get_children(node_id, meeting_id)
        children = []
        for record in children_records:
            node = self._record_to_graph_node(record)
            if node:
                node.children_ids = await self._get_children_ids(node.id, meeting_id)
                children.append(node)
        return children
    
    async def add_node(
        self,
        node_id: str,
        embedding: List[float],
        summary: str,
        parent_id: str,
        meeting_id: str,
        metadata: dict = None
    ) -> GraphNode:
        """
        Add a new node to the graph in database
        
        Args:
            node_id: Unique identifier
            embedding: Vector representation
            summary: Text description
            parent_id: Parent node ID
            meeting_id: Meeting ID (required)
            metadata: Additional data
        """
        # Verify parent exists
        parent = await self.get_node(parent_id, meeting_id)
        if not parent:
            raise ValueError(f"Parent node {parent_id} does not exist for meeting {meeting_id}")
        
        # Calculate depth
        depth = parent.depth + 1
        
        # Prepare metadata
        node_metadata = metadata or {}
        if 'meeting_id' not in node_metadata:
            node_metadata['meeting_id'] = meeting_id
        
        # Save node to database
        import time
        print(f"[{time.strftime('%H:%M:%S')}] [GRAPH_MANAGER] About to save node: {node_id} for meeting_id={meeting_id}")
        try:
            await db.save_node(
                node_id=node_id,
                meeting_id=meeting_id,
                embedding=embedding,
                summary=summary,
                parent_id=parent_id,
                depth=depth,
                metadata=node_metadata
            )
            print(f"[{time.strftime('%H:%M:%S')}] [GRAPH_MANAGER] Successfully called save_node for: {node_id}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [GRAPH_MANAGER ERROR] Failed to save node {node_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Create edge in database
        edge_type = "root" if parent_id.startswith("root") else "extends"
        await db.save_edge(
            from_node=parent_id,
            to_node=node_id,
            meeting_id=meeting_id,
            edge_type=edge_type,
            strength=1.0,
            metadata={"relationship": "parent_child"}
        )
        
        print(f"  [*] Added node: {node_id} (depth={depth}, parent={parent_id})")
        
        # Incrementally assign node to cluster (threshold-based)
        # Don't fail node creation if cluster assignment fails
        try:
            await self._assign_to_cluster(node_id, embedding, meeting_id)
        except Exception as cluster_error:
            print(f"  [WARNING] Failed to assign node {node_id} to cluster (non-fatal): {cluster_error}")
            # Continue - node is still created successfully
        
        # Create and return GraphNode object
        node = GraphNode(
            id=node_id,
            embedding=embedding,
            summary=summary,
            parent_id=parent_id,
            children_ids=[],
            depth=depth,
            last_updated=time.time(),
            metadata=node_metadata
        )
        
        return node
    
    async def _assign_to_cluster(self, node_id: str, embedding: List[float], meeting_id: str):
        """
        Incrementally assign a new node to an existing cluster or create a new one
        Uses threshold-based approach: if similarity to any centroid >= threshold, join that cluster
        Otherwise, create a new cluster
        
        Args:
            node_id: ID of the node to assign
            embedding: Embedding vector of the node
            meeting_id: Meeting ID (required)
        """
        # Get all clusters for this meeting
        clusters = await db.get_clusters(meeting_id)
        
        if len(clusters) == 0:
            # Create first cluster
            cluster_id = await db.get_next_cluster_id(meeting_id)
            color = self.get_cluster_color(cluster_id)
            await db.save_cluster(cluster_id, meeting_id, embedding.copy(), color)
            await db.add_cluster_member(cluster_id, node_id, meeting_id)
            
            # Update node metadata
            node = await self.get_node(node_id, meeting_id)
            if node:
                node.metadata["cluster_id"] = cluster_id
                await db.save_node(
                    node_id=node_id,
                    meeting_id=meeting_id,
                    embedding=node.embedding,
                    summary=node.summary,
                    parent_id=node.parent_id,
                    depth=node.depth,
                    metadata=node.metadata
                )
            
            print(f"  [*] Created cluster {cluster_id} with node {node_id}")
            return
        
        # Find best matching cluster
        best_cluster_id = None
        best_similarity = -1.0
        
        for cluster_record in clusters:
            cluster_id = cluster_record['cluster_id']
            centroid_json = cluster_record['centroid']
            centroid = json.loads(centroid_json) if isinstance(centroid_json, str) else centroid_json
            
            similarity = self.cosine_similarity(embedding, centroid)
            if similarity > best_similarity:
                best_similarity = similarity
                best_cluster_id = cluster_id
        
        # Check if similarity meets threshold
        if best_similarity >= self.CLUSTER_SIMILARITY_THRESHOLD:
            # Assign to existing cluster
            cluster_id = best_cluster_id
            await db.add_cluster_member(cluster_id, node_id, meeting_id)
            
            # Update node metadata
            node = await self.get_node(node_id, meeting_id)
            if node:
                node.metadata["cluster_id"] = cluster_id
                await db.save_node(
                    node_id=node_id,
                    meeting_id=meeting_id,
                    embedding=node.embedding,
                    summary=node.summary,
                    parent_id=node.parent_id,
                    depth=node.depth,
                    metadata=node.metadata
                )
            
            # Update centroid (running average)
            await self._update_centroid(cluster_id, embedding, meeting_id)
            
            print(f"  [*] Assigned node {node_id} to cluster {cluster_id} (similarity: {best_similarity:.3f})")
        else:
            # Create new cluster
            next_cluster_id = await db.get_next_cluster_id(meeting_id)
            cluster_id = next_cluster_id
            color = self.get_cluster_color(cluster_id)
            await db.save_cluster(cluster_id, meeting_id, embedding.copy(), color)
            await db.add_cluster_member(cluster_id, node_id, meeting_id)
            
            # Update node metadata
            node = await self.get_node(node_id, meeting_id)
            if node:
                node.metadata["cluster_id"] = cluster_id
                await db.save_node(
                    node_id=node_id,
                    meeting_id=meeting_id,
                    embedding=node.embedding,
                    summary=node.summary,
                    parent_id=node.parent_id,
                    depth=node.depth,
                    metadata=node.metadata
                )
            
            print(f"  [*] Created new cluster {cluster_id} for node {node_id} (best similarity: {best_similarity:.3f} < {self.CLUSTER_SIMILARITY_THRESHOLD})")
    
    async def _update_centroid(self, cluster_id: int, new_embedding: List[float], meeting_id: str):
        """
        Update cluster centroid using running average
        New centroid = (old_centroid * (n-1) + new_embedding) / n
        
        Args:
            cluster_id: ID of the cluster to update
            new_embedding: Embedding of the newly added node
            meeting_id: Meeting ID (required)
        """
        cluster = await db.get_cluster(cluster_id, meeting_id)
        if not cluster:
            return
        
        # Get current centroid
        centroid_json = cluster['centroid']
        old_centroid = json.loads(centroid_json) if isinstance(centroid_json, str) else centroid_json
        
        # Get cluster member count
        members = await db.get_cluster_members(cluster_id, meeting_id)
        n = len(members)
        
        if n == 0:
            return
        
        # Calculate running average
        old_centroid_np = np.array(old_centroid)
        new_embedding_np = np.array(new_embedding)
        new_centroid = (old_centroid_np * (n - 1) + new_embedding_np) / n
        
        # Update in database
        color = cluster.get('color') or self.get_cluster_color(cluster_id)
        await db.save_cluster(cluster_id, meeting_id, new_centroid.tolist(), color)
    
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
    
    async def get_all_nodes(self, meeting_id: str) -> List[GraphNode]:
        """Get all nodes in the graph from database, filtered by meeting_id"""
        if meeting_id is None:
            raise ValueError("meeting_id is required for database operations")
        
        records = await db.get_all_nodes(meeting_id)
        nodes = []
        for record in records:
            node = self._record_to_graph_node(record)
            if node:
                node.children_ids = await self._get_children_ids(node.id, meeting_id)
                nodes.append(node)
        return nodes
    
    async def get_all_nodes_except_root(self, meeting_id: str) -> List[GraphNode]:
        """Get all nodes except root from database, filtered by meeting_id"""
        if meeting_id is None:
            raise ValueError("meeting_id is required for database operations")
        
        all_nodes = await self.get_all_nodes(meeting_id)
        meeting_root_id = f"root_meeting_{meeting_id}"
        return [node for node in all_nodes if node.id != meeting_root_id]
    
    async def get_all_edges(self, meeting_id: str) -> List[dict]:
        """
        Get all edges in the graph from database
        
        Args:
            meeting_id: Meeting ID (required)
        
        Returns:
            List of edge dictionaries with from_node, to_node, type, strength, metadata
        """
        edge_records = await db.get_edges(meeting_id)
        edges = []
        for record in edge_records:
            edge = {
                "from_node": record['from_node'],
                "to_node": record['to_node'],
                "type": record['edge_type'],
                "strength": record['strength'],
                "metadata": json.loads(record['metadata']) if isinstance(record['metadata'], str) else record['metadata']
            }
            edges.append(edge)
        return edges
    
    async def get_recent_chunk_nodes(self, num_chunks: int = 5, meeting_id: Optional[str] = None) -> List[tuple[str, List[GraphNode]]]:
        """
        Get nodes from the most recent N chunks, grouped by chunk_id
        
        Args:
            num_chunks: Number of recent chunks to retrieve (default: 5)
            meeting_id: Meeting ID (required)
        
        Returns:
            List of (chunk_id, [nodes]) tuples, ordered by chunk timestamp (oldest first)
            chunk_id will be "unknown" if not set in metadata
        """
        if meeting_id is None:
            raise ValueError("meeting_id is required for database operations")
        
        # Get all nodes except root
        all_nodes = await self.get_all_nodes_except_root(meeting_id)
        
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
    
    async def get_node_path(self, node_id: str, meeting_id: str) -> List[str]:
        """Get path from root to node (for LLM context)"""
        path = []
        current = await self.get_node(node_id, meeting_id)
        while current and current.parent_id:
            path.insert(0, current.id)
            current = await self.get_node(current.parent_id, meeting_id)
        return path
    
    async def find_globally_similar_nodes(
        self,
        candidate_embedding: List[float],
        exclude_node_id: Optional[str] = None,
        filter_by_threshold: bool = False,
        meeting_id: Optional[str] = None
    ) -> List[tuple[str, float, GraphNode]]:
        """
        Find top-K most similar nodes in entire graph from database
        
        Args:
            candidate_embedding: Embedding to compare against
            exclude_node_id: Node ID to exclude from search
            filter_by_threshold: If True, only return nodes >= SIMILARITY_THRESHOLD
            meeting_id: Meeting ID (required)
        
        Returns:
            List of (node_id, similarity, node) tuples, sorted by similarity descending
        """
        if meeting_id is None:
            raise ValueError("meeting_id is required for database operations")
        
        all_nodes = await self.get_all_nodes_except_root(meeting_id=meeting_id)
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
    
    async def get_downward_paths(self, node_id: str, meeting_id: str) -> dict:
        """
        Get all paths from node to its last children (leaf nodes)
        Uses DFS to find all paths to leaf nodes
        
        Args:
            node_id: Starting node ID
            meeting_id: Meeting ID (required)
        
        Returns:
            {
                "paths": [[node_id, child_id, ...], ...],
                "all_nodes_in_paths": [node_ids],
                "last_children": [node_ids]
            }
        """
        async def find_leaf_paths(current_id, current_path):
            current_node = await self.get_node(current_id, meeting_id)
            if not current_node:
                return []
            
            current_path = current_path + [current_id]
            
            # If leaf node (no children), return this path
            if not current_node.children_ids:
                return [current_path]
            
            # Otherwise, continue DFS
            all_paths = []
            for child_id in current_node.children_ids:
                child_paths = await find_leaf_paths(child_id, current_path)
                all_paths.extend(child_paths)
            
            return all_paths
        
        all_paths = await find_leaf_paths(node_id, [])
        
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
    
    async def get_path_to_root(self, node_id: str, meeting_id: str) -> dict:
        """
        Get path from node to root (backtracking)
        
        Args:
            node_id: Starting node ID
            meeting_id: Meeting ID (required)
        
        Returns:
            {
                "path": [root_id, ..., node_id],
                "all_nodes": [node_ids]
            }
        """
        path = []
        current = await self.get_node(node_id, meeting_id)
        
        # Backtrack to root
        while current:
            path.insert(0, current.id)
            if current.parent_id:
                current = await self.get_node(current.parent_id, meeting_id)
            else:
                break
        
        return {
            "path": path,
            "all_nodes": path
        }
    
    async def calculate_maturity(self, node_id: str, meeting_id: str) -> dict:
        """
        Calculate maturity score for a node
        
        Args:
            node_id: Node ID
            meeting_id: Meeting ID (required)
        
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
        node = await self.get_node(node_id, meeting_id)
        if not node:
            return {"score": 0, "breakdown": {}}
        
        # Count all descendants
        async def count_descendants(n_id):
            n = await self.get_node(n_id, meeting_id)
            if not n:
                return 0
            count = len(n.children_ids)
            for child_id in n.children_ids:
                count += await count_descendants(child_id)
            return count
        
        descendants = await count_descendants(node_id)
        
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
    
    async def calculate_influence(self, node_id: str, meeting_id: str) -> dict:
        """
        Calculate influence score for a node
        
        Args:
            node_id: Node ID
            meeting_id: Meeting ID (required)
        
        Returns:
            {
                "score": int (total nodes influenced),
                "direct": int (direct children),
                "indirect": int (all descendants)
            }
        """
        node = await self.get_node(node_id, meeting_id)
        if not node:
            return {"score": 0, "direct": 0, "indirect": 0}
        
        # Count all descendants (direct + indirect)
        async def count_all_descendants(n_id):
            n = await self.get_node(n_id, meeting_id)
            if not n:
                return 0
            total = len(n.children_ids)  # Direct children
            
            # Recursively count descendants
            for child_id in n.children_ids:
                total += await count_all_descendants(child_id)
            
            return total
        
        direct = len(node.children_ids)
        indirect = await count_all_descendants(node_id) - direct
        total = direct + indirect
        
        return {
            "score": total,
            "direct": direct,
            "indirect": indirect
        }
    
    async def reset(self, meeting_id: Optional[str] = None):
        """Reset graph for a meeting (delete all nodes) - WARNING: This deletes data!"""
        if meeting_id is None:
            raise ValueError("meeting_id is required for database operations")
        
        # Delete all nodes for meeting (cascade will delete edges and cluster members)
        await db.execute(
            "DELETE FROM graph_nodes WHERE meeting_id = $1",
            meeting_id
        )
        
        # Delete clusters for meeting
        await db.execute(
            "DELETE FROM clusters WHERE meeting_id = $1",
            meeting_id
        )
        
        print(f"[*] Graph reset for meeting: {meeting_id}")
