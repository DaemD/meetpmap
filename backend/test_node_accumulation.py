"""
Test script to verify nodes are accumulating properly
"""
import asyncio
import os
from dotenv import load_dotenv
from services.meetmap_service import MeetMapService
from models.schemas import TranscriptChunk

load_dotenv()

async def test():
    service = MeetMapService()
    
    print("Initial nodes:", len(service.nodes))
    print("Initial counter:", service.node_counter)
    
    # Simulate multiple chunks
    chunks = [
        TranscriptChunk(start=0, end=5, text="We need to finalize the budget.", chunk_id="chunk_1"),
        TranscriptChunk(start=5, end=10, text="Let's set a deadline for next week.", chunk_id="chunk_2"),
        TranscriptChunk(start=10, end=15, text="I propose we review the timeline.", chunk_id="chunk_3"),
    ]
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Processing chunk {i} ---")
        nodes = await service.extract_nodes(chunk)
        print(f"Extracted {len(nodes)} nodes from chunk {i}")
        print(f"Total nodes now: {len(service.nodes)}")
        print(f"Node counter: {service.node_counter}")
        print("Node IDs:", [n.id for n in service.nodes])
        print("Node texts:", [n.text for n in service.nodes])
    
    print(f"\n=== Final State ===")
    print(f"Total nodes: {len(service.nodes)}")
    print(f"Node counter: {service.node_counter}")
    for node in service.nodes:
        print(f"  - {node.id}: {node.text} ({node.type})")

if __name__ == "__main__":
    asyncio.run(test())











