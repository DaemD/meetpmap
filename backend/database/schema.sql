-- MeetMap PostgreSQL Database Schema v2
-- Changed from user_id to meeting_id based architecture
-- Each meeting belongs to a user, but all nodes/edges belong to meetings

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

-- Meetings table
-- Each meeting contains its own graph (user_id is optional)
CREATE TABLE IF NOT EXISTS meetings (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    title VARCHAR(255) NOT NULL DEFAULT 'Untitled Meeting',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at);

-- Graph nodes table
-- Now uses meeting_id instead of user_id
CREATE TABLE IF NOT EXISTS graph_nodes (
    id VARCHAR(255) PRIMARY KEY,
    meeting_id VARCHAR(255) NOT NULL,
    embedding JSONB NOT NULL,
    summary TEXT NOT NULL,
    parent_id VARCHAR(255),
    depth INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_node_meeting FOREIGN KEY (meeting_id) 
        REFERENCES meetings(id) ON DELETE CASCADE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_graph_nodes_meeting_id ON graph_nodes(meeting_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_parent_id ON graph_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_meeting_parent ON graph_nodes(meeting_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_last_updated ON graph_nodes(last_updated);

-- Graph edges table
-- Now uses meeting_id instead of user_id
CREATE TABLE IF NOT EXISTS graph_edges (
    from_node VARCHAR(255) NOT NULL,
    to_node VARCHAR(255) NOT NULL,
    meeting_id VARCHAR(255) NOT NULL,
    edge_type VARCHAR(50) DEFAULT 'extends',
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (from_node, to_node),
    
    -- Foreign keys
    CONSTRAINT fk_from_node FOREIGN KEY (from_node) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_to_node FOREIGN KEY (to_node) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE,
    CONSTRAINT fk_edge_meeting FOREIGN KEY (meeting_id) 
        REFERENCES meetings(id) ON DELETE CASCADE
);

-- Indexes for edges
CREATE INDEX IF NOT EXISTS idx_graph_edges_meeting_id ON graph_edges(meeting_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_from_node ON graph_edges(from_node);
CREATE INDEX IF NOT EXISTS idx_graph_edges_to_node ON graph_edges(to_node);

-- Clusters table
-- Now uses meeting_id instead of user_id
CREATE TABLE IF NOT EXISTS clusters (
    cluster_id INTEGER NOT NULL,
    meeting_id VARCHAR(255) NOT NULL,
    centroid JSONB NOT NULL,
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (cluster_id, meeting_id),
    UNIQUE (cluster_id, meeting_id),
    CONSTRAINT fk_cluster_meeting FOREIGN KEY (meeting_id) 
        REFERENCES meetings(id) ON DELETE CASCADE
);

-- Index for clusters
CREATE INDEX IF NOT EXISTS idx_clusters_meeting_id ON clusters(meeting_id);

-- Cluster members table (junction table)
-- Now uses meeting_id instead of user_id
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id INTEGER NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    meeting_id VARCHAR(255) NOT NULL,
    PRIMARY KEY (cluster_id, node_id),
    CONSTRAINT fk_cluster FOREIGN KEY (cluster_id, meeting_id) 
        REFERENCES clusters(cluster_id, meeting_id) ON DELETE CASCADE,
    CONSTRAINT fk_node FOREIGN KEY (node_id) 
        REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- Indexes for cluster members
CREATE INDEX IF NOT EXISTS idx_cluster_members_cluster_id ON cluster_members(cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_node_id ON cluster_members(node_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_meeting_id ON cluster_members(meeting_id);

-- Graphs table (kept for compatibility, but not used in v2)
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

-- Comments for documentation
COMMENT ON TABLE meetings IS 'Stores meeting metadata - each meeting belongs to a user and contains its own graph';
COMMENT ON TABLE graph_nodes IS 'Stores all graph nodes with embeddings and relationships - linked to meetings';
COMMENT ON TABLE graph_edges IS 'Stores explicit edges between nodes - linked to meetings';
COMMENT ON TABLE clusters IS 'Stores cluster information for node grouping - linked to meetings';
COMMENT ON TABLE cluster_members IS 'Junction table linking nodes to clusters - linked to meetings';

