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
            
            # Global search for similar nodes (filtered by meeting_id)
            search_start = time.time()
            print(f"[{time.strftime('%H:%M:%S')}]     Searching for similar nodes in graph...")
            meeting_id_for_search = chunk.meeting_id if chunk.meeting_id else None
            if not meeting_id_for_search:
                raise ValueError("meeting_id is required for similarity search")
            similar_nodes = await self.graph_manager.find_globally_similar_nodes(
                candidate_embedding=embedding,
                exclude_node_id=None,
                filter_by_threshold=False,  # Get top-K regardless of threshold
                meeting_id=meeting_id_for_search  # Filter by meeting_id
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
                    similar_nodes=similar_nodes,
                    meeting_id=chunk.meeting_id
                )
                # Validate: ensure parent_id is not the node being created (prevent cycles)
                # Also ensure it's not creating a cycle by checking if parent exists
                parent_node = await self.graph_manager.get_node(parent_id, meeting_id=chunk.meeting_id)
                if not parent_node:
                    print(f"[{time.strftime('%H:%M:%S')}]     [WARNING] LLM selected invalid parent {parent_id}, falling back to root")
                    parent_id = root_id
            else:
                # No nodes in graph - place under meeting-specific root
                if chunk.meeting_id:
                    # Get or create meeting-specific root
                    meeting_root = await self.graph_manager.get_root(meeting_id=chunk.meeting_id)
                    if not meeting_root:
                        # Create meeting-specific root
                        await self.graph_manager._initialize_root(meeting_id=chunk.meeting_id)
                        meeting_root = await self.graph_manager.get_root(meeting_id=chunk.meeting_id)
                    parent_id = meeting_root.id if meeting_root else f"root_meeting_{chunk.meeting_id}"
                else:
                    raise ValueError("meeting_id is required for node placement")
                print(f"[{time.strftime('%H:%M:%S')}]     No existing nodes found, placing under root: {parent_id}")
            llm_elapsed = time.time() - llm_start
            print(f"[{time.strftime('%H:%M:%S')}]     Placement decision completed in {llm_elapsed:.2f}s - placing under {parent_id}")
            
            # Place node in graph
            place_start = time.time()
            self.node_counter += 1
            # Make node IDs unique per meeting to avoid conflicts
            meeting_id_for_node = chunk.meeting_id if chunk.meeting_id else None
            if not meeting_id_for_node:
                raise ValueError("meeting_id is required for node creation")
            node_id = f"node_{meeting_id_for_node}_{self.node_counter}"
            
            # Include meeting_id in metadata
            node_metadata = {
                "chunk_id": chunk.chunk_id,
                "timestamp": chunk.start,
                "end_time": chunk.end,
                "speaker": chunk.speaker,
                "meeting_id": chunk.meeting_id
            }
            
            graph_node = await self.graph_manager.add_node(
                node_id=node_id,
                embedding=embedding,
                summary=idea_text,
                parent_id=parent_id,
                meeting_id=meeting_id_for_node,
                metadata=node_metadata
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
        nodes, edges = await self._graph_to_frontend_format(new_graph_nodes, meeting_id=chunk.meeting_id)
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
        meeting_id_for_context = chunk.meeting_id if chunk.meeting_id else None
        if not meeting_id_for_context:
            raise ValueError("meeting_id is required for context retrieval")
        recent_chunks = await self.graph_manager.get_recent_chunk_nodes(num_chunks=5, meeting_id=meeting_id_for_context)
        
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
    
    async def _graph_to_frontend_format(
        self,
        new_graph_nodes: List,
        meeting_id: Optional[str] = None
    ) -> Tuple[List[NodeData], List[EdgeData]]:
        """
        Convert graph nodes to frontend-compatible format
        Creates NodeData and EdgeData from parent-child relationships
        Includes root node only once (on first chunk)
        
        Args:
            new_graph_nodes: List of newly created GraphNode objects
            meeting_id: Meeting ID to get meeting-specific root
        """
        nodes = []
        edges = []
        
        if not meeting_id:
            raise ValueError("meeting_id is required")
        
        # Determine root ID (meeting-specific)
        root_id = f"root_meeting_{meeting_id}"
        
        # Include root node if it exists and we have new nodes
        # Check if any new node has this root as parent (indicates root was just created or is needed)
        if len(new_graph_nodes) > 0:
            root = await self.graph_manager.get_root(meeting_id=meeting_id)
            if root:
                # Check if any new node connects to this root
                has_root_connection = any(
                    node.parent_id == root.id for node in new_graph_nodes
                )
                if has_root_connection:
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
                # Determine if parent is a root node (meeting-specific)
                is_root_parent = graph_node.parent_id == root_id
                
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
        
        return nodes, edges
    
    async def decide_placement(
        self,
        candidate_summary: str,
        candidate_embedding: List[float],
        similar_nodes: List[tuple[str, float, Any]],  # (node_id, similarity, GraphNode)
        meeting_id: Optional[str] = None
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
        meeting_id_for_path = meeting_id if meeting_id else None
        if not meeting_id_for_path:
            raise ValueError("meeting_id is required for path retrieval")
        for idx, (node_id, similarity, node) in enumerate(similar_nodes, 1):
            path = await self.graph_manager.get_node_path(node_id, meeting_id_for_path)
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
            
            # Get appropriate root ID (meeting-specific)
            meeting_id_for_placement = meeting_id if meeting_id else None
            if not meeting_id_for_placement:
                raise ValueError("meeting_id is required for placement")
            meeting_root = await self.graph_manager.get_root(meeting_id=meeting_id_for_placement)
            fallback_root_id = meeting_root.id if meeting_root else f"root_meeting_{meeting_id_for_placement}"
            
            # Enforce placement rules based on decision type
            if target_node_id:
                target_node = await self.graph_manager.get_node(target_node_id, meeting_id_for_placement)
                if target_node:
                    if decision == "continuation" or decision == "resolution":
                        # Place as child of target node
                        parent_id = target_node_id
                    elif decision == "branch":
                        # Place as sibling of target (child of target's parent)
                        parent_id = target_node.parent_id if target_node.parent_id else fallback_root_id
                    else:
                        # Unknown decision type, use target's parent as fallback
                        parent_id = target_node.parent_id if target_node.parent_id else fallback_root_id
                else:
                    # Target node doesn't exist, use root as fallback
                    parent_id = fallback_root_id
            else:
                # No target_node_id, use root as fallback
                parent_id = fallback_root_id
            
            # Final validation: ensure parent_id exists in graph
            parent_check = await self.graph_manager.get_node(parent_id, meeting_id_for_placement)
            if not parent_check:
                print(f"      ⚠️ LLM returned invalid parent_id: {parent_id}, using fallback")
                if target_node_id:
                    target_node = await self.graph_manager.get_node(target_node_id, meeting_id_for_placement)
                    if target_node:
                        parent_id = target_node.parent_id if target_node.parent_id else fallback_root_id
                    else:
                        parent_id = fallback_root_id
                else:
                    parent_id = fallback_root_id
            
            # Get parent node description for logging
            parent_node = await self.graph_manager.get_node(parent_id, meeting_id_for_placement)
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
            # Get appropriate root ID (meeting-specific)
            meeting_id_for_fallback = meeting_id if meeting_id else None
            if not meeting_id_for_fallback:
                raise ValueError("meeting_id is required for fallback")
            meeting_root = await self.graph_manager.get_root(meeting_id=meeting_id_for_fallback)
            fallback_root_id = meeting_root.id if meeting_root else f"root_meeting_{meeting_id_for_fallback}"
            # Fallback: use most similar node's parent
            if similar_nodes:
                best_match_id, best_similarity, best_node = similar_nodes[0]
                return best_node.parent_id if best_node.parent_id else fallback_root_id
            return fallback_root_id
    
    async def get_graph_summary(self, meeting_id: str) -> dict:
        """Get summary of current graph state (for debugging)"""
        all_nodes = await self.graph_manager.get_all_nodes(meeting_id=meeting_id)
        return {
            "total_nodes": len(all_nodes),
            "root_id": f"root_meeting_{meeting_id}",
            "max_depth": max([n.depth for n in all_nodes]) if all_nodes else 0,
            "nodes_by_depth": {
                depth: len([n for n in all_nodes if n.depth == depth])
                for depth in range(max([n.depth for n in all_nodes]) + 1) if all_nodes
            }
        }
    
    async def generate_path_summary(self, node_summaries: List[str]) -> str:
        """
        Generate a concise summary (max 50 words) of conversation path
        
        Args:
            node_summaries: List of node summaries from root to target node
        
        Returns:
            Summary string (max 50 words)
        """
        if not node_summaries:
            return "No conversation content available."
        
        # Filter out root node summary if it's generic
        filtered_summaries = [
            s for s in node_summaries 
            if s and s.lower() not in ["meeting start", "root", ""]
        ]
        
        if not filtered_summaries:
            return "Conversation started but no ideas discussed yet."
        
        # Build prompt
        conversation_text = "\n".join([
            f"{i+1}. {summary}" 
            for i, summary in enumerate(filtered_summaries)
        ])
        
        prompt = f"""You are summarizing a conversation that progressed through these ideas:

{conversation_text}

Generate a concise, flowing summary (maximum 50 words) of the entire conversation up to this point. 
Make it read like a natural narrative of what was discussed.

IMPORTANT: 
- Maximum 50 words
- Make it flow naturally
- Focus on the progression of ideas
- Return ONLY the summary text, no numbering, no formatting, no quotes

Return ONLY the summary text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise, flowing summaries of conversations. Always return exactly what is requested, no extra formatting."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100  # Limit tokens to enforce 50-word limit
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Remove any quotes or formatting
            summary = summary.strip('"').strip("'").strip()
            
            # Enforce 50-word limit (safety check)
            words = summary.split()
            if len(words) > 50:
                summary = " ".join(words[:50]) + "..."
            
            return summary
            
        except Exception as e:
            print(f"[ERROR] Error generating path summary: {e}")
            # Fallback: simple concatenation
            return ". ".join(filtered_summaries[:3]) + "."
