"""
Test script for the MeetMap pipeline
Run this to verify the pipeline works correctly
"""

import asyncio
import json
from services.stt_service import STTService
from services.talktraces_service import TalkTracesService
from services.meetmap_service import MeetMapService
from services.merge_service import MergeService
from models.schemas import TranscriptChunk

async def test_pipeline():
    """Test the complete pipeline with sample data"""
    
    # Initialize services
    stt_service = STTService()
    talktraces_service = TalkTracesService()
    meetmap_service = MeetMapService()
    merge_service = MergeService()
    
    # Sample transcript chunks
    test_chunks = [
        {
            "speaker": None,
            "start": 0.0,
            "end": 5.2,
            "text": "We need to finalize the budget for next quarter."
        },
        {
            "speaker": None,
            "start": 5.3,
            "end": 10.0,
            "text": "Let's set a deadline for next week. I'll assign this task to the finance team."
        },
        {
            "speaker": None,
            "start": 10.1,
            "end": 15.5,
            "text": "I propose we review the timeline and allocate resources accordingly. We should also consider the marketing budget."
        }
    ]
    
    print("🧪 Testing MeetMap Pipeline\n")
    print("=" * 50)
    
    all_topics = []
    all_nodes = []
    
    for i, chunk_data in enumerate(test_chunks, 1):
        print(f"\n📝 Processing Chunk {i}:")
        print(f"   Text: {chunk_data['text'][:50]}...")
        
        chunk = TranscriptChunk(**chunk_data)
        
        # 1. TalkTraces: Topic Detection
        print("\n   🔍 TalkTraces: Detecting topics...")
        topics = await talktraces_service.detect_topics(chunk)
        all_topics.extend(topics)
        for topic in topics:
            print(f"      ✓ Topic: {topic.topic} (confidence: {topic.confidence:.2f})")
        
        # 2. MeetMap: Node Extraction
        print("\n   🗺️  MeetMap: Extracting nodes...")
        nodes = await meetmap_service.extract_nodes(chunk)
        all_nodes.extend(nodes)
        for node in nodes:
            print(f"      ✓ {node.type.upper()}: {node.text[:50]}...")
        
        # 3. Merge: Cross-reference
        print("\n   🔗 Merge: Cross-referencing...")
        merged = await merge_service.merge_topics_and_nodes(topics, nodes)
        print(f"      ✓ Created {len(merged['edges'])} connections")
        
        print("\n" + "-" * 50)
    
    # Summary
    print("\n📊 Pipeline Summary:")
    print(f"   Total Topics: {len(all_topics)}")
    print(f"   Total Nodes: {len(all_nodes)}")
    
    # Generate final edges
    edges = meetmap_service.generate_edges()
    print(f"   Total Connections: {len(edges)}")
    
    print("\n✅ Pipeline test completed successfully!")
    
    return {
        "topics": [t.dict() for t in all_topics],
        "nodes": [n.dict() for n in all_nodes],
        "edges": [e.dict() for e in edges]
    }

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for OpenAI API key
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("   Please create a .env file with your OpenAI API key")
        exit(1)
    
    # Run test
    result = asyncio.run(test_pipeline())
    
    # Save results
    with open("test_results.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\n💾 Results saved to test_results.json")







