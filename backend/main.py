"""
MeetMap Prototype - Main FastAPI Application
Simple pipeline: Receive chunk → Extract nodes → Return to frontend
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import os
import time
from typing import Optional

from services.meetmap_service import MeetMapService
from services.database import db
from models.schemas import TranscriptChunk

load_dotenv()

app_start = time.time()
print(f"\n[{time.strftime('%H:%M:%S')}] 🚀 Starting MeetMap Backend...")

app = FastAPI(title="MeetMap Prototype API")

# CORS middleware
cors_start = time.time()
# Get frontend URL from environment (for production) or use localhost defaults
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://meetpmap.vercel.app",  # Vercel deployment
    "https://graph.miless.app",  # Custom domain
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
cors_elapsed = time.time() - cors_start
print(f"[{time.strftime('%H:%M:%S')}] ✅ CORS middleware configured ({cors_elapsed:.3f}s)")

# Initialize services
service_start = time.time()
print(f"[{time.strftime('%H:%M:%S')}] 📦 Initializing MeetMapService...")
meetmap_service = MeetMapService()
service_elapsed = time.time() - service_start
print(f"[{time.strftime('%H:%M:%S')}] ✅ MeetMapService initialization complete ({service_elapsed:.2f}s)")

app_elapsed = time.time() - app_start
print(f"[{time.strftime('%H:%M:%S')}] 🎉 Backend initialization complete! (Total: {app_elapsed:.2f}s)\n")


# Database lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup and run migration if needed"""
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 🔌 Connecting to database...")
        await db.connect()
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Database connected")
        
        # Run migration automatically (creates tables if they don't exist)
        # This is safe because schema.sql uses "CREATE TABLE IF NOT EXISTS"
        try:
            from pathlib import Path
            schema_file = Path(__file__).parent / "database" / "schema.sql"
            if schema_file.exists():
                print(f"[{time.strftime('%H:%M:%S')}] 📦 Running database migration...")
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                await db.execute(schema_sql)
                
                # Verify tables
                tables = await db.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                print(f"[{time.strftime('%H:%M:%S')}] ✅ Database ready - {len(tables)} tables found")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Schema file not found, skipping migration")
        except Exception as migration_error:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Migration error (tables may already exist): {migration_error}")
            # Continue anyway - tables might already exist
            
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Database connection failed: {e}")
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Continuing without database (will use in-memory storage)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        await db.close()
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Database connection closed")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Error closing database: {e}")


@app.get("/")
async def root():
    return {"message": "MeetMap Prototype API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint - includes database status"""
    try:
        db_health = await db.health_check()
        return {
            "status": "healthy",
            "database": db_health
        }
    except Exception as e:
        return {
            "status": "healthy",
            "database": {"status": "error", "error": str(e)}
        }


@app.get("/api/db/test")
async def test_database():
    """Test database connection and basic operations"""
    try:
        # Check connection
        health = await db.health_check()
        if health.get("status") != "connected":
            return JSONResponse(
                status_code=503,
                content={"status": "error", "message": "Database not connected", "health": health}
            )
        
        # Test query: Get table count
        table_count = await db.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        # Test query: Get graph_nodes count
        node_count = await db.fetchval("SELECT COUNT(*) FROM graph_nodes")
        
        return {
            "status": "success",
            "message": "Database connection working",
            "database": health.get("database"),
            "tables": table_count,
            "nodes": node_count
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/api/transcript")
async def process_transcript_chunk(chunk: dict):
    """Process a single transcript chunk and return nodes/edges"""
    try:
        # Validate chunk structure
        if not chunk or not isinstance(chunk, dict):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid chunk format. Expected a dictionary."}
            )
        
        transcript_chunk = TranscriptChunk(**chunk)
        
        # Note: user_id is optional - if not provided, nodes are shared across all users
        # If user_id is provided, nodes are isolated per user
        
        # Extract nodes and edges with full context
        nodes, edges = await meetmap_service.extract_nodes(transcript_chunk)
        
        print(f"✅ Extracted {len(nodes)} node(s) and {len(edges)} edge(s) from chunk")
        
        return {
            "status": "success",
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges]
        }
        
    except ValueError as e:
        # Pydantic validation errors
        print(f"❌ Validation error: {e}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Invalid chunk data: {str(e)}"}
        )
    except Exception as e:
        print(f"❌ Error processing chunk: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/graph/path/down/{node_id}")
async def get_downward_path(node_id: str, user_id: str = Query(..., description="User ID (required)")):
    """Get all paths from node down to its last children"""
    try:
        if not node_id or not node_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "node_id is required"}
            )
        graph_manager = meetmap_service.graph_manager
        result = await graph_manager.get_downward_paths(node_id, user_id)
        return {"status": "success", **result}
    except KeyError as e:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Node not found: {node_id}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/graph/path/up/{node_id}")
async def get_upward_path(node_id: str, user_id: str = Query(..., description="User ID (required)")):
    """Get path from node up to root"""
    try:
        if not node_id or not node_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "node_id is required"}
            )
        graph_manager = meetmap_service.graph_manager
        result = await graph_manager.get_path_to_root(node_id, user_id)
        return {"status": "success", **result}
    except KeyError as e:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Node not found: {node_id}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/graph/maturity/{node_id}")
async def get_maturity(node_id: str, user_id: str = Query(..., description="User ID (required)")):
    """Get maturity score for a node"""
    try:
        if not node_id or not node_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "node_id is required"}
            )
        graph_manager = meetmap_service.graph_manager
        result = await graph_manager.calculate_maturity(node_id, user_id)
        return {"status": "success", **result}
    except KeyError as e:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Node not found: {node_id}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/graph/influence/{node_id}")
async def get_influence(node_id: str, user_id: str = Query(..., description="User ID (required)")):
    """Get influence score for a node"""
    try:
        if not node_id or not node_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "node_id is required"}
            )
        graph_manager = meetmap_service.graph_manager
        result = await graph_manager.calculate_influence(node_id, user_id)
        return {"status": "success", **result}
    except KeyError as e:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": f"Node not found: {node_id}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/api/graph/state")
async def get_graph_state(user_id: str = Query(..., description="User ID (required)")):
    """Get the complete graph state (all nodes and edges) for a user"""
    try:
        graph_manager = meetmap_service.graph_manager
        
        # Get all nodes filtered by user_id
        all_graph_nodes = await graph_manager.get_all_nodes(user_id=user_id)
        
        # Convert to frontend format using the service's conversion method
        from models.schemas import NodeData, EdgeData
        
        nodes = []
        edges = []
        
        # Include root node (user-specific)
        root = await graph_manager.get_root(user_id=user_id)
        if root:
            root_node_data = NodeData(
                id=root.id,
                text=root.summary,
                type="idea",
                timestamp=0.0,
                confidence=1.0,
                metadata={
                    "depth": 0,
                    "is_root": True,
                    **root.metadata
                }
            )
            nodes.append(root_node_data)
        
        # Convert all other nodes
        user_root_id = f"root_{user_id}"
        for graph_node in all_graph_nodes:
            # Skip root nodes (already added above)
            if graph_node.id == user_root_id:
                continue
            
            cluster_id = graph_node.metadata.get("cluster_id")
            cluster_color = graph_manager.get_cluster_color(cluster_id) if cluster_id is not None else None
            
            node_data = NodeData(
                id=graph_node.id,
                text=graph_node.summary,
                type="idea",
                speaker=graph_node.metadata.get("speaker"),
                timestamp=graph_node.metadata.get("timestamp", 0.0),
                confidence=1.0,
                metadata={
                    "depth": graph_node.depth,
                    "parent_id": graph_node.parent_id,
                    "children_count": len(graph_node.children_ids),
                    "cluster_id": cluster_id,
                    "cluster_color": cluster_color,
                    **graph_node.metadata
                }
            )
            nodes.append(node_data)
            
            # Create edge from parent to this node
            if graph_node.parent_id:
                # Determine if parent is a root node (user-specific)
                is_root_parent = graph_node.parent_id == user_root_id
                
                edge = EdgeData(
                    from_node=graph_node.parent_id,
                    to_node=graph_node.id,
                    type="root" if is_root_parent else "extends",
                    strength=1.0,
                    metadata={
                        "relationship": "parent_child"
                    }
                )
                edges.append(edge)
        
        return {
            "status": "success",
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges]
        }
        
    except Exception as e:
        print(f"❌ Error getting graph state: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )






if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
