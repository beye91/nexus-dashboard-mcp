-- Migration: Add LDAP Integration and User-Cluster Assignment
-- Version: 003
-- Date: 2025-12-04
-- Description: Adds LDAP configuration, group mappings, and user-cluster assignment

-- ==================== User-Cluster Assignment ====================

-- User-Cluster assignment (M:M) - Restrict which clusters a user can access
CREATE TABLE IF NOT EXISTS user_clusters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, cluster_id)
);

CREATE INDEX IF NOT EXISTS idx_user_clusters_user_id ON user_clusters(user_id);
CREATE INDEX IF NOT EXISTS idx_user_clusters_cluster_id ON user_clusters(cluster_id);

-- ==================== LDAP Configuration ====================

-- LDAP Server Configuration (supports multiple LDAP servers)
CREATE TABLE IF NOT EXISTS ldap_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    is_enabled BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,

    -- Connection Settings
    server_url VARCHAR(500) NOT NULL,           -- ldap:// or ldaps://
    base_dn VARCHAR(500) NOT NULL,              -- e.g., "dc=example,dc=com"
    bind_dn VARCHAR(500),                       -- Admin user DN for searches
    bind_password_encrypted TEXT,               -- Encrypted with Fernet

    -- TLS/SSL Settings
    use_ssl BOOLEAN DEFAULT FALSE,              -- Use LDAPS (port 636)
    use_starttls BOOLEAN DEFAULT FALSE,         -- Use STARTTLS
    verify_ssl BOOLEAN DEFAULT TRUE,            -- Verify server certificate
    ca_certificate TEXT,                        -- Optional CA cert for verification

    -- User Search Settings
    user_search_base VARCHAR(500),              -- Subtree for user search (relative to base_dn)
    user_search_filter VARCHAR(500) DEFAULT '(objectClass=person)',
    user_object_class VARCHAR(100) DEFAULT 'person',

    -- User Attribute Mapping (configurable for AD vs OpenLDAP)
    username_attribute VARCHAR(100) DEFAULT 'sAMAccountName',  -- AD: sAMAccountName, LDAP: uid
    email_attribute VARCHAR(100) DEFAULT 'mail',
    display_name_attribute VARCHAR(100) DEFAULT 'displayName',
    member_of_attribute VARCHAR(100) DEFAULT 'memberOf',

    -- Group Search Settings
    group_search_base VARCHAR(500),             -- Subtree for group search
    group_search_filter VARCHAR(500) DEFAULT '(objectClass=group)',
    group_object_class VARCHAR(100) DEFAULT 'group',
    group_name_attribute VARCHAR(100) DEFAULT 'cn',
    group_member_attribute VARCHAR(100) DEFAULT 'member',

    -- Sync Settings
    sync_interval_minutes INTEGER DEFAULT 60,
    auto_create_users BOOLEAN DEFAULT TRUE,     -- Create users on first login
    auto_sync_groups BOOLEAN DEFAULT TRUE,      -- Sync group memberships
    default_role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,

    -- Status Tracking
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),               -- 'success', 'partial', 'failed'
    last_sync_message TEXT,
    last_sync_users_created INTEGER DEFAULT 0,
    last_sync_users_updated INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ldap_config_enabled ON ldap_config(is_enabled);
CREATE INDEX IF NOT EXISTS idx_ldap_config_primary ON ldap_config(is_primary);

-- ==================== LDAP Group Mappings ====================

-- LDAP Group to Role Mapping
CREATE TABLE IF NOT EXISTS ldap_group_role_mappings (
    id SERIAL PRIMARY KEY,
    ldap_config_id INTEGER NOT NULL REFERENCES ldap_config(id) ON DELETE CASCADE,
    ldap_group_dn VARCHAR(500) NOT NULL,        -- Full DN of LDAP group
    ldap_group_name VARCHAR(255) NOT NULL,      -- Display name for UI
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(ldap_config_id, ldap_group_dn, role_id)
);

CREATE INDEX IF NOT EXISTS idx_ldap_group_role_config ON ldap_group_role_mappings(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_ldap_group_role_role ON ldap_group_role_mappings(role_id);

-- LDAP Group to Cluster Mapping (for cluster access based on LDAP groups)
CREATE TABLE IF NOT EXISTS ldap_group_cluster_mappings (
    id SERIAL PRIMARY KEY,
    ldap_config_id INTEGER NOT NULL REFERENCES ldap_config(id) ON DELETE CASCADE,
    ldap_group_dn VARCHAR(500) NOT NULL,        -- Full DN of LDAP group
    ldap_group_name VARCHAR(255) NOT NULL,      -- Display name for UI
    cluster_id INTEGER NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(ldap_config_id, ldap_group_dn, cluster_id)
);

CREATE INDEX IF NOT EXISTS idx_ldap_group_cluster_config ON ldap_group_cluster_mappings(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_ldap_group_cluster_cluster ON ldap_group_cluster_mappings(cluster_id);

-- ==================== Extend Users Table for LDAP ====================

-- Add LDAP-specific columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS ldap_dn VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS ldap_config_id INTEGER REFERENCES ldap_config(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_users_ldap_dn ON users(ldap_dn);
CREATE INDEX IF NOT EXISTS idx_users_ldap_config_id ON users(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_users_auth_type ON users(auth_type);

-- ==================== Comments ====================

COMMENT ON TABLE user_clusters IS 'Maps users to clusters they can access. Empty = all clusters allowed for superusers.';
COMMENT ON TABLE ldap_config IS 'LDAP server configuration. Supports AD and OpenLDAP with configurable attribute mapping.';
COMMENT ON TABLE ldap_group_role_mappings IS 'Maps LDAP groups to roles for automatic role assignment.';
COMMENT ON TABLE ldap_group_cluster_mappings IS 'Maps LDAP groups to clusters for automatic cluster access.';
COMMENT ON COLUMN users.ldap_dn IS 'Distinguished Name from LDAP server for LDAP-authenticated users.';
COMMENT ON COLUMN users.ldap_config_id IS 'Reference to LDAP config for LDAP-authenticated users.';
