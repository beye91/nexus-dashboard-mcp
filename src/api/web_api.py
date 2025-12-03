"""FastAPI web application for Nexus Dashboard MCP Server management UI."""

import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
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
from src.services.credential_manager import CredentialManager
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


# Initialize services
credential_manager = CredentialManager()
settings = get_settings()
db = get_db()

# Global startup time for uptime calculation
startup_time = datetime.utcnow()


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
