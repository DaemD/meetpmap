import { useState } from 'react'
import './TranscriptInput.css'

export default function TranscriptInput({ onSubmit }) {
  const [text, setText] = useState('')
  const [startTime, setStartTime] = useState(0)
  const [endTime, setEndTime] = useState(5) // Default 5 seconds duration
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!text.trim()) {
      alert('Please enter transcript text')
      return
    }

    if (endTime <= startTime) {
      alert('End time must be greater than start time')
      return
    }

    setIsSubmitting(true)

    const chunk = {
      speaker: null, // As per requirements, no speaker names
      start: parseFloat(startTime),
      end: parseFloat(endTime),
      text: text.trim(),
      chunk_id: `chunk_${Date.now()}`,
    }

    try {
      onSubmit(chunk)
      // Reset form
      setText('')
      setStartTime(endTime) // Next chunk starts where this one ended
      setEndTime(endTime + 5) // Default 5 second duration
    } catch (error) {
      console.error('Error submitting transcript:', error)
      alert('Error submitting transcript. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="transcript-input">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="start-time">Start Time (seconds)</label>
          <input
            id="start-time"
            type="number"
            step="0.1"
            min="0"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="end-time">End Time (seconds)</label>
          <input
            id="end-time"
            type="number"
            step="0.1"
            min="0"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="transcript-text">Transcript Text</label>
          <textarea
            id="transcript-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter conversation transcript here..."
            rows={5}
            required
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !text.trim()}
          className="submit-button"
        >
          {isSubmitting ? 'Processing...' : 'Submit Transcript Chunk'}
        </button>
      </form>

      <div className="input-hint">
        <p>💡 Tip: Enter transcript chunks as the conversation progresses. The system will:</p>
        <ul>
          <li>Detect topics in real-time (TalkTraces)</li>
          <li>Extract ideas, actions, and decisions (MeetMap)</li>
          <li>Create visual connections between concepts</li>
        </ul>
      </div>
    </div>
  )
}

