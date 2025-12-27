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


class NodeData(BaseModel):
    """MeetMap node (idea/action/decision)"""
    id: str
    text: str
    type: str  # "decision", "action", "idea", "proposal"
    speaker: Optional[str] = None
    topic: Optional[str] = None
    topic_id: Optional[str] = None
    timestamp: float
    confidence: float = 1.0
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

