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
    backgroundColor: hexToRgba(clusterColor, 0.15), // 15% opacity background
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

export default function NodeMap({ nodes: nodeData, edges: edgeData = [], meetingId }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [hoveredNodeId, setHoveredNodeId] = useState(null) // For visual effects (enlarge, dim)
  const [clickedNodeId, setClickedNodeId] = useState(null) // Track clicked node for summary bubble
  const [clickedNodePosition, setClickedNodePosition] = useState(null)
  const [userModifiedNodes, setUserModifiedNodes] = useState(new Set()) // Track nodes user has manually moved
  const [hasDeviated, setHasDeviated] = useState(false) // Track if user has deviated from original position
  const reactFlowInstance = useRef(null)
  const hoveredNodeIdRef = useRef(null) // Ref to track hover state for layout effect (still used for dimming)
  const isAutoFittingRef = useRef(false) // Track if we're auto-fitting to prevent deviation detection
  const initialViewportRef = useRef(null) // Store initial viewport (x, y, zoom) to detect deviation
  const previousNodeCountRef = useRef(0) // Track previous node count to detect new nodes
  const nodesRef = useRef([]) // Ref to store current nodes for layout effect
  
  // Handle node drag end - mark node as user-modified
  const onNodeDragStop = useCallback((event, node) => {
    setUserModifiedNodes(prev => new Set(prev).add(node.id))
  }, [])
  
  // Handle ReactFlow initialization
  const onInit = useCallback((instance) => {
    reactFlowInstance.current = instance
    // Don't store initial viewport yet - wait for nodes to be laid out and centered first
    // This prevents storing an incorrect initial position that causes left-side positioning
  }, [])
  
  // Track when user starts moving (for potential future use)
  const onMoveStart = useCallback(() => {
    // Can be used for tracking if needed
  }, [])
  
  // Track when user stops moving (for potential future use)
  const onMoveEnd = useCallback(() => {
    // Can be used for tracking if needed
  }, [])
  
  // Track viewport changes (zoom and pan) to detect deviation
  const onViewportChange = useCallback((viewport) => {
    // Don't detect changes during auto-fit
    if (isAutoFittingRef.current || !initialViewportRef.current) {
      return
    }
    
    const initial = initialViewportRef.current
    const zoomDiff = Math.abs(viewport.zoom - initial.zoom)
    const panDiff = Math.sqrt(
      Math.pow(viewport.x - initial.x, 2) + 
      Math.pow(viewport.y - initial.y, 2)
    )
    
    // If user has zoomed or panned significantly, mark as deviated
    if (zoomDiff > 0.01 || panDiff > 10) {
      setHasDeviated(true)
    }
  }, [])
  
  
  // Handle recentre button click - improved centering
  const handleRecentre = useCallback(() => {
    if (reactFlowInstance.current && nodes.length > 0) {
      isAutoFittingRef.current = true
      
      // Use fitView with improved parameters for better centering
      reactFlowInstance.current.fitView({ 
        padding: 0.15, // Tighter padding for better view of graph
        duration: 500, // Smooth animation
        minZoom: 0.3,  // Don't zoom out too much
        maxZoom: 1.2   // Don't zoom in too much
      })
      
      setTimeout(() => {
        const viewport = reactFlowInstance.current?.getViewport()
        if (viewport) {
          // Update initial viewport to the new centered position
          initialViewportRef.current = {
            x: viewport.x,
            y: viewport.y,
            zoom: viewport.zoom
          }
          setHasDeviated(false) // Reset deviation state
        }
        isAutoFittingRef.current = false
      }, 600) // Slightly longer timeout for smoother transition
    }
  }, [nodes])
  
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
      previousNodeCountRef.current = 0
      return
    }
    
    console.log('NodeMap: Applying layout -', nodeData.length, 'nodes,', reactFlowEdges.length, 'edges')
    
    // Convert nodeData to ReactFlow node format
    const flowNodes = nodeData.map(node => {
      // Check if this node already exists in current nodes (to preserve position and styles if user-modified)
      // Use ref to avoid dependency on nodes state
      const existingNode = nodesRef.current.find(n => n.id === node.id)
      const existingPosition = existingNode?.position
      const existingStyle = existingNode?.style // Preserve existing styles (including opacity from hover)
      
      return {
        id: node.id,
        type: node.type || 'idea',
        position: existingPosition || { x: 0, y: 0 }, // Temporary position, will be updated by dagre
        style: existingStyle, // Preserve existing styles
        data: {
          label: node.text || '',
          timestamp: node.timestamp,
          topic: node.topic,
          confidence: node.confidence,
          isRoot: node.id === 'root' || node.metadata?.is_root,
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
      // Preserve existing styles (opacity) when applying layout, including hover state
      const currentHoveredId = hoveredNodeIdRef.current
      const nodesWithPreservedStyles = layoutedNodes.map(layoutedNode => {
        // Use ref to avoid dependency on nodes state
        const existingNode = nodesRef.current.find(n => n.id === layoutedNode.id)
        const isHovered = currentHoveredId === layoutedNode.id
        const shouldDim = currentHoveredId !== null && !isHovered
        
        // Preserve existing style or apply hover-based opacity
        const preservedStyle = existingNode?.style || {}
        return {
          ...layoutedNode,
          style: {
            ...preservedStyle,
            opacity: shouldDim ? 0.4 : (preservedStyle.opacity !== undefined ? preservedStyle.opacity : 1),
          },
        }
      })
      console.log('NodeMap: Layouted nodes:', nodesWithPreservedStyles.map(n => ({ id: n.id, pos: n.position })))
      setNodes(nodesWithPreservedStyles)
      // Update ref
      nodesRef.current = nodesWithPreservedStyles
      
      // Auto-fit to center ONLY when new nodes are added (compare node count)
      const currentNodeCount = nodeData.length
      const previousNodeCount = previousNodeCountRef.current
      
      if (currentNodeCount > previousNodeCount && reactFlowInstance.current) {
        // New nodes were added - auto-center with improved logic
        isAutoFittingRef.current = true
        setTimeout(() => {
          if (reactFlowInstance.current) {
            // Use improved fitView with better parameters
            reactFlowInstance.current.fitView({ 
              padding: 0.15, // Tighter padding for better view
              duration: 500, // Slightly longer for smoother animation
              minZoom: 0.3,  // Don't zoom out too much
              maxZoom: 1.2   // Don't zoom in too much
            })
            // Update initial viewport after auto-fit
            setTimeout(() => {
              const viewport = reactFlowInstance.current?.getViewport()
              if (viewport) {
                initialViewportRef.current = {
                  x: viewport.x,
                  y: viewport.y,
                  zoom: viewport.zoom
                }
                setHasDeviated(false) // Reset deviation after auto-centering new nodes
              }
              isAutoFittingRef.current = false
            }, 600)
          }
        }, 150) // Slightly longer delay to ensure layout is complete
      }
      
      // Update previous node count
      previousNodeCountRef.current = currentNodeCount
    } else if (flowNodes.length > 0) {
      // No edges yet, position root at center-top, others below
      console.log('NodeMap: No edges, using simple positioning for', flowNodes.length, 'nodes')
      // Preserve hover styles when positioning nodes without edges
      const currentHoveredId = hoveredNodeIdRef.current
      const positionedNodes = flowNodes.map((node, index) => {
        // Use ref to avoid dependency on nodes state
        const existingNode = nodesRef.current.find(n => n.id === node.id)
        const baseNode = node.data.isRoot
          ? { ...node, position: { x: 400, y: 50 } }
          : { ...node, position: existingNode?.position || { x: 400, y: 150 + index * 150 } }
        
        // Preserve existing styles and apply hover state
        const isHovered = currentHoveredId === node.id
        const shouldDim = currentHoveredId !== null && !isHovered
        const preservedStyle = existingNode?.style || {}
        
        return {
          ...baseNode,
          style: {
            ...preservedStyle,
            opacity: shouldDim ? 0.4 : (preservedStyle.opacity !== undefined ? preservedStyle.opacity : 1),
          },
        }
      })
      console.log('NodeMap: Positioned nodes:', positionedNodes.map(n => ({ id: n.id, pos: n.position })))
      setNodes(positionedNodes)
      // Update ref
      nodesRef.current = positionedNodes
      
      // Auto-fit to center ONLY when new nodes are added (compare node count)
      const currentNodeCount = nodeData.length
      const previousNodeCount = previousNodeCountRef.current
      
      if (currentNodeCount > previousNodeCount && reactFlowInstance.current) {
        // New nodes were added - auto-center with improved logic
        isAutoFittingRef.current = true
        setTimeout(() => {
          if (reactFlowInstance.current) {
            reactFlowInstance.current.fitView({ 
              padding: 0.15,
              duration: 500,
              minZoom: 0.3,
              maxZoom: 1.2
            })
            setTimeout(() => {
              const viewport = reactFlowInstance.current?.getViewport()
              if (viewport) {
                initialViewportRef.current = {
                  x: viewport.x,
                  y: viewport.y,
                  zoom: viewport.zoom
                }
                setHasDeviated(false)
              }
              isAutoFittingRef.current = false
            }, 600)
          }
        }, 150)
      } else if (previousNodeCount === 0 && currentNodeCount > 0 && reactFlowInstance.current) {
        // First time nodes appear - auto-center with longer delay to ensure layout is complete
        isAutoFittingRef.current = true
        setTimeout(() => {
          if (reactFlowInstance.current) {
            // Use fitView to center the graph properly
            reactFlowInstance.current.fitView({ 
              padding: 0.15,
              duration: 600, // Longer duration for smoother initial centering
              minZoom: 0.3,
              maxZoom: 1.2,
              includeHiddenNodes: false
            })
            setTimeout(() => {
              const viewport = reactFlowInstance.current?.getViewport()
              if (viewport) {
                // Store the centered viewport as initial
                initialViewportRef.current = {
                  x: viewport.x,
                  y: viewport.y,
                  zoom: viewport.zoom
                }
                setHasDeviated(false)
              }
              isAutoFittingRef.current = false
            }, 700) // Longer timeout to ensure animation completes
          }
        }, 300) // Longer delay to ensure dagre layout is fully applied
      }
      
      // Update previous node count
      previousNodeCountRef.current = currentNodeCount
    }
  }, [nodeData, reactFlowEdges, userModifiedNodes]) // Removed nodes from deps to prevent infinite loop

  // Update ref when hover changes
  useEffect(() => {
    hoveredNodeIdRef.current = hoveredNodeId
  }, [hoveredNodeId])
  
  // Update node styles based on hover state (simplified - just dim non-hovered nodes)
  // This effect runs independently and preserves node positions
  useEffect(() => {
    setNodes((nds) => {
      if (nds.length === 0) return nds
      
      const currentHoveredId = hoveredNodeIdRef.current
      
      const updatedNodes = nds.map((node) => {
        const isHovered = currentHoveredId === node.id
        const shouldDim = currentHoveredId !== null && !isHovered

        return {
          ...node,
          // Preserve all existing properties, only update opacity and hover state
          style: {
            ...node.style,
            opacity: shouldDim ? 0.4 : 1,
          },
          data: {
            ...node.data,
            isHovered: isHovered,
          }
        }
      })
      
      // Update ref
      nodesRef.current = updatedNodes
      return updatedNodes
    })
  }, [hoveredNodeId, setNodes]) // setNodes is stable, so this is safe

  // Update edge styles based on hover (dim edges when hovering)
  useEffect(() => {
    setEdges((eds) => eds.map((edge) => {
      const shouldDim = hoveredNodeId !== null && 
                       hoveredNodeId !== edge.source && 
                       hoveredNodeId !== edge.target

      return {
        ...edge,
        style: {
          ...edge.style,
          opacity: shouldDim ? 0.3 : 1,
        }
      }
    }))
  }, [hoveredNodeId, setEdges])

  // Update edges when edgeData changes - only after nodes are set
  useEffect(() => {
    // Don't validate edges if nodes haven't been set yet
    if (nodes.length === 0 && reactFlowEdges.length > 0) {
      console.log('NodeMap: Waiting for nodes before validating edges')
      return
    }
    
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
          onViewportChange={onViewportChange}
          onWheel={(event) => {
            // Track wheel zoom - mark as deviated immediately
            if (event.deltaY !== 0 && !isAutoFittingRef.current) {
              setHasDeviated(true)
            }
          }}
          onNodeDragStop={onNodeDragStop}
          onNodeClick={(event, node) => {
            console.log('[CLICK] Node clicked:', node.id)
            
            // Skip root nodes
            if (node.id.startsWith('root') || node.id === 'root') {
              console.log('[CLICK] Skipping root node')
              return
            }
            
            // Toggle: if same node clicked, hide bubble; otherwise show for new node
            if (clickedNodeId === node.id) {
              console.log('[CLICK] Toggling off bubble for node:', node.id)
              setClickedNodeId(null)
              setClickedNodePosition(null)
            } else {
              console.log('[CLICK] Showing bubble for node:', node.id)
              setClickedNodeId(node.id)
              // Get node's screen position from the event target
              const nodeElement = event.currentTarget
              if (nodeElement) {
                const rect = nodeElement.getBoundingClientRect()
                // Center of the node
                const screenX = rect.left + rect.width / 2
                const screenY = rect.top + rect.height / 2
                console.log('[CLICK] Node screen position:', { x: screenX, y: screenY })
                setClickedNodePosition({ x: screenX, y: screenY })
              } else {
                console.log('[CLICK] No node element, using graph position')
                // Fallback: use graph coordinates
                setClickedNodePosition(node.position)
              }
            }
          }}
          onNodeMouseEnter={(event, node) => {
            // Keep hover for visual effects (enlarge, dim others)
            setHoveredNodeId(node.id)
          }}
          onNodeMouseLeave={() => {
            // Keep hover for visual effects
            setHoveredNodeId(null)
          }}
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
          <MiniMap 
            nodeColor={(node) => {
              // Get cluster color from node data
              const clusterColor = node.data?.metadata?.cluster_color
              if (clusterColor) {
                return clusterColor
              }
              // Default colors based on node type
              if (node.data?.isRoot) return '#4caf50'
              if (node.type === 'decision') return '#2196f3'
              if (node.type === 'action') return '#4caf50'
              if (node.type === 'proposal') return '#e91e63'
              return '#ff9800' // idea
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
            style={{
              backgroundColor: '#fafafa',
            }}
          />
          {hasDeviated && (
            <button
              className="recentre-button"
              onClick={handleRecentre}
              title="Recentre graph"
            >
              ↻ Recentre
            </button>
          )}
        </ReactFlow>
      )}
      {/* Node summary bubble - rendered outside ReactFlow to not affect layout */}
      {clickedNodeId && clickedNodePosition && meetingId && !clickedNodeId.startsWith('root') && (
        <NodeHoverBubble
          nodeId={clickedNodeId}
          meetingId={meetingId}
          nodePosition={clickedNodePosition}
          reactFlowInstance={reactFlowInstance.current}
        />
      )}
    </div>
  )
}

