"""
Database service for PostgreSQL connection and operations
Uses asyncpg for async database operations
VERSION 2: Changed from user_id to meeting_id based architecture
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
        self.database_url = os.getenv("DATABASE_URL")
        
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
        
        try:
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
        """Execute a query (INSERT, UPDATE, DELETE)"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            result = await connection.execute(query, *args)
            return result
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return rows
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return row
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            val = await connection.fetchval(query, *args)
            return val
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connection health"""
        try:
            if not self.pool:
                return {"status": "disconnected", "error": "Pool not initialized"}
            
            result = await self.fetchval("SELECT 1")
            if result == 1:
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
    # Meeting Methods
    # ============================================
    
    async def create_or_get_user(self, user_id: str) -> str:
        """Create user if doesn't exist, or get existing user"""
        await self.execute(
            """
            INSERT INTO users (id, last_active)
            VALUES ($1, NOW())
            ON CONFLICT (id) DO UPDATE SET
                last_active = NOW()
            """,
            user_id
        )
        return "User created or updated"
    
    async def link_user_to_meeting(self, user_id: str, meeting_id: str) -> str:
        """Link a user to a meeting in user_meetings table"""
        await self.execute(
            """
            INSERT INTO user_meetings (user_id, meeting_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, meeting_id) DO NOTHING
            """,
            user_id, meeting_id
        )
        return "User linked to meeting"
    
    async def create_meeting(
        self,
        meeting_id: str,
        title: str = "Untitled Meeting",
        description: Optional[str] = None
    ) -> str:
        """Create a new meeting"""
        await self.execute(
            """
            INSERT INTO meetings (id, title, description)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description
            """,
            meeting_id, title, description or ""
        )
        return "Meeting created"
    
    async def get_meeting(self, meeting_id: str) -> Optional[asyncpg.Record]:
        """Get a meeting by ID"""
        return await self.fetchrow(
            "SELECT * FROM meetings WHERE id = $1",
            meeting_id
        )
    
    async def get_meetings_by_user(self, user_id: str) -> List[asyncpg.Record]:
        """Get all meetings for a user via user_meetings junction table"""
        return await self.fetch(
            """
            SELECT m.* 
            FROM meetings m
            INNER JOIN user_meetings um ON m.id = um.meeting_id
            WHERE um.user_id = $1
            ORDER BY m.created_at DESC
            """,
            user_id
        )
    
    # ============================================
    # Transcription Methods
    # ============================================
    
    async def save_transcription(self, meeting_id: str, transcription_text: str) -> str:
        """
        Save or append transcription for a meeting.
        If meeting_id doesn't exist, creates new row.
        If meeting_id exists, concatenates new transcription to existing one.
        """
        await self.execute(
            """
            INSERT INTO transcriptions (meeting_id, transcription, updated_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (meeting_id) DO UPDATE SET
                transcription = transcriptions.transcription || ' ' || EXCLUDED.transcription,
                updated_at = NOW()
            """,
            meeting_id, transcription_text.strip()
        )
        return "Transcription saved"
    
    async def get_transcription(self, meeting_id: str) -> Optional[asyncpg.Record]:
        """Get transcription for a meeting"""
        return await self.fetchrow(
            "SELECT * FROM transcriptions WHERE meeting_id = $1",
            meeting_id
        )
    
    # ============================================
    # Graph Node Methods (with meeting_id filtering)
    # ============================================
    
    async def get_node(self, node_id: str, meeting_id: str) -> Optional[asyncpg.Record]:
        """Get a single node by ID, filtered by meeting_id"""
        return await self.fetchrow(
            "SELECT * FROM graph_nodes WHERE id = $1 AND meeting_id = $2",
            node_id, meeting_id
        )
    
    async def get_all_nodes(self, meeting_id: str) -> List[asyncpg.Record]:
        """Get all nodes for a meeting"""
        return await self.fetch(
            "SELECT * FROM graph_nodes WHERE meeting_id = $1 ORDER BY last_updated",
            meeting_id
        )
    
    async def get_root_node(self, meeting_id: str) -> Optional[asyncpg.Record]:
        """Get root node for a meeting"""
        root_id = f"root_meeting_{meeting_id}"
        return await self.get_node(root_id, meeting_id)
    
    async def get_children(self, parent_id: str, meeting_id: str) -> List[asyncpg.Record]:
        """Get all children of a node, filtered by meeting_id"""
        return await self.fetch(
            "SELECT * FROM graph_nodes WHERE parent_id = $1 AND meeting_id = $2",
            parent_id, meeting_id
        )
    
    async def save_node(
        self,
        node_id: str,
        meeting_id: str,
        embedding: List[float],
        summary: str,
        parent_id: Optional[str],
        depth: int,
        metadata: Dict[str, Any]
    ) -> str:
        """Save a node to database (meeting_id required)"""
        import json
        
        embedding_json = json.dumps(embedding)
        metadata_json = json.dumps(metadata)
        
        import time
        try:
            await self.execute(
                """
                INSERT INTO graph_nodes (id, meeting_id, embedding, summary, parent_id, depth, metadata)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    summary = EXCLUDED.summary,
                    parent_id = EXCLUDED.parent_id,
                    depth = EXCLUDED.depth,
                    metadata = EXCLUDED.metadata,
                    last_updated = NOW()
                """,
                node_id, meeting_id, embedding_json, summary, parent_id, depth, metadata_json
            )
            print(f"[{time.strftime('%H:%M:%S')}] [DB] Saved node: {node_id} for meeting_id={meeting_id}")
            return "Node saved"
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] [DB ERROR] Failed to save node {node_id} for meeting_id={meeting_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # ============================================
    # Edge Methods (with meeting_id filtering)
    # ============================================
    
    async def get_edges(self, meeting_id: str) -> List[asyncpg.Record]:
        """Get all edges for a meeting"""
        return await self.fetch(
            "SELECT * FROM graph_edges WHERE meeting_id = $1",
            meeting_id
        )
    
    async def save_edge(
        self,
        from_node: str,
        to_node: str,
        meeting_id: str,
        edge_type: str = "extends",
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save an edge to database (meeting_id required)"""
        import json
        
        metadata_json = json.dumps(metadata or {})
        
        await self.execute(
            """
            INSERT INTO graph_edges (from_node, to_node, meeting_id, edge_type, strength, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (from_node, to_node) DO UPDATE SET
                edge_type = EXCLUDED.edge_type,
                strength = EXCLUDED.strength,
                metadata = EXCLUDED.metadata
            """,
            from_node, to_node, meeting_id, edge_type, strength, metadata_json
        )
        
        return "Edge saved"
    
    # ============================================
    # Cluster Methods (with meeting_id filtering)
    # ============================================
    
    async def get_clusters(self, meeting_id: str) -> List[asyncpg.Record]:
        """Get all clusters for a meeting"""
        return await self.fetch(
            "SELECT * FROM clusters WHERE meeting_id = $1 ORDER BY cluster_id",
            meeting_id
        )
    
    async def get_cluster(self, cluster_id: int, meeting_id: str) -> Optional[asyncpg.Record]:
        """Get a single cluster by ID, filtered by meeting_id"""
        return await self.fetchrow(
            "SELECT * FROM clusters WHERE cluster_id = $1 AND meeting_id = $2",
            cluster_id, meeting_id
        )
    
    async def save_cluster(
        self,
        cluster_id: int,
        meeting_id: str,
        centroid: List[float],
        color: str
    ) -> str:
        """Save or update a cluster"""
        import json
        
        centroid_json = json.dumps(centroid)
        
        await self.execute(
            """
            INSERT INTO clusters (cluster_id, meeting_id, centroid, color, updated_at)
            VALUES ($1, $2, $3::jsonb, $4, NOW())
            ON CONFLICT (cluster_id, meeting_id) DO UPDATE SET
                centroid = EXCLUDED.centroid,
                color = EXCLUDED.color,
                updated_at = NOW()
            """,
            cluster_id, meeting_id, centroid_json, color
        )
        
        return "Cluster saved"
    
    async def get_cluster_members(self, cluster_id: int, meeting_id: str) -> List[asyncpg.Record]:
        """Get all nodes in a cluster"""
        return await self.fetch(
            "SELECT * FROM cluster_members WHERE cluster_id = $1 AND meeting_id = $2",
            cluster_id, meeting_id
        )
    
    async def add_cluster_member(self, cluster_id: int, node_id: str, meeting_id: str) -> str:
        """Add a node to a cluster"""
        await self.execute(
            """
            INSERT INTO cluster_members (cluster_id, node_id, meeting_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (cluster_id, node_id) DO NOTHING
            """,
            cluster_id, node_id, meeting_id
        )
        
        return "Cluster member added"
    
    async def get_next_cluster_id(self, meeting_id: str) -> int:
        """Get the next available cluster ID for a meeting"""
        result = await self.fetchval(
            "SELECT COALESCE(MAX(cluster_id), -1) + 1 FROM clusters WHERE meeting_id = $1",
            meeting_id
        )
        return result if result is not None else 0


# Global database instance
db = Database()

