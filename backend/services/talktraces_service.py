"""
TalkTraces Service - Topic Detection Layer
Detects topics in real-time using keyword extraction and embeddings
"""

import os
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from keybert import KeyBERT
from rake_nltk import Rake
from models.schemas import TranscriptChunk, TopicData

class TalkTracesService:
    """Service for topic detection and tracking"""
    
    def __init__(self):
        # Initialize models
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.keybert_model = KeyBERT()
        self.rake = Rake()
        
        # Topic tracking
        self.active_topics: List[TopicData] = []
        self.topic_embeddings = []
        self.topic_counter = 0
    
    async def detect_topics(self, chunk: TranscriptChunk) -> List[TopicData]:
        """
        Detect topics in a transcript chunk
        Uses keyword extraction + embeddings + clustering
        """
        text = chunk.text
        
        # 1. Extract keywords using multiple methods
        keywords = self._extract_keywords(text)
        
        # 2. Generate embedding for the chunk
        chunk_embedding = self.embedding_model.encode([text])[0]
        
        # 3. Match to existing topics or create new
        topics = self._match_or_create_topic(
            text, 
            keywords, 
            chunk_embedding, 
            chunk.start, 
            chunk.end
        )
        
        return topics
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords using KeyBERT and RAKE"""
        keywords = []
        
        # KeyBERT extraction
        try:
            keybert_keywords = self.keybert_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 2),
                top_n=top_n
            )
            keywords.extend([kw[0] for kw in keybert_keywords])
        except:
            pass
        
        # RAKE extraction
        try:
            self.rake.extract_keywords_from_text(text)
            rake_keywords = self.rake.get_ranked_phrases()[:top_n]
            keywords.extend(rake_keywords)
        except:
            pass
        
        # Remove duplicates and return
        return list(set(keywords))[:top_n]
    
    def _match_or_create_topic(
        self, 
        text: str, 
        keywords: List[str], 
        embedding: np.ndarray, 
        start: float, 
        end: float
    ) -> List[TopicData]:
        """
        Match chunk to existing topic or create new topic
        Uses cosine similarity on embeddings
        """
        topics = []
        similarity_threshold = 0.7
        
        if not self.active_topics:
            # First topic
            topic = self._create_new_topic(text, keywords, embedding, start, end)
            topics.append(topic)
            return topics
        
        # Calculate similarity with existing topics
        similarities = []
        for topic_emb in self.topic_embeddings:
            similarity = np.dot(embedding, topic_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(topic_emb)
            )
            similarities.append(similarity)
        
        max_similarity = max(similarities) if similarities else 0
        max_index = similarities.index(max_similarity) if similarities else -1
        
        if max_similarity >= similarity_threshold:
            # Match to existing topic
            existing_topic = self.active_topics[max_index]
            # Update topic end time
            existing_topic.end = end
            existing_topic.confidence = max(existing_topic.confidence, float(max_similarity))
            topics.append(existing_topic)
        else:
            # Create new topic
            topic = self._create_new_topic(text, keywords, embedding, start, end)
            topics.append(topic)
        
        return topics
    
    def _create_new_topic(
        self, 
        text: str, 
        keywords: List[str], 
        embedding: np.ndarray, 
        start: float, 
        end: float
    ) -> TopicData:
        """Create a new topic"""
        self.topic_counter += 1
        topic_name = keywords[0] if keywords else "General Discussion"
        
        topic = TopicData(
            topic=topic_name,
            start=start,
            end=end,
            confidence=0.8,
            keywords=keywords[:3],  # Top 3 keywords
            topic_id=f"topic_{self.topic_counter}"
        )
        
        self.active_topics.append(topic)
        self.topic_embeddings.append(embedding)
        
        return topic
    
    def get_topic_timeline(self) -> List[TopicData]:
        """Get all active topics for timeline visualization"""
        return self.active_topics
    
    def reset_topics(self):
        """Reset topic tracking (for new meeting)"""
        self.active_topics = []
        self.topic_embeddings = []
        self.topic_counter = 0

