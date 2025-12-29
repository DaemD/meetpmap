# System Audio Capture Plan

## Goal
Capture system audio (what's playing on the computer) in 10-second chunks and send to OpenAI Whisper-1 for transcription.

## Platform: Windows

## Options for System Audio Capture

### Option 1: pysysaudio (Recommended)
**Pros:**
- Specifically designed for system audio capture
- Works on Windows with WASAPI loopback
- Simple API
- Cross-platform (Windows/macOS)

**Cons:**
- Newer library, less community support
- May require admin permissions

**Installation:**
```bash
pip install pysysaudio
```

**Usage:**
```python
import pysysaudio

with pysysaudio.Capture() as capture:
    capture.start()
    # Record audio chunks
    audio_data = capture.read()  # Get audio chunk
    capture.stop()
```

---

### Option 2: sounddevice with WASAPI Loopback
**Pros:**
- Well-established library
- Good documentation
- Supports WASAPI loopback on Windows
- More control over audio parameters

**Cons:**
- Requires WASAPI setup
- Slightly more complex API

**Installation:**
```bash
pip install sounddevice numpy
```

**Usage:**
```python
import sounddevice as sd
import numpy as np

# List devices to find loopback
devices = sd.query_devices()
# Find WASAPI loopback device

# Record from loopback device
audio_data = sd.rec(
    frames=44100 * 10,  # 10 seconds at 44.1kHz
    samplerate=44100,
    channels=2,
    device=loopback_device_id
)
```

---

### Option 3: pyaudio with WASAPI
**Pros:**
- Very popular library
- Lots of examples

**Cons:**
- Requires WASAPI backend setup
- More complex for loopback
- May need additional dependencies

---

## Recommended Approach: sounddevice

**Why sounddevice:**
1. Well-maintained and reliable
2. Good Windows WASAPI support
3. Easy to get device list and find loopback
4. Simple API for chunked recording
5. Good numpy integration for audio processing

---

## Implementation Plan

### Step 1: Audio Capture Service
Create `backend/services/audio_capture_service.py`

**Features:**
- List available audio devices
- Find WASAPI loopback device
- Capture audio in 10-second chunks
- Convert to format suitable for Whisper API

### Step 2: Chunked Recording
- Record 10-second chunks continuously
- Convert to WAV format (or send raw PCM)
- Send each chunk to Whisper API

### Step 3: Integration with STT Service
- Update `STTService` to accept audio chunks
- Send to Whisper API
- Return `TranscriptChunk` objects

### Step 4: WebSocket Audio Streaming
- Add WebSocket endpoint for audio chunks
- Frontend sends audio chunks (or backend captures directly)
- Backend processes and returns transcripts

---

## Technical Details

### Audio Format for Whisper
- Format: WAV, MP3, M4A, etc.
- Sample Rate: 16kHz (Whisper's preferred)
- Channels: Mono or Stereo (Whisper handles both)
- Bit Depth: 16-bit recommended

### Chunking Strategy
1. Record 10 seconds continuously
2. Convert to WAV format
3. Send to Whisper API
4. Get transcript with timestamps
5. Create TranscriptChunk
6. Send to pipeline

### Device Selection
- Auto-detect WASAPI loopback device
- Or allow user to select device
- Fallback to default if loopback not available

---

## File Structure

```
backend/
├── services/
│   ├── audio_capture_service.py (NEW)
│   └── stt_service.py (MODIFY - add chunk processing)
├── main.py (MODIFY - add audio WebSocket endpoint)
└── requirements.txt (ADD - sounddevice, numpy)
```

---

## Implementation Steps

1. **Install dependencies**
   ```bash
   pip install sounddevice numpy soundfile
   ```

2. **Create AudioCaptureService**
   - List devices
   - Find loopback
   - Record chunks

3. **Update STTService**
   - Add method to transcribe audio chunks
   - Process Whisper response

4. **Add WebSocket endpoint**
   - Receive audio chunks OR
   - Start/stop recording

5. **Frontend (optional)**
   - Button to start/stop recording
   - Or auto-start on meeting start

---

## Challenges & Solutions

### Challenge 1: Finding Loopback Device
**Solution:** Query devices, look for "WASAPI" and "loopback" in name

### Challenge 2: Continuous Recording
**Solution:** Use threading/async to record chunks while processing previous ones

### Challenge 3: Audio Format Conversion
**Solution:** Use `soundfile` or `pydub` to convert to WAV

### Challenge 4: Real-time Processing
**Solution:** Process chunks in parallel (record next while transcribing current)

---

## Testing

1. Test device detection
2. Test 10-second chunk recording
3. Test Whisper API integration
4. Test end-to-end: audio → transcript → nodes

