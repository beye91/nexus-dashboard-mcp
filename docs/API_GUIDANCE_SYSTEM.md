# API Guidance System Documentation

## Overview

The API Guidance System is a database-driven framework that enhances Claude's ability to work with Nexus Dashboard APIs by providing customizable guidance, workflows, tool descriptions, and system prompts. All guidance is stored in the database and can be updated without code changes.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Guidance System                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
         ┌──────▼──────┐           ┌───────▼────────┐
         │   Models    │           │    Service     │
         │  (guidance) │           │ (GuidanceService)│
         └─────────────┘           └────────────────┘
                │                           │
    ┌───────────┼───────────┐              │
    │           │           │              │
┌───▼───┐  ┌───▼───┐  ┌────▼────┐    ┌────▼────┐
│ API   │  │Category│  │Workflow │    │ System  │
│Guidance│  │Guidance│  │  &      │    │ Prompt  │
│       │  │        │  │ Steps   │    │ Sections│
└───────┘  └────────┘  └─────────┘    └─────────┘
                │
           ┌────▼────┐
           │  Tool   │
           │Override │
           └─────────┘
```

## Database Models

### 1. APIGuidance

Stores API-level guidance and best practices for each API (e.g., 'manage', 'analyze', 'infra').

**Fields:**
- `api_name` (str, unique): API identifier ('manage', 'analyze', etc.)
- `display_name` (str): Human-readable name
- `description` (text): General description
- `general_guidance` (text): Best practices and tips
- `common_patterns` (text): Common usage patterns
- `gotchas` (text): Common pitfalls
- `examples` (json): List of example use cases
- `is_active` (bool): Whether to include in system prompt
- `section_order` (int): Order in system prompt

**Relationships:**
- Has many `CategoryGuidance` entries

### 2. CategoryGuidance

Stores category-level guidance within an API (e.g., 'fabric', 'sites', 'policies').

**Fields:**
- `api_guidance_id` (int): Foreign key to APIGuidance
- `category_name` (str): Category identifier
- `display_name` (str): Human-readable name
- `description` (text): What this category covers
- `usage_tips` (text): Specific tips
- `prerequisites` (text): What needs to be configured first
- `related_categories` (json): List of related categories
- `is_active` (bool): Whether to include

**Relationships:**
- Belongs to one `APIGuidance`

### 3. Workflow

Stores multi-step workflows for common tasks (e.g., "Deploy New Fabric").

**Fields:**
- `name` (str, unique): Unique identifier
- `display_name` (str): Human-readable name
- `description` (text): What this workflow accomplishes
- `use_case` (text): When to use this workflow
- `prerequisites` (text): What's needed before running
- `estimated_duration` (str): e.g., "5-10 minutes"
- `use_case_tags` (json): List of tags for categorization
- `is_active` (bool): Whether to include

**Relationships:**
- Has many `WorkflowStep` entries (ordered by step_order)

### 4. WorkflowStep

Individual steps within a workflow.

**Fields:**
- `workflow_id` (int): Foreign key to Workflow
- `step_order` (int): Order of execution
- `step_name` (str): Human-readable step name
- `operation_name` (str, optional): MCP tool/operation to use
- `description` (text): What this step does
- `parameters` (json): Example parameters
- `expected_result` (text): What to expect after this step
- `validation` (text): How to validate success
- `notes` (text): Additional notes or warnings

**Relationships:**
- Belongs to one `Workflow`

### 5. ToolDescriptionOverride

Overrides/enhances MCP tool descriptions for specific operations.

**Fields:**
- `operation_name` (str, unique): Tool/operation name
- `custom_description` (text): Enhanced description
- `usage_guidance` (text): When and how to use
- `parameter_guidance` (json): Dict of parameter tips
- `examples` (json): List of usage examples
- `warnings` (text): Important warnings or caveats
- `is_active` (bool): Whether to apply

### 6. SystemPromptSection

Modular system prompt sections that can be combined.

**Fields:**
- `section_name` (str, unique): Section identifier
- `display_name` (str): Human-readable name
- `content` (text): The actual prompt text
- `section_order` (int): Order in final prompt
- `is_active` (bool): Whether to include

## GuidanceService API

### API Guidance Methods

#### `async def get_api_guidance(api_name: str) -> Optional[APIGuidance]`
Get API guidance by API name with categories loaded.

#### `async def list_api_guidance(active_only: bool = True) -> List[APIGuidance]`
List all API guidance entries, optionally filtered to active only.

#### `async def upsert_api_guidance(api_name: str, **kwargs) -> APIGuidance`
Create or update API guidance. If it exists, updates fields; otherwise creates new entry.

**Example:**
```python
guidance = await service.upsert_api_guidance(
    api_name="manage",
    display_name="Nexus Dashboard Manage API",
    description="Manages NDFC fabrics, policies, and networks",
    general_guidance="Always check fabric state before modifications",
    is_active=True,
    section_order=1
)
```

#### `async def delete_api_guidance(api_name: str) -> bool`
Delete API guidance and all related category guidance (CASCADE).

### Category Guidance Methods

#### `async def get_category_guidance(api_name: str, category_name: str) -> Optional[CategoryGuidance]`
Get category guidance by API and category name.

#### `async def list_category_guidance(api_name: Optional[str] = None, active_only: bool = True) -> List[CategoryGuidance]`
List category guidance, optionally filtered by API name.

#### `async def upsert_category_guidance(api_name: str, category_name: str, **kwargs) -> CategoryGuidance`
Create or update category guidance. Raises ValueError if API guidance doesn't exist.

**Example:**
```python
category = await service.upsert_category_guidance(
    api_name="manage",
    category_name="fabric",
    display_name="Fabric Management",
    description="Operations for creating and managing NDFC fabrics",
    usage_tips="Always deploy fabric changes after configuration",
    prerequisites="Ensure seed IP is reachable",
    is_active=True
)
```

#### `async def delete_category_guidance(id: int) -> bool`
Delete category guidance by ID.

### Workflow Methods

#### `async def create_workflow(name: str, display_name: str, **kwargs) -> Workflow`
Create a new workflow. Raises ValueError if workflow name already exists.

**Example:**
```python
workflow = await service.create_workflow(
    name="deploy_fabric",
    display_name="Deploy New Fabric",
    description="Create and deploy a new NDFC fabric from scratch",
    use_case="When setting up a new data center fabric",
    prerequisites="Switches reachable, credentials configured",
    estimated_duration="10-15 minutes",
    use_case_tags=["fabric", "deployment", "setup"],
    is_active=True
)
```

#### `async def get_workflow(workflow_id: int) -> Optional[Workflow]`
Get workflow by ID with steps loaded (ordered by step_order).

#### `async def list_workflows(active_only: bool = True, use_case_tag: Optional[str] = None) -> List[Workflow]`
List workflows, optionally filtered by active status and use case tag.

#### `async def update_workflow(workflow_id: int, **kwargs) -> Optional[Workflow]`
Update workflow properties (cannot change name or ID).

#### `async def delete_workflow(workflow_id: int) -> bool`
Delete workflow and all its steps (CASCADE).

#### `async def set_workflow_steps(workflow_id: int, steps: List[Dict]) -> Optional[Workflow]`
Set workflow steps, replacing any existing steps.

**Example:**
```python
workflow = await service.set_workflow_steps(
    workflow_id=1,
    steps=[
        {
            "step_order": 1,
            "step_name": "Create Fabric",
            "operation_name": "manage_create_fabric",
            "description": "Create the fabric with basic configuration",
            "parameters": {"fabric_name": "DC1", "template": "Easy_Fabric"},
            "expected_result": "Fabric created with status 'ok'",
            "validation": "Check fabric appears in fabric list",
            "notes": "Use Easy_Fabric template for VXLAN EVPN"
        },
        {
            "step_order": 2,
            "step_name": "Add Switches",
            "operation_name": "manage_add_switches",
            "description": "Discover and add switches to fabric",
            "parameters": {"seed_ip": "10.1.1.1", "auth_protocol": "MD5"},
            "expected_result": "Switches added with role assigned",
            "validation": "Verify switch count matches expected",
            "notes": None
        }
    ]
)
```

### Tool Override Methods

#### `async def get_tool_override(operation_name: str) -> Optional[ToolDescriptionOverride]`
Get tool description override for a specific operation.

#### `async def get_all_tool_overrides() -> Dict[str, ToolDescriptionOverride]`
Get all active tool overrides as a dictionary keyed by operation_name.

#### `async def list_tool_overrides(active_only: bool = True) -> List[ToolDescriptionOverride]`
List all tool description overrides.

#### `async def upsert_tool_override(operation_name: str, **kwargs) -> ToolDescriptionOverride`
Create or update tool description override.

**Example:**
```python
override = await service.upsert_tool_override(
    operation_name="manage_deploy_fabric",
    custom_description="Deploys pending fabric configuration to switches. This is a critical operation that pushes all pending changes.",
    usage_guidance="Only use after verifying configuration in config preview. Always check fabric state first.",
    parameter_guidance={
        "fabric_name": "Must match existing fabric exactly (case-sensitive)",
        "force": "Use with caution - bypasses some safety checks"
    },
    examples=[
        {"description": "Deploy fabric 'DC1' after config changes"},
        {"description": "Force deploy when switches are unreachable (dangerous)"}
    ],
    warnings="This operation modifies production network. Always verify changes first.",
    is_active=True
)
```

#### `async def delete_tool_override(operation_name: str) -> bool`
Delete tool description override.

### System Prompt Methods

#### `async def get_system_prompt_sections(active_only: bool = True) -> List[SystemPromptSection]`
Get all system prompt sections ordered by section_order.

#### `async def upsert_system_prompt_section(section_name: str, **kwargs) -> SystemPromptSection`
Create or update system prompt section.

**Example:**
```python
section = await service.upsert_system_prompt_section(
    section_name="introduction",
    display_name="Introduction",
    content="""You are an expert network automation assistant specialized in
Cisco Nexus Dashboard operations. Your role is to help users manage and
automate their data center network infrastructure efficiently and safely.""",
    section_order=1,
    is_active=True
)
```

#### `async def delete_system_prompt_section(section_name: str) -> bool`
Delete system prompt section.

### Composite Methods

#### `async def generate_system_prompt() -> str`
Generate complete system prompt from all active sources:
1. System prompt sections (ordered by section_order)
2. API guidance formatted as reference
3. Workflow summaries with steps

Returns the complete prompt text ready to use.

**Example Output Structure:**
```
# Introduction
[Content from section_order=1]

# API Reference and Best Practices

## Nexus Dashboard Manage API
[Description, guidance, patterns, gotchas]

## Nexus Dashboard Analyze API
[Description, guidance, patterns, gotchas]

# Available Workflows

## Deploy New Fabric
[Description, use case, prerequisites, steps]

## Add Site to Fabric
[Description, use case, prerequisites, steps]
```

#### `async def build_enhanced_tool_description(operation: Dict) -> str`
Build enhanced description for a tool operation. Checks for custom override and combines with original description.

**Example:**
```python
# operation dict from OpenAPI spec
operation = {
    "operationId": "manage_deploy_fabric",
    "description": "Deploy fabric configuration",
    ...
}

# Get enhanced description
enhanced = await service.build_enhanced_tool_description(operation)

# If override exists, returns:
# "Deploys pending fabric configuration to switches. This is a critical operation...
#
# **Usage Guidance:** Only use after verifying configuration in config preview...
#
# **Warning:** This operation modifies production network..."
```

## Usage Examples

### Basic Setup

```python
from src.services.guidance_service import GuidanceService

service = GuidanceService()
```

### Creating a Complete Guidance Set

```python
# 1. Create API guidance
api_guidance = await service.upsert_api_guidance(
    api_name="manage",
    display_name="Nexus Dashboard Manage API",
    description="NDFC API for managing fabrics, policies, and networks",
    general_guidance="Always verify fabric state before modifications",
    common_patterns="Get fabric -> Modify config -> Deploy -> Verify",
    gotchas="Deploy operations are async - always check completion status",
    examples=[
        {"use_case": "Create fabric", "steps": ["create", "configure", "deploy"]},
        {"use_case": "Add network", "steps": ["verify fabric", "create network", "deploy"]}
    ],
    is_active=True,
    section_order=1
)

# 2. Add category guidance
fabric_category = await service.upsert_category_guidance(
    api_name="manage",
    category_name="fabric",
    display_name="Fabric Management",
    description="Create, configure, and manage NDFC fabrics",
    usage_tips="Use Easy_Fabric template for VXLAN EVPN deployments",
    prerequisites="Switches must be reachable and have basic config",
    related_categories=["switches", "networks"],
    is_active=True
)

# 3. Create workflow
workflow = await service.create_workflow(
    name="deploy_fabric",
    display_name="Deploy New Fabric",
    description="End-to-end fabric deployment workflow",
    use_case="Setting up new data center fabric",
    prerequisites="Switches powered on, management IPs configured",
    estimated_duration="10-15 minutes",
    use_case_tags=["fabric", "deployment"],
    is_active=True
)

# 4. Add workflow steps
await service.set_workflow_steps(
    workflow_id=workflow.id,
    steps=[
        {
            "step_order": 1,
            "step_name": "Create Fabric",
            "operation_name": "manage_create_fabric",
            "description": "Create fabric with VXLAN EVPN template",
            "parameters": {"fabric_name": "DC1", "template": "Easy_Fabric"},
            "expected_result": "Fabric created successfully",
            "validation": "Fabric appears in fabric list"
        },
        {
            "step_order": 2,
            "step_name": "Discover Switches",
            "operation_name": "manage_discover_switches",
            "description": "Discover and import switches",
            "parameters": {"seed_ip": "10.1.1.1"},
            "expected_result": "All switches discovered",
            "validation": "Switch count matches expected"
        },
        {
            "step_order": 3,
            "step_name": "Deploy Fabric",
            "operation_name": "manage_deploy_fabric",
            "description": "Deploy configuration to all switches",
            "parameters": {"fabric_name": "DC1"},
            "expected_result": "All configs deployed successfully",
            "validation": "Check deployment status is 'complete'"
        }
    ]
)

# 5. Add tool overrides for critical operations
await service.upsert_tool_override(
    operation_name="manage_deploy_fabric",
    custom_description="CRITICAL: Deploys configuration to production switches",
    usage_guidance="Always preview changes first. Verify switches are in maintenance window.",
    warnings="This modifies production network. Cannot be rolled back automatically.",
    is_active=True
)

# 6. Create system prompt sections
await service.upsert_system_prompt_section(
    section_name="safety_guidelines",
    display_name="Safety Guidelines",
    content="""Always follow these safety guidelines:
1. Verify current state before making changes
2. Use read-only operations to understand the environment first
3. For destructive operations, confirm with user before executing
4. Check for maintenance windows on production systems
5. Validate configuration before deployment""",
    section_order=2,
    is_active=True
)
```

### Generating System Prompt

```python
# Generate complete system prompt
prompt = await service.generate_system_prompt()

# Use in MCP server initialization
mcp_server.set_system_prompt(prompt)
```

### Enhancing Tool Descriptions

```python
# When registering MCP tools
for operation in api_operations:
    # Get enhanced description
    enhanced_description = await service.build_enhanced_tool_description(operation)

    # Register tool with enhanced description
    mcp_server.add_tool(
        name=operation['operationId'],
        description=enhanced_description,
        parameters=operation['parameters']
    )
```

## Integration with MCP Server

The guidance system integrates with the MCP server at these points:

1. **Server Initialization**: Generate system prompt and set it
2. **Tool Registration**: Enhance tool descriptions with overrides
3. **Runtime Updates**: Reload guidance when database is updated

```python
# In MCP server initialization
async def initialize_mcp_server():
    guidance_service = GuidanceService()

    # Set system prompt
    system_prompt = await guidance_service.generate_system_prompt()
    server.set_system_prompt(system_prompt)

    # Get tool overrides
    tool_overrides = await guidance_service.get_all_tool_overrides()

    # Register tools with enhanced descriptions
    for operation in all_operations:
        operation_name = operation['operationId']

        # Check for override
        if operation_name in tool_overrides:
            description = await guidance_service.build_enhanced_tool_description(operation)
        else:
            description = operation.get('description', '')

        server.add_tool(
            name=operation_name,
            description=description,
            parameters=operation['parameters']
        )
```

## Best Practices

### Guidance Content

1. **Be Specific**: Provide concrete examples and specific guidance
2. **Include Context**: Explain why certain patterns are recommended
3. **Highlight Pitfalls**: Document common mistakes and how to avoid them
4. **Keep Updated**: Review and update guidance as APIs evolve

### Workflows

1. **Complete Steps**: Include all necessary steps, don't skip validation
2. **Real Parameters**: Use realistic example parameters
3. **Error Handling**: Document what to do if steps fail
4. **Prerequisites**: Clearly state what's needed before starting

### Tool Overrides

1. **Enhance, Don't Replace**: Add context to original descriptions
2. **Safety First**: Highlight dangerous operations clearly
3. **Parameter Guidance**: Explain non-obvious parameters
4. **Real Examples**: Provide actual use cases

### System Prompts

1. **Modular Sections**: Keep sections focused on one topic
2. **Logical Order**: Use section_order to create coherent flow
3. **Consistent Tone**: Maintain consistent voice across sections
4. **Regular Review**: Update as system capabilities evolve

## Database Schema

```sql
-- API Guidance table
CREATE TABLE api_guidance (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    general_guidance TEXT,
    common_patterns TEXT,
    gotchas TEXT,
    examples JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    section_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Category Guidance table
CREATE TABLE category_guidance (
    id SERIAL PRIMARY KEY,
    api_guidance_id INTEGER REFERENCES api_guidance(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    usage_tips TEXT,
    prerequisites TEXT,
    related_categories JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflows table
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    use_case TEXT,
    prerequisites TEXT,
    estimated_duration VARCHAR(50),
    use_case_tags JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Workflow Steps table
CREATE TABLE workflow_steps (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    operation_name VARCHAR(255),
    description TEXT NOT NULL,
    parameters JSONB,
    expected_result TEXT,
    validation TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tool Description Overrides table
CREATE TABLE tool_description_overrides (
    id SERIAL PRIMARY KEY,
    operation_name VARCHAR(255) UNIQUE NOT NULL,
    custom_description TEXT NOT NULL,
    usage_guidance TEXT,
    parameter_guidance JSONB,
    examples JSONB,
    warnings TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- System Prompt Sections table
CREATE TABLE system_prompt_sections (
    id SERIAL PRIMARY KEY,
    section_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    section_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_api_guidance_active ON api_guidance(is_active);
CREATE INDEX idx_category_guidance_active ON category_guidance(is_active);
CREATE INDEX idx_workflows_active ON workflows(is_active);
CREATE INDEX idx_tool_overrides_active ON tool_description_overrides(is_active);
CREATE INDEX idx_system_prompt_active ON system_prompt_sections(is_active);
CREATE INDEX idx_system_prompt_order ON system_prompt_sections(section_order);
```

## Future Enhancements

1. **Versioning**: Track changes to guidance over time
2. **Import/Export**: Bulk import/export of guidance configurations
3. **Templates**: Pre-built guidance sets for common use cases
4. **Analytics**: Track which guidance is most useful
5. **User Feedback**: Allow users to rate and improve guidance
6. **Auto-Generation**: Generate guidance from API specs and usage patterns
7. **Localization**: Support multiple languages
8. **Context-Aware**: Adjust guidance based on user expertise level

## Troubleshooting

### Guidance Not Appearing in System Prompt

- Check `is_active` is set to `True`
- Verify `section_order` is set correctly
- Check database connection
- Review logs for errors during prompt generation

### Tool Overrides Not Applied

- Verify `operation_name` matches exactly (case-sensitive)
- Check `is_active` is `True`
- Ensure tool registration happens after override retrieval
- Clear any caches

### Workflows Not Loading

- Verify workflow `is_active` is `True`
- Check workflow steps exist and have correct `step_order`
- Ensure foreign key relationships are intact
- Check for database constraint violations

## Support

For issues or questions about the API Guidance System:

1. Check this documentation
2. Review the service code at `src/services/guidance_service.py`
3. Review the models at `src/models/guidance.py`
4. Check database schema and migrations
5. Enable debug logging for detailed troubleshooting
