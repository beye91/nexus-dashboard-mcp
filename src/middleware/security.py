"""Security middleware for enforcing read-only mode and edit permissions."""

import asyncio
import logging
from typing import Optional

from src.services.security_service import SecurityConfigService

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Middleware for security enforcement and access control.

    This middleware reads security configuration from the database,
    allowing dynamic control of edit mode without server restarts.
    """

    # Write operations that require edit mode
    WRITE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    # Read-only operations (always allowed)
    READ_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self):
        """Initialize security middleware."""
        self.security_service = SecurityConfigService()
        self._edit_mode_cache: Optional[bool] = None

    async def is_edit_mode_enabled(self) -> bool:
        """Check if edit mode is currently enabled.

        Reads from database with caching for performance.

        Returns:
            True if edit mode enabled, False otherwise
        """
        return await self.security_service.is_edit_mode_enabled(use_cache=True)

    def is_write_operation(self, method: str) -> bool:
        """Check if HTTP method is a write operation.

        Args:
            method: HTTP method to check

        Returns:
            True if write operation, False otherwise
        """
        return method.upper() in self.WRITE_METHODS

    def is_read_operation(self, method: str) -> bool:
        """Check if HTTP method is a read operation.

        Args:
            method: HTTP method to check

        Returns:
            True if read operation, False otherwise
        """
        return method.upper() in self.READ_METHODS

    async def check_operation_allowed(
        self,
        method: str,
        operation_id: Optional[str] = None,
        path: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Check if an operation is allowed based on security settings.

        Args:
            method: HTTP method
            operation_id: OpenAPI operation ID
            path: API endpoint path

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        method_upper = method.upper()

        # Read operations are always allowed
        if self.is_read_operation(method_upper):
            return True, None

        # Write operations require edit mode
        if self.is_write_operation(method_upper):
            edit_mode_enabled = await self.is_edit_mode_enabled()
            if not edit_mode_enabled:
                error_msg = (
                    f"Edit mode required for {method_upper} operations. "
                    f"Current mode: READ-ONLY. "
                    f"To enable write operations, update the security_config table in the database "
                    f"or use the Web UI to toggle edit mode."
                )
                logger.warning(
                    f"Blocked {method_upper} operation {operation_id or path}: "
                    f"Edit mode not enabled"
                )
                return False, error_msg

            # Edit mode is enabled, allow operation
            logger.info(
                f"Allowing {method_upper} operation {operation_id or path}: "
                f"Edit mode enabled"
            )
            return True, None

        # Unknown method - deny by default
        error_msg = f"Unsupported HTTP method: {method}"
        logger.error(f"Blocked operation with unsupported method: {method}")
        return False, error_msg

    async def enforce_security(
        self,
        method: str,
        operation_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        """Enforce security policy for an operation.

        Args:
            method: HTTP method
            operation_id: OpenAPI operation ID
            path: API endpoint path

        Raises:
            PermissionError: If operation is not allowed
        """
        allowed, error_message = await self.check_operation_allowed(
            method, operation_id, path
        )

        if not allowed:
            raise PermissionError(error_message)

    async def get_security_status(self) -> dict:
        """Get current security configuration status.

        Returns:
            Dictionary with security status information
        """
        edit_mode = await self.is_edit_mode_enabled()
        return {
            "edit_mode_enabled": edit_mode,
            "read_only_mode": not edit_mode,
            "allowed_read_methods": list(self.READ_METHODS),
            "blocked_write_methods": list(self.WRITE_METHODS)
            if not edit_mode
            else [],
        }

    async def refresh_config(self):
        """Force refresh of security configuration from database.

        Call this method if you need to ensure the latest config is loaded.
        """
        await self.security_service.refresh_cache()
        logger.info("Security configuration refreshed from database")
