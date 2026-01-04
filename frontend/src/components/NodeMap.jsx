import React, { useMemo, useEffect, useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import './NodeMap.css'
import NodeHoverBubble from './NodeHoverBubble'

const nodeTypes = {
  decision: DecisionNode,
  action: ActionNode,
  idea: IdeaNode,
  proposal: ProposalNode,
}

function DecisionNode({ data }) {
  return (
    <div className="custom-node decision-node">
      <Handle type="target" position={Position.Top} />
      <div className="node-header">Decision</div>
      <div className="node-content">{data.label}</div>
      {data.timestamp && (
        <div className="node-meta">{data.timestamp.toFixed(1)}s</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function ActionNode({ data }) {
  return (
    <div className="custom-node action-node">
      <Handle type="target" position={Position.Top} />
      <div className="node-header">Action</div>
      <div className="node-content">{data.label}</div>
      {data.timestamp && (
        <div className="node-meta">{data.timestamp.toFixed(1)}s</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function IdeaNode({ data, id: nodeId }) {
  const isRoot = data.isRoot || false
  const isHovered = data.isHovered || false

  // Get cluster color from metadata
  const clusterColor = data.metadata?.cluster_color || null
  
  // Convert hex to rgba for background with opacity
  const hexToRgba = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }
  
  const nodeStyle = clusterColor && !isRoot ? {
    backgroundColor: hexToRgba(clusterColor, 0.15),
    borderColor: clusterColor,
    borderWidth: '2px'
  } : {}

  return (
    <div 
      className={`custom-node idea-node${isRoot ? ' root-node' : ''} ${isHovered ? 'hovered' : ''}`}
      style={nodeStyle}
    >
      <Handle type="target" position={Position.Top} />
      <div className="node-header">{isRoot ? 'Root' : 'Idea'}</div>
      <div className="node-content">{data.label}</div>
      {data.timestamp && !isRoot && (
        <div className="node-meta">{data.timestamp.toFixed(1)}s</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

function ProposalNode({ data }) {
  return (
    <div className="custom-node proposal-node">
      <Handle type="target" position={Position.Top} />
      <div className="node-header">Proposal</div>
      <div className="node-content">{data.label}</div>
      {data.timestamp && (
        <div className="node-meta">{data.timestamp.toFixed(1)}s</div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

export default function NodeMap({ nodes: nodeData, edges: edgeData = [], userId }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [hoveredNodeId, setHoveredNodeId] = useState(null)
  const [hoveredNodePosition, setHoveredNodePosition] = useState(null)
  const [summaryCache, setSummaryCache] = useState({})
  const [hoverTimeout, setHoverTimeout] = useState(null)
  const reactFlowInstance = useRef(null)
  const previousNodeCountRef = useRef(0)

  // Simple layout: root at center, children positioned in a circle around parent
  const calculateLayout = useCallback((nodesData, edgesData) => {
    if (!nodesData || nodesData.length === 0) {
      console.log('NodeMap: No nodes data for layout')
      return new Map()
    }

    console.log('NodeMap: Calculating layout for', nodesData.length, 'nodes,', edgesData.length, 'edges')

    // Find root node
    const rootNode = nodesData.find(n => n.id === 'root' || n.id.startsWith('root_') || n.metadata?.is_root)
    console.log('NodeMap: Root node found:', rootNode?.id)
    
    // Center position (middle of viewport)
    const centerX = 500
    const centerY = 400

    // Build parent-child map
    const childrenMap = new Map()
    edgesData.forEach(edge => {
      const parent = edge.from_node || edge.source
      const child = edge.to_node || edge.target
      if (parent && child) {
        if (!childrenMap.has(parent)) {
          childrenMap.set(parent, [])
        }
        childrenMap.get(parent).push(child)
      }
    })
    console.log('NodeMap: Children map:', Array.from(childrenMap.entries()).map(([p, c]) => `${p}: [${c.join(', ')}]`))

    // Calculate positions using simple hierarchical layout
    const positions = new Map()
    const visited = new Set()

    // Position root at center
    if (rootNode) {
      positions.set(rootNode.id, { x: centerX, y: centerY })
      visited.add(rootNode.id)
      console.log('NodeMap: Positioned root at center:', rootNode.id)
    }

    // Position children in levels
    const positionNode = (nodeId, parentId, level, indexInLevel) => {
      if (visited.has(nodeId)) return
      
      visited.add(nodeId)
      
      if (parentId && positions.has(parentId)) {
        const parentPos = positions.get(parentId)
        const siblings = childrenMap.get(parentId) || []
        const angle = siblings.length > 1 ? (indexInLevel / siblings.length) * Math.PI * 2 : 0
        const radius = 250 + (level * 150) // Increase radius for deeper levels
        const x = parentPos.x + Math.cos(angle) * radius
        const y = parentPos.y + Math.sin(angle) * radius
        positions.set(nodeId, { x, y })
        console.log(`NodeMap: Positioned ${nodeId} at (${x.toFixed(0)}, ${y.toFixed(0)}) - parent: ${parentId}, level: ${level}`)
      } else {
        // Fallback: position relative to center
        const angle = (indexInLevel / nodesData.length) * Math.PI * 2
        const radius = 200
        positions.set(nodeId, {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius
        })
        console.log(`NodeMap: Positioned ${nodeId} at fallback position (${positions.get(nodeId).x.toFixed(0)}, ${positions.get(nodeId).y.toFixed(0)})`)
      }

      // Position children
      const children = childrenMap.get(nodeId) || []
      children.forEach((childId, childIndex) => {
        positionNode(childId, nodeId, level + 1, childIndex)
      })
    }

    // Position all nodes starting from root
    if (rootNode) {
      const rootChildren = childrenMap.get(rootNode.id) || []
      rootChildren.forEach((childId, index) => {
        positionNode(childId, rootNode.id, 1, index)
      })
    }

    // Position any remaining unvisited nodes
    nodesData.forEach((node, index) => {
      if (!visited.has(node.id)) {
        const parentEdge = edgesData.find(e => (e.to_node || e.target) === node.id)
        const parentId = parentEdge ? (parentEdge.from_node || parentEdge.source) : null
        positionNode(node.id, parentId, 0, index)
      }
    })

    console.log('NodeMap: Layout complete, positioned', positions.size, 'nodes')
    return positions
  }, [])

  // Convert nodeData to ReactFlow format
  useEffect(() => {
    console.log('NodeMap: useEffect triggered - nodeData:', nodeData?.length, 'edges:', edgeData?.length)
    
    if (!nodeData || nodeData.length === 0) {
      console.log('NodeMap: No node data, clearing nodes')
      setNodes([])
      previousNodeCountRef.current = 0
      return
    }

    // Calculate positions
    const positions = calculateLayout(nodeData, edgeData)
    console.log('NodeMap: Got positions for', positions.size, 'nodes')

    // Convert to ReactFlow nodes
    const flowNodes = nodeData.map(node => {
      const position = positions.get(node.id) || { x: 500, y: 400 }
      const existingNode = nodes.find(n => n.id === node.id)
      console.log(`NodeMap: Converting node ${node.id} - position:`, position, 'existing:', !!existingNode)

      return {
        id: node.id,
        type: node.type || 'idea',
        position: existingNode?.position || position, // Preserve user-modified positions
        data: {
          label: node.text || '',
          timestamp: node.timestamp,
          topic: node.topic,
          confidence: node.confidence,
          isRoot: node.id === 'root' || node.id.startsWith('root_') || node.metadata?.is_root,
          isHovered: hoveredNodeId === node.id,
          metadata: node.metadata || {},
        },
        style: {
          opacity: hoveredNodeId && hoveredNodeId !== node.id ? 0.4 : 1,
          transform: hoveredNodeId === node.id ? 'scale(1.1)' : 'scale(1)',
          transition: 'opacity 0.2s ease, transform 0.2s ease',
          zIndex: hoveredNodeId === node.id ? 10 : 1,
        },
      }
    })

    console.log('NodeMap: Setting', flowNodes.length, 'flow nodes')
    console.log('NodeMap: Flow nodes sample:', flowNodes.slice(0, 2).map(n => ({ id: n.id, pos: n.position, label: n.data.label })))
    setNodes(flowNodes)

    // Auto-center when new nodes are added
    const currentNodeCount = nodeData.length
    const previousNodeCount = previousNodeCountRef.current

    if (currentNodeCount > previousNodeCount && reactFlowInstance.current) {
      console.log('NodeMap: New nodes detected, auto-centering')
      setTimeout(() => {
        if (reactFlowInstance.current) {
          reactFlowInstance.current.fitView({ 
            padding: 0.2, 
            duration: 400
          })
        }
      }, 100)
    }

    previousNodeCountRef.current = currentNodeCount
  }, [nodeData, edgeData, calculateLayout, hoveredNodeId, nodes, setNodes])

  // Convert edgeData to ReactFlow edges
  const reactFlowEdges = useMemo(() => {
    if (!edgeData || edgeData.length === 0) {
      return []
    }

    return edgeData.map((edge) => {
      const source = edge.from_node || edge.source
      const target = edge.to_node || edge.target

      if (!source || !target) return null

      return {
        id: `edge-${source}-${target}`,
        source: source,
        target: target,
        type: 'bezier',
        style: {
          strokeWidth: 2,
          opacity: hoveredNodeId && hoveredNodeId !== source && hoveredNodeId !== target ? 0.3 : 0.6,
          stroke: '#b1b1b7',
        },
        animated: false,
      }
    }).filter(e => e !== null)
  }, [edgeData, hoveredNodeId])

  const [edges, setEdges, onEdgesChange] = useEdgesState(reactFlowEdges)

  // Update edges when they change
  useEffect(() => {
    setEdges(reactFlowEdges)
  }, [reactFlowEdges, setEdges])

  // Handle node hover
  const handleNodeMouseEnter = useCallback((event, node) => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout)
    }

    const timeout = setTimeout(() => {
      setHoveredNodeId(node.id)
      const nodeElement = event.currentTarget
      const rect = nodeElement.getBoundingClientRect()
      setHoveredNodePosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2
      })
    }, 300)

    setHoverTimeout(timeout)
  }, [hoverTimeout])

  const handleNodeMouseLeave = useCallback(() => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout)
      setHoverTimeout(null)
    }
    setHoveredNodeId(null)
    setHoveredNodePosition(null)
  }, [hoverTimeout])

  return (
    <div className="node-map-container">
      {nodes.length === 0 ? (
        <div className="empty-state">
          <p>No nodes yet. Submit transcript chunks to see ideas, actions, and decisions appear.</p>
        </div>
      ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onInit={(instance) => {
            reactFlowInstance.current = instance
            // Center on initial load
            setTimeout(() => {
              instance.fitView({ padding: 0.2, duration: 400 })
            }, 100)
          }}
          onNodeMouseEnter={handleNodeMouseEnter}
          onNodeMouseLeave={handleNodeMouseLeave}
          nodeTypes={nodeTypes}
          minZoom={0.1}
          maxZoom={2}
          defaultEdgeOptions={{
            style: { strokeWidth: 2, stroke: '#b1b1b7' },
            type: 'bezier',
            animated: false,
          }}
        >
          <Background />
          <Controls />
          <MiniMap 
            nodeColor={(node) => {
              const clusterColor = node.data?.metadata?.cluster_color
              if (clusterColor) return clusterColor
              if (node.data?.isRoot) return '#4caf50'
              if (node.type === 'decision') return '#2196f3'
              if (node.type === 'action') return '#4caf50'
              if (node.type === 'proposal') return '#e91e63'
              return '#ff9800'
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
            style={{ backgroundColor: '#fafafa' }}
          />
        </ReactFlow>
      )}
      {hoveredNodeId && hoveredNodePosition && userId && (
        <NodeHoverBubble
          nodeId={hoveredNodeId}
          nodePosition={hoveredNodePosition}
          userId={userId}
          summaryCache={summaryCache}
          setSummaryCache={setSummaryCache}
          onClose={handleNodeMouseLeave}
        />
      )}
    </div>
  )
}
