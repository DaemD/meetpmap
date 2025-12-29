"""
MeetMap Service - Semantic Idea-Evolution Graph
Step 1: GPT extracts ideas only
Step 2: Generate embeddings
Step 3: Semantic traversal (BST-style)
Step 4: Node placement
"""

import os
import time
from typing import List, Tuple
from openai import OpenAI
import json
from sentence_transformers import SentenceTransformer
from models.schemas import TranscriptChunk, NodeData, EdgeData
from services.graph_manager import GraphManager

class MeetMapService:
    """Service for building semantic idea-evolution graph"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment variables."
            )
        self.client = OpenAI(api_key=api_key)
        self.node_counter = 0
        self.root_sent = False  # Track if root node has been sent to frontend
        
        # Initialize graph manager (creates root node)
        self.graph_manager = GraphManager()
        
        # Initialize embedding model
        start_time = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 📦 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        elapsed = time.time() - start_time
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Embedding model loaded (took {elapsed:.2f}s)")
    
    async def extract_nodes(self, chunk: TranscriptChunk) -> Tuple[List[NodeData], List[EdgeData]]:
        """
        Process a transcript chunk through the pipeline:
        1. Extract ideas (GPT only)
        2. Generate embeddings
        3. Traverse graph semantically
        4. Place nodes
        5. Convert to frontend format
        
        Returns: (nodes, edges) in frontend-compatible format
        """
        pipeline_start = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] 📥 Processing chunk: {chunk.text[:50]}...")
        
        # Step 1: Extract ideas using GPT (only role of GPT)
        step1_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] STEP 1: Starting GPT idea extraction...")
        idea_descriptions = await self._extract_ideas(chunk)
        step1_elapsed = time.time() - step1_start
        print(f"[{time.strftime('%H:%M:%S')}] STEP 1: Completed in {step1_elapsed:.2f}s - Extracted {len(idea_descriptions)} idea(s)")
        
        if not idea_descriptions:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ No ideas extracted from chunk")
            return [], []
        
        # Step 2: Generate embeddings for each idea
        # Step 3 & 4: Traverse and place nodes
        step2_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] STEP 2-4: Starting embedding generation and node placement for {len(idea_descriptions)} idea(s)...")
        new_graph_nodes = []
        
        for idx, idea_text in enumerate(idea_descriptions, 1):
            idea_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]   Processing idea {idx}/{len(idea_descriptions)}: {idea_text[:50]}...")
            
            # Generate embedding
            embed_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]     Generating embedding...")
            embedding = self.embedding_model.encode(idea_text).tolist()
            embed_elapsed = time.time() - embed_start
            print(f"[{time.strftime('%H:%M:%S')}]     Embedding generated in {embed_elapsed:.2f}s (embedding dim: {len(embedding)})")
            
            # Traverse graph to find placement
            traverse_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]     Traversing graph to find placement...")
            parent_id = self.graph_manager.traverse_and_place(
                candidate_embedding=embedding,
                candidate_summary=idea_text
            )
            traverse_elapsed = time.time() - traverse_start
            print(f"[{time.strftime('%H:%M:%S')}]     Traversal completed in {traverse_elapsed:.3f}s - placing under {parent_id}")
            
            # Place node in graph
            place_start = time.time()
            self.node_counter += 1
            node_id = f"node_{self.node_counter}"
            
            graph_node = self.graph_manager.add_node(
                node_id=node_id,
                embedding=embedding,
                summary=idea_text,
                parent_id=parent_id,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "timestamp": chunk.start,
                    "end_time": chunk.end,
                    "speaker": chunk.speaker
                }
            )
            place_elapsed = time.time() - place_start
            print(f"[{time.strftime('%H:%M:%S')}]     Node placement completed in {place_elapsed:.3f}s")
            
            new_graph_nodes.append(graph_node)
            idea_elapsed = time.time() - idea_start
            print(f"[{time.strftime('%H:%M:%S')}]   ✓ Idea {idx} completed in {idea_elapsed:.2f}s (embed: {embed_elapsed:.2f}s, traverse: {traverse_elapsed:.3f}s, place: {place_elapsed:.3f}s)")
        
        step2_elapsed = time.time() - step2_start
        print(f"[{time.strftime('%H:%M:%S')}] STEP 2-4: Completed in {step2_elapsed:.2f}s - Processed {len(new_graph_nodes)} node(s)")
        
        # Step 5: Convert graph structure to frontend format
        step5_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] STEP 5: Converting to frontend format...")
        nodes, edges = self._graph_to_frontend_format(new_graph_nodes)
        step5_elapsed = time.time() - step5_start
        print(f"[{time.strftime('%H:%M:%S')}] STEP 5: Completed in {step5_elapsed:.3f}s")
        
        total_elapsed = time.time() - pipeline_start
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Pipeline complete: {len(nodes)} node(s), {len(edges)} edge(s) in {total_elapsed:.2f}s total")
        print(f"[{time.strftime('%H:%M:%S')}]   Breakdown: GPT={step1_elapsed:.2f}s, Embed+Place={step2_elapsed:.2f}s, Convert={step5_elapsed:.3f}s")
        return nodes, edges
    
    async def _extract_ideas(self, chunk: TranscriptChunk) -> List[str]:
        """
        Step 1: Extract idea descriptions from transcript chunk
        GPT's ONLY role - no graph decisions, no parent selection
        """
        gpt_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}]     Preparing GPT prompt (chunk length: {len(chunk.text)} chars)...")
        
        prompt = f"""You are analyzing a conversation transcript chunk.

Your task is to extract distinct ideas, decisions, actions, or proposals from this chunk.

Transcript chunk: "{chunk.text}"

Extract each distinct idea as a short, self-contained summary (1-2 sentences max).
Focus on:
- New ideas or proposals
- Decisions being made
- Actions being discussed
- Important points raised

Return JSON:
{{
  "ideas": [
    "idea description 1",
    "idea description 2",
    ...
  ]
}}

IMPORTANT:
- Return ONLY idea descriptions (short summaries)
- Do NOT make any decisions about graph structure
- Do NOT decide parent-child relationships
- Do NOT reference existing nodes
- Just extract clean, minimal idea summaries

Return ONLY the JSON object, no other text."""

        try:
            api_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]     Calling OpenAI API (model: gpt-4o-mini)...")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting clear, concise ideas from conversation transcripts. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            api_elapsed = time.time() - api_start
            print(f"[{time.strftime('%H:%M:%S')}]     OpenAI API responded in {api_elapsed:.2f}s")
            
            parse_start = time.time()
            content = response.choices[0].message.content.strip()
            
            # Parse JSON (handle markdown code blocks)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            extracted = json.loads(content)
            ideas = extracted.get("ideas", [])
            
            # Filter out empty ideas
            ideas = [idea.strip() for idea in ideas if idea.strip()]
            parse_elapsed = time.time() - parse_start
            print(f"[{time.strftime('%H:%M:%S')}]     Parsed response in {parse_elapsed:.3f}s - found {len(ideas)} idea(s)")
            
            total_elapsed = time.time() - gpt_start
            print(f"[{time.strftime('%H:%M:%S')}]     GPT extraction total: {total_elapsed:.2f}s (API: {api_elapsed:.2f}s, parse: {parse_elapsed:.3f}s)")
            
            return ideas
            
        except Exception as e:
            elapsed = time.time() - gpt_start
            print(f"[{time.strftime('%H:%M:%S')}]     ❌ Error extracting ideas after {elapsed:.2f}s: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _graph_to_frontend_format(
        self,
        new_graph_nodes: List
    ) -> Tuple[List[NodeData], List[EdgeData]]:
        """
        Convert graph nodes to frontend-compatible format
        Creates NodeData and EdgeData from parent-child relationships
        Includes root node only once (on first chunk)
        """
        nodes = []
        edges = []
        
        # Include root node only once (on first chunk with new nodes)
        if not self.root_sent and len(new_graph_nodes) > 0:
            root = self.graph_manager.get_root()
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
            self.root_sent = True
        
        for graph_node in new_graph_nodes:
            # Convert GraphNode to NodeData
            node_data = NodeData(
                id=graph_node.id,
                text=graph_node.summary,
                type="idea",  # Default type
                speaker=graph_node.metadata.get("speaker"),
                timestamp=graph_node.metadata.get("timestamp", 0.0),
                confidence=1.0,
                metadata={
                    "depth": graph_node.depth,
                    "parent_id": graph_node.parent_id,
                    "children_count": len(graph_node.children_ids),
                    **graph_node.metadata
                }
            )
            nodes.append(node_data)
            
            # Create edge from parent to this node
            if graph_node.parent_id:
                    edge = EdgeData(
                    from_node=graph_node.parent_id,
                    to_node=graph_node.id,
                    type="extends" if graph_node.parent_id != "root" else "root",
                    strength=1.0,
                    metadata={
                        "relationship": "parent_child"
                    }
                    )
                    edges.append(edge)
        
        return nodes, edges
    
    def get_graph_summary(self) -> dict:
        """Get summary of current graph state (for debugging)"""
        all_nodes = self.graph_manager.get_all_nodes()
        return {
            "total_nodes": len(all_nodes),
            "root_id": self.graph_manager.root_id,
            "max_depth": max([n.depth for n in all_nodes]) if all_nodes else 0,
            "nodes_by_depth": {
                depth: len([n for n in all_nodes if n.depth == depth])
                for depth in range(max([n.depth for n in all_nodes]) + 1) if all_nodes
            }
        }
