# GuidanceService Quick Reference

## Import

```python
from src.services.guidance_service import GuidanceService

service = GuidanceService()
```

## API Guidance (4 methods)

```python
# Get by API name
guidance = await service.get_api_guidance("manage")

# List all (active only by default)
all_guidance = await service.list_api_guidance()
all_guidance = await service.list_api_guidance(active_only=False)

# Create or update
guidance = await service.upsert_api_guidance(
    api_name="manage",
    display_name="Nexus Dashboard Manage API",
    description="NDFC fabric management",
    general_guidance="Best practices...",
    common_patterns="Common patterns...",
    gotchas="Watch out for...",
    examples=[{"use_case": "Deploy fabric", "steps": [...]}],
    is_active=True,
    section_order=1
)

# Delete
deleted = await service.delete_api_guidance("manage")
```

## Category Guidance (4 methods)

```python
# Get by API and category name
category = await service.get_category_guidance("manage", "fabric")

# List all (optionally filter by API)
all_categories = await service.list_category_guidance()
manage_categories = await service.list_category_guidance(api_name="manage")
inactive = await service.list_category_guidance(active_only=False)

# Create or update (API guidance must exist first)
category = await service.upsert_category_guidance(
    api_name="manage",
    category_name="fabric",
    display_name="Fabric Management",
    description="Create and manage fabrics",
    usage_tips="Use Easy_Fabric template",
    prerequisites="Switches reachable",
    related_categories=["switches", "networks"],
    is_active=True
)

# Delete by ID
deleted = await service.delete_category_guidance(category_id=1)
```

## Workflows (6 methods)

```python
# Create new workflow
workflow = await service.create_workflow(
    name="deploy_fabric",
    display_name="Deploy New Fabric",
    description="End-to-end fabric deployment",
    use_case="Setting up new DC fabric",
    prerequisites="Switches powered on",
    estimated_duration="10-15 minutes",
    use_case_tags=["fabric", "deployment"],
    is_active=True
)

# Get by ID (with steps loaded)
workflow = await service.get_workflow(workflow_id=1)

# List workflows
all_workflows = await service.list_workflows()
active_workflows = await service.list_workflows(active_only=True)
fabric_workflows = await service.list_workflows(use_case_tag="fabric")

# Update workflow
workflow = await service.update_workflow(
    workflow_id=1,
    description="Updated description",
    estimated_duration="15-20 minutes"
)

# Delete workflow (and all steps)
deleted = await service.delete_workflow(workflow_id=1)

# Set workflow steps (replaces existing)
workflow = await service.set_workflow_steps(
    workflow_id=1,
    steps=[
        {
            "step_order": 1,
            "step_name": "Create Fabric",
            "operation_name": "manage_create_fabric",
            "description": "Create fabric with VXLAN template",
            "parameters": {"fabric_name": "DC1"},
            "expected_result": "Fabric created",
            "validation": "Check fabric list",
            "notes": "Optional notes"
        },
        {
            "step_order": 2,
            "step_name": "Add Switches",
            ...
        }
    ]
)
```

## Tool Overrides (5 methods)

```python
# Get by operation name
override = await service.get_tool_override("manage_deploy_fabric")

# Get all as dict {operation_name: override}
all_overrides = await service.get_all_tool_overrides()

# List all
overrides = await service.list_tool_overrides()
inactive_overrides = await service.list_tool_overrides(active_only=False)

# Create or update
override = await service.upsert_tool_override(
    operation_name="manage_deploy_fabric",
    custom_description="Deploy fabric configuration to switches",
    usage_guidance="Always verify config first",
    parameter_guidance={"fabric_name": "Must match exactly"},
    examples=[{"description": "Deploy DC1 fabric"}],
    warnings="This modifies production network",
    is_active=True
)

# Delete
deleted = await service.delete_tool_override("manage_deploy_fabric")
```

## System Prompt Sections (3 methods)

```python
# Get all sections (ordered by section_order)
sections = await service.get_system_prompt_sections()
all_sections = await service.get_system_prompt_sections(active_only=False)

# Create or update
section = await service.upsert_system_prompt_section(
    section_name="safety_guidelines",
    display_name="Safety Guidelines",
    content="Always follow these guidelines:\n1. ...\n2. ...",
    section_order=2,
    is_active=True
)

# Delete
deleted = await service.delete_system_prompt_section("safety_guidelines")
```

## Composite Methods (2 methods)

```python
# Generate complete system prompt
prompt = await service.generate_system_prompt()
# Returns: Combined text from all active sections + API guidance + workflows

# Enhance tool description
operation = {
    "operationId": "manage_deploy_fabric",
    "description": "Deploy fabric configuration",
    ...
}
enhanced_desc = await service.build_enhanced_tool_description(operation)
# Returns: Custom description if override exists, otherwise original
```

## Complete Example

```python
from src.services.guidance_service import GuidanceService

async def setup_guidance():
    service = GuidanceService()

    # 1. Create API guidance
    await service.upsert_api_guidance(
        api_name="manage",
        display_name="Nexus Dashboard Manage API",
        general_guidance="Always verify state before changes",
        is_active=True
    )

    # 2. Add category
    await service.upsert_category_guidance(
        api_name="manage",
        category_name="fabric",
        display_name="Fabric Management",
        usage_tips="Use Easy_Fabric template",
        is_active=True
    )

    # 3. Create workflow
    workflow = await service.create_workflow(
        name="deploy_fabric",
        display_name="Deploy New Fabric",
        description="Complete fabric deployment",
        is_active=True
    )

    # 4. Add steps
    await service.set_workflow_steps(
        workflow_id=workflow.id,
        steps=[
            {
                "step_order": 1,
                "step_name": "Create Fabric",
                "operation_name": "manage_create_fabric",
                "description": "Create fabric",
                "parameters": {"fabric_name": "DC1"}
            }
        ]
    )

    # 5. Add tool override
    await service.upsert_tool_override(
        operation_name="manage_deploy_fabric",
        custom_description="CRITICAL: Deploys to production",
        warnings="Cannot rollback automatically",
        is_active=True
    )

    # 6. Add system prompt section
    await service.upsert_system_prompt_section(
        section_name="intro",
        display_name="Introduction",
        content="You are a network automation expert",
        section_order=1,
        is_active=True
    )

    # 7. Generate final prompt
    system_prompt = await service.generate_system_prompt()
    return system_prompt
```

## Return Types

- `Optional[Model]` - Returns model or None if not found
- `List[Model]` - Returns list (empty if none found)
- `bool` - Returns True if operation succeeded
- `Dict[str, Model]` - Returns dictionary keyed by name
- `str` - Returns text string

## Error Handling

```python
try:
    guidance = await service.upsert_category_guidance(
        api_name="nonexistent",
        category_name="test"
    )
except ValueError as e:
    print(f"Error: {e}")  # API guidance not found
```

## Common Patterns

### Upsert Pattern
All `upsert_*` methods create if not exists, update if exists:

```python
# First call creates
guidance = await service.upsert_api_guidance(api_name="manage", ...)

# Second call updates
guidance = await service.upsert_api_guidance(api_name="manage", ...)
```

### Active Filtering
Most list methods support `active_only` parameter:

```python
# Only active entries (default)
active = await service.list_api_guidance()

# All entries including inactive
all_entries = await service.list_api_guidance(active_only=False)
```

### Cascade Deletes
Some deletes cascade to related records:

```python
# Deletes API guidance AND all its categories
await service.delete_api_guidance("manage")

# Deletes workflow AND all its steps
await service.delete_workflow(workflow_id=1)
```

## Model Properties

### All Models Have
- `id` (int)
- `created_at` (datetime)
- `to_dict()` method
- `__repr__()` method

### Most Models Have
- `is_active` (bool)
- `updated_at` (datetime)

### Ordering Fields
- `section_order` (APIGuidance, SystemPromptSection)
- `step_order` (WorkflowStep)

## JSON Fields

All JSON fields accept Python dicts/lists:

```python
# examples field
examples=[
    {"use_case": "Deploy fabric", "steps": ["create", "deploy"]},
    {"use_case": "Add network", "steps": ["verify", "create"]}
]

# use_case_tags field
use_case_tags=["fabric", "deployment", "production"]

# parameter_guidance field
parameter_guidance={
    "fabric_name": "Must match existing fabric",
    "force": "Use with caution"
}
```

## Database Tables

- `api_guidance` - API-level guidance
- `category_guidance` - Category-level guidance
- `workflows` - Multi-step workflows
- `workflow_steps` - Individual workflow steps
- `tool_description_overrides` - Custom tool descriptions
- `system_prompt_sections` - System prompt sections

All tables have proper indexes on:
- Primary keys
- Unique constraints
- Foreign keys
- `is_active` fields
- `section_order` and `step_order` fields
