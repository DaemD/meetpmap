# MeetMap Backend API

FastAPI backend implementing the full MeetMap pipeline.

## Pipeline Overview

1. **STT Layer**: Speech-to-Text transcription (OpenAI Realtime API)
2. **TalkTraces Layer**: Topic detection using keyword extraction + embeddings
3. **MeetMap Layer**: Node extraction (ideas/actions/decisions) using LLM
4. **Merge Layer**: Cross-reference topics and nodes
5. **Visualization**: Real-time updates via WebSocket

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --reload
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health status
- `POST /api/transcript` - Process single transcript chunk
- `POST /api/batch-process` - Process multiple chunks
- `WebSocket /ws` - Real-time updates

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for LLM and STT
- `NEO4J_URI` - Neo4j database URI (optional)
- `PORT` - Server port (default: 8000)

