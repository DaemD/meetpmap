import { useState } from 'react'
import NodeMap from './NodeMap'
import TranscriptInput from './TranscriptInput'
import './Dashboard.css'

export default function Dashboard() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])

  const handleNodesReceived = (data) => {
    console.log('📊 Received nodes/edges:', data)
    
    const nodesData = data.nodes || []
    const edgesData = data.edges || []
    
    // Add new nodes
    if (nodesData && Array.isArray(nodesData) && nodesData.length > 0) {
      setNodes(prevNodes => {
        const existingIds = new Set(prevNodes.map(n => n.id))
        const newNodes = nodesData.filter(n => !existingIds.has(n.id))
        
        if (newNodes.length > 0) {
          console.log(`✅ Adding ${newNodes.length} new node(s)`)
          return [...prevNodes, ...newNodes]
        }
        return prevNodes
      })
    }
    
    // Add new edges
    if (edgesData && Array.isArray(edgesData) && edgesData.length > 0) {
      console.log('Received edges from backend:', edgesData)
      setEdges(prevEdges => {
        const existingEdgeSet = new Set(
          prevEdges.map(e => `${e.from_node || e.source}-${e.to_node || e.target}`)
        )
        
        const newEdges = edgesData.filter(edge => {
          const edgeId = `${edge.from_node || edge.source}-${edge.to_node || edge.target}`
          const isNew = !existingEdgeSet.has(edgeId)
          if (isNew) {
            console.log('New edge:', edgeId, edge)
          }
          return isNew
        })
        
        if (newEdges.length > 0) {
          console.log(`✅ Adding ${newEdges.length} semantic edge(s) from backend:`, newEdges)
          return [...prevEdges, ...newEdges]
        }
        console.log('No new edges to add')
        return prevEdges
      })
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>MeetMap Prototype</h1>
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
          <TranscriptInput onNodesReceived={handleNodesReceived} />
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
