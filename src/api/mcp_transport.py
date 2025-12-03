"""MCP HTTP/SSE Transport for remote Claude Desktop connections.

This module provides HTTP/SSE transport for the MCP protocol, enabling
Claude Desktop to connect to the MCP server running on a remote host.

Usage:
  - GET /mcp/sse - Server-Sent Events endpoint for MCP messages
  - POST /mcp/message - Send MCP requests to the server
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.core.mcp_server import NexusDashboardMCP
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router for MCP endpoints
router = APIRouter(prefix="/mcp", tags=["MCP Transport"])

# Global MCP server instance (initialized on first request)
_mcp_instance: Optional[NexusDashboardMCP] = None
_mcp_initialized = False

# Store for SSE connections and their message queues
_sse_connections: Dict[str, asyncio.Queue] = {}


class MCPRequest(BaseModel):
    """MCP protocol request."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP protocol response."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
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


def validate_token(authorization: Optional[str]) -> bool:
    """Validate the MCP API token if configured."""
    settings = get_settings()
    expected_token = os.environ.get("MCP_API_TOKEN")

    # If no token is configured, allow access (for development)
    if not expected_token:
        return True

    if not authorization:
        return False

    # Support both "Bearer <token>" and just "<token>"
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    return token == expected_token


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
async def mcp_sse(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """Server-Sent Events endpoint for MCP communication.

    This endpoint establishes an SSE connection that Claude Desktop uses
    to receive MCP responses and notifications.
    """
    if not validate_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    # Generate unique connection ID
    connection_id = str(uuid.uuid4())

    # Create message queue for this connection
    message_queue: asyncio.Queue = asyncio.Queue()
    _sse_connections[connection_id] = message_queue

    logger.info(f"MCP SSE connection established: {connection_id}")

    async def event_generator():
        """Generate SSE events."""
        try:
            # Send initial connection event with connection ID
            init_event = {
                "type": "connection",
                "connection_id": connection_id,
                "message": "MCP SSE connection established",
            }
            yield f"event: connection\ndata: {json.dumps(init_event)}\n\n"

            # Send server capabilities
            mcp = await get_mcp_instance()
            capabilities = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                    },
                    "serverInfo": {
                        "name": "nexus-dashboard-mcp",
                        "version": "1.0.0",
                    },
                },
            }
            yield f"event: message\ndata: {json.dumps(capabilities)}\n\n"

            # Keep connection alive and send messages from queue
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for messages with timeout (for keepalive)
                    message = await asyncio.wait_for(
                        message_queue.get(),
                        timeout=30.0
                    )
                    yield f"event: message\ndata: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f"event: ping\ndata: {json.dumps({'type': 'ping', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

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
            "X-Connection-Id": connection_id,
        },
    )


@router.post("/message")
async def mcp_message(
    request: MCPRequest,
    connection_id: Optional[str] = Header(None, alias="X-Connection-Id"),
    authorization: Optional[str] = Header(None),
):
    """Handle MCP protocol messages.

    This endpoint receives MCP requests from Claude Desktop and returns
    responses. It also sends responses to the SSE connection if available.
    """
    if not validate_token(authorization):
        raise HTTPException(status_code=401, detail="Invalid or missing API token")

    mcp = await get_mcp_instance()

    try:
        result = None
        error = None

        if request.method == "initialize":
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

        elif request.method == "tools/list":
            # List available tools
            tools = []
            for operation in mcp.operations:
                tool = mcp._build_tool_from_operation(operation)
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                })
            result = {"tools": tools}

        elif request.method == "tools/call":
            # Execute a tool
            params = request.params or {}
            tool_name = params.get("name", "")
            tool_arguments = params.get("arguments", {})

            if not tool_name:
                error = {"code": -32602, "message": "Missing tool name"}
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

        elif request.method == "ping":
            # Respond to ping
            result = {"pong": True}

        else:
            error = {
                "code": -32601,
                "message": f"Method not found: {request.method}",
            }

        # Build response
        response = MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            result=result,
            error=error,
        )

        # Send to SSE connection if available
        if connection_id and connection_id in _sse_connections:
            await _sse_connections[connection_id].put(response.model_dump())

        return response.model_dump()

    except Exception as e:
        logger.error(f"MCP message handling error: {e}", exc_info=True)
        return MCPResponse(
            jsonrpc="2.0",
            id=request.id,
            error={"code": -32603, "message": str(e)},
        ).model_dump()


@router.get("/tools")
async def list_tools(authorization: Optional[str] = Header(None)):
    """List all available MCP tools (convenience endpoint)."""
    if not validate_token(authorization):
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

    return {
        "count": len(tools),
        "tools": tools,
    }
