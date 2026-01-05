-- Migration: Change from user_id to meeting_id
-- This migration:
-- 1. Creates meetings table
-- 2. Creates meetings for existing users
-- 3. Changes user_id columns to meeting_id
-- 4. Migrates existing data

-- Step 1: Create meetings table
CREATE TABLE IF NOT EXISTS meetings (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'Legacy Meeting',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at);

-- Step 2: Create meetings for existing users (one meeting per user)
-- This creates a "Legacy Meeting" for each unique user_id in graph_nodes
INSERT INTO meetings (id, user_id, title, description)
SELECT 
    'meeting_' || user_id || '_legacy' as id,
    user_id,
    'Legacy Meeting' as title,
    'Migrated from old user-based system' as description
FROM (
    SELECT DISTINCT user_id 
    FROM graph_nodes 
    WHERE user_id IS NOT NULL
) AS unique_users
ON CONFLICT (id) DO NOTHING;

-- Step 3: Add meeting_id column to graph_nodes (temporarily keep user_id)
ALTER TABLE graph_nodes ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(255);

-- Step 4: Assign existing nodes to meetings
UPDATE graph_nodes gn
SET meeting_id = 'meeting_' || gn.user_id || '_legacy'
WHERE gn.meeting_id IS NULL AND gn.user_id IS NOT NULL;

-- Step 5: Add foreign key constraint for meeting_id
ALTER TABLE graph_nodes 
ADD CONSTRAINT fk_node_meeting 
FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;

-- Step 6: Create index for meeting_id
CREATE INDEX IF NOT EXISTS idx_graph_nodes_meeting_id ON graph_nodes(meeting_id);

-- Step 7: Drop old user_id index and create new meeting_id index
DROP INDEX IF EXISTS idx_graph_nodes_user_id;
DROP INDEX IF EXISTS idx_graph_nodes_user_parent;
DROP INDEX IF EXISTS idx_graph_nodes_user_id_unique;

-- Step 8: Remove user_id column from graph_nodes (after data migration)
-- We'll do this in a separate step after verifying data

-- Step 9: Update graph_edges
ALTER TABLE graph_edges ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(255);

-- Step 10: Assign existing edges to meetings based on their nodes
UPDATE graph_edges ge
SET meeting_id = (
    SELECT meeting_id 
    FROM graph_nodes gn 
    WHERE gn.id = ge.from_node 
    LIMIT 1
)
WHERE ge.meeting_id IS NULL;

-- Step 11: Add foreign key and index for edges
ALTER TABLE graph_edges 
ADD CONSTRAINT fk_edge_meeting 
FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_graph_edges_meeting_id ON graph_edges(meeting_id);
DROP INDEX IF EXISTS idx_graph_edges_user_id;

-- Step 12: Update clusters table
-- First, create new clusters table structure
ALTER TABLE clusters ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(255);

-- Step 13: Migrate clusters to meetings
-- This is complex - we'll assign clusters to meetings based on their nodes
UPDATE clusters c
SET meeting_id = (
    SELECT DISTINCT gn.meeting_id
    FROM cluster_members cm
    JOIN graph_nodes gn ON cm.node_id = gn.id
    WHERE cm.cluster_id = c.cluster_id AND cm.user_id = c.user_id
    LIMIT 1
)
WHERE c.meeting_id IS NULL;

-- Step 14: Update cluster_members
ALTER TABLE cluster_members ADD COLUMN IF NOT EXISTS meeting_id VARCHAR(255);

UPDATE cluster_members cm
SET meeting_id = (
    SELECT meeting_id 
    FROM graph_nodes gn 
    WHERE gn.id = cm.node_id 
    LIMIT 1
)
WHERE cm.meeting_id IS NULL;

-- Step 15: Update cluster primary key and foreign keys
-- Drop old constraints
ALTER TABLE clusters DROP CONSTRAINT IF EXISTS clusters_pkey;
ALTER TABLE clusters DROP CONSTRAINT IF EXISTS clusters_cluster_id_user_id_key;

-- Add new primary key with meeting_id
ALTER TABLE clusters ADD PRIMARY KEY (cluster_id, meeting_id);
ALTER TABLE clusters ADD UNIQUE (cluster_id, meeting_id);

-- Update cluster_members foreign key
ALTER TABLE cluster_members DROP CONSTRAINT IF EXISTS fk_cluster;
ALTER TABLE cluster_members 
ADD CONSTRAINT fk_cluster 
FOREIGN KEY (cluster_id, meeting_id) 
REFERENCES clusters(cluster_id, meeting_id) ON DELETE CASCADE;

-- Step 16: Create new indexes
CREATE INDEX IF NOT EXISTS idx_clusters_meeting_id ON clusters(meeting_id);
CREATE INDEX IF NOT EXISTS idx_cluster_members_meeting_id ON cluster_members(meeting_id);
DROP INDEX IF EXISTS idx_clusters_user_id;
DROP INDEX IF EXISTS idx_cluster_members_user_id;

-- Step 17: Make meeting_id NOT NULL after migration
-- We'll do this after verifying all data is migrated
-- ALTER TABLE graph_nodes ALTER COLUMN meeting_id SET NOT NULL;
-- ALTER TABLE graph_edges ALTER COLUMN meeting_id SET NOT NULL;
-- ALTER TABLE clusters ALTER COLUMN meeting_id SET NOT NULL;
-- ALTER TABLE cluster_members ALTER COLUMN meeting_id SET NOT NULL;

-- Step 18: Remove user_id columns (DO THIS LAST, after verifying everything works)
-- ALTER TABLE graph_nodes DROP COLUMN user_id;
-- ALTER TABLE graph_edges DROP COLUMN user_id;
-- ALTER TABLE clusters DROP COLUMN user_id;
-- ALTER TABLE cluster_members DROP COLUMN user_id;

