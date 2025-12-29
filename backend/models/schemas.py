"""
Pydantic models for data structures
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TranscriptChunk(BaseModel):
    """Transcript chunk with timestamps"""
    speaker: Optional[str] = None  # Will be None if not diarized
    start: float
    end: float
    text: str
    chunk_id: Optional[str] = None


class TopicData(BaseModel):
    """Topic detection result"""
    topic: str
    start: float
    end: float
    confidence: float
    keywords: List[str] = []
    topic_id: Optional[str] = None


class GraphNode(BaseModel):
    """Graph node representing a single idea in the semantic graph"""
    id: str
    embedding: List[float]  # Vector representation (core identity)
    summary: str  # Short text description (for UI/debug)
    parent_id: Optional[str] = None  # Primary parent node ID
    children_ids: List[str] = []  # List of child node IDs
    depth: int = 0  # Distance from root
    last_updated: float  # Timestamp
    metadata: dict = {}  # Additional data (chunk_id, timestamp, etc.)


class NodeData(BaseModel):
    """Frontend-compatible node format (for visualization)"""
    id: str
    text: str
    type: str  # "decision", "action", "idea", "proposal"
    speaker: Optional[str] = None
    topic: Optional[str] = None
    topic_id: Optional[str] = None
    timestamp: float
    confidence: float = 1.0
    idea_id: Optional[str] = None  # Groups related nodes (no versioning)
    metadata: dict = {}


class EdgeData(BaseModel):
    """Connection between nodes"""
    from_node: str
    to_node: str
    type: str  # "chronological", "thematic", "participant", "reference", "continues", "branches"
    strength: float = 1.0
    metadata: dict = {}


class MergedData(BaseModel):
    """Merged topic and node data"""
    topics: List[TopicData]
    nodes: List[NodeData]
    edges: List[EdgeData]
    topic_node_mapping: dict  # topic_id -> [node_ids]


class PipelineResponse(BaseModel):
    """Complete pipeline response"""
    transcript_chunk: TranscriptChunk
    topics: List[TopicData]
    nodes: List[NodeData]
    merged: MergedData

