"""
MeetMap Prototype - Main FastAPI Application
Simple pipeline: Receive chunk → Extract nodes → Return to frontend
"""

from fastapi import FastAPI
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

# Initialize services
meetmap_service = MeetMapService()


@app.get("/")
async def root():
    return {"message": "MeetMap Prototype API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/transcript")
async def process_transcript_chunk(chunk: dict):
    """Process a single transcript chunk and return nodes/edges"""
    try:
        transcript_chunk = TranscriptChunk(**chunk)
        
        # Extract nodes and edges with full context
        nodes, edges = await meetmap_service.extract_nodes(transcript_chunk)
        
        print(f"✅ Extracted {len(nodes)} node(s) and {len(edges)} edge(s) from chunk")
        
        return {
            "status": "success",
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges]
        }
        
    except Exception as e:
        print(f"❌ Error processing chunk: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )






if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
