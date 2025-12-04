-- Nexus Dashboard MCP Server Database Schema

-- Clusters table for storing Nexus Dashboard cluster credentials
CREATE TABLE IF NOT EXISTS clusters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,
    verify_ssl BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Security configuration table
CREATE TABLE IF NOT EXISTS security_config (
    id SERIAL PRIMARY KEY,
    edit_mode_enabled BOOLEAN DEFAULT FALSE,
    allowed_operations TEXT[], -- Array of allowed operation IDs in edit mode
    audit_logging BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API endpoints mapping table
CREATE TABLE IF NOT EXISTS api_endpoints (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL, -- 'manage', 'analyze', 'infra', etc.
    operation_id VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    path VARCHAR(512) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    requires_edit_mode BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(api_name, operation_id)
);

-- Audit log for tracking all operations
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    cluster_id INTEGER REFERENCES clusters(id),
    user_id VARCHAR(255),
    operation_id VARCHAR(255),
    http_method VARCHAR(10),
    path VARCHAR(512),
    request_body JSONB,
    response_status INTEGER,
    response_body JSONB,
    error_message TEXT,
    client_ip VARCHAR(45),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- ==================== RBAC Tables ====================

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    api_token VARCHAR(64) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    auth_type VARCHAR(50) DEFAULT 'local',  -- 'local' or 'ldap'
    ldap_dn VARCHAR(500),                   -- Distinguished Name for LDAP users
    ldap_config_id INTEGER,                 -- References ldap_config(id) - added later
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Roles table for RBAC
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    edit_mode_enabled BOOLEAN DEFAULT FALSE,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Role operations mapping
CREATE TABLE IF NOT EXISTS role_operations (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    operation_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(role_id, operation_name)
);

-- User-Role association table (M:M)
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, role_id)
);

-- User sessions for authentication
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- User-Cluster assignment (M:M) - Restrict which clusters a user can access
CREATE TABLE IF NOT EXISTS user_clusters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, cluster_id)
);

-- ==================== LDAP Tables ====================

-- LDAP Server Configuration
CREATE TABLE IF NOT EXISTS ldap_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    is_enabled BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,
    server_url VARCHAR(500) NOT NULL,
    base_dn VARCHAR(500) NOT NULL,
    bind_dn VARCHAR(500),
    bind_password_encrypted TEXT,
    use_ssl BOOLEAN DEFAULT FALSE,
    use_starttls BOOLEAN DEFAULT FALSE,
    verify_ssl BOOLEAN DEFAULT TRUE,
    ca_certificate TEXT,
    user_search_base VARCHAR(500),
    user_search_filter VARCHAR(500) DEFAULT '(objectClass=person)',
    user_object_class VARCHAR(100) DEFAULT 'person',
    username_attribute VARCHAR(100) DEFAULT 'sAMAccountName',
    email_attribute VARCHAR(100) DEFAULT 'mail',
    display_name_attribute VARCHAR(100) DEFAULT 'displayName',
    member_of_attribute VARCHAR(100) DEFAULT 'memberOf',
    group_search_base VARCHAR(500),
    group_search_filter VARCHAR(500) DEFAULT '(objectClass=group)',
    group_object_class VARCHAR(100) DEFAULT 'group',
    group_name_attribute VARCHAR(100) DEFAULT 'cn',
    group_member_attribute VARCHAR(100) DEFAULT 'member',
    sync_interval_minutes INTEGER DEFAULT 60,
    auto_create_users BOOLEAN DEFAULT TRUE,
    auto_sync_groups BOOLEAN DEFAULT TRUE,
    default_role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    last_sync_message TEXT,
    last_sync_users_created INTEGER DEFAULT 0,
    last_sync_users_updated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- LDAP Group to Role Mapping
CREATE TABLE IF NOT EXISTS ldap_group_role_mappings (
    id SERIAL PRIMARY KEY,
    ldap_config_id INTEGER NOT NULL REFERENCES ldap_config(id) ON DELETE CASCADE,
    ldap_group_dn VARCHAR(500) NOT NULL,
    ldap_group_name VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(ldap_config_id, ldap_group_dn, role_id)
);

-- LDAP Group to Cluster Mapping
CREATE TABLE IF NOT EXISTS ldap_group_cluster_mappings (
    id SERIAL PRIMARY KEY,
    ldap_config_id INTEGER NOT NULL REFERENCES ldap_config(id) ON DELETE CASCADE,
    ldap_group_dn VARCHAR(500) NOT NULL,
    ldap_group_name VARCHAR(255) NOT NULL,
    cluster_id INTEGER NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(ldap_config_id, ldap_group_dn, cluster_id)
);

-- ==================== Indexes ====================

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_cluster_id ON audit_log(cluster_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation_id ON audit_log(operation_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_client_ip ON audit_log(client_ip);

-- API endpoints indexes
CREATE INDEX IF NOT EXISTS idx_api_endpoints_api_name ON api_endpoints(api_name);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_enabled ON api_endpoints(enabled);

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_token ON users(api_token);

-- Role indexes
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- Role operations indexes
CREATE INDEX IF NOT EXISTS idx_role_operations_role_id ON role_operations(role_id);
CREATE INDEX IF NOT EXISTS idx_role_operations_operation_name ON role_operations(operation_name);

-- User roles indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);

-- User sessions indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- User clusters indexes
CREATE INDEX IF NOT EXISTS idx_user_clusters_user_id ON user_clusters(user_id);
CREATE INDEX IF NOT EXISTS idx_user_clusters_cluster_id ON user_clusters(cluster_id);

-- LDAP config indexes
CREATE INDEX IF NOT EXISTS idx_ldap_config_enabled ON ldap_config(is_enabled);
CREATE INDEX IF NOT EXISTS idx_ldap_config_primary ON ldap_config(is_primary);

-- LDAP group mappings indexes
CREATE INDEX IF NOT EXISTS idx_ldap_group_role_config ON ldap_group_role_mappings(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_ldap_group_role_role ON ldap_group_role_mappings(role_id);
CREATE INDEX IF NOT EXISTS idx_ldap_group_cluster_config ON ldap_group_cluster_mappings(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_ldap_group_cluster_cluster ON ldap_group_cluster_mappings(cluster_id);

-- User LDAP fields indexes
CREATE INDEX IF NOT EXISTS idx_users_ldap_dn ON users(ldap_dn);
CREATE INDEX IF NOT EXISTS idx_users_ldap_config_id ON users(ldap_config_id);
CREATE INDEX IF NOT EXISTS idx_users_auth_type ON users(auth_type);

-- ==================== Default Data ====================

-- Insert default security configuration
INSERT INTO security_config (edit_mode_enabled, audit_logging)
VALUES (FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- Insert default system roles
INSERT INTO roles (name, description, edit_mode_enabled, is_system_role)
VALUES
    ('Administrator', 'Full access to all features and operations', TRUE, TRUE),
    ('Operator', 'View and execute read-only operations', FALSE, TRUE),
    ('Viewer', 'Read-only access to view data', FALSE, TRUE)
ON CONFLICT (name) DO NOTHING;

-- ==================== Comments ====================

COMMENT ON TABLE clusters IS 'Stores Nexus Dashboard cluster connection information with encrypted credentials';
COMMENT ON TABLE security_config IS 'Global security configuration for the MCP server';
COMMENT ON TABLE api_endpoints IS 'Registry of all available API endpoints from OpenAPI specs';
COMMENT ON TABLE audit_log IS 'Audit trail of all operations performed through the MCP server';
COMMENT ON TABLE users IS 'User accounts for authentication and RBAC';
COMMENT ON TABLE roles IS 'Roles for role-based access control';
COMMENT ON TABLE role_operations IS 'Maps roles to allowed operations';
COMMENT ON TABLE user_roles IS 'Many-to-many relationship between users and roles';
COMMENT ON TABLE user_sessions IS 'Active user sessions for authentication';

-- ==================== API Guidance System Tables ====================

-- API-level guidance table
CREATE TABLE IF NOT EXISTS api_guidance (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    when_to_use TEXT,
    when_not_to_use TEXT,
    examples JSONB DEFAULT '[]',
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Category/tag guidance table
CREATE TABLE IF NOT EXISTS category_guidance (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    when_to_use TEXT,
    related_categories JSONB DEFAULT '[]',
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(api_name, category_name)
);

-- Workflow definitions table
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    problem_statement TEXT,
    use_case_tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow steps table
CREATE TABLE IF NOT EXISTS workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    operation_name VARCHAR(255) NOT NULL,
    description TEXT,
    expected_output TEXT,
    optional BOOLEAN DEFAULT FALSE,
    fallback_operation VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workflow_id, step_order)
);

-- Tool description overrides table
CREATE TABLE IF NOT EXISTS tool_description_overrides (
    id SERIAL PRIMARY KEY,
    operation_name VARCHAR(255) NOT NULL UNIQUE,
    enhanced_description TEXT,
    usage_hint TEXT,
    related_tools JSONB DEFAULT '[]',
    common_parameters JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System prompt sections table
CREATE TABLE IF NOT EXISTS system_prompt_sections (
    id SERIAL PRIMARY KEY,
    section_name VARCHAR(100) NOT NULL UNIQUE,
    section_order INTEGER DEFAULT 0,
    title VARCHAR(255),
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Guidance indexes
CREATE INDEX IF NOT EXISTS idx_api_guidance_api_name ON api_guidance(api_name);
CREATE INDEX IF NOT EXISTS idx_api_guidance_priority ON api_guidance(priority);
CREATE INDEX IF NOT EXISTS idx_api_guidance_is_active ON api_guidance(is_active);
CREATE INDEX IF NOT EXISTS idx_category_guidance_api_name ON category_guidance(api_name);
CREATE INDEX IF NOT EXISTS idx_category_guidance_category_name ON category_guidance(category_name);
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_tool_description_overrides_operation_name ON tool_description_overrides(operation_name);
CREATE INDEX IF NOT EXISTS idx_system_prompt_sections_section_name ON system_prompt_sections(section_name);

-- Default API guidance
INSERT INTO api_guidance (api_name, display_name, description, when_to_use, when_not_to_use, priority)
VALUES
    ('manage', 'Manage API', 'Core management operations for VLAN, VRF, BD, EPG, and policy configuration', 'Use for creating, updating, or deleting network configurations.', 'Avoid for read-only operations or analysis tasks.', 10),
    ('analyze', 'Analyze API', 'Network analysis and troubleshooting operations', 'Use for troubleshooting connectivity issues and analyzing network behavior.', 'Avoid for configuration changes.', 20),
    ('infra', 'Infrastructure API', 'Infrastructure operations for fabric nodes and interfaces', 'Use for infrastructure queries and node status.', 'Avoid for policy configuration.', 30),
    ('one_manage', 'OneManage API', 'Centralized management across multiple network domains', 'Use for cross-domain operations.', 'Avoid for single-fabric operations.', 40)
ON CONFLICT (api_name) DO NOTHING;

-- Default system prompt sections
INSERT INTO system_prompt_sections (section_name, section_order, title, content)
VALUES
    ('overview', 10, 'API Overview', 'You are working with Cisco Nexus Dashboard APIs. Select the appropriate API based on the task.'),
    ('api_selection', 20, 'API Selection Guidelines', 'Identify if the task is configuration (manage), troubleshooting (analyze), infrastructure query (infra), or cross-domain (one_manage).'),
    ('best_practices', 30, 'Best Practices', 'Always verify prerequisites before configuration changes. Use read operations to validate state.')
ON CONFLICT (section_name) DO NOTHING;

COMMENT ON TABLE api_guidance IS 'API-level guidance for tool selection';
COMMENT ON TABLE category_guidance IS 'Category/tag specific guidance';
COMMENT ON TABLE workflows IS 'Multi-step workflow definitions';
COMMENT ON TABLE workflow_steps IS 'Individual steps within workflows';
COMMENT ON TABLE tool_description_overrides IS 'Enhanced tool descriptions';
COMMENT ON TABLE system_prompt_sections IS 'System prompt configuration sections';
