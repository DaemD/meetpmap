import { useState, useEffect } from 'react'
import NodeMap from './NodeMap'
import TranscriptInput from './TranscriptInput'
import './Dashboard.css'

export default function Dashboard({ wsService }) {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Set up WebSocket listeners
    wsService.on('connect', () => {
      setIsConnected(true)
    })

    wsService.on('disconnect', () => {
      setIsConnected(false)
    })

    // Handle new nodes from backend
    wsService.on('new_nodes', (data) => {
      console.log('Received new_nodes event:', data)
      
      if (data.nodes && Array.isArray(data.nodes)) {
        setNodes(prevNodes => {
          const existingIds = new Set(prevNodes.map(n => n.id))
          const newNodes = data.nodes.filter(n => !existingIds.has(n.id))
          
          if (newNodes.length > 0) {
            console.log(`Adding ${newNodes.length} new node(s)`)
            const updatedNodes = [...prevNodes, ...newNodes]
            
            // Generate chronological edges
            if (updatedNodes.length > 1) {
              setEdges(prevEdges => {
                const newEdges = []
                const existingEdgeSet = new Set(prevEdges.map(e => `${e.from_node || e.source}-${e.to_node || e.target}`))
                
                // Connect last node to new nodes sequentially
                for (let i = 0; i < updatedNodes.length - 1; i++) {
                  const sourceNode = updatedNodes[i]
                  const targetNode = updatedNodes[i + 1]
                  const edgeId = `${sourceNode.id}-${targetNode.id}`
                  
                  if (!existingEdgeSet.has(edgeId)) {
                    newEdges.push({
                      id: edgeId,
                      from_node: sourceNode.id,
                      to_node: targetNode.id,
                      type: 'chronological',
                      strength: 0.7
                    })
                    existingEdgeSet.add(edgeId)
                  }
                }
                
                if (newEdges.length > 0) {
                  console.log(`✅ Adding ${newEdges.length} new edge(s)`)
                  return [...prevEdges, ...newEdges]
                }
                return prevEdges
              })
            }
            
            return updatedNodes
          }
          return prevNodes
        })
      }
    })

    wsService.on('error', (error) => {
      console.error('WebSocket error:', error)
    })

    return () => {
      wsService.off('connect')
      wsService.off('disconnect')
      wsService.off('new_nodes')
      wsService.off('error')
    }
  }, [wsService])

  const handleTranscriptSubmit = (chunk) => {
    if (wsService.isConnected()) {
      wsService.sendTranscriptChunk(chunk)
    } else {
      console.warn('WebSocket not connected')
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>MeetMap Prototype</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Center Panel: Node Map */}
        <div className="panel map-panel">
          <h2>Dialogue Map</h2>
          <NodeMap nodes={nodes} edges={edges} />
        </div>

        {/* Right Panel: Transcript Input */}
        <div className="panel input-panel">
          <h2>Transcript Input</h2>
          <TranscriptInput onSubmit={handleTranscriptSubmit} />
          <div className="stats">
            <div className="stat">
              <span className="stat-label">Nodes:</span>
              <span className="stat-value">{nodes.length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Connections:</span>
              <span className="stat-value">{edges.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

