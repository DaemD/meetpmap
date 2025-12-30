# MeetMap Prototype

Real-time collaborative dialogue mapping system that combines **TalkTraces** (topic detection) and **MeetMap** (idea/action extraction) using LLMs.

## 🎯 Overview

This prototype implements a complete pipeline for processing meeting conversations:

1. **Speech-to-Text (STT)** - Real-time transcription with timestamps
2. **TalkTraces Layer** - Topic detection using keyword extraction and embeddings
3. **MeetMap Layer** - LLM-powered extraction of ideas, actions, and decisions
4. **Merge Layer** - Cross-referencing topics and nodes
5. **Visualization Dashboard** - Real-time updates via WebSocket

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React + Vite) │
│                 │
│  - Dashboard    │
│  - TopicTimeline│
│  - NodeMap      │
│  - Input Form   │
└────────┬────────┘
         │ WebSocket
         │ REST API
┌────────▼────────┐
│   Backend API   │
│  (FastAPI)      │
│                 │
│  - STT Service  │
│  - TalkTraces   │
│  - MeetMap      │
│  - Merge        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│  LLM  │ │  ML   │
│  API  │ │Models │
└───────┘ └───────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Run the server:**
```bash
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

## 📝 Usage

### 1. Start Both Servers

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### 2. Open the Dashboard

Navigate to `http://localhost:5173` in your browser.

### 3. Submit Transcript Chunks

In the right panel, enter:
- **Start Time**: When the conversation segment started (in seconds)
- **End Time**: When it ended
- **Transcript Text**: The actual conversation text

Example:
```
Start Time: 0.0
End Time: 5.2
Text: "We need to finalize the budget. Let's set a deadline for next week."
```

### 4. Watch Real-Time Updates

- **Topic Timeline (Left)**: Shows topics detected over time
- **Dialogue Map (Center)**: Visual graph of ideas, actions, and decisions
- **Stats**: Live count of topics, nodes, and connections

## 🔧 Pipeline Details

### Layer 1: Speech-to-Text (STT)

- **Input**: Audio stream or transcript chunks
- **Output**: Time-aligned transcript with timestamps
- **Implementation**: OpenAI Realtime API (placeholder) / Manual input for MVP

### Layer 2: TalkTraces - Topic Detection

- **Methods**:
  - Keyword extraction (RAKE, KeyBERT)
  - Embeddings + clustering (SentenceTransformers)
  - Optional: BERTopic for dynamic topic modeling
- **Output**: Topics with start/end times, confidence scores, keywords

### Layer 3: MeetMap - Node Extraction

- **LLM-Powered Extraction**:
  - Decisions: "we will", "decided", "approved"
  - Actions: "task", "deadline", "next steps"
  - Ideas/Proposals: Key concepts mentioned
- **Output**: Nodes with type, timestamp, confidence

### Layer 4: Merge - Cross-Reference

- Links nodes to topics based on timestamp overlap
- Generates edges:
  - Chronological (sequential nodes)
  - Thematic (same topic)
  - Participant (same speaker - if available)

### Layer 5: Visualization

- **Topic Timeline**: Horizontal bars showing topic duration
- **Node Map**: Interactive graph (React Flow)
- **Real-time Updates**: WebSocket for live data

## 📊 Data Flow

```
Transcript Chunk
    ↓
[STT Service] → Time-aligned text
    ↓
[TalkTraces Service] → Topics detected
    ↓
[MeetMap Service] → Nodes extracted (LLM)
    ↓
[Merge Service] → Cross-reference topics & nodes
    ↓
[WebSocket] → Real-time updates to frontend
    ↓
[Dashboard] → Visualize topics, nodes, connections
```

## 🎨 Features

- ✅ Real-time topic detection
- ✅ LLM-powered node extraction
- ✅ Interactive node graph visualization
- ✅ Topic timeline with confidence scores
- ✅ WebSocket for live updates
- ✅ Cross-referencing topics and nodes
- ✅ Multiple node types (decision, action, idea, proposal)

## 🔑 Environment Variables

Create a `.env` file in the `backend` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
PORT=8000
```

## 📦 Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── services/
│   │   ├── stt_service.py      # Speech-to-text
│   │   ├── talktraces_service.py  # Topic detection
│   │   ├── meetmap_service.py    # Node extraction
│   │   └── merge_service.py      # Cross-reference
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TopicTimeline.jsx
│   │   │   ├── NodeMap.jsx
│   │   │   └── TranscriptInput.jsx
│   │   ├── services/
│   │   │   ├── websocket.js
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
│
└── README.md
```

## 🧪 Testing

### Test with Sample Data

You can test the pipeline using the REST API:

```bash
curl -X POST http://localhost:8000/api/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": null,
    "start": 0.0,
    "end": 5.2,
    "text": "We need to finalize the budget. Let'\''s set a deadline for next week."
  }'
```

### Example Transcript Chunks

```json
[
  {
    "speaker": null,
    "start": 0.0,
    "end": 5.2,
    "text": "We need to finalize the budget."
  },
  {
    "speaker": null,
    "start": 5.3,
    "end": 10.0,
    "text": "Let's set a deadline next week."
  },
  {
    "speaker": null,
    "start": 10.1,
    "end": 15.5,
    "text": "I propose we review the timeline and allocate resources accordingly."
  }
]
```

## 🚧 Future Enhancements

- [ ] Real-time audio streaming with OpenAI Realtime API
- [ ] Speaker diarization
- [ ] Thematic similarity edges (embedding-based)
- [ ] Export maps as images/JSON
- [ ] Multi-user collaboration
- [ ] Meeting recording playback
- [ ] Advanced filtering and search

## 📚 Research References

- **MeetMap Paper**: Real-Time Collaborative Dialogue Mapping with LLMs
- **TalkTraces**: Concept of tracking conversation flow over time
- **TRACE System**: Real-time multimodal common ground tracking

## 🤝 Contributing

This is a prototype implementation. Contributions welcome!

## 📄 License

MIT License

---

**Built with**: FastAPI, React, React Flow, OpenAI API, SentenceTransformers, KeyBERT












