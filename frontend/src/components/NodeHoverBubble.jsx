import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import './NodeHoverBubble.css'

export default function NodeHoverBubble({ nodeId, meetingId, nodePosition, reactFlowInstance }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [bubblePosition, setBubblePosition] = useState({ top: 0, left: 0 })

  // Fetch summary when component mounts
  useEffect(() => {
    console.log('[BUBBLE] Component mounted/updated:', { nodeId, meetingId })
    if (!nodeId || !meetingId || nodeId.startsWith('root')) {
      console.log('[BUBBLE] Skipping fetch - invalid params')
      setLoading(false)
      return
    }

    let cancelled = false

    const fetchSummary = async () => {
      try {
        console.log('[BUBBLE] Fetching summary for node:', nodeId, 'meeting:', meetingId)
        setLoading(true)
        setError(null)
        const response = await api.getNodeSummary(nodeId, meetingId)
        console.log('[BUBBLE] Summary response:', response)
        
        if (!cancelled) {
          if (response.status === 'success') {
            setSummary(response.summary)
            console.log('[BUBBLE] Summary received:', response.summary)
          } else {
            setError(response.message || 'Failed to load summary')
            console.log('[BUBBLE] Error in response:', response.message)
          }
          setLoading(false)
        }
      } catch (err) {
        console.error('[BUBBLE] Error fetching summary:', err)
        if (!cancelled) {
          setError('Unable to load summary')
          setLoading(false)
        }
      }
    }

    fetchSummary()

    return () => {
      cancelled = true
    }
  }, [nodeId, meetingId])

  // Calculate bubble position based on node screen position
  useEffect(() => {
    if (!nodePosition) return

    const calculatePosition = () => {
      // nodePosition is already in screen coordinates (from getBoundingClientRect)
      const screenX = nodePosition.x
      const screenY = nodePosition.y

      // Bubble dimensions
      const bubbleWidth = 350
      const bubbleHeight = 200
      const arrowHeight = 8
      const padding = 10

      // Default: position above node
      let top = screenY - bubbleHeight - arrowHeight - padding
      let left = screenX - bubbleWidth / 2

      // Adjust if too close to top
      if (top < 10) {
        top = screenY + 50 // Position below instead
      }

      // Adjust if too close to left edge
      if (left < 10) {
        left = 10
      }

      // Adjust if too close to right edge
      if (left + bubbleWidth > window.innerWidth - 10) {
        left = window.innerWidth - bubbleWidth - 10
      }

      setBubblePosition({ top, left })
    }

    calculatePosition()

    // Recalculate on window resize
    const handleResize = () => calculatePosition()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [nodePosition])

  // Don't show for root nodes
  if (nodeId.startsWith('root') || nodeId === 'root') {
    return null
  }

  return (
    <div 
      className="node-hover-bubble"
      style={{
        top: `${bubblePosition.top}px`,
        left: `${bubblePosition.left}px`,
      }}
    >
      <div className="bubble-arrow"></div>
      <div className="bubble-content">
        {loading && (
          <div className="bubble-loading">Loading summary...</div>
        )}
        {error && (
          <div className="bubble-error">{error}</div>
        )}
        {summary && !loading && !error && (
          <div className="bubble-summary">{summary}</div>
        )}
      </div>
    </div>
  )
}

