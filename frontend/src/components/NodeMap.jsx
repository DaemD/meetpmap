import React, { useMemo, useEffect, useState, useCallback, useRef } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  applyNodeChanges,
  Handle,
  Position,
} from 'reactflow'
import dagre from 'dagre'
import 'reactflow/dist/style.css'
import './NodeMap.css'
import { api } from '../services/api'

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
  const [maturity, setMaturity] = useState(null)
  const [influence, setInfluence] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
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
    backgroundColor: hexToRgba(clusterColor, 0.15), // 15% opacity background
    borderColor: clusterColor,
    borderWidth: '2px'
  } : {}

  // Fetch maturity and influence on mount and when data changes
  useEffect(() => {
    if (!isRoot && nodeId) {
      setIsLoading(true)
      Promise.all([
        api.getMaturity(nodeId).catch(() => ({ score: 0 })),
        api.getInfluence(nodeId).catch(() => ({ score: 0 }))
      ]).then(([maturityData, influenceData]) => {
        setMaturity(maturityData.score || 0)
        setInfluence(influenceData.score || 0)
        setIsLoading(false)
      })
    }
  }, [nodeId, isRoot])

  return (
    <div 
      className={`custom-node idea-node${isRoot ? ' root-node' : ''} ${isHovered ? 'hovered' : ''} ${data.isClicked ? 'clicked' : ''} ${data.inDownwardPath ? 'in-downward-path' : ''} ${data.inUpwardPath ? 'in-upward-path' : ''}`}
      style={nodeStyle}
    >
      <Handle type="target" position={Position.Top} />
      <div className="node-header">{isRoot ? 'Root' : 'Idea'}</div>
      <div className="node-content">{data.label}</div>
      {data.timestamp && !isRoot && (
        <div className="node-meta">{data.timestamp.toFixed(1)}s</div>
      )}
      {!isRoot && isHovered && !isLoading && (
        <div className="node-tooltip">
          <div>Maturity: {maturity}%</div>
          <div>Influence: {influence}</div>
        </div>
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

// Dagre layout function - calculates hierarchical positions for nodes
const getLayoutedElements = (nodes, edges, userModifiedNodes = new Set(), direction = 'TB') => {
  try {
    const dagreGraph = new dagre.graphlib.Graph()
    dagreGraph.setDefaultEdgeLabel(() => ({}))
    dagreGraph.setGraph({ 
      rankdir: direction,  // TB = top to bottom
      nodesep: 150,        // Horizontal spacing between nodes
      ranksep: 200,        // Vertical spacing between ranks
      marginx: 50,
      marginy: 50,
    })

    // Set node dimensions (dagre needs width/height for layout calculation)
    nodes.forEach((node) => {
      dagreGraph.setNode(node.id, { 
        width: 200,  // Approximate node width
        height: 100  // Approximate node height
      })
    })

    // Add edges
    edges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target)
    })

    // Calculate layout
    dagre.layout(dagreGraph)

    // Update node positions, but preserve user-modified positions
    const layoutedNodes = nodes.map((node) => {
      // If user has manually moved this node, keep its position
      if (userModifiedNodes.has(node.id) && node.position) {
        return node
      }
      
      // Otherwise, use dagre-calculated position
      const nodeWithPosition = dagreGraph.node(node.id)
      if (!nodeWithPosition || nodeWithPosition.x === undefined || nodeWithPosition.y === undefined) {
        console.warn(`Dagre: No position for node ${node.id}, using fallback`)
        return {
          ...node,
          position: { x: 400, y: 100 + nodes.indexOf(node) * 150 }
        }
      }
      
      const position = {
        x: nodeWithPosition.x - 100, // Center the node (subtract half width)
        y: nodeWithPosition.y - 50,   // Center the node (subtract half height)
      }
      
      console.log(`Dagre: Node ${node.id} positioned at (${position.x}, ${position.y})`)
      return {
        ...node,
        position,
      }
    })

    console.log('Dagre: Layout completed successfully', layoutedNodes.length, 'nodes')
    return { nodes: layoutedNodes, edges }
  } catch (error) {
    console.error('Dagre layout error:', error)
    // Fallback: simple positioning
    const fallbackNodes = nodes.map((node, index) => ({
      ...node,
      position: node.data.isRoot 
        ? { x: 400, y: 50 }
        : { x: 400, y: 150 + index * 150 }
    }))
    return { nodes: fallbackNodes, edges }
  }
}

export default function NodeMap({ nodes: nodeData, edges: edgeData = [] }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [hoveredNodeId, setHoveredNodeId] = useState(null)
  const [clickedNodeId, setClickedNodeId] = useState(null)
  const [clickState, setClickState] = useState(0) // 0=normal, 1=down, 2=up, 3=clear
  const [downwardPathNodes, setDownwardPathNodes] = useState(new Set())
  const [upwardPathNodes, setUpwardPathNodes] = useState(new Set())
  const [userModifiedNodes, setUserModifiedNodes] = useState(new Set()) // Track nodes user has manually moved
  const [isUserDragging, setIsUserDragging] = useState(false) // Track if user is actively dragging/panning
  const reactFlowInstance = useRef(null)
  
  // Handle node drag end - mark node as user-modified
  const onNodeDragStop = useCallback((event, node) => {
    setUserModifiedNodes(prev => new Set(prev).add(node.id))
  }, [])
  
  // Handle ReactFlow initialization
  const onInit = useCallback((instance) => {
    reactFlowInstance.current = instance
  }, [])
  
  // Track when user starts dragging/panning the map
  const onMoveStart = useCallback(() => {
    setIsUserDragging(true)
  }, [])
  
  // Track when user stops dragging/panning the map
  const onMoveEnd = useCallback(() => {
    setIsUserDragging(false)
  }, [])
  
  const reactFlowEdges = useMemo(() => {
    console.log('NodeMap: Creating React Flow edges from', edgeData.length, 'edges')
    console.log('NodeMap: Edge data:', edgeData)
    
    if (!edgeData || edgeData.length === 0) {
      return []
    }
    
    const flowEdges = edgeData.map((edge) => {
      const source = edge.from_node || edge.source
      const target = edge.to_node || edge.target
      
      if (!source || !target) {
        console.warn('Edge missing source or target:', edge)
        return null
      }
      
      const flowEdge = {
        id: `edge-${source}-${target}`,
        source: source,
        target: target,
        type: 'bezier',
        label: edge.type || 'semantic',
        style: {
          strokeWidth: 2 * (edge.strength || 1),
          opacity: 0.6,
          stroke: '#b1b1b7',
        },
        animated: false, // Semantic edges, not chronological
      }
      console.log('Created edge:', flowEdge.id, flowEdge.source, '→', flowEdge.target, 'type:', flowEdge.label)
      return flowEdge
    }).filter(e => e !== null) // Remove null edges
    
    console.log('NodeMap: Total React Flow edges:', flowEdges.length)
    return flowEdges
  }, [edgeData])
  
  const [edges, setEdges, onEdgesChange] = useEdgesState(reactFlowEdges)

  // Convert nodeData to ReactFlow format and apply dagre layout
  useEffect(() => {
    if (!nodeData || nodeData.length === 0) {
      return
    }
    
    console.log('NodeMap: Applying layout -', nodeData.length, 'nodes,', reactFlowEdges.length, 'edges')
    
    // Convert nodeData to ReactFlow node format
    const flowNodes = nodeData.map(node => {
      // Check if this node already exists in current nodes (to preserve position if user-modified)
      const existingNode = nodes.find(n => n.id === node.id)
      const existingPosition = existingNode?.position
      
      return {
        id: node.id,
        type: node.type || 'idea',
        position: existingPosition || { x: 0, y: 0 }, // Temporary position, will be updated by dagre
        data: {
          label: node.text || '',
          timestamp: node.timestamp,
          topic: node.topic,
          confidence: node.confidence,
          isRoot: node.id === 'root' || node.metadata?.is_root,
          isClicked: clickedNodeId === node.id,
          inDownwardPath: downwardPathNodes.has(node.id),
          inUpwardPath: upwardPathNodes.has(node.id),
          isHovered: hoveredNodeId === node.id,
          metadata: node.metadata || {},
        },
      }
    })
    
    // Apply dagre layout if we have edges (hierarchical layout needs edges)
    if (reactFlowEdges.length > 0 && flowNodes.length > 0) {
      console.log('NodeMap: Applying dagre layout to', flowNodes.length, 'nodes with', reactFlowEdges.length, 'edges')
      const { nodes: layoutedNodes } = getLayoutedElements(
        flowNodes, 
        reactFlowEdges, 
        userModifiedNodes
      )
      console.log('NodeMap: Layouted nodes:', layoutedNodes.map(n => ({ id: n.id, pos: n.position })))
      setNodes(layoutedNodes)
      
      // Auto-fit to center the graph, but only if user is not actively dragging
      if (!isUserDragging) {
        setTimeout(() => {
          if (reactFlowInstance.current) {
            reactFlowInstance.current.fitView({ 
              padding: 0.2, 
              duration: 400
            })
          }
        }, 100)
      }
    } else if (flowNodes.length > 0) {
      // No edges yet, position root at center-top, others below
      console.log('NodeMap: No edges, using simple positioning for', flowNodes.length, 'nodes')
      const positionedNodes = flowNodes.map((node, index) => {
        if (node.data.isRoot) {
          return { ...node, position: { x: 400, y: 50 } }
        }
        // For nodes without edges, use simple positioning
        const existingNode = nodes.find(n => n.id === node.id)
        return { ...node, position: existingNode?.position || { x: 400, y: 150 + index * 150 } }
      })
      console.log('NodeMap: Positioned nodes:', positionedNodes.map(n => ({ id: n.id, pos: n.position })))
      setNodes(positionedNodes)
      
      // Auto-fit to center the graph, but only if user is not actively dragging
      if (!isUserDragging) {
        setTimeout(() => {
          if (reactFlowInstance.current) {
            reactFlowInstance.current.fitView({ 
              padding: 0.2, 
              duration: 400
            })
          }
        }, 100)
      }
    }
  }, [nodeData, reactFlowEdges, clickedNodeId, downwardPathNodes, upwardPathNodes, hoveredNodeId, userModifiedNodes, isUserDragging])

  // Handle node click
  const handleNodeClick = async (event, node) => {
    const nodeId = node.id
    
    if (clickedNodeId === nodeId) {
      // Same node clicked - cycle through states
      if (clickState === 0) {
        // First click: show downward path
        setClickState(1)
        await fetchDownwardPath(nodeId)
      } else if (clickState === 1) {
        // Second click: show upward path
        setClickState(2)
        await fetchUpwardPath(nodeId)
      } else {
        // Third click: clear all
        setClickState(0)
        clearHighlights()
      }
    } else {
      // Different node clicked - reset to state 1
      setClickedNodeId(nodeId)
      setClickState(1)
      await fetchDownwardPath(nodeId)
    }
  }

  const fetchDownwardPath = async (nodeId) => {
    try {
      const response = await api.getDownwardPath(nodeId)
      const pathNodes = new Set(response.all_nodes_in_paths || [])
      setDownwardPathNodes(pathNodes)
      setUpwardPathNodes(new Set())
      updateNodeStyles(pathNodes, new Set(), nodeId, hoveredNodeId)
    } catch (error) {
      console.error('Error fetching downward path:', error)
    }
  }

  const fetchUpwardPath = async (nodeId) => {
    try {
      const response = await api.getUpwardPath(nodeId)
      const pathNodes = new Set(response.all_nodes || [])
      setUpwardPathNodes(pathNodes)
      setDownwardPathNodes(new Set())
      updateNodeStyles(new Set(), pathNodes, nodeId, hoveredNodeId)
    } catch (error) {
      console.error('Error fetching upward path:', error)
    }
  }

  const clearHighlights = () => {
    setDownwardPathNodes(new Set())
    setUpwardPathNodes(new Set())
    setClickedNodeId(null)
    updateNodeStyles(new Set(), new Set(), null, hoveredNodeId)
  }

  const updateNodeStyles = (downNodes, upNodes, clickedId, hoveredId) => {
    setNodes((nds) => {
      if (nds.length === 0) return nds // Don't update if no nodes
      
      return nds.map((node) => {
        const isInDownPath = downNodes.has(node.id)
        const isInUpPath = upNodes.has(node.id)
        const isClicked = clickedId === node.id
        const isHovered = hoveredId === node.id
        const shouldDim = (clickedId || hoveredId) && !isInDownPath && !isInUpPath && !isClicked && !isHovered

        // Preserve all existing node properties
        return {
          ...node,
          style: {
            ...node.style,
            opacity: shouldDim ? 0.3 : 1,
            zIndex: (isClicked || isHovered) ? 10 : 1,
          },
          data: {
            ...node.data,
            isClicked: isClicked,
            inDownwardPath: isInDownPath,
            inUpwardPath: isInUpPath,
            isHovered: isHovered,
          }
        }
      })
    })
  }

  // Update edge styles based on paths
  useEffect(() => {
    setEdges((eds) => eds.map((edge) => {
      const isInDownPath = downwardPathNodes.has(edge.source) && downwardPathNodes.has(edge.target)
      const isInUpPath = upwardPathNodes.has(edge.source) && upwardPathNodes.has(edge.target)
      const shouldDim = (clickedNodeId || hoveredNodeId) && !isInDownPath && !isInUpPath

      return {
        ...edge,
        style: {
          ...edge.style,
          stroke: isInDownPath ? '#4CAF50' : isInUpPath ? '#FFC107' : edge.style?.stroke || '#b1b1b7',
          strokeWidth: isInDownPath || isInUpPath ? 4 : edge.style?.strokeWidth || 2,
          opacity: shouldDim ? 0.2 : 1,
        }
      }
    }))
  }, [downwardPathNodes, upwardPathNodes, clickedNodeId, hoveredNodeId, setEdges])

  // Update nodes when hover state or path state changes
  useEffect(() => {
    updateNodeStyles(downwardPathNodes, upwardPathNodes, clickedNodeId, hoveredNodeId)
  }, [hoveredNodeId, clickedNodeId, downwardPathNodes, upwardPathNodes])

  // Update edges when edgeData changes
  useEffect(() => {
    console.log('NodeMap: Updating edges -', reactFlowEdges.length, 'edges')
    console.log('NodeMap: Current nodes:', nodes.map(n => n.id))
    console.log('NodeMap: Edge details:', reactFlowEdges.map(e => `${e.source}→${e.target}`))
    
    // Verify edges reference existing nodes
    const nodeIds = new Set(nodes.map(n => n.id))
    const validEdges = reactFlowEdges.filter(e => {
      const valid = nodeIds.has(e.source) && nodeIds.has(e.target)
      if (!valid) {
        console.warn(`Edge ${e.id} references non-existent nodes: ${e.source} or ${e.target}`)
      }
      return valid
    })
    
    console.log(`NodeMap: ${validEdges.length} valid edges (out of ${reactFlowEdges.length})`)
    setEdges(validEdges)
  }, [reactFlowEdges, nodes, setEdges])

  // Debug: Log nodes and edges before rendering
  useEffect(() => {
    if (nodes.length > 0) {
      console.log('NodeMap: Rendering with', nodes.length, 'nodes and', edges.length, 'edges')
      console.log('NodeMap: Node positions:', nodes.map(n => ({ id: n.id, pos: n.position, type: n.type })))
    }
  }, [nodes, edges])

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
          onInit={onInit}
          onMoveStart={onMoveStart}
          onMoveEnd={onMoveEnd}
          onNodeClick={handleNodeClick}
          onNodeDragStop={onNodeDragStop}
          onNodeMouseEnter={(event, node) => setHoveredNodeId(node.id)}
          onNodeMouseLeave={() => setHoveredNodeId(null)}
          nodeTypes={nodeTypes}
          minZoom={0.1}  // Allow very deep zoom out for large graphs (manual zoom)
          maxZoom={2}    // Allow zoom in
          defaultEdgeOptions={{
            style: { strokeWidth: 2, stroke: '#b1b1b7' },
            type: 'bezier',
            animated: false,
          }}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      )}
    </div>
  )
}

