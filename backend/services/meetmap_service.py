"""
MeetMap Service - Semantic Idea-Evolution Graph
Step 1: GPT extracts ideas only
Step 2: Generate embeddings
Step 3: Semantic traversal (BST-style)
Step 4: Node placement
"""

import os
import time
from typing import List, Tuple, Any, Optional
from openai import OpenAI
import json
from sentence_transformers import SentenceTransformer
from models.schemas import TranscriptChunk, NodeData, EdgeData
from services.graph_manager import GraphManager

class MeetMapService:
    """Service for building semantic idea-evolution graph"""
    
    def __init__(self):
        service_start = time.time()
        print(f"\n[{time.strftime('%H:%M:%S')}] 🚀 Initializing MeetMapService...")
        
        # Initialize OpenAI client
        client_start = time.time()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment variables."
            )
        self.client = OpenAI(api_key=api_key)
        client_elapsed = time.time() - client_start
        print(f"[{time.strftime('%H:%M:%S')}] ✅ OpenAI client initialized ({client_elapsed:.3f}s)")
        
        self.node_counter = 0
        self.root_sent = False  # Track if root node has been sent to frontend
        
        # Initialize graph manager (creates root node)
        graph_start = time.time()
        self.graph_manager = GraphManager()
        graph_elapsed = time.time() - graph_start
        print(f"[{time.strftime('%H:%M:%S')}] ✅ GraphManager initialized ({graph_elapsed:.3f}s)")
        
        # Load embedding model at startup (required for constant embedding generation)
        model_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] 📦 Loading embedding model 'all-MiniLM-L6-v2'...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        model_elapsed = time.time() - model_start
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Embedding model loaded ({model_elapsed:.2f}s)")
        
        service_elapsed = time.time() - service_start
        print(f"[{time.strftime('%H:%M:%S')}] 🎉 MeetMapService ready! (Total: {service_elapsed:.2f}s)\n")
    
    async def extract_nodes(self, chunk: TranscriptChunk) -> Tuple[List[NodeData], List[EdgeData]]:
        """
        Process a transcript chunk through the pipeline:
        1. Extract ideas (GPT only)
        2. Generate embeddings
        3. Global search + LLM placement
        4. Convert to frontend format
        
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
        # Step 3: Global search + LLM placement
        step2_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] STEP 2-3: Starting embedding generation and node placement for {len(idea_descriptions)} idea(s)...")
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
            
            # Global search for similar nodes
            search_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]     Searching for similar nodes in graph...")
            similar_nodes = self.graph_manager.find_globally_similar_nodes(
                candidate_embedding=embedding,
                exclude_node_id=None,
                filter_by_threshold=False  # Get top-K regardless of threshold
            )
            search_elapsed = time.time() - search_start
            print(f"[{time.strftime('%H:%M:%S')}]     Global search completed in {search_elapsed:.3f}s - found {len(similar_nodes)} similar node(s)")
            
            if similar_nodes:
                print(f"[{time.strftime('%H:%M:%S')}]     Top similar nodes:")
                for i, (node_id, sim_score, node) in enumerate(similar_nodes[:5], 1):
                    print(f"        {i}. '{node.summary[:60]}...' (id: {node_id}, similarity: {sim_score:.3f})")
            
            # LLM decides placement
            llm_start = time.time()
            if similar_nodes:
                print(f"[{time.strftime('%H:%M:%S')}]     Calling LLM for placement decision...")
                parent_id = await self.decide_placement(
                    candidate_summary=idea_text,
                    candidate_embedding=embedding,
                    similar_nodes=similar_nodes
                )
            else:
                # No nodes in graph (only root exists) - place under root
                parent_id = self.graph_manager.root_id
                print(f"[{time.strftime('%H:%M:%S')}]     No existing nodes found, placing under root")
            llm_elapsed = time.time() - llm_start
            print(f"[{time.strftime('%H:%M:%S')}]     Placement decision completed in {llm_elapsed:.2f}s - placing under {parent_id}")
            
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
            print(f"[{time.strftime('%H:%M:%S')}]   ✓ Idea {idx} completed in {idea_elapsed:.2f}s (embed: {embed_elapsed:.2f}s, search: {search_elapsed:.3f}s, llm: {llm_elapsed:.2f}s, place: {place_elapsed:.3f}s)")
        
        step2_elapsed = time.time() - step2_start
        print(f"[{time.strftime('%H:%M:%S')}] STEP 2-3: Completed in {step2_elapsed:.2f}s - Processed {len(new_graph_nodes)} node(s)")
        
        # Step 5: Convert graph structure to frontend format
        step5_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] STEP 5: Converting to frontend format...")
        nodes, edges = self._graph_to_frontend_format(new_graph_nodes)
        step5_elapsed = time.time() - step5_start
        print(f"[{time.strftime('%H:%M:%S')}] STEP 5: Completed in {step5_elapsed:.3f}s")
        
        total_elapsed = time.time() - pipeline_start
        print(f"[{time.strftime('%H:%M:%S')}] ✅ Pipeline complete: {len(nodes)} node(s), {len(edges)} edge(s) in {total_elapsed:.2f}s total")
        print(f"[{time.strftime('%H:%M:%S')}]   Breakdown: GPT={step1_elapsed:.2f}s, Embed+Search+LLM={step2_elapsed:.2f}s, Convert={step5_elapsed:.3f}s")
        return nodes, edges
    
    async def _extract_ideas(self, chunk: TranscriptChunk) -> List[str]:
        """
        Step 1: Extract idea descriptions from transcript chunk
        GPT's ONLY role - no graph decisions, no parent selection
        Includes context from recent chunks' nodes
        """
        gpt_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}]     Preparing GPT prompt (chunk length: {len(chunk.text)} chars)...")
        
        # Get recent chunk nodes for context (most recent 3-5 chunks)
        recent_chunks = self.graph_manager.get_recent_chunk_nodes(num_chunks=5)
        
        # Build context string from recent nodes
        context_parts = []
        if recent_chunks:
            context_parts.append("Recent conversation context (ideas from previous chunks, in order):")
            for chunk_id, nodes in recent_chunks:
                if nodes:
                    node_descriptions = [f"  - {node.summary}" for node in nodes]
                    context_parts.append(f"\nChunk {chunk_id}:")
                    context_parts.extend(node_descriptions)
            context_str = "\n".join(context_parts)
            print(f"[{time.strftime('%H:%M:%S')}]     Including context from {len(recent_chunks)} recent chunk(s) with {sum(len(nodes) for _, nodes in recent_chunks)} node(s)")
        else:
            context_str = ""
            print(f"[{time.strftime('%H:%M:%S')}]     No previous chunks found, starting fresh")
        
        prompt = f"""You are analyzing a conversation transcript chunk.

{context_str}

Current chunk: "{chunk.text}"

Your task is to extract distinct ideas, decisions, actions, or proposals from the current chunk.

Consider the conversation context above to understand:
- Where the conversation is heading
- Whether ideas in this chunk are continuations, refinements, or new directions
- What would help users understand the conversation flow in a graph

Extract each distinct idea as a short, self-contained summary (1-2 sentences max).
Focus on:
- New ideas or proposals
- Decisions being made
- Actions being discussed
- Important points raised
- Ideas that add value to understanding the conversation flow

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
- Do NOT reference existing nodes by ID
- Just extract clean, minimal idea summaries
- Consider context but extract ideas naturally from the current chunk

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
            # Get cluster info
            cluster_id = graph_node.metadata.get("cluster_id")
            cluster_color = self.graph_manager.get_cluster_color(cluster_id) if cluster_id is not None else None
            
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
                    "cluster_id": cluster_id,
                    "cluster_color": cluster_color,
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
    
    async def decide_placement(
        self,
        candidate_summary: str,
        candidate_embedding: List[float],
        similar_nodes: List[tuple[str, float, Any]]  # (node_id, similarity, GraphNode)
    ) -> str:
        """
        Use LLM to decide node placement based on global similarity search
        
        Args:
            candidate_summary: Text description of new node
            candidate_embedding: Embedding vector of new node
            similar_nodes: List of (node_id, similarity, node) tuples from global search
        
        Returns:
            parent_id where node should be placed
        """
        # Format similar nodes for prompt
        similar_nodes_text = ""
        for idx, (node_id, similarity, node) in enumerate(similar_nodes, 1):
            path = self.graph_manager.get_node_path(node_id)
            path_str = " → ".join(path) if path else "root"
            similar_nodes_text += f"{idx}. Node ID: {node_id}\n"
            similar_nodes_text += f"   Text: \"{node.summary}\"\n"
            similar_nodes_text += f"   Similarity: {similarity:.3f}\n"
            similar_nodes_text += f"   Depth: {node.depth}\n"
            similar_nodes_text += f"   Path: {path_str}\n"
            similar_nodes_text += f"   Parent: {node.parent_id}\n\n"
        
        prompt = f"""You are analyzing a conversation graph. A new idea needs placement.

New idea: "{candidate_summary}"

Similar existing nodes (found via semantic similarity search):
{similar_nodes_text}

The meeting will be conversational based, so you dont have to be very rigid in deciding the placement, take it as how the conversation is progressing in a natural manner, no hard and fast rule. The goal is to construct a graph that accurately shows how the conversation progresses as a graph.

Decide placement:
- "continuation":
  The new idea deepens, elaborates, narrows, supports or adds detail to an existing idea.
  its talking about the same idea, can be an alternative but falls in the same space when taking it conceptually and conversationaly
  It cannot stand alone without the target idea.

  for example if one node says we
  → Place as CHILD of the target_node.

- "branch":
  The new idea is different and would take the conversation to a different side
  
  It does not depend on the target idea, but shares the same parent topic.
  → Place as SIBLING of the target_node
    (i.e., CHILD of target_node's parent).

- "resolution":
  The new idea directly answers, decides, or resolves an open question,
  uncertainty, or problem raised by the target idea.
  → Place as CHILD of the target_node.

Return JSON:
{{
  "decision": "continuation|branch|resolution",
  "target_node_id": "node_X",  // Which existing node it relates to (from list above)
  "parent_id": "node_Y",  // Where to place (see IMPORTANT rules below)
  "reasoning": "brief explanation"
}}

IMPORTANT:
- For "continuation" or "resolution": parent_id should be the target_node_id (place as child of target)
- For "branch": parent_id should be the target_node_id's parent (place as sibling of target, under same topic)
- target_node_id must be one of the node IDs from the similar nodes list above
- parent_id must exist in the graph

Return ONLY the JSON object, no other text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at understanding conversational flow and semantic relationships. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON (handle markdown code blocks)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            extracted = json.loads(content)
            decision = extracted.get("decision", "branch")
            target_node_id = extracted.get("target_node_id")
            parent_id = extracted.get("parent_id")
            reasoning = extracted.get("reasoning", "")
            
            # Validate target_node_id exists in similar_nodes
            valid_node_ids = {node_id for node_id, _, _ in similar_nodes}
            if target_node_id and target_node_id not in valid_node_ids:
                print(f"      ⚠️ LLM returned invalid target_node_id: {target_node_id}, using fallback")
                target_node_id = similar_nodes[0][0]  # Use first similar node
            
            # Enforce placement rules based on decision type
            if target_node_id:
                target_node = self.graph_manager.get_node(target_node_id)
                if target_node:
                    if decision == "continuation" or decision == "resolution":
                        # Place as child of target node
                        parent_id = target_node_id
                    elif decision == "branch":
                        # Place as sibling of target (child of target's parent)
                        parent_id = target_node.parent_id if target_node.parent_id else self.graph_manager.root_id
                    else:
                        # Unknown decision type, use target's parent as fallback
                        parent_id = target_node.parent_id if target_node.parent_id else self.graph_manager.root_id
                else:
                    # Target node doesn't exist, use root as fallback
                    parent_id = self.graph_manager.root_id
            else:
                # No target_node_id, use root as fallback
                parent_id = self.graph_manager.root_id
            
            # Final validation: ensure parent_id exists in graph
            if not self.graph_manager.get_node(parent_id):
                print(f"      ⚠️ LLM returned invalid parent_id: {parent_id}, using fallback")
                if target_node_id:
                    target_node = self.graph_manager.get_node(target_node_id)
                    if target_node:
                        parent_id = target_node.parent_id if target_node.parent_id else self.graph_manager.root_id
                    else:
                        parent_id = self.graph_manager.root_id
                else:
                    parent_id = self.graph_manager.root_id
            
            # Get parent node description for logging
            parent_node = self.graph_manager.get_node(parent_id)
            parent_description = parent_node.summary if parent_node else "N/A"
            
            print(f"      → LLM Decision:")
            print(f"        Decision type: {decision}")
            print(f"        Target node: {target_node_id}")
            print(f"        Parent node: '{parent_description}' (id: {parent_id})")
            print(f"        Reasoning: {reasoning}")
            return parent_id
            
        except Exception as e:
            print(f"      ❌ Error in LLM placement decision: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: use most similar node's parent
            if similar_nodes:
                best_match_id, best_similarity, best_node = similar_nodes[0]
                return best_node.parent_id if best_node.parent_id else self.graph_manager.root_id
            return self.graph_manager.root_id
    
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
