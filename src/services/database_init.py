"""Database initialization service for default data."""

import logging

from sqlalchemy import select

from src.config.database import get_db
from src.models.security import SecurityConfig

logger = logging.getLogger(__name__)


async def initialize_security_config():
    """Initialize default security configuration if none exists.

    This ensures that the security_config table has at least one row
    so the MCP server can read edit_mode settings from the database.
    """
    db = get_db()

    async with db.session() as session:
        # Check if any security config exists
        result = await session.execute(
            select(SecurityConfig).limit(1)
        )
        existing_config = result.scalar_one_or_none()

        if existing_config:
            logger.info("Security configuration already exists in database")
            logger.info(f"Edit mode: {existing_config.edit_mode_enabled}")
            return existing_config

        # Create default security configuration
        default_config = SecurityConfig(
            edit_mode_enabled=False,  # Start with read-only mode for safety
            audit_logging=True,       # Enable audit logging by default
            allowed_operations=[]     # No specific operation restrictions
        )

        session.add(default_config)
        await session.commit()
        await session.refresh(default_config)

        logger.info("Created default security configuration:")
        logger.info(f"  - Edit mode: {default_config.edit_mode_enabled}")
        logger.info(f"  - Audit logging: {default_config.audit_logging}")
        logger.info("  - Update via Web UI or database to enable write operations")

        return default_config


async def initialize_database_defaults():
    """Initialize all default database records.

    This function is called during database initialization to ensure
    required default data exists.
    """
    logger.info("Initializing database default values...")

    # Initialize security configuration
    await initialize_security_config()

    logger.info("Database initialization completed")
