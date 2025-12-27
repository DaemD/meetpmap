"""
MeetMap Prototype - Main FastAPI Application
Simple pipeline: Receive chunk → Extract nodes → Send to frontend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv
import os

from services.meetmap_service import MeetMapService
from models.schemas import TranscriptChunk

load_dotenv()

app = FastAPI(title="MeetMap Prototype API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
meetmap_service = MeetMapService()

# Store active connections
active_connections: list[WebSocket] = []


@app.get("/")
async def root():
    return {"message": "MeetMap Prototype API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "transcript_chunk":
                await process_chunk(data["data"], websocket)
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {data.get('type')}"
                })
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def process_chunk(transcript_chunk: dict, websocket: WebSocket):
    """
    Simple pipeline: Extract nodes from chunk and send to frontend
    """
    try:
        chunk = TranscriptChunk(**transcript_chunk)
        
        # Extract nodes
        nodes = await meetmap_service.extract_nodes(chunk)
        
        # Send nodes to frontend
        response = {
            "type": "new_nodes",
            "data": {
                "nodes": [node.dict() for node in nodes]
            }
        }
        
        print(f"✅ Extracted {len(nodes)} node(s) from chunk")
        await websocket.send_json(response)
        
    except Exception as e:
        print(f"❌ Error processing chunk: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
