import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import './NodeHoverBubble.css'

export default function NodeHoverBubble({ nodeId, nodePosition, userId, summaryCache, setSummaryCache, onClose }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Check cache first, then fetch if needed
  useEffect(() => {
    if (!nodeId || !userId) return

    // Check if summary is already cached
    if (summaryCache[nodeId]) {
      setSummary(summaryCache[nodeId])
      setLoading(false)
      return
    }

    // Not in cache, fetch it
    let isMounted = true

    const fetchSummary = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await api.getNodeSummary(nodeId, userId)
        if (isMounted) {
          const summaryText = response.summary || 'No summary available.'
          setSummary(summaryText)
          setLoading(false)
          // Cache it
          setSummaryCache(prev => ({
            ...prev,
            [nodeId]: summaryText
          }))
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
  }, [nodeId, userId, summaryCache, setSummaryCache])

  // Simple positioning: above the node, centered
  const bubbleWidth = 400
  const bubbleHeight = 300
  const padding = 20
  
  const position = nodePosition ? {
    top: nodePosition.y - bubbleHeight - padding,
    left: nodePosition.x - bubbleWidth / 2
  } : { top: 0, left: 0 }

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
      className="node-hover-bubble"
      style={{
        position: 'fixed',
        top: `${position.top}px`,
        left: `${position.left}px`,
        zIndex: 1000,
        pointerEvents: 'auto',
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

