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
    auth_type VARCHAR(50) DEFAULT 'local',
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
