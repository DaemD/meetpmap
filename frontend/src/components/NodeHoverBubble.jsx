import React, { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import './NodeHoverBubble.css'

export default function NodeHoverBubble({ nodeId, nodePosition, userId, onClose }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const bubbleRef = useRef(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  // Fetch summary when component mounts
  useEffect(() => {
    if (!nodeId || !userId) return

    let isMounted = true

    const fetchSummary = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await api.getNodeSummary(nodeId, userId)
        if (isMounted) {
          setSummary(response.summary || 'No summary available.')
          setLoading(false)
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load summary')
          setLoading(false)
        }
      }
    }

    fetchSummary()

    return () => {
      isMounted = false
    }
  }, [nodeId, userId])

  // Calculate smart positioning
  useEffect(() => {
    if (!nodePosition || !bubbleRef.current) return

    const bubble = bubbleRef.current
    const bubbleWidth = 400
    const bubbleHeight = 300
    const padding = 20
    const screenWidth = window.innerWidth
    const screenHeight = window.innerHeight

    // Default: position above node
    let top = nodePosition.y - bubbleHeight - padding
    let left = nodePosition.x - bubbleWidth / 2

    // Adjust if too close to top
    if (top < padding) {
      top = nodePosition.y + 60 // Position below instead
    }

    // Adjust if too close to bottom
    if (top + bubbleHeight > screenHeight - padding) {
      top = nodePosition.y - bubbleHeight - padding
      // If still doesn't fit, position at top
      if (top < padding) {
        top = padding
      }
    }

    // Adjust if too close to left edge
    if (left < padding) {
      left = padding
    }

    // Adjust if too close to right edge
    if (left + bubbleWidth > screenWidth - padding) {
      left = screenWidth - bubbleWidth - padding
    }

    setPosition({ top, left })
  }, [nodePosition])

  // Parse markdown bold (**text**) to <strong>
  const renderSummary = (text) => {
    if (!text) return null
    
    const parts = text.split(/(\*\*.*?\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      return <span key={i}>{part}</span>
    })
  }

  if (!nodeId || !nodePosition) return null

  return (
    <div
      ref={bubbleRef}
      className="node-hover-bubble"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
      }}
      onMouseLeave={onClose}
    >
      <div className="bubble-content">
        {loading && (
          <div className="bubble-loading">Loading summary...</div>
        )}
        {error && (
          <div className="bubble-error">Error: {error}</div>
        )}
        {summary && !loading && !error && (
          <div className="bubble-summary">
            {renderSummary(summary)}
          </div>
        )}
      </div>
      <div className="bubble-arrow"></div>
    </div>
  )
}

