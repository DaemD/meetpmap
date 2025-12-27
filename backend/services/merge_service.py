"""
Merge Service - Cross-Reference Layer
Links topics (TalkTraces) and nodes (MeetMap) together
"""

from typing import List, Dict
from models.schemas import TopicData, NodeData, EdgeData, MergedData

class MergeService:
    """Service for merging topic and node data"""
    
    async def merge_topics_and_nodes(
        self, 
        topics: List[TopicData], 
        nodes: List[NodeData]
    ) -> Dict:
        """
        Merge topics and nodes, creating cross-references
        """
        # Create topic-node mapping
        topic_node_mapping: Dict[str, List[str]] = {}
        
        for topic in topics:
            topic_node_mapping[topic.topic_id] = []
            
            # Match nodes to topics based on timestamp overlap
            for node in nodes:
                if self._timestamp_overlaps(topic, node):
                    topic_node_mapping[topic.topic_id].append(node.id)
                    # Link node to topic
                    node.topic = topic.topic
                    node.topic_id = topic.topic_id
        
        # Generate edges (can be enhanced with thematic similarity)
        edges = self._generate_edges(nodes)
        print(f"Merge: Generated {len(edges)} edges for {len(nodes)} nodes")
        print(f"Merge: Node IDs being sent: {[n.id for n in nodes]}")
        print(f"Merge: Node texts: {[n.text[:30] for n in nodes]}")
        
        merged_data = MergedData(
            topics=topics,
            nodes=nodes,
            edges=edges,
            topic_node_mapping=topic_node_mapping
        )
        
        result = merged_data.dict()
        print(f"Merge: Result dict has {len(result.get('nodes', []))} nodes")
        return result
    
    def _timestamp_overlaps(self, topic: TopicData, node: NodeData) -> bool:
        """Check if node timestamp overlaps with topic time range"""
        node_time = node.timestamp
        return topic.start <= node_time <= topic.end
    
    def _generate_edges(self, nodes: List[NodeData]) -> List[EdgeData]:
        """Generate edges between nodes - SIMPLIFIED: no edges for now"""
        # For simplicity, no edges for now
        # Can add later when we have multiple nodes
        return []

