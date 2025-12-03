"""MCP HTTP/SSE Transport for remote Claude Desktop connections.

This module provides HTTP/SSE transport for the MCP protocol, enabling
Claude Desktop to connect to the MCP server running on a remote host.

Usage:
  - GET /mcp/sse - Server-Sent Events endpoint for MCP messages
  - POST /mcp/message - Send MCP requests to the server (SSE transport)
  - POST /mcp/sse - Send MCP requests to the server (Streamable HTTP)

Authentication:
  - Per-user API tokens: Each user gets a unique API token for Claude Desktop
  - Legacy MCP_API_TOKEN: Still supported for backward compatibility (all permissions)
  - Users without API token = no user context (uses global settings)
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core.mcp_server import NexusDashboardMCP
from src.config.settings import get_settings
from src.services.user_service import UserService
from src.models.user import User

logger = logging.getLogger(__name__)

# Create router for MCP endpoints
router = APIRouter(prefix="/mcp", tags=["MCP Transport"])

# Global MCP server instance (initialized on first request)
_mcp_instance: Optional[NexusDashboardMCP] = None
_mcp_initialized = False

# User service instance
_user_service: Optional[UserService] = None

# Store for SSE connections with user context
@dataclass
class SSEConnection:
    """Represents an SSE connection with user context."""
    queue: asyncio.Queue
    user: Optional[User] = None
    allowed_operations: Optional[Set[str]] = None
    has_edit_mode: bool = False

_sse_connections: Dict[str, SSEConnection] = {}


class MCPRequest(BaseModel):
    """MCP protocol request."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP protocol response."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


async def get_mcp_instance() -> NexusDashboardMCP:
    """Get or create the MCP server instance."""
    global _mcp_instance, _mcp_initialized

    if _mcp_instance is None:
        _mcp_instance = NexusDashboardMCP(cluster_name="default")

    if not _mcp_initialized:
        # Load all APIs
        loaded_count = await _mcp_instance.load_all_apis()
        if loaded_count == 0:
            logger.warning("No APIs loaded for MCP server")
        else:
            logger.info(f"MCP HTTP transport: Loaded {loaded_count} APIs with {len(_mcp_instance.operations)} operations")
        _mcp_initialized = True

    return _mcp_instance


def get_user_service() -> UserService:
    """Get or create the UserService instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service


@dataclass
class AuthResult:
    """Result of token validation."""
    is_valid: bool
    user: Optional[User] = None
    allowed_operations: Optional[Set[str]] = None
    has_edit_mode: bool = False
    is_legacy_token: bool = False  # True if using MCP_API_TOKEN


async def validate_token(authorization: Optional[str]) -> AuthResult:
    """Validate the MCP API token and return user context if available.

    This function supports:
    1. Per-user API tokens (looked up from users table)
    2. Legacy MCP_API_TOKEN environment variable (all permissions)
    3. No token configured (development mode, all permissions)

    Args:
        authorization: Authorization header value

    Returns:
        AuthResult with validation status and user context
    """
    expected_token = os.environ.get("MCP_API_TOKEN")

    # Extract token from header
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

    # Case 1: No token provided
    if not token:
        # If no MCP_API_TOKEN configured, allow unauthenticated access
        if not expected_token:
            return AuthResult(is_valid=True, has_edit_mode=True)
        return AuthResult(is_valid=False)

    # Case 2: Check legacy MCP_API_TOKEN first
    if expected_token and token == expected_token:
        logger.debug("Authenticated via legacy MCP_API_TOKEN")
        return AuthResult(
            is_valid=True,
            has_edit_mode=True,
            is_legacy_token=True,
        )

    # Case 3: Look up user by API token
    user_service = get_user_service()
    user = await user_service.get_user_by_api_token(token)

    if user:
        # Get user's allowed operations from all roles
        allowed_ops = user.get_all_operations()
        has_edit = user.has_edit_mode()

        logger.info(f"Authenticated user '{user.username}' via API token ({len(allowed_ops)} operations allowed)")

        return AuthResult(
            is_valid=True,
            user=user,
            allowed_operations=allowed_ops if allowed_ops else None,
            has_edit_mode=has_edit,
        )

    # Case 4: Invalid token
    # If no MCP_API_TOKEN is set and user lookup failed, deny access
    if not expected_token:
        # No legacy token required but user token invalid - deny
        return AuthResult(is_valid=False)

    return AuthResult(is_valid=False)


def filter_tools_for_user(tools: List[Dict], auth_result: AuthResult) -> List[Dict]:
    """Filter tools based on user's allowed operations.

    Args:
        tools: List of tool dictionaries
        auth_result: Authentication result with user permissions

    Returns:
        Filtered list of tools the user is allowed to use
    """
    # If no user context or using legacy token, return all tools
    if auth_result.is_legacy_token or not auth_result.user:
        return tools

    # If user is superuser, return all tools
    if auth_result.user.is_superuser:
        return tools

    # If no operations are allowed, filter to read-only operations
    allowed_ops = auth_result.allowed_operations
    if not allowed_ops:
        # No explicit operations = no tools (or could filter to GET-only)
        logger.info(f"User '{auth_result.user.username}' has no allowed operations")
        return []

    # Filter tools by allowed operations
    filtered = []
    for tool in tools:
        tool_name = tool.get("name", "")
        if tool_name in allowed_ops:
            filtered.append(tool)

    logger.debug(f"Filtered {len(tools)} tools to {len(filtered)} for user '{auth_result.user.username}'")
    return filtered


def can_execute_tool(tool_name: str, auth_result: AuthResult) -> bool:
    """Check if user can execute a specific tool.

    Args:
        tool_name: Name of the tool to execute
        auth_result: Authentication result with user permissions

    Returns:
        True if user can execute the tool
    """
    # Legacy token or no user context = allow all
    if auth_result.is_legacy_token or not auth_result.user:
        return True

    # Superuser can do anything
    if auth_result.user.is_superuser:
        return True

    # Check if operation is in allowed list
    if auth_result.allowed_operations and tool_name in auth_result.allowed_operations:
        return True

    return False


@router.get("/health")
async def mcp_health():
    """Health check for MCP HTTP transport."""
    mcp = await get_mcp_instance()
    return {
        "status": "healthy",
        "transport": "http/sse",
        "operations_loaded": len(mcp.operations),
        "apis_loaded": len(mcp.loaded_apis),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/sse")
async def mcp_sse_get(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Server-Sent Events endpoint for MCP communication (GET).

    This endpoint establishes an SSE connection that Claude Desktop uses
    to receive MCP responses and notifications.
    """
    auth_result = await validate_token(authorization)
    if not auth_result.is_valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    # Generate unique connection ID
    connection_id = str(uuid.uuid4())

    # Create message queue for this connection with user context
    message_queue: asyncio.Queue = asyncio.Queue()
    _sse_connections[connection_id] = SSEConnection(
        queue=message_queue,
        user=auth_result.user,
        allowed_operations=auth_result.allowed_operations,
        has_edit_mode=auth_result.has_edit_mode,
    )

    user_info = f" (user: {auth_result.user.username})" if auth_result.user else ""
    logger.info(f"MCP SSE connection established: {connection_id}{user_info}")

    async def event_generator():
        """Generate SSE events."""
        try:
            # Send endpoint event first (required by MCP SSE transport spec)
            # This tells the client where to POST messages
            yield f"event: endpoint\ndata: /mcp/message\n\n"

            # Send server capabilities
            mcp = await get_mcp_instance()

            # Get the connection's queue
            conn = _sse_connections.get(connection_id)
            if not conn:
                return

            # Keep connection alive and send messages from queue
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for messages with timeout (for keepalive)
                    message = await asyncio.wait_for(
                        conn.queue.get(),
                        timeout=30.0
                    )
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive comment (: prefix means comment in SSE)
                    yield ": keepalive\n\n"

        except asyncio.CancelledError:
            logger.info(f"MCP SSE connection cancelled: {connection_id}")
        except Exception as e:
            logger.error(f"MCP SSE error: {e}")
        finally:
            # Cleanup connection
            if connection_id in _sse_connections:
                del _sse_connections[connection_id]
            logger.info(f"MCP SSE connection closed: {connection_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Mcp-Session-Id": connection_id,
        },
    )


@router.post("/sse")
async def mcp_sse_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    authorization: Optional[str] = Header(None),
):
    """Handle MCP messages via POST to SSE endpoint.

    This is the Streamable HTTP transport - clients POST JSON-RPC messages
    to the same endpoint and receive responses.
    """
    auth_result = await validate_token(authorization)
    if not auth_result.is_valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    # Parse the request body
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    mcp = await get_mcp_instance()

    # Handle the MCP request
    mcp_request = MCPRequest(**body)

    try:
        result = None
        error = None

        if mcp_request.method == "initialize":
            # Handle initialization
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                },
                "serverInfo": {
                    "name": "nexus-dashboard-mcp",
                    "version": "1.0.0",
                },
            }

        elif mcp_request.method == "notifications/initialized":
            # Client acknowledging initialization - no response needed
            return {}

        elif mcp_request.method == "tools/list":
            # List available tools (filtered by user permissions)
            tools = []
            for operation in mcp.operations:
                tool = mcp._build_tool_from_operation(operation)
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                })
            # Filter tools based on user permissions
            filtered_tools = filter_tools_for_user(tools, auth_result)
            result = {"tools": filtered_tools}

        elif mcp_request.method == "tools/call":
            # Execute a tool
            params = mcp_request.params or {}
            tool_name = params.get("name", "")
            tool_arguments = params.get("arguments", {})

            if not tool_name:
                error = {"code": -32602, "message": "Missing tool name"}
            elif not can_execute_tool(tool_name, auth_result):
                # Permission denied
                user_info = f" for user '{auth_result.user.username}'" if auth_result.user else ""
                error = {"code": -32600, "message": f"Permission denied{user_info}: operation '{tool_name}' not allowed"}
                logger.warning(f"Permission denied: {tool_name}{user_info}")
            else:
                # Call the tool handler
                contents = await mcp.handle_call_tool(tool_name, tool_arguments)

                # Extract text from TextContent responses
                result = {
                    "content": [
                        {"type": c.type, "text": c.text}
                        for c in contents
                    ]
                }

        elif mcp_request.method == "ping":
            # Respond to ping
            result = {"pong": True}

        else:
            error = {
                "code": -32601,
                "message": f"Method not found: {mcp_request.method}",
            }

        # Build response
        response = MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            result=result,
            error=error,
        )

        # Also send to SSE connection if available
        response_data = response.model_dump(exclude_none=True)
        if mcp_session_id and mcp_session_id in _sse_connections:
            await _sse_connections[mcp_session_id].queue.put(response_data)

        return response_data

    except Exception as e:
        logger.error(f"MCP message handling error: {e}", exc_info=True)
        return MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            error={"code": -32603, "message": str(e)},
        ).model_dump(exclude_none=True)


@router.post("/message")
async def mcp_message(
    request: Request,
    connection_id: Optional[str] = Header(None, alias="X-Connection-Id"),
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    authorization: Optional[str] = Header(None),
):
    """Handle MCP protocol messages (SSE transport message endpoint).

    This endpoint receives MCP requests from clients using SSE transport
    and returns responses directly via HTTP.
    """
    auth_result = await validate_token(authorization)
    if not auth_result.is_valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    # Use either connection_id or mcp_session_id
    session_id = connection_id or mcp_session_id
    logger.info(f"MCP /message request - session_id: {session_id}, active_connections: {list(_sse_connections.keys())}")

    # Parse the request body
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    mcp_request = MCPRequest(**body)
    mcp = await get_mcp_instance()

    try:
        result = None
        error = None

        if mcp_request.method == "initialize":
            # Handle initialization
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                },
                "serverInfo": {
                    "name": "nexus-dashboard-mcp",
                    "version": "1.0.0",
                },
            }

        elif mcp_request.method == "notifications/initialized":
            # Client acknowledging initialization - return empty accepted response
            return {}

        elif mcp_request.method == "tools/list":
            # List available tools (filtered by user permissions)
            tools = []
            for operation in mcp.operations:
                tool = mcp._build_tool_from_operation(operation)
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                })
            # Filter tools based on user permissions
            filtered_tools = filter_tools_for_user(tools, auth_result)
            result = {"tools": filtered_tools}

        elif mcp_request.method == "tools/call":
            # Execute a tool
            params = mcp_request.params or {}
            tool_name = params.get("name", "")
            tool_arguments = params.get("arguments", {})

            if not tool_name:
                error = {"code": -32602, "message": "Missing tool name"}
            elif not can_execute_tool(tool_name, auth_result):
                # Permission denied
                user_info = f" for user '{auth_result.user.username}'" if auth_result.user else ""
                error = {"code": -32600, "message": f"Permission denied{user_info}: operation '{tool_name}' not allowed"}
                logger.warning(f"Permission denied: {tool_name}{user_info}")
            else:
                # Call the tool handler
                contents = await mcp.handle_call_tool(tool_name, tool_arguments)

                # Extract text from TextContent responses
                result = {
                    "content": [
                        {"type": c.type, "text": c.text}
                        for c in contents
                    ]
                }

        elif mcp_request.method == "ping":
            # Respond to ping
            result = {"pong": True}

        else:
            error = {
                "code": -32601,
                "message": f"Method not found: {mcp_request.method}",
            }

        # Build response
        response = MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            result=result,
            error=error,
        )

        # For legacy SSE transport: Send response to SSE stream
        # mcp-remote doesn't send session IDs, so we broadcast to all active connections
        # In production, you'd want proper session correlation
        # Use exclude_none=True to avoid including "error": null in success responses
        response_data = response.model_dump(exclude_none=True)

        if session_id and session_id in _sse_connections:
            # If we have a specific session, use it
            logger.info(f"Sending response via SSE to session: {session_id}")
            await _sse_connections[session_id].queue.put(response_data)
        elif _sse_connections:
            # Broadcast to all connections (works for single-client SSE transport)
            logger.info(f"Broadcasting response to {len(_sse_connections)} SSE connection(s)")
            for conn_id, conn in _sse_connections.items():
                try:
                    await conn.queue.put(response_data)
                except Exception as e:
                    logger.warning(f"Failed to send to connection {conn_id}: {e}")
        else:
            logger.info("No active SSE connections, returning via HTTP only")

        return response_data

    except Exception as e:
        logger.error(f"MCP message handling error: {e}", exc_info=True)
        return MCPResponse(
            jsonrpc="2.0",
            id=mcp_request.id,
            error={"code": -32603, "message": str(e)},
        ).model_dump(exclude_none=True)


@router.get("/tools")
async def list_tools(authorization: Optional[str] = Header(None)):
    """List all available MCP tools (convenience endpoint).

    Tools are filtered based on the authenticated user's permissions.
    """
    auth_result = await validate_token(authorization)
    if not auth_result.is_valid:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    mcp = await get_mcp_instance()

    tools = []
    for operation in mcp.operations:
        tool = mcp._build_tool_from_operation(operation)
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        })

    # Filter tools based on user permissions
    filtered_tools = filter_tools_for_user(tools, auth_result)

    user_info = ""
    if auth_result.user:
        user_info = f" (user: {auth_result.user.username})"
    elif auth_result.is_legacy_token:
        user_info = " (legacy token)"

    return {
        "count": len(filtered_tools),
        "total_available": len(tools),
        "user": auth_result.user.username if auth_result.user else None,
        "tools": filtered_tools,
    }
