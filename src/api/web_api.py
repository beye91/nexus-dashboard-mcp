"""FastAPI web application for Nexus Dashboard MCP Server management UI."""

import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.settings import get_settings
from src.models.audit import AuditLog
from src.models.cluster import Cluster
from src.models.security import SecurityConfig
from src.models.user import User
from src.models.role import Role
from src.services.credential_manager import CredentialManager
from src.services.user_service import UserService
from src.services.role_service import RoleService
from src.utils.encryption import decrypt_password
from src.api.mcp_transport import router as mcp_router

# Initialize FastAPI app
app = FastAPI(
    title="Nexus Dashboard MCP Server - Web API",
    description="REST API for managing Nexus Dashboard MCP Server via web UI",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:7001", "http://127.0.0.1:7001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include MCP HTTP/SSE transport router
app.include_router(mcp_router)

# Pydantic models for request/response
class ClusterCreate(BaseModel):
    """Request model for creating a cluster."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    verify_ssl: bool = False


class ClusterUpdate(BaseModel):
    """Request model for updating a cluster."""
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: Optional[bool] = None


class ClusterResponse(BaseModel):
    """Response model for cluster information."""
    id: int
    name: str
    url: str
    username: str
    verify_ssl: bool
    is_active: bool
    status: str = "unknown"
    created_at: str
    updated_at: str


class SecurityConfigUpdate(BaseModel):
    """Request model for updating security configuration."""
    edit_mode_enabled: Optional[bool] = None
    allowed_operations: Optional[List[str]] = None
    audit_logging: Optional[bool] = None


class EditModeUpdate(BaseModel):
    """Request model for updating edit mode."""
    enabled: bool


class AuditLogResponse(BaseModel):
    """Response model for audit log entry."""
    id: int
    cluster_id: Optional[int]
    cluster_name: Optional[str]
    cluster_url: Optional[str]
    user_id: Optional[str]
    operation_id: Optional[str]
    http_method: Optional[str]
    path: Optional[str]
    request_body: Optional[dict]
    response_status: Optional[int]
    response_body: Optional[dict]
    error_message: Optional[str]
    client_ip: Optional[str]
    timestamp: str


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""
    total: int
    successful: int
    failed: int
    by_method: dict
    by_status: dict


class ServiceStatus(BaseModel):
    """Status of an individual service."""
    name: str
    status: str  # healthy, degraded, unhealthy
    message: Optional[str]
    response_time_ms: Optional[int]


class SystemHealthResponse(BaseModel):
    """Response model for system health."""
    status: str  # healthy, degraded, unhealthy
    database: bool
    uptime_seconds: int
    services: List[ServiceStatus]
    timestamp: str


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""
    total_operations: int
    clusters_configured: int
    audit_logs_count: int
    edit_mode_enabled: bool


# ==================== Auth/User/Role Pydantic Models ====================

class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Response model for login."""
    token: str
    user: dict


class UserCreate(BaseModel):
    """Request model for creating a user."""
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_superuser: bool = False
    role_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    """Request model for updating a user."""
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    """Response model for user information."""
    id: int
    username: str
    email: Optional[str]
    display_name: Optional[str]
    is_active: bool
    is_superuser: bool
    auth_type: str
    last_login: Optional[str]
    created_at: str
    updated_at: str
    roles: List[dict]
    has_edit_mode: bool


class RoleCreate(BaseModel):
    """Request model for creating a role."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    edit_mode_enabled: bool = False
    operations: Optional[List[str]] = None


class RoleUpdate(BaseModel):
    """Request model for updating a role."""
    name: Optional[str] = None
    description: Optional[str] = None
    edit_mode_enabled: Optional[bool] = None


class RoleResponse(BaseModel):
    """Response model for role information."""
    id: int
    name: str
    description: Optional[str]
    edit_mode_enabled: bool
    is_system_role: bool
    operations_count: int
    operations: Optional[List[str]] = None
    created_at: str
    updated_at: str


class OperationResponse(BaseModel):
    """Response model for an operation."""
    name: str
    method: str
    path: str
    api_name: str
    description: str


class OperationsListResponse(BaseModel):
    """Response model for operations list."""
    total: int
    operations: List[OperationResponse]


class SetRoleOperationsRequest(BaseModel):
    """Request model for setting role operations."""
    operations: List[str]


class AssignRolesRequest(BaseModel):
    """Request model for assigning roles to a user."""
    role_ids: List[int]


# Initialize services
credential_manager = CredentialManager()
user_service = UserService()
role_service = RoleService()
settings = get_settings()
db = get_db()

# Global startup time for uptime calculation
startup_time = datetime.utcnow()


# ==================== Authentication Helpers ====================

SESSION_COOKIE_NAME = "nexus_session"


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME),
) -> Optional[User]:
    """Get current authenticated user from session cookie.

    Args:
        request: FastAPI request object
        session_token: Session token from cookie

    Returns:
        User instance or None if not authenticated
    """
    if not session_token:
        return None
    return await user_service.validate_session(session_token)


async def require_auth(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authentication - raises 401 if not authenticated.

    Args:
        user: Current user from get_current_user

    Returns:
        Authenticated User instance

    Raises:
        HTTPException: 401 if not authenticated
    """
    # Check if any users exist - if not, allow unauthenticated access
    if not await user_service.has_any_users():
        return None

    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_superuser(
    user: User = Depends(require_auth),
) -> User:
    """Require superuser privileges.

    Args:
        user: Current authenticated user

    Returns:
        Authenticated superuser

    Raises:
        HTTPException: 403 if not superuser
    """
    if user and not user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser privileges required")
    return user


# Health and System Endpoints
@app.get("/api/health", response_model=SystemHealthResponse)
async def get_health():
    """Get system health status with detailed service checks."""
    import time
    services = []

    # Check PostgreSQL Database
    database_healthy = False
    db_start = time.time()
    try:
        async with db.session() as session:
            await session.execute(select(1))
            database_healthy = True
            db_time_ms = int((time.time() - db_start) * 1000)
            services.append(ServiceStatus(
                name="PostgreSQL",
                status="healthy",
                message="Database connection successful",
                response_time_ms=db_time_ms
            ))
    except Exception as e:
        db_time_ms = int((time.time() - db_start) * 1000)
        services.append(ServiceStatus(
            name="PostgreSQL",
            status="unhealthy",
            message=f"Database connection failed: {str(e)}",
            response_time_ms=db_time_ms
        ))

    # Check Cluster Connectivity
    cluster_status = "healthy"
    cluster_message = "No clusters configured"
    try:
        async with db.session() as session:
            result = await session.execute(
                select(Cluster).where(Cluster.is_active == True)
            )
            clusters = result.scalars().all()
            if clusters:
                cluster_message = f"{len(clusters)} cluster(s) configured"
            else:
                cluster_status = "degraded"
    except Exception as e:
        cluster_status = "unhealthy"
        cluster_message = f"Failed to check clusters: {str(e)}"

    services.append(ServiceStatus(
        name="Cluster Configuration",
        status=cluster_status,
        message=cluster_message,
        response_time_ms=None
    ))

    # Check MCP Server (via audit logs)
    mcp_status = "healthy"
    mcp_message = "MCP server operational"
    try:
        async with db.session() as session:
            # Check for recent audit logs (last 24 hours)
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            result = await session.execute(
                select(func.count(AuditLog.id)).where(AuditLog.timestamp >= cutoff_time)
            )
            recent_logs = result.scalar()
            if recent_logs > 0:
                mcp_message = f"{recent_logs} operations in last 24h"
            else:
                mcp_status = "degraded"
                mcp_message = "No recent operations logged"
    except Exception as e:
        mcp_status = "unhealthy"
        mcp_message = f"Cannot check MCP activity: {str(e)}"

    services.append(ServiceStatus(
        name="MCP Server",
        status=mcp_status,
        message=mcp_message,
        response_time_ms=None
    ))

    # Determine overall status
    statuses = [s.status for s in services]
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    uptime = int((datetime.utcnow() - startup_time).total_seconds())

    return {
        "status": overall_status,
        "database": database_healthy,
        "uptime_seconds": uptime,
        "services": services,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/stats", response_model=SystemStatsResponse)
async def get_stats():
    """Get system statistics."""
    async with db.session() as session:
        # Count clusters
        cluster_count = await session.execute(
            select(func.count()).select_from(Cluster)
        )
        clusters_configured = cluster_count.scalar() or 0

        # Count audit logs
        audit_count = await session.execute(
            select(func.count()).select_from(AuditLog)
        )
        audit_logs_count = audit_count.scalar() or 0

        # Get security config
        security_result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        security_config = security_result.scalar_one_or_none()
        edit_mode = security_config.edit_mode_enabled if security_config else False

    return {
        "total_operations": 638,  # Known from multi-API implementation
        "clusters_configured": clusters_configured,
        "audit_logs_count": audit_logs_count,
        "edit_mode_enabled": edit_mode,
    }


# Cluster Management Endpoints
@app.get("/api/clusters", response_model=List[ClusterResponse])
async def list_clusters(active_only: bool = Query(True)):
    """List all clusters."""
    clusters = await credential_manager.list_clusters(active_only=active_only)

    return [
        ClusterResponse(
            id=cluster.id,
            name=cluster.name,
            url=cluster.url,
            username=cluster.username,
            verify_ssl=cluster.verify_ssl,
            is_active=cluster.is_active,
            status="active" if cluster.is_active else "inactive",
            created_at=cluster.created_at.isoformat(),
            updated_at=cluster.updated_at.isoformat(),
        )
        for cluster in clusters
    ]


@app.get("/api/clusters/{name}", response_model=ClusterResponse)
async def get_cluster(name: str):
    """Get a specific cluster by name."""
    cluster = await credential_manager.get_cluster(name)

    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{name}' not found")

    return ClusterResponse(
        id=cluster.id,
        name=cluster.name,
        url=cluster.url,
        username=cluster.username,
        verify_ssl=cluster.verify_ssl,
        is_active=cluster.is_active,
        status="active" if cluster.is_active else "inactive",
        created_at=cluster.created_at.isoformat(),
        updated_at=cluster.updated_at.isoformat(),
    )


@app.post("/api/clusters", response_model=ClusterResponse, status_code=201)
async def create_cluster(cluster_data: ClusterCreate):
    """Create a new cluster."""
    try:
        cluster = await credential_manager.store_credentials(
            name=cluster_data.name,
            url=cluster_data.url,
            username=cluster_data.username,
            password=cluster_data.password,
            verify_ssl=cluster_data.verify_ssl,
        )

        return ClusterResponse(
            id=cluster.id,
            name=cluster.name,
            url=cluster.url,
            username=cluster.username,
            verify_ssl=cluster.verify_ssl,
            is_active=cluster.is_active,
            status="active" if cluster.is_active else "inactive",
            created_at=cluster.created_at.isoformat(),
            updated_at=cluster.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/clusters/{name}", response_model=ClusterResponse)
async def update_cluster(name: str, cluster_data: ClusterUpdate):
    """Update an existing cluster."""
    # Get existing cluster
    existing_cluster = await credential_manager.get_cluster(name)
    if not existing_cluster:
        raise HTTPException(status_code=404, detail=f"Cluster '{name}' not found")

    # Get decrypted credentials
    credentials = await credential_manager.get_credentials(name)

    # Update with new values or keep existing
    updated_cluster = await credential_manager.store_credentials(
        name=name,
        url=cluster_data.url or existing_cluster.url,
        username=cluster_data.username or existing_cluster.username,
        password=cluster_data.password or credentials["password"],
        verify_ssl=cluster_data.verify_ssl if cluster_data.verify_ssl is not None else existing_cluster.verify_ssl,
    )

    return ClusterResponse(
        id=updated_cluster.id,
        name=updated_cluster.name,
        url=updated_cluster.url,
        username=updated_cluster.username,
        verify_ssl=updated_cluster.verify_ssl,
        is_active=updated_cluster.is_active,
        status="active" if updated_cluster.is_active else "inactive",
        created_at=updated_cluster.created_at.isoformat(),
        updated_at=updated_cluster.updated_at.isoformat(),
    )


@app.delete("/api/clusters/{name}", status_code=204)
async def delete_cluster(name: str):
    """Delete a cluster."""
    deleted = await credential_manager.delete_credentials(name)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Cluster '{name}' not found")

    return None


@app.post("/api/clusters/test", status_code=200)
async def test_cluster_connection(cluster_data: ClusterCreate):
    """Test cluster connection without saving."""
    # This would require importing the auth middleware and testing the connection
    # For now, return a simple success response
    # TODO: Implement actual connection test
    return {
        "status": "success",
        "message": "Connection test not yet implemented",
        "url": cluster_data.url,
    }


# Security Configuration Endpoints
@app.get("/api/security/config")
async def get_security_config():
    """Get current security configuration."""
    async with db.session() as session:
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        config = result.scalar_one_or_none()

        if not config:
            # Return default configuration
            return {
                "edit_mode_enabled": False,
                "allowed_operations": [],
                "audit_logging": True,
            }

        return config.to_dict()


@app.put("/api/security/config")
async def update_security_config(config_data: SecurityConfigUpdate):
    """Update security configuration."""
    async with db.session() as session:
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        config = result.scalar_one_or_none()

        if not config:
            # Create new config
            config = SecurityConfig(
                edit_mode_enabled=config_data.edit_mode_enabled or False,
                allowed_operations=config_data.allowed_operations or [],
                audit_logging=config_data.audit_logging if config_data.audit_logging is not None else True,
            )
            session.add(config)
        else:
            # Update existing config
            if config_data.edit_mode_enabled is not None:
                config.edit_mode_enabled = config_data.edit_mode_enabled
            if config_data.allowed_operations is not None:
                config.allowed_operations = config_data.allowed_operations
            if config_data.audit_logging is not None:
                config.audit_logging = config_data.audit_logging

        await session.commit()
        await session.refresh(config)

        return config.to_dict()


@app.get("/api/security/edit-mode")
async def get_edit_mode():
    """Get current edit mode status."""
    async with db.session() as session:
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        config = result.scalar_one_or_none()

        return {
            "enabled": config.edit_mode_enabled if config else False
        }


@app.put("/api/security/edit-mode")
async def set_edit_mode(mode: EditModeUpdate):
    """Enable or disable edit mode."""
    async with db.session() as session:
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        config = result.scalar_one_or_none()

        if not config:
            config = SecurityConfig(edit_mode_enabled=mode.enabled)
            session.add(config)
        else:
            config.edit_mode_enabled = mode.enabled

        await session.commit()
        await session.refresh(config)

        return {"enabled": config.edit_mode_enabled}


# Audit Log Endpoints
@app.get("/api/audit", response_model=List[AuditLogResponse])
async def list_audit_logs(
    cluster_id: Optional[int] = Query(None),
    operation_id: Optional[str] = Query(None),
    http_method: Optional[str] = Query(None),
    status_min: Optional[int] = Query(None),
    status_max: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
):
    """List audit logs with optional filtering."""
    async with db.session() as session:
        # Join with clusters table to get cluster name and URL
        query = select(
            AuditLog,
            Cluster.name.label('cluster_name'),
            Cluster.url.label('cluster_url')
        ).outerjoin(
            Cluster, AuditLog.cluster_id == Cluster.id
        ).order_by(AuditLog.timestamp.desc())

        # Apply filters
        if cluster_id is not None:
            query = query.where(AuditLog.cluster_id == cluster_id)
        if operation_id:
            query = query.where(AuditLog.operation_id == operation_id)
        if http_method:
            query = query.where(AuditLog.http_method == http_method.upper())
        if status_min is not None:
            query = query.where(AuditLog.response_status >= status_min)
        if status_max is not None:
            query = query.where(AuditLog.response_status <= status_max)

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        rows = result.all()

        return [
            AuditLogResponse(
                id=row[0].id,
                cluster_id=row[0].cluster_id,
                cluster_name=row[1],
                cluster_url=row[2],
                user_id=row[0].user_id,
                operation_id=row[0].operation_id,
                http_method=row[0].http_method,
                path=row[0].path,
                request_body=row[0].request_body,
                response_status=row[0].response_status,
                response_body=row[0].response_body,
                error_message=row[0].error_message,
                client_ip=row[0].client_ip,
                timestamp=row[0].timestamp.isoformat(),
            )
            for row in rows
        ]


@app.get("/api/audit/export")
async def export_audit_logs(
    cluster_id: Optional[int] = Query(None),
    operation_id: Optional[str] = Query(None),
    http_method: Optional[str] = Query(None),
):
    """Export audit logs as CSV."""
    async with db.session() as session:
        # Join with clusters table to get cluster name and URL
        query = select(
            AuditLog,
            Cluster.name.label('cluster_name'),
            Cluster.url.label('cluster_url')
        ).outerjoin(
            Cluster, AuditLog.cluster_id == Cluster.id
        ).order_by(AuditLog.timestamp.desc())

        # Apply filters
        if cluster_id is not None:
            query = query.where(AuditLog.cluster_id == cluster_id)
        if operation_id:
            query = query.where(AuditLog.operation_id == operation_id)
        if http_method:
            query = query.where(AuditLog.http_method == http_method.upper())

        result = await session.execute(query)
        rows = result.all()

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Cluster Name", "Cluster URL", "User ID", "Operation ID", "HTTP Method",
            "Path", "Response Status", "Error Message", "Client IP", "Timestamp"
        ])

        # Write data
        for row in rows:
            writer.writerow([
                row[0].id,
                row[1],
                row[2],
                row[0].user_id,
                row[0].operation_id,
                row[0].http_method,
                row[0].path,
                row[0].response_status,
                row[0].error_message,
                row[0].client_ip,
                row[0].timestamp.isoformat(),
            ])

        # Return CSV as streaming response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )


@app.get("/api/audit/stats", response_model=AuditStatsResponse)
async def get_audit_stats():
    """Get audit log statistics."""
    async with db.session() as session:
        # Total count
        total_result = await session.execute(
            select(func.count()).select_from(AuditLog)
        )
        total = total_result.scalar() or 0

        # Successful count (2xx status)
        success_result = await session.execute(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.response_status >= 200,
                AuditLog.response_status < 300
            )
        )
        successful = success_result.scalar() or 0

        # Failed count (4xx or 5xx status or has error_message)
        failed_result = await session.execute(
            select(func.count()).select_from(AuditLog).where(
                (AuditLog.response_status >= 400) | (AuditLog.error_message.isnot(None))
            )
        )
        failed = failed_result.scalar() or 0

        # By method
        method_result = await session.execute(
            select(AuditLog.http_method, func.count()).
            group_by(AuditLog.http_method)
        )
        by_method = {method: count for method, count in method_result.all()}

        # By status
        status_result = await session.execute(
            select(AuditLog.response_status, func.count()).
            group_by(AuditLog.response_status)
        )
        by_status = {str(status): count for status, count in status_result.all() if status is not None}

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "by_method": by_method,
            "by_status": by_status,
        }


@app.get("/api/docs")
async def get_documentation():
    """Get the user guide documentation."""
    import os

    docs_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "USER_GUIDE.md")

    try:
        with open(docs_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Documentation file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading documentation: {str(e)}")


# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, response: Response):
    """Authenticate user and create session."""
    user = await user_service.authenticate(login_data.username, login_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create session
    token = await user_service.create_session(user)

    # Set session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=24 * 60 * 60,  # 24 hours
    )

    return {
        "token": token,
        "user": {
            **user.to_dict(),
            "has_edit_mode": user.has_edit_mode(),
        },
    }


@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Optional[str] = Cookie(None, alias=SESSION_COOKIE_NAME),
):
    """Logout current user and invalidate session."""
    if session_token:
        await user_service.invalidate_session(session_token)

    # Clear session cookie
    response.delete_cookie(key=SESSION_COOKIE_NAME)

    return {"message": "Logged out successfully"}


@app.get("/api/auth/me")
async def get_current_user_info(user: Optional[User] = Depends(get_current_user)):
    """Get current authenticated user information."""
    # Check if any users exist
    has_users = await user_service.has_any_users()

    if not has_users:
        # No users exist - return setup mode indicator
        return {
            "authenticated": False,
            "setup_required": True,
            "message": "No users configured. Create first admin user.",
        }

    if not user:
        return {
            "authenticated": False,
            "setup_required": False,
        }

    return {
        "authenticated": True,
        "setup_required": False,
        "user": {
            **user.to_dict(),
            "has_edit_mode": user.has_edit_mode(),
            "api_token": user.api_token,  # Include for Claude Desktop setup
        },
    }


@app.post("/api/auth/setup")
async def initial_setup(user_data: UserCreate, response: Response):
    """Create the first admin user (only works if no users exist)."""
    # Check if users already exist
    if await user_service.has_any_users():
        raise HTTPException(
            status_code=400,
            detail="Setup already completed. Users already exist."
        )

    try:
        # Create superuser
        user = await user_service.create_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            display_name=user_data.display_name,
            is_superuser=True,
            generate_api_token=True,
        )

        # Assign Administrator role if exists
        admin_role = await role_service.get_role_by_name("Administrator")
        if admin_role:
            await user_service.assign_roles(user.id, [admin_role.id])

        # Create session for auto-login
        token = await user_service.create_session(user)

        # Set session cookie
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=24 * 60 * 60,
        )

        # Reload user to get roles
        user = await user_service.get_user(user.id)

        return {
            "message": "Setup completed successfully",
            "token": token,
            "user": {
                **user.to_dict(),
                "has_edit_mode": user.has_edit_mode(),
                "api_token": user.api_token,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== User Management Endpoints ====================

@app.get("/api/users", response_model=List[UserResponse])
async def list_users(
    active_only: bool = Query(False),
    _user: User = Depends(require_auth),
):
    """List all users."""
    users = await user_service.list_users(active_only=active_only)

    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            display_name=u.display_name,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            auth_type=u.auth_type,
            last_login=u.last_login.isoformat() if u.last_login else None,
            created_at=u.created_at.isoformat(),
            updated_at=u.updated_at.isoformat(),
            roles=[r.to_dict(include_operations=False) for r in u.roles],
            has_edit_mode=u.has_edit_mode(),
        )
        for u in users
    ]


@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    _admin: User = Depends(require_superuser),
):
    """Create a new user (superuser only)."""
    try:
        user = await user_service.create_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            display_name=user_data.display_name,
            is_superuser=user_data.is_superuser,
            generate_api_token=True,
        )

        # Assign roles if provided
        if user_data.role_ids:
            user = await user_service.assign_roles(user.id, user_data.role_ids)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            auth_type=user.auth_type,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            roles=[r.to_dict(include_operations=False) for r in user.roles] if user.roles else [],
            has_edit_mode=user.has_edit_mode(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _user: User = Depends(require_auth),
):
    """Get user by ID."""
    user = await user_service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        auth_type=user.auth_type,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        roles=[r.to_dict(include_operations=False) for r in user.roles] if user.roles else [],
        has_edit_mode=user.has_edit_mode(),
    )


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    _admin: User = Depends(require_superuser),
):
    """Update user (superuser only)."""
    user = await user_service.update_user(
        user_id=user_id,
        email=user_data.email,
        display_name=user_data.display_name,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
        password=user_data.password,
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Reload to get roles
    user = await user_service.get_user(user_id)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        auth_type=user.auth_type,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        roles=[r.to_dict(include_operations=False) for r in user.roles] if user.roles else [],
        has_edit_mode=user.has_edit_mode(),
    )


@app.delete("/api/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    _admin: User = Depends(require_superuser),
):
    """Delete user (superuser only)."""
    deleted = await user_service.delete_user(user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return None


@app.put("/api/users/{user_id}/roles", response_model=UserResponse)
async def assign_user_roles(
    user_id: int,
    roles_data: AssignRolesRequest,
    _admin: User = Depends(require_superuser),
):
    """Assign roles to a user (superuser only)."""
    user = await user_service.assign_roles(user_id, roles_data.role_ids)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        auth_type=user.auth_type,
        last_login=user.last_login.isoformat() if user.last_login else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        roles=[r.to_dict(include_operations=False) for r in user.roles] if user.roles else [],
        has_edit_mode=user.has_edit_mode(),
    )


@app.post("/api/users/{user_id}/regenerate-token")
async def regenerate_user_token(
    user_id: int,
    current_user: User = Depends(require_auth),
):
    """Regenerate API token for a user (user themselves or superuser)."""
    # Users can regenerate their own token, or superusers can regenerate any
    if current_user and not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only regenerate your own token")

    new_token = await user_service.regenerate_api_token(user_id)

    if not new_token:
        raise HTTPException(status_code=404, detail="User not found")

    return {"api_token": new_token}


# ==================== Role Management Endpoints ====================

@app.get("/api/roles", response_model=List[RoleResponse])
async def list_roles(
    include_system: bool = Query(True),
    _user: User = Depends(require_auth),
):
    """List all roles."""
    roles = await role_service.list_roles(include_system=include_system)

    return [
        RoleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            edit_mode_enabled=r.edit_mode_enabled,
            is_system_role=r.is_system_role,
            operations_count=len(r.operations) if r.operations else 0,
            operations=[op.operation_name for op in r.operations] if r.operations else [],
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in roles
    ]


@app.post("/api/roles", response_model=RoleResponse, status_code=201)
async def create_role(
    role_data: RoleCreate,
    _admin: User = Depends(require_superuser),
):
    """Create a new role (superuser only)."""
    try:
        role = await role_service.create_role(
            name=role_data.name,
            description=role_data.description,
            edit_mode_enabled=role_data.edit_mode_enabled,
            operations=role_data.operations,
        )

        # Reload to get operations
        role = await role_service.get_role(role.id)

        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            edit_mode_enabled=role.edit_mode_enabled,
            is_system_role=role.is_system_role,
            operations_count=len(role.operations) if role.operations else 0,
            operations=[op.operation_name for op in role.operations] if role.operations else [],
            created_at=role.created_at.isoformat(),
            updated_at=role.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    _user: User = Depends(require_auth),
):
    """Get role by ID with operations."""
    role = await role_service.get_role(role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        edit_mode_enabled=role.edit_mode_enabled,
        is_system_role=role.is_system_role,
        operations_count=len(role.operations) if role.operations else 0,
        operations=[op.operation_name for op in role.operations] if role.operations else [],
        created_at=role.created_at.isoformat(),
        updated_at=role.updated_at.isoformat(),
    )


@app.put("/api/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    _admin: User = Depends(require_superuser),
):
    """Update role (superuser only)."""
    try:
        role = await role_service.update_role(
            role_id=role_id,
            name=role_data.name,
            description=role_data.description,
            edit_mode_enabled=role_data.edit_mode_enabled,
        )

        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Reload to get operations
        role = await role_service.get_role(role_id)

        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            edit_mode_enabled=role.edit_mode_enabled,
            is_system_role=role.is_system_role,
            operations_count=len(role.operations) if role.operations else 0,
            operations=[op.operation_name for op in role.operations] if role.operations else [],
            created_at=role.created_at.isoformat(),
            updated_at=role.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    _admin: User = Depends(require_superuser),
):
    """Delete role (superuser only, cannot delete system roles)."""
    try:
        deleted = await role_service.delete_role(role_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Role not found")

        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/roles/{role_id}/operations", response_model=RoleResponse)
async def set_role_operations(
    role_id: int,
    ops_data: SetRoleOperationsRequest,
    _admin: User = Depends(require_superuser),
):
    """Set operations for a role (replaces existing)."""
    role = await role_service.set_role_operations(role_id, ops_data.operations)

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        edit_mode_enabled=role.edit_mode_enabled,
        is_system_role=role.is_system_role,
        operations_count=len(role.operations) if role.operations else 0,
        operations=[op.operation_name for op in role.operations] if role.operations else [],
        created_at=role.created_at.isoformat(),
        updated_at=role.updated_at.isoformat(),
    )


# ==================== Operations Endpoints (for searchable dropdown) ====================

@app.get("/api/operations", response_model=OperationsListResponse)
async def list_operations(
    search: Optional[str] = Query(None, description="Search by operation name"),
    api_name: Optional[str] = Query(None, description="Filter by API (manage, analyze, infra, etc.)"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    _user: User = Depends(require_auth),
):
    """List available operations with search and filtering."""
    result = await role_service.get_all_available_operations(
        search=search,
        api_name=api_name,
        limit=limit,
        offset=offset,
    )

    return {
        "total": result["total"],
        "operations": [
            OperationResponse(
                name=op["name"],
                method=op["method"],
                path=op["path"],
                api_name=op["api_name"],
                description=op["description"],
            )
            for op in result["operations"]
        ],
    }


@app.get("/api/operations/grouped")
async def get_operations_grouped(
    _user: User = Depends(require_auth),
):
    """Get all operations grouped by API name."""
    grouped = await role_service.get_operations_by_api()
    return grouped


@app.get("/api/operations/api-names")
async def get_api_names(
    _user: User = Depends(require_auth),
):
    """Get list of unique API names."""
    api_names = await role_service.get_api_names()
    return {"api_names": api_names}


@app.get("/api/operations/count")
async def get_operations_count(
    _user: User = Depends(require_auth),
):
    """Get total count of available operations."""
    count = await role_service.count_operations()
    return {"total": count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
