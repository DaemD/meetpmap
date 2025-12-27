"""
MeetMap Service - Simple Node Extraction
Extracts nodes (decision, action, idea, proposal) from each transcript chunk
"""

import os
from typing import List
from openai import OpenAI
import json
from models.schemas import TranscriptChunk, NodeData

class MeetMapService:
    """Service for extracting nodes from transcript chunks"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment variables."
            )
        self.client = OpenAI(api_key=api_key)
        self.node_counter = 0
    
    async def extract_nodes(self, chunk: TranscriptChunk) -> List[NodeData]:
        """
        Extract nodes from a transcript chunk.
        Returns list of nodes (decision, action, idea, proposal)
        """
        nodes = await self._llm_extract_nodes(chunk)
        return nodes
    
    async def _llm_extract_nodes(self, chunk: TranscriptChunk) -> List[NodeData]:
        """Use LLM to extract nodes from transcript chunk"""
        
        prompt = f"""From the following transcript snippet, extract all decisions, actions, ideas, or proposals. 
Summarize each as a concise statement.

Transcript:
"{chunk.text}"

Extract nodes of these types:
1. Decision: Statements indicating a decision was made (e.g., "we will", "decided", "approved")
2. Action: Action items or tasks (e.g., "task", "deadline", "next steps", "need to")
3. Idea: Key concepts or ideas mentioned
4. Proposal: Suggestions or proposals made

Return a JSON array with this structure:
[
  {{
    "text": "concise summary",
    "type": "decision|action|idea|proposal",
    "confidence": 0.0-1.0
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting key information from conversations. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON (handle markdown code blocks)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            extracted = json.loads(content)
            
            # Convert to NodeData
            nodes = []
            for item in extracted:
                self.node_counter += 1
                node = NodeData(
                    id=f"node_{self.node_counter}",
                    text=item.get("text", ""),
                    type=item.get("type", "idea"),
                    speaker=chunk.speaker,
                    timestamp=chunk.start,
                    confidence=item.get("confidence", 0.8),
                    metadata={
                        "chunk_id": chunk.chunk_id,
                        "end_time": chunk.end
                    }
                )
                nodes.append(node)
            
            return nodes
            
        except Exception as e:
            print(f"Error extracting nodes: {e}")
            return []
