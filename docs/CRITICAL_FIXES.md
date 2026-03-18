# Critical Fixes - Tool Profiles, Descriptions, Multi-Cluster, Workflows

## Overview

This document describes the five critical fixes implemented to make the platform production-ready for MCP integrations with tool-limited clients.

## Phase 1: Operation Name Mismatch Fix

**Problem:** Tool names in MCP use `{api_name}_{operation_id}` format (e.g., `manage_createVlan`) but the operations API returned just `operation_id` (e.g., `createVlan`). This meant role-based tool filtering never matched for manually-created roles.

**Fix:**
- `src/services/role_service.py`: `get_all_available_operations()` and `get_operations_by_api()` now return names with the `{api_name}_` prefix
- Fixed `ep.method` -> `ep.http_method` bug in search filter
- Migration `005_fix_role_operation_names.sql` fixes existing role_operations entries

## Phase 2: Tool Profiles

**Problem:** 638+ tools exceed MCP client limits (typically 40-128). Even superusers got everything.

**Solution:** Tool profiles are named subsets of tools assigned to users.

### New Components
- **Database tables:** `tool_profiles`, `tool_profile_operations`, `users.tool_profile_id`
- **Model:** `src/models/tool_profile.py` (ToolProfile, ToolProfileOperation)
- **Service:** `src/services/tool_profile_service.py` (CRUD + resolution logic)
- **API endpoints:** `/api/tool-profiles/` (CRUD), `/api/users/{id}/tool-profile`
- **Web UI:** `/tool-profiles` page with searchable operations selector

### Resolution Priority
```
1. User has tool profile -> filter to profile operations
2. Superuser without profile -> all tools
3. User has role operations -> filter to role operations
4. No profile, no roles -> no tools
```

### Seed Profiles
- **Fabric Operations** (30 tools) - VLAN, VRF, BD, EPG management
- **Monitoring & Health** (25 tools) - Read-only monitoring
- **Troubleshooting** (25 tools) - Network analysis
- **Full Access** (max_tools=0) - No filtering, backward compatible

## Phase 3: Better Tool Descriptions

**Problem:** Default tool descriptions were just `METHOD /path - summary`, providing poor guidance to LLM clients.

**Fix:**
- Enhanced default format: `{summary}\nEndpoint: {method} {path}\nAPI: {display_name}`
- `enhanced_description` in overrides now **replaces** the default (not appends)
- `usage_hint` remains supplementary
- New `generate_descriptions_from_spec()` method extracts rich descriptions from OpenAPI specs (parameters, request body fields)
- API endpoint: `POST /api/tool-descriptions/generate-batch`
- UI: "Generate from Spec" button on tool overrides page

## Phase 4: Multi-Cluster Support

**Problem:** Single hardcoded cluster binding. Users assigned to different clusters couldn't route tools correctly.

**Solution:** Per-user cluster routing via API token.

### Changes
- `NexusDashboardMCP.__init__()` no longer requires cluster_name
- `handle_call_tool()` accepts `cluster_name` parameter
- `AuthMiddleware` instances cached per cluster (lazy creation)
- MCP transport resolves target cluster from user's assigned clusters (primary = first)
- Users with multiple clusters get a `nexus_list_clusters` utility tool
- `get_mcp_instance()` creates unbound MCP instance

### Architecture
```
User API Token -> validate_token() -> user.clusters -> primary cluster
                                                     -> handle_call_tool(cluster_name=primary)
                                                     -> AuthMiddleware(primary) [cached]
                                                     -> Nexus Dashboard API
```

## Phase 5: Workflow/Use Case Improvements

### WorkflowStep Extensions
New columns: `input_mapping`, `output_key`, `condition_type`, `condition`

```
input_mapping: {"param": "{{step_1.output.field}}"}
output_key: "vlan_list"
condition_type: "always" | "if_equals" | "if_not_empty" | "if_error"
condition: {"field": "step_1.output.status", "value": "success"}
```

### Workflow Execution Tracking
- `workflow_executions` table - tracks runs (status, user, timestamps, context)
- `workflow_step_executions` table - tracks step results (input/output, status)
- API endpoints for listing and viewing executions
- UI: Workflow Execution History page

### Workflow Validation
- `POST /api/guidance/workflows/{id}/validate`
- Checks: operation names exist with correct prefix, input_mapping references valid earlier steps, step order is sequential
- UI: "Validate" button on workflow detail page

### Use Cases as First-Class Entities
- `use_cases` table with name, description, category
- `use_case_workflows` M:M table (replaces `use_case_tags` JSONB approach)
- Full CRUD API and UI page
- Categories for organization

## Database Migrations

```
005_fix_role_operation_names.sql  - Fix unprefixed operation names
006_add_tool_profiles.sql         - Tool profiles tables + seeds
007_workflow_and_usecase_improvements.sql - Workflow extensions + use cases
```

Apply in order:
```bash
psql -U nexus_mcp -d nexus_mcp -f src/config/migrations/005_fix_role_operation_names.sql
psql -U nexus_mcp -d nexus_mcp -f src/config/migrations/006_add_tool_profiles.sql
psql -U nexus_mcp -d nexus_mcp -f src/config/migrations/007_workflow_and_usecase_improvements.sql
```

## New API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tool-profiles` | List all tool profiles |
| POST | `/api/tool-profiles` | Create tool profile |
| GET | `/api/tool-profiles/{id}` | Get tool profile |
| PUT | `/api/tool-profiles/{id}` | Update tool profile |
| DELETE | `/api/tool-profiles/{id}` | Delete tool profile |
| PUT | `/api/tool-profiles/{id}/operations` | Set profile operations |
| PUT | `/api/users/{id}/tool-profile` | Assign profile to user |
| POST | `/api/tool-descriptions/generate-batch` | Generate descriptions from specs |
| POST | `/api/guidance/workflows/{id}/validate` | Validate workflow |
| GET | `/api/guidance/workflow-executions` | List executions |
| GET | `/api/guidance/workflow-executions/{id}` | Get execution details |
| GET | `/api/guidance/use-cases` | List use cases |
| POST | `/api/guidance/use-cases` | Create use case |
| GET | `/api/guidance/use-cases/{id}` | Get use case |
| PUT | `/api/guidance/use-cases/{id}` | Update use case |
| DELETE | `/api/guidance/use-cases/{id}` | Delete use case |
| PUT | `/api/guidance/use-cases/{id}/workflows` | Set use case workflows |

## New Web UI Pages

| Path | Description |
|------|-------------|
| `/tool-profiles` | Tool profile management |
| `/guidance/use-cases` | Use case management |
| `/guidance/workflow-executions` | Execution history |

## Verification Steps

1. **Phase 1**: Create role via UI, assign 5 operations (they now show with prefix), assign to user. Connect with API token -> verify only 5 tools in `tools/list`.
2. **Phase 2**: Create profile with 20 tools, assign to superuser -> verify only 20 tools appear.
3. **Phase 3**: Run batch description generation -> verify richer descriptions with parameter details.
4. **Phase 4**: Assign user to cluster A, connect -> verify all tool calls route to cluster A.
5. **Phase 5**: Create workflow with input mapping, validate -> verify execution history recorded.
