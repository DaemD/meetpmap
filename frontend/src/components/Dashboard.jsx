import { useState, useEffect } from 'react'
import NodeMap from './NodeMap'
import { api } from '../services/api'
import './Dashboard.css'

export default function Dashboard({ userId }) {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])

  // Fetch graph state from backend
  const fetchGraphState = async () => {
    try {
      // userId comes from parent component/service
      const response = await api.getGraphState(userId)
      if (response.status === 'success') {
        console.log('Dashboard: Fetched graph state -', response.nodes?.length || 0, 'nodes,', response.edges?.length || 0, 'edges')
        setNodes(response.nodes || [])
        setEdges(response.edges || [])
      } else {
        console.warn('Dashboard: Graph state response status not success:', response)
      }
    } catch (error) {
      // Only log if it's not a connection refused (backend might not be running)
      if (error.code !== 'ERR_NETWORK' && error.code !== 'ECONNREFUSED') {
        console.error('Error fetching graph state:', error)
      }
    }
  }

  // Poll for graph updates every 2 seconds
  useEffect(() => {
    if (!userId) return // Don't fetch if no userId
    
    // Initial fetch
    fetchGraphState()
    
    // Set up polling
    const interval = setInterval(fetchGraphState, 2000)
    
    return () => clearInterval(interval)
  }, [userId])

  return (
    <div className="dashboard">
      <NodeMap nodes={nodes} edges={edges} />
    </div>
  )
}
