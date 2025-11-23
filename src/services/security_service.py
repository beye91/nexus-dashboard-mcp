"""Security configuration service for database-driven security settings."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select

from src.config.database import get_db
from src.models.security import SecurityConfig

logger = logging.getLogger(__name__)


class SecurityConfigService:
    """Service for managing security configuration from database."""

    # Cache configuration for 30 seconds to reduce database queries
    CACHE_TTL_SECONDS = 30

    def __init__(self):
        """Initialize security configuration service."""
        self.db = get_db()
        self._cached_config: Optional[SecurityConfig] = None
        self._cache_timestamp: Optional[datetime] = None

    async def get_security_config(self, use_cache: bool = True) -> SecurityConfig:
        """Get security configuration from database.

        Args:
            use_cache: If True, return cached config if available and fresh

        Returns:
            SecurityConfig instance

        Raises:
            RuntimeError: If no security configuration exists in database
        """
        # Check cache if enabled
        if use_cache and self._is_cache_valid():
            logger.debug("Returning cached security configuration")
            return self._cached_config

        # Fetch from database
        async with self.db.session() as session:
            result = await session.execute(
                select(SecurityConfig).order_by(SecurityConfig.id.desc()).limit(1)
            )
            config = result.scalar_one_or_none()

            if not config:
                # Create default security config if none exists
                logger.warning("No security configuration found in database, creating default")
                config = SecurityConfig(
                    edit_mode_enabled=False,
                    audit_logging=True,
                    allowed_operations=[]
                )
                session.add(config)
                await session.commit()
                await session.refresh(config)
                logger.info("Created default security configuration (edit_mode=False)")

            # Update cache
            self._cached_config = config
            self._cache_timestamp = datetime.now()

            logger.debug(f"Loaded security config from database: edit_mode={config.edit_mode_enabled}")
            return config

    async def is_edit_mode_enabled(self, use_cache: bool = True) -> bool:
        """Check if edit mode is currently enabled.

        Args:
            use_cache: If True, use cached config if available

        Returns:
            True if edit mode enabled, False otherwise
        """
        config = await self.get_security_config(use_cache=use_cache)
        return config.edit_mode_enabled

    async def set_edit_mode(self, enabled: bool) -> SecurityConfig:
        """Enable or disable edit mode.

        Args:
            enabled: True to enable edit mode, False to disable

        Returns:
            Updated SecurityConfig instance
        """
        async with self.db.session() as session:
            # Get or create config
            result = await session.execute(
                select(SecurityConfig).order_by(SecurityConfig.id.desc()).limit(1)
            )
            config = result.scalar_one_or_none()

            if not config:
                config = SecurityConfig(
                    edit_mode_enabled=enabled,
                    audit_logging=True,
                    allowed_operations=[]
                )
                session.add(config)
            else:
                config.edit_mode_enabled = enabled

            await session.commit()
            await session.refresh(config)

            # Invalidate cache
            self._invalidate_cache()

            logger.info(f"Edit mode {'enabled' if enabled else 'disabled'} via database")
            return config

    async def get_audit_logging_enabled(self, use_cache: bool = True) -> bool:
        """Check if audit logging is enabled.

        Args:
            use_cache: If True, use cached config if available

        Returns:
            True if audit logging enabled, False otherwise
        """
        config = await self.get_security_config(use_cache=use_cache)
        return config.audit_logging

    def _is_cache_valid(self) -> bool:
        """Check if cached configuration is still valid.

        Returns:
            True if cache is valid, False otherwise
        """
        if self._cached_config is None or self._cache_timestamp is None:
            return False

        age = datetime.now() - self._cache_timestamp
        return age < timedelta(seconds=self.CACHE_TTL_SECONDS)

    def _invalidate_cache(self):
        """Invalidate the configuration cache."""
        self._cached_config = None
        self._cache_timestamp = None
        logger.debug("Security configuration cache invalidated")

    async def refresh_cache(self):
        """Force refresh of cached configuration.

        Returns:
            Updated SecurityConfig instance
        """
        logger.debug("Forcing security configuration cache refresh")
        return await self.get_security_config(use_cache=False)
