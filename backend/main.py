"""
MeetMap Prototype - Main FastAPI Application
Simple pipeline: Receive chunk → Extract nodes → Return to frontend
"""

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import os
import time
from typing import Optional
from contextlib import asynccontextmanager
from pydantic import BaseModel
import base64
import tempfile
import io

from services.meetmap_service import MeetMapService
from services.database import db
from models.schemas import TranscriptChunk

load_dotenv()

app_start = time.time()
print(f"\n[{time.strftime('%H:%M:%S')}] [*] Starting MeetMap Backend...")

# Database lifecycle events using lifespan (modern FastAPI approach)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle"""
    # Startup
    try:
        print(f"[{time.strftime('%H:%M:%S')}] [*] Connecting to database...")
        await db.connect()
        print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Database connected")
        
        # Run migration automatically (creates tables if they don't exist)
        # This is safe because schema.sql uses "CREATE TABLE IF NOT EXISTS"
        try:
            from pathlib import Path
            schema_file = Path(__file__).parent / "database" / "schema.sql"
            if schema_file.exists():
                print(f"[{time.strftime('%H:%M:%S')}] [*] Running database migration...")
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # Parse SQL into individual statements properly
                # Handle multi-line statements by tracking when we're inside a statement
                lines = schema_sql.split('\n')
                statements = []
                current_stmt = []
                
                for line in lines:
                    stripped = line.strip()
                    # Skip COMMENT statements and empty/comment-only lines
                    if stripped.upper().startswith('COMMENT') or not stripped or stripped.startswith('--'):
                        continue
                    # Remove inline comments
                    if '--' in line:
                        line = line[:line.index('--')].strip()
                        if not line:
                            continue
                    
                    current_stmt.append(line)
                    
                    # If line ends with semicolon, we have a complete statement
                    if line.rstrip().endswith(';'):
                        stmt = ' '.join(current_stmt).strip()
                        if stmt and len(stmt) > 5:  # Ignore very short statements
                            statements.append(stmt.rstrip(';').strip())
                        current_stmt = []
                
                # If there's a remaining statement without semicolon, add it
                if current_stmt:
                    stmt = ' '.join(current_stmt).strip()
                    if stmt and len(stmt) > 5:
                        statements.append(stmt)
                
                # Separate CREATE TABLE from other statements
                create_table_statements = []
                other_statements = []
                
                for stmt in statements:
                    stmt_upper = stmt.upper().strip()
                    if stmt_upper.startswith('CREATE TABLE'):
                        create_table_statements.append(stmt)
                    elif stmt_upper.startswith('CREATE') or stmt_upper.startswith('ALTER'):
                        other_statements.append(stmt)
                
                # Execute CREATE TABLE statements first
                print(f"[{time.strftime('%H:%M:%S')}] [*] Creating tables ({len(create_table_statements)} statements)...")
                for stmt in create_table_statements:
                    try:
                        await db.execute(stmt)
                        # Extract table name for logging
                        parts = stmt.upper().split('CREATE TABLE')
                        if len(parts) > 1:
                            table_part = parts[1].strip().split()[0]
                            table_name = table_part.replace('IF', '').replace('NOT', '').replace('EXISTS', '').strip()
                            print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Table created/verified: {table_name}")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if 'already exists' not in error_msg:
                            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] Failed to create table: {e}")
                            # Show first 150 chars of statement for debugging
                            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] Statement: {stmt[:150]}...")
                
                # Then execute indexes and other statements
                if other_statements:
                    print(f"[{time.strftime('%H:%M:%S')}] [*] Creating indexes and constraints ({len(other_statements)} statements)...")
                    for stmt in other_statements:
                        try:
                            await db.execute(stmt)
                        except Exception as e:
                            error_msg = str(e).lower()
                            # These errors are often expected (already exists, etc.)
                            if 'already exists' not in error_msg:
                                # Only log if it's not a "does not exist" error (tables should exist by now)
                                if 'does not exist' in error_msg:
                                    print(f"[{time.strftime('%H:%M:%S')}] [WARNING] Index/constraint skipped (table may not exist yet): {stmt[:50]}...")
                                else:
                                    print(f"[{time.strftime('%H:%M:%S')}] [WARNING] Index/constraint may have failed: {stmt[:50]}... Error: {e}")
                
                # Verify tables
                tables = await db.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Database ready - {len(tables)} tables found")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] [WARNING] Schema file not found, skipping migration")
        except Exception as migration_error:
            print(f"[{time.strftime('%H:%M:%S')}] [WARNING] Migration error (tables may already exist): {migration_error}")
            # Continue anyway - tables might already exist
            
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [ERROR] Database connection failed: {e}")
        print(f"[{time.strftime('%H:%M:%S')}] [ERROR] Application requires database - some features may not work")
        # Don't raise - let app start but log the error clearly
    
    yield  # Application runs here
    
    # Shutdown
    try:
        await db.close()
        print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Database connection closed")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [WARNING] Error closing database: {e}")

app = FastAPI(title="MeetMap Prototype API", lifespan=lifespan)

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
print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] CORS middleware configured ({cors_elapsed:.3f}s)")

# Initialize services
service_start = time.time()
print(f"[{time.strftime('%H:%M:%S')}] [*] Initializing MeetMapService...")
meetmap_service = MeetMapService()
service_elapsed = time.time() - service_start
print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] MeetMapService initialization complete ({service_elapsed:.2f}s)")

app_elapsed = time.time() - app_start
print(f"[{time.strftime('%H:%M:%S')}] [*] Backend initialization complete! (Total: {app_elapsed:.2f}s)\n")


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


class TranscribeRequest(BaseModel):
    """Request model for transcribe endpoint"""
    audio: str  # Base64-encoded WAV audio
    user_id: str
    start: float
    end: float


@app.post("/api/transcribe")
async def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe audio using Whisper API and process it to extract nodes.
    Returns only the transcription text (nodes are processed silently).
    """
    try:
        # Validate inputs
        if not request.audio or not request.audio.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "audio is required and cannot be empty"}
            )
        
        if not request.user_id or not request.user_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "user_id is required"}
            )
        
        audio_base64 = request.audio.strip()
        user_id = request.user_id.strip()
        start = request.start
        end = request.end
        
        # Step 1: Decode base64 audio
        try:
            # Remove data URL prefix if present (e.g., "data:audio/wav;base64,")
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",", 1)[1]
            
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as decode_error:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Invalid base64 audio: {str(decode_error)}"}
            )
        
        # Step 2: Create temporary file for Whisper API
        # Whisper API requires a file, so we'll use a temporary file
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            # Step 3: Call OpenAI Whisper API
            print(f"[{time.strftime('%H:%M:%S')}] 🎤 Transcribing audio with Whisper (user: {user_id}, duration: {end - start:.2f}s)...")
            whisper_start = time.time()
            
            with open(temp_file_path, "rb") as audio_file:
                transcription_response = meetmap_service.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"  # Get plain text response
                )
            
            # Extract transcription text (handle both string and object responses)
            if isinstance(transcription_response, str):
                transcription = transcription_response.strip()
            elif hasattr(transcription_response, 'text'):
                transcription = transcription_response.text.strip()
            else:
                transcription = str(transcription_response).strip()
            
            whisper_elapsed = time.time() - whisper_start
            print(f"[{time.strftime('%H:%M:%S')}] ✅ Transcription completed in {whisper_elapsed:.2f}s: {transcription[:50]}...")
            
            if not transcription or not transcription.strip():
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Transcription is empty"}
                )
            
            # Step 4: Process transcription internally using existing endpoint logic
            # Create chunk dict matching TranscriptChunk format
            chunk_dict = {
                "text": transcription.strip(),
                "start": start,
                "end": end,
                "user_id": user_id,
                "speaker": None,  # Whisper doesn't do speaker diarization
                "chunk_id": None
            }
            
            # Call process_transcript_chunk function internally
            # This will extract nodes and save them to database
            print(f"[{time.strftime('%H:%M:%S')}] 🔄 Processing transcription to extract nodes...")
            try:
                await process_transcript_chunk(chunk_dict)
                print(f"[{time.strftime('%H:%M:%S')}] ✅ Nodes extracted and saved to database")
            except Exception as process_error:
                # Log error but still return transcription
                print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Error processing transcription: {process_error}")
                # Continue to return transcription even if node extraction failed
            
            # Step 5: Return only transcription
            return {
                "status": "success",
                "transcription": transcription.strip(),
                "start": start,
                "end": end
            }
            
        finally:
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Failed to cleanup temp file: {cleanup_error}")
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Error in transcribe_audio: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to transcribe audio: {str(e)}"}
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


@app.get("/api/graph/node/{node_id}/summary")
async def get_node_summary(node_id: str, user_id: str = Query(..., description="User ID (required)")):
    """Get conversation summary from root to this node (max 50 words)"""
    try:
        if not node_id or not node_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "node_id is required"}
            )
        
        # Skip root nodes
        if node_id.startswith("root") or node_id == "root":
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Summary not available for root nodes"}
            )
        
        graph_manager = meetmap_service.graph_manager
        
        # Get path from root to this node
        path_result = await graph_manager.get_path_to_root(node_id, user_id)
        path_node_ids = path_result.get("path", [])
        
        if not path_node_ids:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"Path not found for node: {node_id}"}
            )
        
        # Get all nodes in the path
        path_nodes = []
        for path_node_id in path_node_ids:
            node = await graph_manager.get_node(path_node_id, user_id)
            if node:
                path_nodes.append(node)
        
        if not path_nodes:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Nodes in path not found"}
            )
        
        # Extract summaries from path nodes
        node_summaries = [node.summary for node in path_nodes]
        
        # Generate summary using LLM
        summary = await meetmap_service.generate_path_summary(node_summaries)
        
        return {
            "status": "success",
            "summary": summary,
            "node_id": node_id
        }
        
    except Exception as e:
        print(f"[ERROR] Error generating node summary: {e}")
        import traceback
        traceback.print_exc()
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




class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str
    user_id: str
    image: Optional[str] = None  # Base64-encoded image (optional)


@app.post("/api/chat/ask")
async def ask_meeting_assistant(request: ChatRequest):
    """
    AI meeting assistant endpoint.
    Answers questions about the meeting or general knowledge helpful for meetings.
    Uses all node descriptions (summaries) from the user's graph as context.
    Supports optional image input for vision-based questions.
    """
    try:
        # Validate inputs
        if not request.question or not request.question.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "question is required and cannot be empty"}
            )
        
        if not request.user_id or not request.user_id.strip():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "user_id is required"}
            )
        
        question = request.question.strip()
        user_id = request.user_id.strip()
        
        # Get all nodes for the user (optional - meeting context)
        all_nodes = await db.get_all_nodes(user_id)
        
        # Extract summaries (descriptions) from nodes, skip root nodes
        node_descriptions = []
        if all_nodes:
            for node in all_nodes:
                node_id = node['id']
                summary = node.get('summary', '')
                
                # Skip root nodes
                if node_id.startswith('root') or node_id == 'root':
                    continue
                
                # Skip empty summaries
                if summary and summary.strip():
                    node_descriptions.append(summary.strip())
        
        # Build context string from node descriptions (if available)
        context_text = ""
        if node_descriptions:
            context_text = "\n".join([
                f"{i+1}. {desc}" 
                for i, desc in enumerate(node_descriptions)
            ])
        
        # Build prompt - handle both cases: with and without meeting context
        if context_text:
            prompt = f"""You are a helpful meeting assistant. The user may send you:
- Questions about the meeting/conversation
- Direct transcriptions from the meeting
- General questions or requests

Meeting Context (ideas discussed, in chronological order):
{context_text}

User Input: {question}

Instructions:
- If the input is about the meeting, use the context above to help answer
- If it's a direct transcription, acknowledge it and provide relevant insights
- If it's a general question, answer using your knowledge
- If no meeting context is needed, answer directly
- Be concise and to-the-point
- Not every input will be a question - handle statements, transcriptions, and questions appropriately"""
        else:
            prompt = f"""You are a helpful meeting assistant. The user may send you:
- Questions about meetings or collaboration
- Direct transcriptions from meetings
- General questions or requests

User Input: {question}

Instructions:
- Answer using your general knowledge
- If it's a direct transcription, acknowledge it and provide relevant insights
- If it's a question, answer it directly
- If it's a statement, acknowledge and respond appropriately
- Be concise and to-the-point
- Not every input will be a question - handle statements, transcriptions, and questions appropriately"""
        
        # Prepare user message content (text + optional image)
        user_content = [{"type": "text", "text": prompt}]
        
        # Add image if provided
        if request.image:
            # Handle base64 image - accept with or without data URL prefix
            image_data = request.image.strip()
            
            # If it already has data URL prefix, use as-is
            if image_data.startswith("data:"):
                image_url = image_data
            else:
                # Otherwise, assume it's raw base64 and add JPEG data URL prefix
                image_url = f"data:image/jpeg;base64,{image_data}"
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        
        # Call GPT-4o-mini (supports vision)
        try:
            response = meetmap_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful meeting assistant. You can receive questions, direct meeting transcriptions, or general requests. Use meeting context if available to help answer, otherwise use your general knowledge. If an image is provided, analyze it in the context of the input. Be concise and to-the-point. Not every input will be a question - handle statements, transcriptions, and questions appropriately."
                    },
                    {"role": "user", "content": user_content}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "answer": answer
            }
            
        except Exception as openai_error:
            print(f"[ERROR] OpenAI API error: {openai_error}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Failed to generate answer. Please try again later."
                }
            )
        
    except Exception as e:
        print(f"[ERROR] Error in ask_meeting_assistant: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
