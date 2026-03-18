-- Migration 010: Add tool_profile_id to roles for role-level tool scoping
-- Version: 010
-- Date: 2026-03-18
-- Description: Extends the roles table with an optional tool profile FK so that
--              administrators can assign a default tool profile at the role level.
--              User-level profiles (from migration 006) continue to take priority
--              over role-level profiles when both are set.

-- ============================================================================
-- SCHEMA CHANGE: Add tool_profile_id column to roles
-- ============================================================================

ALTER TABLE roles
    ADD COLUMN IF NOT EXISTS tool_profile_id INTEGER
        REFERENCES tool_profiles(id) ON DELETE SET NULL;

-- Index for FK lookups and profile-based role queries
CREATE INDEX IF NOT EXISTS idx_roles_tool_profile_id ON roles(tool_profile_id);

COMMENT ON COLUMN roles.tool_profile_id IS
    'Optional tool profile for role-level tool scoping. When set, users with this role get these tools unless overridden by user-level profile.';

-- ============================================================================
-- SEED ADDITIONAL DEFAULT TOOL PROFILES
-- "Full Access" already exists from migration 006 - skip it.
-- ============================================================================

INSERT INTO tool_profiles (name, description, max_tools, is_active)
VALUES
    (
        'Read-Only Analyst',
        'Read-only analysis tools for monitoring and reporting',
        120,
        TRUE
    ),
    (
        'Network Operator',
        'Read and write tools for network operations',
        400,
        TRUE
    ),
    (
        'Infrastructure Viewer',
        'Infrastructure and analysis read-only tools',
        200,
        TRUE
    ),
    (
        'Troubleshooting Only',
        'Troubleshooting workflow tools',
        50,
        TRUE
    )
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- POPULATE tool_profile_operations FOR EACH NEW PROFILE
-- Operation names follow the convention: api_name || '_' || operation_id
-- which matches the format used throughout role_operations and MCP tool names.
-- ============================================================================

-- "Read-Only Analyst": GET operations from the analyze API only
INSERT INTO tool_profile_operations (profile_id, operation_name)
SELECT
    (SELECT id FROM tool_profiles WHERE name = 'Read-Only Analyst'),
    api_name || '_' || operation_id
FROM api_endpoints
WHERE api_name = 'analyze'
  AND http_method = 'GET'
ON CONFLICT DO NOTHING;

-- "Network Operator": All methods across analyze and manage APIs
INSERT INTO tool_profile_operations (profile_id, operation_name)
SELECT
    (SELECT id FROM tool_profiles WHERE name = 'Network Operator'),
    api_name || '_' || operation_id
FROM api_endpoints
WHERE api_name IN ('analyze', 'manage')
ON CONFLICT DO NOTHING;

-- "Infrastructure Viewer": GET operations from infra and analyze APIs
INSERT INTO tool_profile_operations (profile_id, operation_name)
SELECT
    (SELECT id FROM tool_profiles WHERE name = 'Infrastructure Viewer'),
    api_name || '_' || operation_id
FROM api_endpoints
WHERE api_name IN ('infra', 'analyze')
  AND http_method = 'GET'
ON CONFLICT DO NOTHING;

-- "Troubleshooting Only": Distinct operation names referenced by active workflow steps
INSERT INTO tool_profile_operations (profile_id, operation_name)
SELECT DISTINCT
    (SELECT id FROM tool_profiles WHERE name = 'Troubleshooting Only'),
    ws.operation_name
FROM workflow_steps ws
JOIN workflows w ON ws.workflow_id = w.id
WHERE w.is_active = TRUE
ON CONFLICT DO NOTHING;

-- ============================================================================
-- ASSIGN DEFAULT PROFILES TO SYSTEM ROLES
-- ============================================================================

-- Administrator gets full unrestricted access
UPDATE roles
SET tool_profile_id = (SELECT id FROM tool_profiles WHERE name = 'Full Access')
WHERE name = 'Administrator'
  AND is_system_role = TRUE;

-- Network Operator role maps to the Network Operator tool profile
UPDATE roles
SET tool_profile_id = (SELECT id FROM tool_profiles WHERE name = 'Network Operator')
WHERE name = 'Network Operator'
  AND is_system_role = TRUE;

-- Read-Only User role maps to the Read-Only Analyst tool profile
UPDATE roles
SET tool_profile_id = (SELECT id FROM tool_profiles WHERE name = 'Read-Only Analyst')
WHERE name = 'Read-Only User'
  AND is_system_role = TRUE;
