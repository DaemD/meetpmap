import { useMemo } from 'react'
import './TopicTimeline.css'

export default function TopicTimeline({ topics }) {
  const sortedTopics = useMemo(() => {
    return [...topics].sort((a, b) => a.start - b.start)
  }, [topics])

  const maxTime = useMemo(() => {
    if (sortedTopics.length === 0) return 100
    return Math.max(...sortedTopics.map(t => t.end || t.start + 10))
  }, [sortedTopics])

  return (
    <div className="topic-timeline">
      {sortedTopics.length === 0 ? (
        <div className="empty-state">
          <p>No topics detected yet. Submit transcript chunks to see topics appear in real-time.</p>
        </div>
      ) : (
        <div className="timeline-container">
          <div className="timeline-axis">
            <div className="axis-label">Time (seconds)</div>
            <div className="axis-ticks">
              {[0, maxTime / 4, maxTime / 2, (maxTime * 3) / 4, maxTime].map(t => (
                <div key={t} className="tick" style={{ left: `${(t / maxTime) * 100}%` }}>
                  <span className="tick-label">{t.toFixed(1)}s</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="timeline-bars">
            {sortedTopics.map((topic, index) => {
              const left = (topic.start / maxTime) * 100
              const width = ((topic.end - topic.start) / maxTime) * 100
              const confidence = topic.confidence || 0.8
              
              return (
                <div
                  key={topic.topic_id || index}
                  className="topic-bar"
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                    opacity: confidence,
                    backgroundColor: `hsl(${index * 60}, 70%, 60%)`
                  }}
                  title={`${topic.topic} (${topic.start.toFixed(1)}s - ${topic.end.toFixed(1)}s, confidence: ${(confidence * 100).toFixed(0)}%)`}
                >
                  <div className="topic-label">{topic.topic}</div>
                  {topic.keywords && topic.keywords.length > 0 && (
                    <div className="topic-keywords">
                      {topic.keywords.slice(0, 2).map((kw, i) => (
                        <span key={i} className="keyword-tag">{kw}</span>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}







