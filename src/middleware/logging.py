"""Audit logging middleware for tracking all operations."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select

from src.config.database import get_db
from src.models import AuditLog, Cluster

logger = logging.getLogger(__name__)


class AuditLogger:
    """Middleware for audit logging of all operations."""

    def __init__(self, cluster_name: str = "default"):
        """Initialize audit logger.

        Args:
            cluster_name: Name of the cluster for audit logs
        """
        self.cluster_name = cluster_name
        self.db = get_db()

    async def get_cluster_id(self) -> Optional[int]:
        """Get cluster ID from default cluster name.

        Returns:
            Cluster ID or None if not found
        """
        return await self._get_cluster_id_by_name(self.cluster_name)

    async def _get_cluster_id_by_name(self, cluster_name: str) -> Optional[int]:
        """Get cluster ID from cluster name.

        Args:
            cluster_name: Name of the cluster to look up

        Returns:
            Cluster ID or None if not found
        """
        async with self.db.session() as session:
            result = await session.execute(
                select(Cluster.id).where(Cluster.name == cluster_name)
            )
            cluster_id = result.scalar_one_or_none()
            return cluster_id

    async def log_operation(
        self,
        method: str,
        path: str,
        operation_id: Optional[str] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        cluster_name: Optional[str] = None,
    ):
        """Log an operation to the audit log.

        Args:
            method: HTTP method
            path: API endpoint path
            operation_id: OpenAPI operation ID
            request_body: Request body as dict
            response_status: HTTP response status code
            response_body: Response body as dict
            error_message: Error message if operation failed
            user_id: User identifier (if available)
            client_ip: Client IP address (if available)
            cluster_name: Name of the cluster used (overrides default)
        """
        try:
            # Use provided cluster_name or fall back to default
            lookup_name = cluster_name or self.cluster_name
            cluster_id = await self._get_cluster_id_by_name(lookup_name)

            async with self.db.session() as session:
                audit_entry = AuditLog(
                    cluster_id=cluster_id,
                    user_id=user_id,
                    client_ip=client_ip,
                    operation_id=operation_id,
                    http_method=method.upper(),
                    path=path,
                    request_body=request_body,
                    response_status=response_status,
                    response_body=response_body,
                    error_message=error_message,
                )

                session.add(audit_entry)
                await session.commit()

                # Log to application logger as well
                user_info = f" [user: {user_id}]" if user_id else ""
                if error_message:
                    logger.error(
                        f"Audit: {method} {path}{user_info} - Error: {error_message}"
                    )
                elif response_status:
                    logger.info(
                        f"Audit: {method} {path}{user_info} - Status: {response_status}"
                    )
                else:
                    logger.info(f"Audit: {method} {path}{user_info} - Logged")

        except Exception as e:
            # Don't let audit logging failures break the application
            logger.error(f"Failed to write audit log: {e}", exc_info=True)

    async def get_recent_logs(
        self,
        limit: int = 100,
        operation_id: Optional[str] = None,
        method: Optional[str] = None,
    ) -> list[AuditLog]:
        """Get recent audit log entries.

        Args:
            limit: Maximum number of entries to return
            operation_id: Filter by operation ID
            method: Filter by HTTP method

        Returns:
            List of AuditLog instances
        """
        async with self.db.session() as session:
            query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

            if operation_id:
                query = query.where(AuditLog.operation_id == operation_id)

            if method:
                query = query.where(AuditLog.http_method == method.upper())

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_error_logs(self, limit: int = 50) -> list[AuditLog]:
        """Get recent error log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of AuditLog instances with errors
        """
        async with self.db.session() as session:
            query = (
                select(AuditLog)
                .where(AuditLog.error_message.isnot(None))
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics.

        Returns:
            Dictionary with statistics about logged operations
        """
        from sqlalchemy import func

        async with self.db.session() as session:
            # Total operations
            total_result = await session.execute(
                select(func.count(AuditLog.id))
            )
            total_operations = total_result.scalar()

            # Operations by method
            method_result = await session.execute(
                select(AuditLog.http_method, func.count(AuditLog.id))
                .group_by(AuditLog.http_method)
            )
            operations_by_method = {
                method: count for method, count in method_result.fetchall()
            }

            # Success vs error count
            success_result = await session.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.response_status.between(200, 299))
            )
            success_count = success_result.scalar() or 0

            error_result = await session.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.error_message.isnot(None))
            )
            error_count = error_result.scalar() or 0

            return {
                "total_operations": total_operations or 0,
                "operations_by_method": operations_by_method,
                "successful_operations": success_count,
                "failed_operations": error_count,
                "success_rate": (success_count / total_operations * 100)
                if total_operations
                else 0,
            }
