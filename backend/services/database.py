"""
Database service for PostgreSQL connection and operations
Uses asyncpg for async database operations
"""

import os
import asyncpg
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import json
import time

load_dotenv()


class Database:
    """PostgreSQL database connection manager"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url: Optional[str] = None
    
    async def connect(self):
        """Create database connection pool"""
        # Get DATABASE_URL from environment (Railway provides this)
        self.database_url = os.getenv("DATABASE_URL")
        
        # Strip whitespace if present
        if self.database_url:
            self.database_url = self.database_url.strip()
        
        if not self.database_url:
            error_msg = (
                "DATABASE_URL environment variable is required.\n"
                "Please set it in Railway:\n"
                "1. Go to your backend service in Railway\n"
                "2. Click on 'Variables' tab\n"
                "3. Add DATABASE_URL from your PostgreSQL service\n"
                "   Format: postgresql://user:password@postgres.railway.internal:5432/railway"
            )
            print(f"[ERROR] {error_msg}")
            raise ValueError(error_msg)
        
        # Parse DATABASE_URL and create connection pool
        # Railway DATABASE_URL format: postgresql://user:password@host:port/dbname
        # asyncpg needs: postgresql://user:password@host:port/dbname
        
        try:
            # Create connection pool
            # min_size: minimum connections in pool
            # max_size: maximum connections in pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            print(f"[SUCCESS] Database connection pool created successfully")
        except Exception as e:
            print(f"[ERROR] Error creating database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            print("[SUCCESS] Database connection pool closed")
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute a query (INSERT, UPDATE, DELETE)
        Returns: status message
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            result = await connection.execute(query, *args)
            return result
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch multiple rows
        Returns: List of records
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return rows
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch a single row
        Returns: Single record or None
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return row
    
    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch a single value
        Returns: Single value or None
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            val = await connection.fetchval(query, *args)
            return val
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database connection health
        Returns: Health status dictionary
        """
        try:
            if not self.pool:
                return {"status": "disconnected", "error": "Pool not initialized"}
            
            # Try a simple query
            result = await self.fetchval("SELECT 1")
            if result == 1:
                # Get database info
                db_name = await self.fetchval("SELECT current_database()")
                db_version = await self.fetchval("SELECT version()")
                
                return {
                    "status": "connected",
                    "database": db_name,
                    "version": db_version.split(",")[0] if db_version else "unknown"
                }
            else:
                return {"status": "error", "error": "Health check query failed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # ============================================
    # Graph Node Methods (with user_id filtering)
    # ============================================
    
    async def get_node(self, node_id: str, user_id: str) -> Optional[asyncpg.Record]:
        """
        Get a single node by ID, filtered by user_id for isolation
        
        Args:
            node_id: Node ID
            user_id: User ID (required for isolation)
        
        Returns:
            Node record or None if not found
        """
        return await self.fetchrow(
            "SELECT * FROM graph_nodes WHERE id = $1 AND user_id = $2",
            node_id, user_id
        )
    
    async def get_all_nodes(self, user_id: str) -> List[asyncpg.Record]:
        """
        Get all nodes for a user (user isolation enforced)
        
        Args:
            user_id: User ID (required)
        
        Returns:
            List of node records
        """
        return await self.fetch(
            "SELECT * FROM graph_nodes WHERE user_id = $1 ORDER BY last_updated",
            user_id
        )
    
    async def get_root_node(self, user_id: str) -> Optional[asyncpg.Record]:
        """
        Get root node for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Root node record or None
        """
        root_id = f"root_{user_id}"
        return await self.get_node(root_id, user_id)
    
    async def get_children(self, parent_id: str, user_id: str) -> List[asyncpg.Record]:
        """
        Get all children of a node, filtered by user_id
        
        Args:
            parent_id: Parent node ID
            user_id: User ID (required for isolation)
        
        Returns:
            List of child node records
        """
        return await self.fetch(
            "SELECT * FROM graph_nodes WHERE parent_id = $1 AND user_id = $2",
            parent_id, user_id
        )
    
    async def save_node(
        self,
        node_id: str,
        user_id: str,
        embedding: List[float],
        summary: str,
        parent_id: Optional[str],
        depth: int,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save a node to database (user_id required)
        
        Args:
            node_id: Node ID
            user_id: User ID (required)
            embedding: Embedding vector
            summary: Node summary text
            parent_id: Parent node ID (optional)
            depth: Node depth
            metadata: Additional metadata (will be stored as JSONB)
        
        Returns:
            Status message
        """
        import json
        
        # Convert embedding and metadata to JSON
        embedding_json = json.dumps(embedding)
        metadata_json = json.dumps(metadata)
        
        import time
        try:
            await self.execute(
                """
                INSERT INTO graph_nodes (id, user_id, embedding, summary, parent_id, depth, metadata)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    summary = EXCLUDED.summary,
                    parent_id = EXCLUDED.parent_id,
                    depth = EXCLUDED.depth,
                    metadata = EXCLUDED.metadata,
                    last_updated = NOW()
                """,
                node_id, user_id, embedding_json, summary, parent_id, depth, metadata_json
            )
            print(f"[{time.strftime('%H:%M:%S')}] [DB] Saved node: {node_id} for user_id={user_id}")
            return "Node saved"
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [DB ERROR] Failed to save node {node_id} for user_id={user_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # ============================================
    # Edge Methods (with user_id filtering)
    # ============================================
    
    async def get_edges(self, user_id: str) -> List[asyncpg.Record]:
        """
        Get all edges for a user (user isolation enforced)
        
        Args:
            user_id: User ID (required)
        
        Returns:
            List of edge records
        """
        return await self.fetch(
            "SELECT * FROM graph_edges WHERE user_id = $1",
            user_id
        )
    
    async def save_edge(
        self,
        from_node: str,
        to_node: str,
        user_id: str,
        edge_type: str = "extends",
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save an edge to database (user_id required)
        
        Args:
            from_node: Source node ID
            to_node: Destination node ID
            user_id: User ID (required)
            edge_type: Type of edge
            strength: Edge strength
            metadata: Additional metadata
        
        Returns:
            Status message
        """
        import json
        
        metadata_json = json.dumps(metadata or {})
        
        await self.execute(
            """
            INSERT INTO graph_edges (from_node, to_node, user_id, edge_type, strength, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (from_node, to_node) DO UPDATE SET
                edge_type = EXCLUDED.edge_type,
                strength = EXCLUDED.strength,
                metadata = EXCLUDED.metadata
            """,
            from_node, to_node, user_id, edge_type, strength, metadata_json
        )
        
        return "Edge saved"
    
    # ============================================
    # Cluster Methods (with user_id filtering)
    # ============================================
    
    async def get_clusters(self, user_id: str) -> List[asyncpg.Record]:
        """
        Get all clusters for a user
        
        Args:
            user_id: User ID (required)
        
        Returns:
            List of cluster records
        """
        return await self.fetch(
            "SELECT * FROM clusters WHERE user_id = $1 ORDER BY cluster_id",
            user_id
        )
    
    async def get_cluster(self, cluster_id: int, user_id: str) -> Optional[asyncpg.Record]:
        """
        Get a single cluster by ID, filtered by user_id
        
        Args:
            cluster_id: Cluster ID
            user_id: User ID (required)
        
        Returns:
            Cluster record or None
        """
        return await self.fetchrow(
            "SELECT * FROM clusters WHERE cluster_id = $1 AND user_id = $2",
            cluster_id, user_id
        )
    
    async def save_cluster(
        self,
        cluster_id: int,
        user_id: str,
        centroid: List[float],
        color: str
    ) -> str:
        """
        Save or update a cluster
        
        Args:
            cluster_id: Cluster ID
            user_id: User ID (required)
            centroid: Centroid embedding vector
            color: Hex color code
        
        Returns:
            Status message
        """
        import json
        
        centroid_json = json.dumps(centroid)
        
        await self.execute(
            """
            INSERT INTO clusters (cluster_id, user_id, centroid, color, updated_at)
            VALUES ($1, $2, $3::jsonb, $4, NOW())
            ON CONFLICT (cluster_id, user_id) DO UPDATE SET
                centroid = EXCLUDED.centroid,
                color = EXCLUDED.color,
                updated_at = NOW()
            """,
            cluster_id, user_id, centroid_json, color
        )
        
        return "Cluster saved"
    
    async def get_cluster_members(self, cluster_id: int, user_id: str) -> List[asyncpg.Record]:
        """
        Get all nodes in a cluster
        
        Args:
            cluster_id: Cluster ID
            user_id: User ID (required)
        
        Returns:
            List of cluster member records
        """
        return await self.fetch(
            "SELECT * FROM cluster_members WHERE cluster_id = $1 AND user_id = $2",
            cluster_id, user_id
        )
    
    async def add_cluster_member(self, cluster_id: int, node_id: str, user_id: str) -> str:
        """
        Add a node to a cluster
        
        Args:
            cluster_id: Cluster ID
            node_id: Node ID
            user_id: User ID (required)
        
        Returns:
            Status message
        """
        await self.execute(
            """
            INSERT INTO cluster_members (cluster_id, node_id, user_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (cluster_id, node_id) DO NOTHING
            """,
            cluster_id, node_id, user_id
        )
        
        return "Cluster member added"
    
    async def get_next_cluster_id(self, user_id: str) -> int:
        """
        Get the next available cluster ID for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Next cluster ID
        """
        result = await self.fetchval(
            "SELECT COALESCE(MAX(cluster_id), -1) + 1 FROM clusters WHERE user_id = $1",
            user_id
        )
        return result if result is not None else 0


# Global database instance
db = Database()

