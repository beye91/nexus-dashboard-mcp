-- Migration: Add API Guidance System
-- Version: 004
-- Date: 2025-12-04
-- Description: Adds tables for API guidance, workflows, tool descriptions, and system prompts

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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_guidance_api_name ON api_guidance(api_name);
CREATE INDEX IF NOT EXISTS idx_api_guidance_priority ON api_guidance(priority);
CREATE INDEX IF NOT EXISTS idx_api_guidance_is_active ON api_guidance(is_active);

CREATE INDEX IF NOT EXISTS idx_category_guidance_api_name ON category_guidance(api_name);
CREATE INDEX IF NOT EXISTS idx_category_guidance_category_name ON category_guidance(category_name);
CREATE INDEX IF NOT EXISTS idx_category_guidance_priority ON category_guidance(priority);
CREATE INDEX IF NOT EXISTS idx_category_guidance_is_active ON category_guidance(is_active);

CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_priority ON workflows(priority);
CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_step_order ON workflow_steps(workflow_id, step_order);

CREATE INDEX IF NOT EXISTS idx_tool_description_overrides_operation_name ON tool_description_overrides(operation_name);
CREATE INDEX IF NOT EXISTS idx_tool_description_overrides_is_active ON tool_description_overrides(is_active);

CREATE INDEX IF NOT EXISTS idx_system_prompt_sections_section_name ON system_prompt_sections(section_name);
CREATE INDEX IF NOT EXISTS idx_system_prompt_sections_section_order ON system_prompt_sections(section_order);
CREATE INDEX IF NOT EXISTS idx_system_prompt_sections_is_active ON system_prompt_sections(is_active);

-- Insert default API guidance
INSERT INTO api_guidance (api_name, display_name, description, when_to_use, when_not_to_use, priority)
VALUES
    (
        'manage',
        'Manage API',
        'Core management operations for VLAN, VRF, BD, EPG, and policy configuration',
        'Use for creating, updating, or deleting network configurations. Best for direct policy changes and object creation.',
        'Avoid for read-only operations or analysis tasks. Use analyze API instead for troubleshooting.',
        10
    ),
    (
        'analyze',
        'Analyze API',
        'Network analysis and troubleshooting operations including connectivity, path tracing, and diagnostics',
        'Use for troubleshooting connectivity issues, validating configurations, and analyzing network behavior.',
        'Avoid for configuration changes or infrastructure management.',
        20
    ),
    (
        'infra',
        'Infrastructure API',
        'Infrastructure operations for fabric nodes, interfaces, and physical topology',
        'Use for infrastructure queries, node status, interface configurations, and physical topology.',
        'Avoid for policy or logical network configuration. Use manage API for policy changes.',
        30
    ),
    (
        'one_manage',
        'OneManage API',
        'Centralized network management operations across multiple network domains',
        'Use for cross-domain operations and centralized management tasks when multiple fabrics are involved.',
        'Avoid for single-fabric operations where direct manage API is more appropriate.',
        40
    )
ON CONFLICT (api_name) DO NOTHING;

-- Insert default system prompt sections
INSERT INTO system_prompt_sections (section_name, section_order, title, content)
VALUES
    (
        'overview',
        10,
        'API Overview',
        'You are working with Cisco Nexus Dashboard APIs. The system provides four main API categories: Manage (configuration), Analyze (troubleshooting), Infrastructure (physical topology), and OneManage (cross-domain). Always select the most appropriate API based on the user task.'
    ),
    (
        'api_selection',
        20,
        'API Selection Guidelines',
        'When selecting operations: 1) Identify if the task is configuration (manage), troubleshooting (analyze), infrastructure query (infra), or cross-domain (one_manage). 2) Check category guidance for specific operation types. 3) Consider workflows for common multi-step tasks. 4) Validate required parameters are available before attempting operations.'
    ),
    (
        'best_practices',
        30,
        'Best Practices',
        'Follow these practices: 1) Always verify prerequisites before configuration changes. 2) Use read operations to validate state before and after changes. 3) For complex tasks, break them into logical steps. 4) Handle errors gracefully and provide clear feedback. 5) Log all configuration changes for audit purposes.'
    )
ON CONFLICT (section_name) DO NOTHING;
