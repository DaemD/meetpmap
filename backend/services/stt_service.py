"""
Speech-to-Text Service
Handles real-time transcription using OpenAI Realtime API
"""

import os
import json
import asyncio
from openai import OpenAI
from typing import List, Optional, AsyncIterator
from models.schemas import TranscriptChunk

class STTService:
    """Service for speech-to-text transcription"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not set. STT features will be limited.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        self.transcript_buffer: List[TranscriptChunk] = []
        self.current_session = None
    
    async def transcribe_realtime(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[TranscriptChunk]:
        """
        Transcribe audio stream in real-time using OpenAI Realtime API
        Yields transcript chunks with timestamps as they arrive
        
        Note: OpenAI Realtime API requires WebSocket connection
        This is a simplified implementation - full implementation would use:
        - OpenAI Realtime API WebSocket endpoint
        - Audio streaming protocol
        - Event handling for transcript.delta events
        """
        try:
            # For MVP: Use OpenAI Whisper API for now
            # Full Realtime API implementation would require WebSocket connection
            # See: https://platform.openai.com/docs/guides/realtime
            
            # Placeholder: In production, this would:
            # 1. Connect to OpenAI Realtime API WebSocket
            # 2. Stream audio chunks
            # 3. Receive transcript.delta events
            # 4. Convert events to TranscriptChunk format
            
            # For now, we'll use a mock implementation that processes audio chunks
            # and returns transcript chunks with timestamps
            
            async for audio_chunk in audio_stream:
                # In real implementation, send audio to OpenAI Realtime API
                # and receive transcript events
                # For MVP, we'll simulate this
                pass
                
        except Exception as e:
            print(f"Error in realtime transcription: {e}")
    
    def process_transcript_event(self, event: dict) -> Optional[TranscriptChunk]:
        """
        Process a transcript event from OpenAI Realtime API
        Converts to our TranscriptChunk format
        
        Expected event format from OpenAI Realtime API:
        {
            "type": "transcript.delta",
            "delta": "text chunk",
            "timestamp": 123.45
        }
        or
        {
            "type": "transcript.done",
            "text": "full transcript",
            "start": 0.0,
            "end": 5.2
        }
        """
        event_type = event.get("type")
        
        if event_type == "transcript.delta":
            # Incremental transcript update
            text = event.get("delta", "")
            timestamp = event.get("timestamp", 0.0)
            
            # For delta events, we need to accumulate text
            # This is simplified - real implementation would handle buffering
            
            return TranscriptChunk(
                speaker=None,  # Will be None if not diarized
                start=timestamp,
                end=timestamp + 0.5,  # Estimate
                text=text,
                chunk_id=f"chunk_{timestamp}"
            )
        
        elif event_type == "transcript.done":
            # Complete transcript segment
            text = event.get("text", "")
            start = event.get("start", 0.0)
            end = event.get("end", 0.0)
            
            return TranscriptChunk(
                speaker=None,
                start=start,
                end=end,
                text=text,
                chunk_id=f"chunk_{start}_{end}"
            )
        
        return None
    
    async def transcribe_audio_file(self, audio_file_path: str) -> List[TranscriptChunk]:
        """
        Transcribe an audio file using OpenAI Whisper API
        Useful for testing and batch processing
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            chunks = []
            for segment in transcript.segments:
                chunk = TranscriptChunk(
                    speaker=None,
                    start=segment.get("start", 0.0),
                    end=segment.get("end", 0.0),
                    text=segment.get("text", ""),
                    chunk_id=f"chunk_{segment.get('start', 0.0)}"
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"Error transcribing audio file: {e}")
            return []
    
    def segment_transcript(self, full_transcript: str, segment_size: int = 3) -> List[str]:
        """
        Segment transcript into chunks (1-3 sentences)
        For TalkTraces topic detection
        """
        sentences = full_transcript.split('. ')
        segments = []
        
        current_segment = []
        for sentence in sentences:
            current_segment.append(sentence)
            if len(current_segment) >= segment_size:
                segments.append('. '.join(current_segment))
                current_segment = []
        
        if current_segment:
            segments.append('. '.join(current_segment))
        
        return segments

