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
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_cluster_id ON audit_log(cluster_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation_id ON audit_log(operation_id);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_api_name ON api_endpoints(api_name);
CREATE INDEX IF NOT EXISTS idx_api_endpoints_enabled ON api_endpoints(enabled);

-- Insert default security configuration
INSERT INTO security_config (edit_mode_enabled, audit_logging)
VALUES (FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE clusters IS 'Stores Nexus Dashboard cluster connection information with encrypted credentials';
COMMENT ON TABLE security_config IS 'Global security configuration for the MCP server';
COMMENT ON TABLE api_endpoints IS 'Registry of all available API endpoints from OpenAPI specs';
COMMENT ON TABLE audit_log IS 'Audit trail of all operations performed through the MCP server';
