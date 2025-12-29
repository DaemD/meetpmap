import { useMemo, useEffect } from 'react'
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
import 'reactflow/dist/style.css'
import './NodeMap.css'

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

function IdeaNode({ data }) {
  const isRoot = data.isRoot || false
  return (
    <div className={`custom-node idea-node${isRoot ? ' root-node' : ''}`}>
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

export default function NodeMap({ nodes: nodeData, edges: edgeData = [] }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  
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
        type: 'smoothstep',
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

  // Update nodes when data changes - Only add new nodes, preserve existing positions
  useEffect(() => {
    if (!nodeData || nodeData.length === 0) {
      return
    }
    
    console.log('NodeMap: Updating -', nodeData.length, 'nodes in data,', nodes.length, 'in React Flow')
    
    const existingIds = new Set(nodes.map(n => n.id))
    const changes = []
    
    // Only add nodes that don't exist yet
    nodeData.forEach(node => {
      if (!existingIds.has(node.id)) {
        // Special positioning for root node
        let newPosition
        if (node.id === 'root' || node.metadata?.is_root) {
          newPosition = { x: 400, y: 50 } // Center-top for root
        } else {
          // Calculate position for new node based on depth if available
          const depth = node.metadata?.depth || 0
          const existingCount = existingIds.size
          const siblingsAtDepth = nodeData.filter(n => 
            (n.metadata?.depth || 0) === depth && existingIds.has(n.id)
          ).length
          
          newPosition = {
            x: 400 + (siblingsAtDepth - depth * 2) * 250, // Spread horizontally by depth
            y: 50 + depth * 150, // Stack vertically by depth
          }
        }
        
        const flowNode = {
          id: node.id,
          type: node.type || 'idea',
          position: newPosition,
          data: {
            label: node.text || '',
            timestamp: node.timestamp,
            topic: node.topic,
            confidence: node.confidence,
            isRoot: node.id === 'root' || node.metadata?.is_root,
          },
        }
        
        changes.push({ type: 'add', item: flowNode })
        console.log('Adding new node:', flowNode.id, flowNode.data.label)
      }
      // Existing nodes are left untouched - their positions are preserved
    })
    
    // Apply only new node additions
    if (changes.length > 0) {
      setNodes((nds) => applyNodeChanges(changes, nds))
    }
  }, [nodeData, nodes, setNodes])

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
          nodeTypes={nodeTypes}
          fitView
          defaultEdgeOptions={{
            style: { strokeWidth: 2, stroke: '#b1b1b7' },
            type: 'smoothstep',
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

