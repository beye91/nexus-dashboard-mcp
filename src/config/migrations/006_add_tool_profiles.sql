-- Migration 006: Add Tool Profiles for controlling tool exposure to MCP clients
-- Tool profiles allow administrators to limit which tools/operations are visible
-- to specific users, addressing the MCP client limit (typically 40-128 tools).

-- Tool profiles table
CREATE TABLE IF NOT EXISTS tool_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    max_tools INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Tool profile operations (M:M between profile and operation names)
CREATE TABLE IF NOT EXISTS tool_profile_operations (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES tool_profiles(id) ON DELETE CASCADE,
    operation_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(profile_id, operation_name)
);

-- Add tool_profile_id to users (nullable - users without a profile use role-based filtering)
ALTER TABLE users ADD COLUMN IF NOT EXISTS tool_profile_id INTEGER REFERENCES tool_profiles(id) ON DELETE SET NULL;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tool_profiles_name ON tool_profiles(name);
CREATE INDEX IF NOT EXISTS idx_tool_profiles_active ON tool_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_tool_profile_operations_profile_id ON tool_profile_operations(profile_id);
CREATE INDEX IF NOT EXISTS idx_tool_profile_operations_operation_name ON tool_profile_operations(operation_name);
CREATE INDEX IF NOT EXISTS idx_users_tool_profile_id ON users(tool_profile_id);

-- Seed default profiles
-- max_tools=0 on 'Full Access' profile means no filtering
INSERT INTO tool_profiles (name, description, max_tools) VALUES
    ('Fabric Operations', 'Common fabric management operations for VLAN, VRF, BD, and EPG', 30),
    ('Monitoring & Health', 'Read-only monitoring and health check operations', 25),
    ('Troubleshooting', 'Network analysis and troubleshooting tools', 25),
    ('Full Access', 'All available operations (no filtering)', 0)
ON CONFLICT (name) DO NOTHING;

COMMENT ON TABLE tool_profiles IS 'Profiles that control which tools/operations are exposed to MCP clients per user';
COMMENT ON TABLE tool_profile_operations IS 'Maps tool profiles to allowed operation names';
COMMENT ON COLUMN tool_profiles.max_tools IS 'Maximum number of tools to expose. 0 means no limit (Full Access).';
COMMENT ON COLUMN users.tool_profile_id IS 'Optional tool profile assignment. Takes priority over role-based tool filtering.';
