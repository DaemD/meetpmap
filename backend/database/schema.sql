-- MeetMap PostgreSQL Database Schema
-- This schema stores graph nodes, edges, clusters, and user data

-- Enable UUID extension (for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (optional, for future user management)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Graph nodes table
-- Stores all graph nodes with their embeddings and metadata
CREATE TABLE IF NOT EXISTS graph_nodes (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    embedding JSONB NOT NULL,  -- Store as JSON array of floats
    summary TEXT NOT NULL,
    parent_id VARCHAR(255),
    depth INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Foreign key to parent (self-referential)
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    
    -- Note: We'll create indexes separately below
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_graph_nodes_user_id ON graph_nodes(user_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_parent_id ON graph_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_user_parent ON graph_nodes(user_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_last_updated ON graph_nodes(last_updated);

-- Unique constraint: ensures (user_id, id) combination is unique
-- Note: Since id is PRIMARY KEY (globally unique), this index is redundant but harmless
-- It's kept for potential future schema changes where node_id might be per-user
CREATE UNIQUE INDEX IF NOT EXISTS idx_graph_nodes_user_id_unique ON graph_nodes(user_id, id);

-- Graph edges table (explicit storage, though we can derive from parent_id)
-- Useful for future: multiple edge types, edge weights, etc.
CREATE TABLE IF NOT EXISTS graph_edges (
    from_node VARCHAR(255) NOT NULL,
    to_node VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    edge_type VARCHAR(50) DEFAULT 'extends',
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (from_node, to_node),
    
    -- Foreign keys
    CONSTRAINT fk_from_node FOREIGN KEY (from_node) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_to_node FOREIGN KEY (to_node) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- Indexes for edges
CREATE INDEX IF NOT EXISTS idx_graph_edges_user_id ON graph_edges(user_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_from_node ON graph_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_graph_edges_to_node ON graph_edges(to_node);

-- Clusters table
-- Stores cluster information (centroids, colors)
CREATE TABLE IF NOT EXISTS clusters (
    cluster_id INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    centroid JSONB NOT NULL,  -- Store as JSON array of floats
    color VARCHAR(7),  -- Hex color code
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (cluster_id, user_id)
);

-- Index for clusters
CREATE INDEX IF NOT EXISTS idx_clusters_user_id ON clusters(user_id);

-- Cluster members table (junction table)
-- Links nodes to clusters
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id INTEGER NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    
    PRIMARY KEY (cluster_id, node_id),
    
    -- Foreign keys
    CONSTRAINT fk_cluster FOREIGN KEY (cluster_id) 
        REFERENCES clusters(cluster_id) ON DELETE CASCADE,
    CONSTRAINT fk_node FOREIGN KEY (node_id) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- Indexes for cluster members
CREATE INDEX IF NOT EXISTS idx_cluster_members_cluster_id ON cluster_members(cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_node_id ON cluster_members(node_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_user_id ON cluster_members(user_id);

-- Graphs table (for multiple graphs per user - future feature)
CREATE TABLE IF NOT EXISTS graphs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL DEFAULT 'Untitled Graph',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for graphs
CREATE INDEX IF NOT EXISTS idx_graphs_user_id ON graphs(user_id);

-- Add graph_id to graph_nodes (for future multiple graphs support)
-- We'll add this column later if needed, for now keeping it simple

-- Comments for documentation
COMMENT ON TABLE graph_nodes IS 'Stores all graph nodes with embeddings and relationships';
COMMENT ON TABLE graph_edges IS 'Stores explicit edges between nodes (can be derived from parent_id)';
COMMENT ON TABLE clusters IS 'Stores cluster information for node grouping';
COMMENT ON TABLE cluster_members IS 'Junction table linking nodes to clusters';
COMMENT ON TABLE graphs IS 'Stores graph metadata (for multiple graphs per user)';

