"""Resource grouping for MCP tool consolidation.

This module provides functionality to group API operations by resource type,
reducing the number of MCP tools from 638+ individual operations to ~67
resource-based tools.

The grouping strategy:
1. Extract resource name from API path (first path segment)
2. Group by "{api_name}_{resource}" key
3. Each consolidated tool lists available operations via enum
4. RBAC filtering is applied per-operation within each tool
"""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


def extract_resource_from_path(path: str) -> str:
    """Extract primary resource name from API path.

    The resource is typically the first path segment after the leading slash.

    Args:
        path: API path like "/fabrics/{id}" or "/anomalyRules/complianceRules"

    Returns:
        Resource name (e.g., "fabrics", "anomalyRules")

    Examples:
        >>> extract_resource_from_path("/fabrics/{id}")
        'fabrics'
        >>> extract_resource_from_path("/anomalyRules/complianceRules")
        'anomalyRules'
        >>> extract_resource_from_path("/api/v1/users")
        'api'
    """
    parts = path.strip('/').split('/')
    return parts[0] if parts and parts[0] else 'misc'


def group_operations_by_resource(operations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group API operations by resource type.

    Each operation is grouped by a key of "{api_name}_{resource}".

    Args:
        operations: List of operation dictionaries containing:
            - api_name: API name (analyze, infra, manage, onemanage)
            - path: API path
            - operation_id: Unique operation identifier
            - method: HTTP method
            - summary: Operation summary
            - description: Operation description
            - parameters: List of parameters
            - requestBody: Request body schema (if any)

    Returns:
        Dict mapping resource_key to list of operations.
        Keys are formatted as "{api_name}_{resource}".

    Example:
        >>> ops = [
        ...     {"api_name": "analyze", "path": "/fabrics", "operation_id": "getFabrics"},
        ...     {"api_name": "analyze", "path": "/fabrics/{id}", "operation_id": "getFabricById"},
        ... ]
        >>> grouped = group_operations_by_resource(ops)
        >>> "analyze_fabrics" in grouped
        True
        >>> len(grouped["analyze_fabrics"])
        2
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}

    for op in operations:
        api_name = op.get('api_name', 'manage')
        resource = extract_resource_from_path(op.get('path', ''))
        key = f"{api_name}_{resource}"

        if key not in groups:
            groups[key] = []
        groups[key].append(op)

    logger.debug(f"Grouped {len(operations)} operations into {len(groups)} resource groups")
    return groups


def build_resource_description(resource_key: str, operations: List[Dict[str, Any]]) -> str:
    """Build a description for a consolidated resource tool.

    Args:
        resource_key: Resource key like "analyze_fabrics"
        operations: List of operations in this resource group

    Returns:
        Human-readable description of the resource and available operations
    """
    # Parse API name and resource from key
    parts = resource_key.split('_', 1)
    api_name = parts[0] if len(parts) > 0 else "unknown"
    resource = parts[1] if len(parts) > 1 else resource_key

    # Count operations by HTTP method
    method_counts = {}
    for op in operations:
        method = op.get('method', 'GET').upper()
        method_counts[method] = method_counts.get(method, 0) + 1

    # Build method summary
    method_summary = ", ".join(f"{count} {method}" for method, count in sorted(method_counts.items()))

    # Get sample operation summaries (first 3)
    sample_summaries = []
    for op in operations[:3]:
        if op.get('summary'):
            sample_summaries.append(op['summary'])

    description = f"Operations for {resource} resource ({api_name} API). "
    description += f"Contains {len(operations)} operations ({method_summary})."

    if sample_summaries:
        description += f" Examples: {'; '.join(sample_summaries)}"

    return description


def build_consolidated_tool_schema(
    resource_key: str,
    operations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build input schema for a consolidated resource tool.

    The schema has:
    - operation: enum of available operation IDs
    - params: object for operation-specific parameters

    Args:
        resource_key: Resource key like "analyze_fabrics"
        operations: List of operations in this resource group

    Returns:
        JSON Schema for the tool's input
    """
    # Extract operation IDs for enum
    op_ids = [op['operation_id'] for op in operations if op.get('operation_id')]

    # Build descriptions for each operation
    op_descriptions = []
    for op in operations:
        op_id = op.get('operation_id', '')
        method = op.get('method', 'GET')
        path = op.get('path', '')
        summary = op.get('summary', '')
        desc = f"- {op_id}: {method} {path}"
        if summary:
            desc += f" ({summary})"
        op_descriptions.append(desc)

    return {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": op_ids,
                "description": "Operation to execute. Available operations:\n" + "\n".join(op_descriptions[:20])
                              + (f"\n... and {len(op_descriptions) - 20} more" if len(op_descriptions) > 20 else "")
            },
            "params": {
                "type": "object",
                "description": "Operation-specific parameters. Check the operation's path for required path parameters.",
                "additionalProperties": True
            }
        },
        "required": ["operation"]
    }


def build_consolidated_tool(
    resource_key: str,
    operations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build a complete consolidated tool definition for a resource group.

    Args:
        resource_key: Resource key like "analyze_fabrics"
        operations: List of operations in this resource group

    Returns:
        Tool definition dict with name, description, and inputSchema
    """
    return {
        "name": resource_key,
        "description": build_resource_description(resource_key, operations),
        "inputSchema": build_consolidated_tool_schema(resource_key, operations)
    }


def get_operation_by_id(
    operations: List[Dict[str, Any]],
    operation_id: str
) -> Optional[Dict[str, Any]]:
    """Find an operation by its operation_id.

    Args:
        operations: List of all operations
        operation_id: The operation_id to find

    Returns:
        Operation dict if found, None otherwise
    """
    for op in operations:
        if op.get('operation_id') == operation_id:
            return op
    return None


def filter_operations_by_allowed(
    operations: List[Dict[str, Any]],
    allowed_operations: Optional[Set[str]]
) -> List[Dict[str, Any]]:
    """Filter operations to only those in the allowed set.

    Args:
        operations: List of operations to filter
        allowed_operations: Set of allowed operation_ids, or None for all

    Returns:
        Filtered list of operations
    """
    if allowed_operations is None:
        return operations

    return [
        op for op in operations
        if op.get('operation_id') in allowed_operations
    ]


def filter_consolidated_tool_operations(
    tool: Dict[str, Any],
    allowed_operations: Set[str]
) -> Optional[Dict[str, Any]]:
    """Filter a consolidated tool's operations enum to only allowed operations.

    Args:
        tool: Consolidated tool definition
        allowed_operations: Set of allowed operation_ids

    Returns:
        Filtered tool definition, or None if no operations are allowed
    """
    schema = tool.get("inputSchema", {})
    props = schema.get("properties", {})
    op_prop = props.get("operation", {})
    op_enum = op_prop.get("enum", [])

    # Filter to allowed operations
    allowed_in_tool = [op for op in op_enum if op in allowed_operations]

    if not allowed_in_tool:
        # No allowed operations in this tool
        return None

    # Create filtered tool
    filtered_tool = {
        "name": tool["name"],
        "description": tool["description"],
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": allowed_in_tool,
                    "description": f"Operation to execute ({len(allowed_in_tool)} available)"
                },
                "params": props.get("params", {"type": "object"})
            },
            "required": ["operation"]
        }
    }

    return filtered_tool
