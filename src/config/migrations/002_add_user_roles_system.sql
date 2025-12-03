-- Migration: Add Multi-User Role-Based Access Control System
-- Version: 002
-- Date: 2025-12-03
-- Description: Adds users, roles, and permissions tables for RBAC

-- Users table for local authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    api_token VARCHAR(64) UNIQUE,        -- For Claude Desktop auth
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    auth_type VARCHAR(50) DEFAULT 'local',  -- 'local' or 'ldap' for future
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Roles table for custom role definitions
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    edit_mode_enabled BOOLEAN DEFAULT FALSE,  -- Per-role edit permission
    is_system_role BOOLEAN DEFAULT FALSE,     -- Built-in vs user-created
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Role operations (M:M relationship between roles and allowed operations)
CREATE TABLE IF NOT EXISTS role_operations (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    operation_name VARCHAR(255) NOT NULL,  -- e.g., "manage_createVlan"
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(role_id, operation_name)
);

-- User roles (M:M relationship between users and roles)
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, role_id)
);

-- User sessions for Web UI authentication
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_api_token ON users(api_token);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_role_operations_role_id ON role_operations(role_id);
CREATE INDEX IF NOT EXISTS idx_role_operations_operation_name ON role_operations(operation_name);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Default system roles
INSERT INTO roles (name, description, edit_mode_enabled, is_system_role)
VALUES
    ('Administrator', 'Full access to all operations with edit mode enabled', TRUE, TRUE),
    ('Network Operator', 'Read-write access to network operational tasks', TRUE, TRUE),
    ('Read-Only User', 'View-only access to all data without edit capabilities', FALSE, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Update audit_log to link to users table (optional foreign key)
-- Note: We don't add FK constraint to preserve existing logs without users
ALTER TABLE audit_log
    ADD COLUMN IF NOT EXISTS auth_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_audit_log_auth_user_id ON audit_log(auth_user_id);
