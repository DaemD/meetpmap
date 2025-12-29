"""
Context Manager - Accumulates chunks and nodes for full-context analysis
"""

from typing import List, Dict
from models.schemas import TranscriptChunk, NodeData, EdgeData


class ContextManager:
    """Manages conversation context: chunks and nodes"""
    
    def __init__(self):
        self.chunks_buffer: List[TranscriptChunk] = []
        self.all_nodes: List[NodeData] = []
        self.all_edges: List[EdgeData] = []
        self.idea_counter = 0  # For generating idea_id
    
    def add_chunk(self, chunk: TranscriptChunk):
        """Add chunk to buffer"""
        self.chunks_buffer.append(chunk)
        print(f"📦 Added chunk to buffer. Total chunks: {len(self.chunks_buffer)}")
    
    def add_node(self, node: NodeData):
        """Add node to registry"""
        self.all_nodes.append(node)
        print(f"📝 Added node to registry. Total nodes: {len(self.all_nodes)}")
    
    def add_edge(self, edge: EdgeData):
        """Add edge to registry"""
        self.all_edges.append(edge)
        print(f"🔗 Added edge to registry. Total edges: {len(self.all_edges)}")
    
    def get_full_context(self) -> Dict:
        """Get full context: all chunks + all existing nodes"""
        return {
            "chunks": [chunk.model_dump() for chunk in self.chunks_buffer],
            "existing_nodes": [node.model_dump() for node in self.all_nodes],
            "existing_edges": [edge.model_dump() for edge in self.all_edges]
        }
    
    def get_next_idea_id(self) -> str:
        """Generate next idea_id"""
        self.idea_counter += 1
        return f"idea_{self.idea_counter}"
    
    def reset(self):
        """Reset context (for new meeting)"""
        self.chunks_buffer = []
        self.all_nodes = []
        self.all_edges = []
        self.idea_counter = 0

