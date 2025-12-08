-- Migration: 005_add_resource_groups
-- Description: Add resource groups for MCP tool consolidation
-- This allows customization of how API operations are grouped into MCP tools.

-- Resource groups table
-- Defines the consolidated tool groups
CREATE TABLE IF NOT EXISTS resource_groups (
    id SERIAL PRIMARY KEY,
    group_key VARCHAR(100) NOT NULL UNIQUE,   -- e.g., "analyze_fabrics"
    display_name VARCHAR(200),                 -- Human-readable name
    description TEXT,                          -- Description shown in MCP tool
    is_enabled BOOLEAN DEFAULT true,           -- Enable/disable this group
    is_custom BOOLEAN DEFAULT false,           -- True if user-created, false if auto-generated
    sort_order INTEGER DEFAULT 0,              -- For UI ordering
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Resource group mappings table
-- Maps operations to groups (allows custom grouping)
CREATE TABLE IF NOT EXISTS resource_group_mappings (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES resource_groups(id) ON DELETE CASCADE,
    operation_id VARCHAR(255) NOT NULL,        -- The operation_id from api_endpoints
    api_name VARCHAR(50) NOT NULL,             -- API name (analyze, infra, manage, onemanage)
    UNIQUE(operation_id, api_name)             -- Each operation can only be in one group
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_resource_groups_enabled ON resource_groups(is_enabled);
CREATE INDEX IF NOT EXISTS idx_resource_groups_key ON resource_groups(group_key);
CREATE INDEX IF NOT EXISTS idx_resource_group_mappings_group ON resource_group_mappings(group_id);
CREATE INDEX IF NOT EXISTS idx_resource_group_mappings_operation ON resource_group_mappings(operation_id);

-- Function to auto-generate default groups from api_endpoints
-- This creates groups based on the first path segment
CREATE OR REPLACE FUNCTION generate_default_resource_groups()
RETURNS void AS $$
DECLARE
    rec RECORD;
    resource_name TEXT;
    group_key TEXT;
    group_id INTEGER;
BEGIN
    -- Get unique resource types from api_endpoints
    FOR rec IN
        SELECT DISTINCT
            api_name,
            SPLIT_PART(path, '/', 2) as resource,
            COUNT(*) as op_count
        FROM api_endpoints
        WHERE SPLIT_PART(path, '/', 2) != ''
        GROUP BY api_name, SPLIT_PART(path, '/', 2)
    LOOP
        group_key := rec.api_name || '_' || rec.resource;

        -- Insert group if not exists
        INSERT INTO resource_groups (group_key, display_name, description, is_custom)
        VALUES (
            group_key,
            INITCAP(REPLACE(rec.resource, '_', ' ')) || ' (' || rec.api_name || ')',
            'Operations for ' || rec.resource || ' resource in ' || rec.api_name || ' API. ' ||
            rec.op_count || ' operations.',
            false
        )
        ON CONFLICT (group_key) DO NOTHING
        RETURNING id INTO group_id;

        -- If inserted (not conflict), get the id
        IF group_id IS NULL THEN
            SELECT id INTO group_id FROM resource_groups WHERE group_key = group_key;
        END IF;

        -- Map operations to this group
        INSERT INTO resource_group_mappings (group_id, operation_id, api_name)
        SELECT
            group_id,
            operation_id,
            rec.api_name
        FROM api_endpoints
        WHERE api_name = rec.api_name
          AND SPLIT_PART(path, '/', 2) = rec.resource
        ON CONFLICT (operation_id, api_name) DO NOTHING;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Note: The function can be called manually after api_endpoints are populated:
-- SELECT generate_default_resource_groups();
-- Or it will be called during database initialization.

-- Add comment to track migration
COMMENT ON TABLE resource_groups IS 'MCP tool consolidation - groups API operations by resource type';
COMMENT ON TABLE resource_group_mappings IS 'Maps API operations to resource groups for tool consolidation';
